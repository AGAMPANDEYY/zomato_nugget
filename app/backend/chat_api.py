import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from main_chat import get_response  # adapt your entry point
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "*")],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: list[list[str]] = []

class ChatResponse(BaseModel):
    reply: str
    history: list[list[str]]

@app.post('/chat', response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        reply, new_history = get_response(req.message, req.history)
        return ChatResponse(reply=reply, history=new_history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))