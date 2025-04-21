"""
Order of Strategies: We apply hierarchical first for structured menu entries, then semantic and LLM‑guided for deeper context 
Haystack
; less precise methods (entropy, graph) come last.

Deduplication: We hash each chunks text to avoid reindexing duplicates—critical when strategies overlap 
Analytics Vidhya
.

Embedding & Ingestion: We embed via allMiniLML6v2 and index into ChromaDB, storing full metadata for filtered retrieval 
RAG News
.

"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from knowledge_base.fetch_datalake import DataLakeFetcher
from knowledge_base.normalize_records import normalize_records
from knowledge_base.chunking import chunk_record
from knowledge_base.embeddings import generate_embeddings
from knowledge_base.hybrid_rag import HybridRAG
from transformers import pipeline
import asyncio
import hashlib

# 1. Fetch & normalize
datalake = DataLakeFetcher()
hybrid_rag = HybridRAG()
raw_processed = datalake.fetch_records_from_mongodbatlas()
normalized = asyncio.run(normalize_records(raw_processed))

"""
Strcture of the normalized records:
    
    [
        {
            "source": "crawl4ai",
            "url": "https://example.com",
            "text": "Markdown content here",
            "media": ["image1.png", "video.mp4"]
        },
        {
            "source": "seleniumfetcher",
            "url": "https://example2.com",
            "text": "{\"key\": \"value\"}",
            "metadata": {"key": "value"}
        }........................,
    ]
"""

print("Now creating KnowledgeBase from normalized records")

# 4. Define chunking strategies in order of priority
strategies = [
    "hierarchical",  # best for precise menu items & metadata
    "semantic",      # dish‑level context
    "llm_guided",    # comparisons
    "attribute",     # unstated attributes
    "multimodal",    # images
    "entropy",       # dynamic window
    "graph"          # cross‑menu relations
]

def dedupe_and_add(chunks, seen_hashes):
    """Dedup and add to Chroma."""
    for ch in chunks:
        text = ch["text"].strip()
        h = hashlib.sha256(text.encode()).hexdigest()
        if h in seen_hashes:
            continue
        seen_hashes.add(h)
        # Compute the embedding based on text
        embedding = generate_embeddings(text, ch["metadata"])

        #add to Vector DB Weviate 
        hybrid_rag.push_vector_data(embedding)
        #add to Graph DB Neo4j
        hybrid_rag.push_graph_data(ch)

llm=pipeline(
    "text-generation",
    model="google/flan-t5-small",  # or any other model you prefer
    device=0  # Use GPU if available, else set to -1 for CPU
)


"""
The chunk data format would be like this: 


example_chunks = [
    {
        "text": "Name: Bikanervala Restaurant\nAddress: 123 Main Street\nCuisine: North Indian\nRating: 4.2\nTiming: 11 AM - 11 PM\nMenu: Appetizers - Paneer Tikka, Samosa; Main Course - Butter Chicken, Dal Makhani",
        "metadata": {
            "source": "crawl4ai",
            "url": "https://example.com",
            "chunk_type": "hierarchical",  # indicates the chunking strategy used
            "menu_section": "Main Course",
        }
    },
    {
        "text": "Name: Example Restaurant\nAddress: 456 Example Road\nCuisine: Indian\nRating: 4.5\nTiming: 10 AM - 10 PM\nMenu: Entrees - Masala Dosa, Idli, Vada",
        "metadata": {
            "source": "seleniumfetcher",
            "url": "https://example2.com",
            "chunk_type": "semantic",
            "attributes": {"key": "value"}  # any additional metadata extracted during chunking
        }
    }
]

"""

# 5. Orchestrate chunking, dedupe, indexing
seen = set()
for rec in normalized:
    for strat in strategies:
        # Pass LLM for llm_guided and attribute strategies
        kwargs = {}
        if strat in ("llm_guided", "attribute"):
            kwargs["llm"] = llm  # your LLM client
        if strat == "multimodal":
            # assume rec["media"] holds image URLs
            for img_url in rec.get("media", []):
                chunks = chunk_record(rec, strat, image_url=img_url, **kwargs)
                dedupe_and_add(chunks, seen)
            continue

        chunks = chunk_record(rec, strat, **kwargs)
        dedupe_and_add(chunks, seen)

print(f"Indexed {len(seen)} unique chunks into the knowledge base.")

