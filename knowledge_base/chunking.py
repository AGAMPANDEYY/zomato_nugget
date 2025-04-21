import re
import json
from itertools import combinations

# --- 1. Semantic Menu Item Chunking ---
# Uses LangChain Experimental SemanticChunker to split high-level menu sections.
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

# Fallback to character splitter if experimental semantic splitter not available
char_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
embed_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")

def semantic_menu_chunking(text: str, metadata: dict) -> list[dict]:
    # First split by Markdown headers
    sections = re.split(r"(?:^|\n)(#{1,3})\s+", text)
    chunks = []
    for sec in sections:
        # For brevity, apply character splitter as a stand-in for semantic logic
        for sub in char_splitter.split_text(sec):
            chunks.append({"text": sub, "metadata": metadata})
    return chunks


# --- 2. LLM-Guided Dynamic Chunking ---
# Uses LlamaIndex's LLMChunkParser for comparison-focused chunking.
    
from llama_index.node_parser import LLMChunkParser

class SpiceComparatorChunker(LLMChunkParser):
    def __init__(self, llm):
        super().__init__(llm=llm, chunking_strategy="comparative")
    def parse(self, text):
        raw = super().get_chunks(text)  # returns raw JSON string
        try:
            return [{"text": t, "metadata": {}} for t in json.loads(raw)["chunks"]]
        except:
            return []

def llm_guided_chunking(text: str, metadata: dict, llm) -> list[dict]:
    """
    Use LLM-guided chunking to generate comparison-focused chunks.
    This is suited for cross-item comparisons (e.g., spice level comparison).
    """
    return [{"text": c["text"], "metadata": metadata} for c in SpiceComparatorChunker(llm).parse(text)]

# --- 3. Attribute-Aware Hierarchical Chunking ---
from langchain.text_splitter import HTMLHeaderTextSplitter

hier_splitter = HTMLHeaderTextSplitter(headers=["h1","h2","h3"], chunk_size=400)

def hierarchical_chunking(html: str, metadata: dict) -> list[dict]:
    """
    Chunk the HTML based on header structure.
    Returns a list of chunks with added metadata.
    """
    docs = hier_splitter.split_text(html)
    chunk = []
    for d in docs:
        md = metadata.copy()
        # Price & dietary tags extraction
        md["prices"] = re.findall(r"(?:₹|Rs\.?)\s*\d+", d)
        md["diet"] = []
        if "vegetarian" in d.lower(): md["diet"].append("vegetarian")
        if "gluten-free" in d.lower(): md["diet"].append("gluten-free")
        chunk.append({"text": d, "metadata": md})
    return chunk


# --- 4. Multimodal Fusion Chunking ---
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import requests

processor = BlipProcessor.from_pretrained("Salesforce/blip2-opt-2.7b")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip2-opt-2.7b")

def multimodal_chunking(text: str, metadata: dict, image_url: str) -> list[dict]:
    try:
        img = Image.open(requests.get(image_url, stream=True).raw).convert("RGB")
        inputs = processor(images=img, return_tensors="pt")
        caption = model.generate(**inputs)
        cap_text = processor.decode(caption[0], skip_special_tokens=True)
        fused = f"{text}\nVisual: {cap_text}"
    except:
        fused = text
    return [{"text": fused, "metadata": metadata}]



# --- 5. Dynamic Context Window Optimization ---
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

def entropy_based_chunking(text: str, metadata: dict, splitter_func) -> list[dict]:
    vec = TfidfVectorizer().fit_transform([text])
    entropy = -np.sum(vec.data * np.log(vec.data + 1e-12))
    if entropy < 2.0:
        return [{"text": text, "metadata": metadata}]
    return [{"text": chunk, "metadata": metadata} for chunk in splitter_func(text)]

# --- 6. Cross-Menu Relationship Chunking ---
import networkx as nx

