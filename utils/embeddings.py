from langchain_huggingface import HuggingFaceEmbeddings
from huggingface_hub import InferenceClient
import os 

from dotenv import load_dotenv

load_dotenv()

HF_TOKEN= os.getenv("HUGGINGFACE_API_KEY")

def create_embeddings_hf(user_query):
    client = InferenceClient(token=HF_TOKEN)

    embed_model = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3")
    vector = embed_model.embed_query(user_query)
    return vector

# In utils/embeddings.py
def create_embeddings(text: str):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")  # 80MB model
    return model.encode(text)


