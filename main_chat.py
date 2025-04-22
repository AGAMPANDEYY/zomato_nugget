# main.py
import json
from observability.setup_observer import setup_instrumentor
from retrieval.hybridrag import HybridRAG
from utils.embeddings import create_embeddings
from utils.query_processor import preprocess_query
from langchain_agent.agents.agent_initializer import LangchainReactAgent
import uuid

instrumentor = setup_instrumentor()

def query_with_observability(user_query: str):
    with instrumentor.observe(trace_id=f"trace-{hash(user_query)}", session_id="zomato-session", user_id='user-id', metadata={"app_version": "1.0"}) as trace:
        try:
            # preprocessing step
            processed_query, entities = preprocess_query(user_query)
            print(f" Processed query is {processed_query}")
     
            trace.update(metadata={
                "original_query": user_query,
                "processed_query": processed_query,
                "entities": entities
            })
            # Get embeddings for processed query
            query_embeddings = create_embeddings(processed_query)
            hybrid_rag=HybridRAG()
            # Retrieve with processed query and its embeddings
            results = hybrid_rag.query_hybrid(processed_query, query_embeddings)
            hybrid_rag.close()
            
            trace.score(name="query_success", value=1.0)
            trace.score(name="relevance", value=0.95)
            trace.score(name="response_quality", value=0.88)
            return results
        
        except Exception as e:
            trace.score(name="query_error", value=0.0)
            raise e
        finally:
            instrumentor.flush()

if __name__ == "__main__":
    user_query = "Which restaurant offers the best spicy paneer tikka?"
    #aggregated_results = query_with_observability(user_query)
    print("Hybrid Retrieval (with Observability) Results:")
    session_id=str(uuid.uuid4())
    langchain_agent=LangchainReactAgent().get_agent(session_id)
    print("LangChain React Agent chatbot is ready. Type your query or 'exit' to quit.")
    response = langchain_agent.invoke({"input": user_query})['output']
    print(f" Agent response is: {response}")
    instrumentor.flush()
