# main.py
import json
from observability.setup_observer import setup_instrumentor
from retrieval.hybridrag import HybridRAG
from utils.embeddings import create_embeddings
from utils.query_processor import preprocess_query
from langchain_agent.agents.agent_initializer import LangchainReactAgent
from llama_index.core import global_handler
import uuid
 


instrumentor = setup_instrumentor()

def query_with_observability(agent, user_query: str):
    with instrumentor.observe(trace_id=f"agent-{uuid.uuid4()}", session_id=session_id,
                               user_id='user-id', metadata={"app_version": "1.0"}) as trace:
        try:
            # preprocessing step

            processed_query, entities = preprocess_query(user_query)
            print(f" Processed query is {processed_query}")
     
            # Get embeddings for processed query
            query_embeddings = create_embeddings(processed_query)
            hybrid_rag=HybridRAG()
            # Retrieve with processed query and its embeddings
            results = hybrid_rag.query_hybrid(processed_query, query_embeddings)
            hybrid_rag.close()
            response = agent.invoke({"input": user_query, "context": results})['output']
            
            trace.score(name="query_success", value=1.0)
            trace.score(name="relevance", value=0.95)
            trace.score(name="response_quality", value=0.88)
            trace.update(user_id=user_id,session_id=session_id, input=user_query, ouput=response)

            trace.update(metadata={
                "session_id": session_id,
                "original_query": user_query,
                "processed_query": processed_query,
                "entities": entities,
                "agent_response": response
            })
            return response
        
        except Exception as e:
            trace.score(name="query_error", value=0.0)
            raise e
        finally:
            instrumentor.flush()

if __name__ == "__main__":
    user_query = "Which restaurant offers the best spicy paneer tikka?"
    session_id=str(uuid.uuid4())
    user_id="agampandey"
    print(f" Session started: {session_id}")
    langchain_agent=LangchainReactAgent(session_id).get_agent()
    print("LangChain React Agent chatbot is ready. Type your query or 'exit' to quit.")
    response = query_with_observability(langchain_agent,user_query)
    print(f" Agent response is: {response}")
    instrumentor.flush()
