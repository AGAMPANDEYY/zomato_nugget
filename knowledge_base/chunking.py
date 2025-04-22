import re
import json
import requests
import numpy as np
import networkx as nx
from itertools import combinations
from typing import List, Dict, Any
from PIL import Image
from dotenv import load_dotenv
import os
from sklearn.feature_extraction.text import TfidfVectorizer

from langchain.text_splitter import RecursiveCharacterTextSplitter, HTMLHeaderTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from huggingface_hub import InferenceClient


load_dotenv()
HUGGINGFACE_API_KEY= os.getenv("HUGGINGFACE_API_KEY")

# --- Models and Utilities ---
# Text splitters
char_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
hier_splitter = HTMLHeaderTextSplitter(headers_to_split_on=[("h1","Header 1"), ("h2", "Header 2"), ("h3", "Header 3")])

# Embedding model for semantic splitting or later use
embed_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")


# Hugging Face Inference client (uses HF_TOKEN env var)
client = InferenceClient( token =HUGGINGFACE_API_KEY)

# At top of chunking.py, define which keys become metadata:
META_KEYS = ["id", "scraper_name", "restaurant_name", "base_url", "url", "timestamp"]

def extract_image_urls(markdown_text: str) -> list:
    """
    Extract image URLs from markdown text.
    This looks for images with syntax like:
      ![alt text](url)
      and also standalone links using [](url) if needed.
    """
    # Pattern for markdown images: ![...](url)
    pattern_img = r'!\[.*?\]\((.*?)\)'
    urls = re.findall(pattern_img, markdown_text)
    
    # If you need to also capture links without image marker, uncomment:
    # pattern_link = r'\[.*?\]\((https?://[^\)]+)\)'
    # urls += re.findall(pattern_link, markdown_text)
    
    # Remove duplicates (if any)
    return list(set(urls))



def make_metadata(record: dict) -> dict:
    """Extract only the fields we want to carry forward into each chunk's metadata."""
    metadata = {k: record[k] for k in META_KEYS if k in record}
    markdown_text = record.get("markdown", "")
    metadata["image_urls"] = extract_image_urls(markdown_text)
    return metadata

# --- 1. Semantic Chunking ---
def semantic_menu_chunking(record: dict) -> List[Dict[str, Any]]:
    text = record.get("markdown", "")
    metadata = make_metadata(record) 
    sections = re.split(r"(?:^|\n)(#{1,3})\s+", text)
    chunks: List[Dict[str, Any]] = []
    for sec in sections:
        for sub in char_splitter.split_text(sec):
            chunks.append({"text": sub, "metadata": metadata})
    print(f"Semantic menu chunking done.")
    return chunks

# --- 2. LLM-Guided Chunking via Hugging Face API ---
CHUNK_PROMPT = (
    "You are a document chunker. Split the following text into chunks of approximately 200 words, preserving sentence boundaries. "
    "Output a JSON object with key \"chunks\" mapping to a list of text chunks.\n\nText:\n{text}"
)

def llm_guided_chunking(record: dict,llm= None) -> List[Dict[str, Any]]:
    text = record.get("text", "")
    metadata = record.get("metadata", {})
    # Call HF Inference API
    response = client.text_generation(
        model="gpt2",
        prompt=CHUNK_PROMPT.format(text=text),
        max_new_tokens= 512
    )
    raw = response
    try:
        data = json.loads(raw)
        chunks = data.get("chunks", [])
    except json.JSONDecodeError:
        return []
    print(f"LLM Guiding chunking done.")
    return [{"text": c, "metadata": metadata} for c in chunks]

# --- 3. Hierarchical Chunking ---
def hierarchical_chunking(record: dict) -> List[Dict[str, Any]]:
    html =  record.get("html", "") 
    metadata = make_metadata(record)
    docs = hier_splitter.split_text(html)  # returns List[Document]
    out: List[Dict[str, Any]] = []

    for doc in docs:
        # Get the raw text from the Document
        if hasattr(doc, "page_content"):
            content = doc.page_content
        elif isinstance(doc, str):
            content = doc
        else:
            # Fallback if your splitter returns something else
            content = str(doc)

        md = metadata.copy()
        # Now run regex over the string
        md["prices"] = re.findall(r"(?:₹|Rs\.?\s*)\d+", content)
        md["diet"]   = [t for t in ("vegetarian", "gluten-free") if t in content.lower()]
        out.append({"text": content, "metadata": md})

    print(f"Hierarchical chunking done. Produced {len(out)} chunks.")
    return out


