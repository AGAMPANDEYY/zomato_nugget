import os
import logging
from typing import List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pathlib import Path

import json
from observability.setup_observer import setup_instrumentor
from retrieval.hybridrag import HybridRAG
from utils.embeddings import create_embeddings
from utils.query_processor import preprocess_query
from langchain_agent.agents.agent_initializer import LangchainReactAgent
from llama_index.core import global_handler
import uuid
 

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()


# Get base directory (directory of the current script)
BASE_DIR = Path(__file__).parent

# Mount static files (CSS, JS, etc.)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# Mock restaurant data
RESTAURANT_DATA = {
    "Happy Burger": {
        "location": "123 Main St",
        "cuisine": "American",
        "price_range": "$$ (10-25)",
        "vegetarian": "Limited options",
        "vegan": "Few options",
        "gluten_free": "Available for some items",
        "menu": {
            "appetizers": [
                {"name": "Cheese Sticks", "price": "$7.99", "vegetarian": True, "gluten_free": False},
                {"name": "Nachos", "price": "$9.99", "vegetarian": True, "gluten_free": True, "spice_level": "Medium"},
                {"name": "Wings", "price": "$10.99", "vegetarian": False, "gluten_free": True, "spice_level": "Hot"}
            ],
            "mains": [
                {"name": "Classic Burger", "price": "$12.99", "vegetarian": False, "gluten_free": False},
                {"name": "Veggie Burger", "price": "$11.99", "vegetarian": True, "gluten_free": False},
                {"name": "Beyond Meat Burger", "price": "$14.99", "vegetarian": True, "vegan": True, "gluten_free": False}
            ],
            "desserts": [
                {"name": "Ice Cream", "price": "$5.99", "vegetarian": True, "gluten_free": True},
                {"name": "Chocolate Cake", "price": "$6.99", "vegetarian": True, "gluten_free": False}
            ]
        }
    },
    "Spice Garden": {
        "location": "456 Elm St",
        "cuisine": "Indian",
        "price_range": "$$ (15-30)",
        "vegetarian": "Extensive options",
        "vegan": "Many options",
        "gluten_free": "Most dishes are gluten-free",
        "menu": {
            "appetizers": [
                {"name": "Samosas", "price": "$6.99", "vegetarian": True, "gluten_free": False, "spice_level": "Mild"},
                {"name": "Pakoras", "price": "$7.99", "vegetarian": True, "vegan": True, "gluten_free": True, "spice_level": "Mild"}
            ],
            "mains": [
                {"name": "Butter Chicken", "price": "$16.99", "vegetarian": False, "gluten_free": True, "spice_level": "Medium"},
                {"name": "Chana Masala", "price": "$14.99", "vegetarian": True, "vegan": True, "gluten_free": True, "spice_level": "Medium"},
                {"name": "Lamb Vindaloo", "price": "$18.99", "vegetarian": False, "gluten_free": True, "spice_level": "Very Hot"}
            ],
            "desserts": [
                {"name": "Gulab Jamun", "price": "$5.99", "vegetarian": True, "gluten_free": False},
                {"name": "Kheer", "price": "$4.99", "vegetarian": True, "gluten_free": True}
            ]
        }
    },
    "Tandoor Palace": {
        "location": "789 Oak St",
        "cuisine": "Indian",
        "price_range": "$$$ (20-40)",
        "vegetarian": "Many options",
        "vegan": "Several options",
        "gluten_free": "Most dishes available",
        "menu": {
            "appetizers": [
                {"name": "Vegetable Samosas", "price": "$7.99", "vegetarian": True, "vegan": True, "gluten_free": False, "spice_level": "Mild"},
                {"name": "Chicken Tikka", "price": "$10.99", "vegetarian": False, "gluten_free": True, "spice_level": "Medium"}
            ],
            "mains": [
                {"name": "Chicken Tikka Masala", "price": "$17.99", "vegetarian": False, "gluten_free": True, "spice_level": "Medium"},
                {"name": "Palak Paneer", "price": "$15.99", "vegetarian": True, "gluten_free": True, "spice_level": "Mild"},
                {"name": "Lamb Rogan Josh", "price": "$19.99", "vegetarian": False, "gluten_free": True, "spice_level": "Hot"}
            ],
            "desserts": [
                {"name": "Ras Malai", "price": "$6.99", "vegetarian": True, "gluten_free": True},
                {"name": "Kulfi", "price": "$5.99", "vegetarian": True, "gluten_free": True}
            ]
        }
    }
}

