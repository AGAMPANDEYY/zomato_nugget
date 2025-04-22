import os
from dotenv import load_dotenv
from transformers import AutoTokenizer
from langchain_huggingface import HuggingFaceEndpoint
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
import yaml

load_dotenv()

def get_huggingface_llm():
    llm= HuggingFaceEndpoint(
        repo_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0", #"bitext/Mistral-7B-Restaurants", 
        temperature= 0.3, 
        huggingfacehub_api_token=os.getenv("HUGGINGFACE_API_KEY")
    )
    return  ChatHuggingFace(llm=llm)

def load_system_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), "..","prompts", "system_prompt.yaml")
    with open(prompt_path, "r") as f:
        return yaml.safe_load(f)
