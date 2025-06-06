
# 3. Initialize embedding model
from langchain_huggingface import HuggingFaceEmbeddings
from huggingface_hub import InferenceClient

client = InferenceClient()
"""
embed_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3")
"""

from sentence_transformers import SentenceTransformer
embed_model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")  # 80MB model

def generate_embeddings(text, metadata):
    embeddings = []
    vector = embed_model.encode(text)
    embeddings.append({
        "id": f"{metadata['restaurant_name']}_{metadata['url']}_{hash(text)}",
        "vector": vector,
        "metadata": metadata
    })
    return embeddings