# main.py
from observability import setup_observer
from retrieval.hybrid_retriever import hybrid_retrieve

instrumentor = setup_observer()

def query_with_observability(user_query: str):
    with instrumentor.observe(trace_id='custom-trace-id', session_id="your-session-id", user_id='user-id') as trace:
        try:
            results = hybrid_retrieve(user_query)
            trace.score(name="query_success", value=1.0)
            return results
        except Exception as e:
            trace.score(name="query_error", value=0.0)
            raise e
        finally:
            instrumentor.flush()

if __name__ == "__main__":
    sample_query = "Which restaurant offers the best spicy paneer tikka?"
    aggregated_results = query_with_observability(sample_query)
    import json
    print("Hybrid Retrieval (with Observability) Results:")
    print(json.dumps(aggregated_results, indent=4))
    instrumentor.flush()
