import os
from dotenv import load_dotenv
from transformers import AutoTokenizer
from langchain_huggingface import HuggingFaceEndpoint
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
import yaml

load_dotenv()


def get_huggingface_llm():
    llm= HuggingFaceEndpoint(
        repo_id="microsoft/Phi-3-mini-4k-instruct",
        task="chat-completion",
        max_new_tokens=512,
        do_sample=False,
        repetition_penalty=1.03,
        huggingfacehub_api_token=os.getenv("HUGGINGFACE_API_KEY"),
    )
    return  ChatHuggingFace(llm=llm, verbose=True)

def load_system_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), "..","prompts", "system_prompt.yaml")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
