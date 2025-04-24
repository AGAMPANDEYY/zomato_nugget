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
from fastapi.middleware.cors import CORSMiddleware


# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get base directory (directory of the current script)
BASE_DIR = Path(__file__).parent

# Mount static files (CSS, JS, etc.)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory=BASE_DIR / "templates")


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
            print("Hybrid RAG Results:\n", results)

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
    return templates.TemplateResponse(request, "index.html")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    """Handle chat requests and return responses"""
    logger.debug(" Chat endpoint hit!")

    user_msg = payload.message
    history = payload.history or []
    user_query = user_msg
    session_id=str(uuid.uuid4())
    user_id="agampandey"
   
    langchain_agent=LangchainReactAgent(session_id).get_agent()

    response = query_with_observability(langchain_agent,user_query, session_id,user_id)

    logger.debug(f"Received message: {user_msg}")
    history.append(ChatHistoryEntry(role="user", content=user_msg))

    history.append(ChatHistoryEntry(role="assistant", content=response))

    instrumentor.flush()

    return ChatResponse(response=response, history=history)



# For local development
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

#uvicorn app.api.app:app --host 0.0.0.0 --port 5000 --reload