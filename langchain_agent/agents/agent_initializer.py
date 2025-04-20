from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

from tools.hybrid_rag_tool import rag_retriever
from tools.graph_query_tool import graph_query
from tools.dynamic_scrape_tool import dynamic_scrape
from llm.huggingface_llm import get_huggingface_llm, load_system_prompt
from langgraph.prebuilt import create_tool_calling_agent

def get_agent_with_history():
    llm = get_huggingface_llm()
    system_prompt = load_system_prompt()

    tools = [rag_retriever, graph_query, dynamic_scrape]

    prompt = ChatPromptTemplate.from_messages([
        {"role": "system", "content": system_prompt}
    ])

    memory = InMemoryChatMessageHistory(session_id="test-session")
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools)

    return RunnableWithMessageHistory(
        agent_executor,
        lambda session_id: memory,
        input_messages_key="input",
        history_messages_key="chat_history"
    )
