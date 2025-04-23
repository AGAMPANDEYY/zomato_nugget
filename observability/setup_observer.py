# observability.py
from langfuse.llama_index import LlamaIndexInstrumentor

import os
from dotenv import load_dotenv
load_dotenv()

LANGFUSE_PUBLIC_KEY= os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY= os.getenv("LANGFUSE_SECRET_KEY")


def setup_instrumentor():
    instrumentor = LlamaIndexInstrumentor(public_key=LANGFUSE_PUBLIC_KEY, secret_key=LANGFUSE_SECRET_KEY)
    instrumentor.start()
    return instrumentor