# --- 4. Multimodal Chunking & Image Embedding ---
def multimodal_chunking(record: dict) -> List[Dict[str, Any]]:
    text = record.get("markdown", "")
    metadata = make_metadata(record)
    images = metadata.get("image_urls", {})
    chunks: List[Dict[str, Any]] = []
    # Process each image alongside text
    for url in images:
        try:
            img = Image.open(requests.get(url, stream=True).raw).convert("RGB")
            # Simple BLIP captioning
            from transformers import BlipProcessor, BlipForConditionalGeneration
            proc = BlipProcessor.from_pretrained("Salesforce/blip2-opt-2.7b")
            blip = BlipForConditionalGeneration.from_pretrained("Salesforce/blip2-opt-2.7b")
            inputs = proc(images=img, return_tensors="pt")
            cap = blip.generate(**inputs)
            caption = proc.decode(cap[0], skip_special_tokens=True)
            fused = f"{text}\nVisual: {caption}"
        except Exception:
            fused = text
        chunks.append({"text": fused, "metadata": metadata})
    print(f"Multimodal chunking done.")
    return chunks

# --- 5. Entropy-Based Chunking ---
def entropy_based_chunking(record: dict, splitter_func=None):
    text = record.get("markdown", "")
    metadata= make_metadata(record)

    # If text is empty, just return it as one chunk
    if not text.strip():
        return [{"text": text, "metadata": metadata}]

    try:
        # Try computing TF-IDF to get an entropy score
        vec = TfidfVectorizer().fit_transform([text])
        entropy = -np.sum(vec.data * np.log(vec.data + 1e-12))
    except ValueError:
        # Empty vocabulary: fall back to a single chunk
        return [{"text": text, "metadata": metadata}]

    # If the text is very low‑entropy, no need to split
    if entropy < 2.0:
        return [{"text": text, "metadata": metadata}]

    # Otherwise, split using the provided splitter (default to char splitter)
    splitter = splitter_func or char_splitter.split_text
    return [{"text": chunk, "metadata": metadata} for chunk in splitter(text)]

# --- 6. Graph-Based Chunking ---
def extract_dish_name(chunk_text: str) -> str:
    m = re.search(r"Name:\s*([^\n]+)", chunk_text)
    return m.group(1).strip() if m else "Unknown"

def similarity(chunk1: dict, chunk2: dict) -> float:
    tokens1 = set(chunk1.get("text", "").split())
    tokens2 = set(chunk2.get("text", "").split())
    common = tokens1 & tokens2
    return len(common) / max(len(tokens1), len(tokens2), 1)

from networkx.readwrite import json_graph
def build_menu_graph(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    G = nx.Graph()
    for c in chunks:
        dish = extract_dish_name(c["text"])
        G.add_node(dish, **c.get("metadata", {}))
    for a, b in combinations(chunks, 2):
        if similarity(a, b) > 0.7:
            G.add_edge(extract_dish_name(a["text"]), extract_dish_name(b["text"]))
    
    # Convert graph to dictionary
    graph_dict = json_graph.node_link_data(G)
    
    # Return as chunk-compatible format
    return [{
        "text": f"Menu graph with {len(G.nodes)} nodes and {len(G.edges)} edges",
        "metadata": {
            "graph_data": graph_dict,
            "restaurant_name": chunks[0]["metadata"]["restaurant_name"] if chunks else "",
            "url": chunks[0]["metadata"]["url"] if chunks else ""
        }
    }]

# --- 7. Attribute Extraction via HF API ---
ATTRIBUTE_PROMPT = (
    "Extract attributes (vegetarian:boolean, spice:boolean,gluten_free:boolean, spice_level:int, price:number) from this text.\nText:\n{text}"
)

def enrich_chunk(record: dict) -> Dict[str, Any]:
    text = record.get("text", "")
    metadata = record.get("metadata", {})
    resp = client.text_generation(
        model="gpt2",
        prompt=ATTRIBUTE_PROMPT.format(text=text),
        max_new_tokens= 128
    )
    raw = resp
    try:
        attrs = json.loads(raw)
        metadata.update(attrs)
    except:
        pass
    print(f"Attributes based NER with LLM chunking done.")
    return {"text": text, "metadata": metadata}

# --- Dispatcher ---
def chunk_record(
    record: Dict[str, Any],
    strategy: str,
    splitter_func=None,
    llm=None
) -> List[Dict[str, Any]]:
    strategies = {
        "semantic": semantic_menu_chunking,
        "llm_guided": llm_guided_chunking,
        "hierarchical": hierarchical_chunking,
        "multimodal": multimodal_chunking,
        "entropy": lambda r: entropy_based_chunking(r, splitter_func),
        "graph": lambda r: build_menu_graph(semantic_menu_chunking(r)),
        "attribute": lambda r: [enrich_chunk(r)]
    }
    if strategy not in strategies:
        raise ValueError(f"Unknown strategy: {strategy}")
    return strategies[strategy](record)

"""
Output is like this 

[
  {
    "text": "Paneer Tikka ...", 
    "metadata": {"url":"https://zomato.com/resto","id":"abc123"}
  },
  {
    "text": "Butter Chicken ...", 
    "metadata": {"url":"https://zomato.com/resto","id":"abc123"}
  },
  …
]


"""