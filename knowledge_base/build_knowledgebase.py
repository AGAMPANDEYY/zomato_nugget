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
from tqdm import tqdm

# 1. Fetch & normalize
datalake = DataLakeFetcher()
hybrid_rag = HybridRAG()
raw_processed = datalake.fetch_records_from_mongodbatlas()
print(f" raw processed:", raw_processed.keys())

print(f"Loaded processed data from DataLake MongoDB Atlas")
normalized = asyncio.run(normalize_records(raw_processed))

# assume `normalized` is your list of dicts
if not normalized:
    print("No records to show")
else:
    sample = normalized[0]           # get the first dict
    for k, v in sample.items():      # now you can call .items()
        t = type(v).__name__
        # if it’s a sequence, show its length
        size = f"len={len(v)}" if isinstance(v, (str, list, dict)) else ""
        print(f"{k!r}: {t} {size}")


"""
Strcture of the normalized records:

normalized = [
    {
        "id":             "dominos_3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "scraper_name":   "Crawl4AIFetcher",
        "restaurant_name":"dominos",
        "base_url":       "",  # empty string, len=0
        "url":            "https://dominos.in/menu.html?utm_source=api",  # ~79 chars
        "markdown":       "-",  # minimal content, len=1
        "html":           "<html>…full HTML of the menu page…</html>",  # ~4535 chars
        "media": {  # dict with 4 top‑level keys
            "images":    ["https://…/img1.webp", /* … */],
            "videos":    [],
            "documents": [{"type":"menu_pdf","url":"/menus/main.pdf","pages":5}],
            "others":    []  # if you add extra asset types
        },
        "timestamp":      datetime(2025, 4, 21, 18, 7, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    },
    # … more records …
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

"""
Chunks will have these values 

{"text": text, "metadata": metadata}
 'metadata': {'id': 'indian_restaurants_ac20da0d-97a9-4df9-8b2f-769f3daf5305', 
 'scraper_name': 'Crawl4AIFetcher', 'restaurant_name': 'indian_restaurants', 'base_url': '', 
 'url': 'https://indiarestaurant.co.in/contacts.html', 
 'timestamp': datetime.datetime(2025, 4, 22, 8, 39, 58, 889000), 'prices': [], 'diet': []}}
"""

def dedupe_and_add(chunks, seen_hashes,strat):
    for ch in chunks:
        if not isinstance(ch, dict) or strat=="graph":
            print(f"Skipping chunk, not a dict or is a Grpah")
            continue
        text = ch["text"].strip()
        if not text:
            continue
        fp = hashlib.sha256(text.encode()).hexdigest()
        if fp in seen_hashes:
            continue
        seen_hashes.add(fp)

        # Attach stable ID
        restaurant = ch["metadata"]["restaurant_name"]
        url = ch["metadata"]["url"]
        ch["metadata"]["chunk_id"] = f"{restaurant}_{url}_{fp}"
        ch["metadata"]["markdown"] = text

        # Generate embeddings list of dicts
        embeddings = generate_embeddings(text, ch["metadata"])
        hybrid_rag.push_vector_data(embeddings, strat)
        hybrid_rag.push_graph_data(ch, strat)


llm=pipeline(
    "text-generation",
    model="gpt2",  # or any other model you prefer
    device=0  # Use GPU if available, else set to -1 for CPU
)


"""
The chunk data format would be like this: 


example_chunks =

"""

# 5. Orchestrate chunking, dedupe, indexing
seen = set()
for rec in tqdm(normalized, desc="Processing normalized records"):
    for strat in tqdm(strategies, desc="Processing strategies", leave=False):
        kwargs = {}
        if strat in ("llm_guided", "attribute"):
            kwargs["llm"] = llm
        # Uncomment and adjust multimodal handling if needed
        """
        if strat == "multimodal":
            media = rec.get("media", {})
            image_urls = media.get("images", [])
            for img_url in image_urls:
                chunks = chunk_record(rec, strat, image_url=img_url, **kwargs)
                dedupe_and_add(chunks, seen, strat)
            continue
        """
        print(f"strategy is ", strat)
        chunks = chunk_record(rec, strat, **kwargs)
        dedupe_and_add(chunks, seen, strat)


print(f"Indexed {len(seen)} unique chunks into the knowledge base.")
hybrid_rag.close()