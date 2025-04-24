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
from transformers import AutoModelForSequenceClassification
from langchain_huggingface import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
from huggingface_hub import InferenceClient
from flashrank import Ranker, RerankRequest
import torch
from bs4 import BeautifulSoup
import re
import os 

from dotenv import load_dotenv
from langchain_agent.llm.huggingface_llm import get_huggingface_llm, load_system_prompt
from langchain_core.messages import HumanMessage
from langchain_core.messages import AIMessage


load_dotenv()

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

def clean_html(text: str) -> str:
    """Strip HTML/JS/CSS and collapse whitespace."""
    # remove scripts/styles
    soup = BeautifulSoup(text, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    cleaned = soup.get_text(separator=" ", strip=True)
    # collapse any long run of whitespace/newlines into single spaces
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned

def refine_rag_results(raw_results, max_chars=300):
    """
    1. Clean each raw HTML/text block
    2. Dedupe identical snippets
    3. Truncate to max_chars with an ellipsis
    """
    seen = set()
    refined = []
    for item in raw_results:
        text = clean_html(item)
        if not text or text in seen:
            continue
        seen.add(text)
        if len(text) > max_chars:
            text = text[: max_chars].rsplit(" ", 1)[0] + "…"
        refined.append(text)
    return refined


instrumentor = setup_instrumentor()

def query_with_observability(agent_executor, user_query: str,session_id,user_id, reranker, embed_model):
    with instrumentor.observe(trace_id=f"agent-{uuid.uuid4()}", session_id=session_id,
                               user_id='user-id', metadata={"app_version": "1.0"}) as trace:
        try:
            # preprocessing step

            processed_query, entities = preprocess_query(user_query)
            print(f" Processed query is {processed_query}")
     
            # Get embeddings for processed query
            #query_embeddings = create_embeddings(processed_query)
            #query_embeddings = embed_model.embed_query(user_query)
            query_embeddings = embed_model.encode(processed_query)

            hybrid_rag=HybridRAG()
            # Retrieve with processed query and its embeddings
            results = hybrid_rag.query_hybrid(processed_query, query_embeddings, reranker= reranker, limit=5)
            print("Hybrid RAG Results:\n", results)

            hybrid_rag.close()

            raw_results = results  # your list of long HTML/text strings
            snippets = refine_rag_results(raw_results, max_chars=200) 

            # stringify the top-k passages into a context block
            context_block = "\n".join(f"{i+1}. {s}" for i, s in enumerate(snippets))
            # build one prompt that includes both RAG context and the question
            system_prompt=load_system_prompt()[0]["content"]
            full_input = (
                #f"{system_prompt}"
                f"Relevant passages to go through it and answer the user query after this below:\n{context_block}\n\n"
                f"User question:\n{user_query}"
                
            )

            config= {"configurable": {"thread_id": session_id}}

            response=[]
            total_tokens=0
            input_tokens=0
            output_tokens=0
    
            for step in agent_executor.stream({"messages": [HumanMessage(content=full_input)]}, config, stream_mode="values"):      
                
                for msg in step["messages"]:
                    response.append(msg.content)

                    if "usage_metadata" in msg:
                        total_tokens = msg["usage_metadata"].get("total_tokens", 0)
                        input_tokens = msg["usage_metadata"].get("input_tokens", 0)
                        output_tokens = msg["usage_metadata"].get("output_tokens", 0)
            
            # Combine the partial responses
            final_response = "".join(response[-1])    


            trace.score(name="query_success", value=1.0)
            trace.score(name="relevance", value=0.95)
            trace.score(name="response_quality", value=0.88)
            trace.update(user_id=user_id,session_id=session_id, input=user_query, output=final_response,tokens=total_tokens) 
             
            trace.update(metadata={
                "session_id": session_id,
                "original_query": user_query,
                "processed_query": processed_query,
                "entities": entities,
                "agent_response": final_response
            })
            return final_response
        
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


langchain_agent = None
reranker = None
embed_model = None

@app.on_event("startup")
def load_model():
    session_id=str(uuid.uuid4())
    user_id="agampandey"
    global langchain_agent
    # Initialize the Langchain agent with a unique session ID
    langchain_agent=LangchainReactAgent(session_id).get_agent()
    global reranker
    """
    Due to the CPU and app load limitation and slow process
    we are now using FlashRank lightweight pairwise reranker

    # Load the reranker model
    reranker = AutoModelForSequenceClassification.from_pretrained(
            'BAAI/bge-reranker-base',
            torch_dtype=torch.float16,
            device_map="auto", 
            trust_remote_code=True,
        )
    """
  
    reranker = Ranker(max_length=128)
  
    global embed_model
    HF_TOKEN= os.getenv("HUGGINGFACE_API_KEY")

    """
    client = InferenceClient(token=HF_TOKEN)

    embed_model = HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3")
    """
    embed_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")  # 80MB model
    

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
    global langchain_agent
    global reranker
    global embed_model
    response = query_with_observability(langchain_agent,user_query, session_id,user_id, reranker, embed_model)
    
    logger.debug(f"Received message: {user_msg}")
    history.append(ChatHistoryEntry(role="user", content=user_msg))

    history.append(ChatHistoryEntry(role="assistant", content=response))

    instrumentor.flush()

    return ChatResponse(response=response, history=history)



# For local development
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

#uvicorn app.api.app:app --host 0.0.0.0 --port 5000 --reload