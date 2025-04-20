
# 3. Initialize embedding model
from langchain_huggingface import HuggingFaceEmbeddings

embed_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={"encode_kwargs": {"batch_size": 32}}  # Optimize for throughput
)


def generate_embeddings(text, metadata):
    embeddings = []
    vector = embed_model.embed_query(text)
    embeddings.append({
        "id": f"{metadata['source']}_{metadata['url']}_{hash(text)}",
        "vector": vector,
        "metadata": metadata
    })
    return embeddings