def extract_dish_name(chunk_text: str) -> str:
    # A very basic extraction (in practice, use NER or regex improvements)
    match = re.search(r"Name:\s*([^\\n]+)", chunk_text)
    return match.group(1).strip() if match else "Unknown Dish"

def similarity(chunk1: dict, chunk2: dict) -> float:
    # Dummy similarity based on string overlap (replace with actual embedding cosine similarity).
    text1, text2 = chunk1.get("text", ""), chunk2.get("text", "")
    common = set(text1.split()) & set(text2.split())
    return len(common) / max(len(text1.split()), len(text2.split()), 1)

def build_menu_graph(chunks: list[dict]) -> nx.Graph:
    """
    Build a graph where each node is a dish (chunk) and edges state similarity.
    Each chunk is expected to be a dict with at least 'text' and optionally metadata.
    """
    G = nx.Graph()
    for chunk in chunks:
        dish = extract_dish_name(chunk.get("text", ""))
        G.add_node(dish, **chunk.get("metadata", {}))
        
    # Connect similar dishes
    for chunk1, chunk2 in combinations(chunks, 2):
        if similarity(chunk1, chunk2) > 0.7:
            dish1 = extract_dish_name(chunk1.get("text", ""))
            dish2 = extract_dish_name(chunk2.get("text", ""))
            G.add_edge(dish1, dish2)
    return G

# --- 7. LLM-Assisted Attribute Extraction ---
from llama_index.core import PromptTemplate

attribute_prompt = PromptTemplate(
    template="""
Extract from this menu item:
{text}

Output JSON with:
- vegetarian: boolean
- gluten_free: boolean  
- spice_level: integer (0-5)
- price: number
""",
    input_variables=["text"]
)

def enrich_chunk(chunk: dict, llm_obj) -> dict:
    """
    Use LLM-assisted extraction to enrich the chunk with attributes.
    Here llm_obj should have a .complete() method.
    """
    prompt_text = attribute_prompt.format(text=chunk.get("text", ""))
    response = llm_obj.complete(prompt_text)
    # Expect LLM to return JSON text.
    try:
        attributes = json.loads(response.text)
    except Exception:
        attributes = {}
    enriched = {**chunk, **attributes}
    return enriched

# ----------------------------------------------------------------------------
# Optionally, provide a dispatcher which allows you to choose one of
# these chunking strategies on a given record (menu text).
def chunk_record(record: dict, strategy: str, **kwargs):
    """
    Given a record containing restaurant menu text (or markdown), apply the desired chunking strategy.
    Strategies: "semantic", "llm_guided", "hierarchical", "multimodal", "entropy", "graph", "attribute"
    """
    text = record.get("text", "")
    # For Crawl4AI records, text might come from markdown conversion beforehand.
    if strategy == "semantic":
        return semantic_menu_chunking(text)
    elif strategy == "llm_guided":
        return llm_guided_chunking(text)
    elif strategy == "hierarchical":
        return hierarchical_chunking(text)
    elif strategy == "multimodal":
        # Requires an image URL in the record – assume record has "image_url"
        image_url = record.get("image_url", "")
        # In this example, simply process entire text with image caption.
        return multimodal_chunking(text, image_url)
    elif strategy == "entropy":
        # Use semantic splitter as default for entropy splitting.
        return entropy_based_chunking(text, semantic_splitter.split_text)
    elif strategy == "graph":
        # For graph chunking, we assume a list of pre-chunked dictionaries is provided.
        # Here we simply return the graph built from single record (not typical usage).
        return build_menu_graph([{"text": text, "metadata": record.get("metadata", {})}])
    elif strategy == "attribute":
        # For attribute extraction, use a dummy llm object (or pass one via kwargs).
        llm_obj = kwargs.get("llm_obj", llm)
        # Create a chunk dict from text.
        chunk = {"text": text}
        return enrich_chunk(chunk, llm_obj)
    else:
        raise ValueError("Unknown chunking strategy")