from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

from langchain_agent.tools.hybrid_rag_tool import rag_retriever
from langchain_agent.tools.graph_query_tool import graph_query
from langchain_agent.tools.dynamic_scrape_tool import dynamic_scrape
from langchain_agent.llm.huggingface_llm import get_huggingface_llm, load_system_prompt
from langchain.agents import create_tool_calling_agent

class LangchainReactAgent:
    def __init__(self, session_id):
        self.llm=get_huggingface_llm()
        self.messages=load_system_prompt()
        self.tools = [rag_retriever, dynamic_scrape] #graph_query
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.messages[0]['content']),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        self.session_id=session_id
        memory = InMemoryChatMessageHistory(session_id=self.session_id)
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
        self.agent_with_chat_history =RunnableWithMessageHistory(
            agent_executor,
            lambda session_id: memory,
            input_messages_key="input",
            history_messages_key="chat_history"
        )
    def get_agent(self):
        return self.agent_with_chat_history.with_config({
            "configurable": {"session_id": self.session_id}
        })


    
