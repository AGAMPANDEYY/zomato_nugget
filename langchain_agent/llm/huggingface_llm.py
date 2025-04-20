import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEndpoint
import yaml

load_dotenv()

def get_huggingface_llm():
    return HuggingFaceEndpoint(
        repo_id="bitext/Mistral-7B-Restaurants",
        model_kwargs={"temperature": 0.3, "max_length": 512},
        huggingfacehub_api_token=os.getenv("HUGGINGFACE_API_KEY")
    )

def load_system_prompt():
    with open("prompts/system_prompt.yaml", "r") as f:
        return yaml.safe_load(f)