# Function to generate responses
def generate_restaurant_response(query: str) -> str:
    query = query.lower()
    if "vegetarian" in query:
        if "best" in query or "most" in query:
            return "Spice Garden has the most extensive vegetarian options among our restaurants. They offer many dishes like Chana Masala and Palak Paneer that are fully vegetarian."
        for name, data in RESTAURANT_DATA.items():
            if name.lower() in query:
                return f"{name} offers {data['vegetarian']} vegetarian options on their menu."
    if "gluten" in query:
        for name, data in RESTAURANT_DATA.items():
            if name.lower() in query:
                return f"{name} {data['gluten_free']} on their menu."
    if "price" in query or "expensive" in query or "cost" in query:
        for name, data in RESTAURANT_DATA.items():
            if name.lower() in query:
                return f"{name}'s price range is {data['price_range']}."
    if "spice" in query and "compare" in query and "tandoor palace" in query and "spice garden" in query:
        return "Both restaurants offer similar spice levels. Spice Garden's Lamb Vindaloo is rated 'Very Hot', while Tandoor Palace's Lamb Rogan Josh is rated 'Hot'."
    return "I can help with restaurant info. Please ask about Happy Burger, Spice Garden, or Tandoor Palace."


instrumentor = setup_instrumentor()

def query_with_observability(agent, user_query: str,session_id,user_id):
    with instrumentor.observe(trace_id=f"agent-{uuid.uuid4()}", session_id=session_id,
                               user_id='user-id', metadata={"app_version": "1.0"}) as trace:
        try:
            # preprocessing step

            processed_query, entities = preprocess_query(user_query)
            print(f" Processed query is {processed_query}")
     
            # Get embeddings for processed query
            query_embeddings = create_embeddings(processed_query)
            hybrid_rag=HybridRAG()
            # Retrieve with processed query and its embeddings
            results = hybrid_rag.query_hybrid(processed_query, query_embeddings)
            hybrid_rag.close()
            response = agent.invoke({"input": user_query, "context": results})['output']
            
            trace.score(name="query_success", value=1.0)
            trace.score(name="relevance", value=0.95)
            trace.score(name="response_quality", value=0.88)
            trace.update(user_id=user_id,session_id=session_id, input=user_query, ouput=response)

            trace.update(metadata={
                "session_id": session_id,
                "original_query": user_query,
                "processed_query": processed_query,
                "entities": entities,
                "agent_response": response
            })
            return response
        
        except Exception as e:
            trace.score(name="query_error", value=0.0)
            raise e
        finally:
            instrumentor.flush()

# Pydantic models
class ChatHistoryEntry(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatHistoryEntry]] = []

class ChatResponse(BaseModel):
    response: str
    history: List[ChatHistoryEntry]

# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page with chat interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    """Handle chat requests and return responses"""
    user_msg = payload.message
    history = payload.history or []
    user_query = user_msg
    session_id=str(uuid.uuid4())
    user_id="agampandey"
   
    langchain_agent=LangchainReactAgent(session_id).get_agent()

    response = query_with_observability(langchain_agent,user_query, session_id,user_id)

    logger.debug(f"Received message: {user_msg}")
    history.append(ChatHistoryEntry(role="user", content=user_msg))

    answer = generate_restaurant_response(user_msg)
    history.append(ChatHistoryEntry(role="assistant", content=answer))

    instrumentor.flush()

    return response


# For local development
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)