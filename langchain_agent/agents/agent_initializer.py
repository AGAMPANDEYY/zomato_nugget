from langchain.agents import AgentExecutor,create_react_agent, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder  
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

from langchain_agent.tools.hybrid_rag_tool import rag_retriever
from langchain_agent.tools.graph_query_tool import graph_query
from langchain_agent.tools.dynamic_scrape_tool import dynamic_scrape
from langchain_agent.llm.huggingface_llm import get_huggingface_llm, load_system_prompt
from langchain.agents import create_tool_calling_agent
from langchain.agents import initialize_agent
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver


@tool("DummyTool", description="dummy NUll")
def dummy_tool() -> str:
    return "dummy tool called"


class LangchainReactAgent:
    def __init__(self, session_id):
        self.llm=get_huggingface_llm()
        self.memory=MemorySaver()
        self.messages=load_system_prompt()
        self.tools = [rag_retriever]#, dynamic_scrape] #graph_query
        system_prompt = load_system_prompt()[0]["content"] 
        prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    ("human", "{input}"),
                    # Placeholders fill up a **list** of messages
                    ("placeholder", "{agent_scratchpad}"),
                    ("placeholder", "{chat_history}"),
                ]
            )
        self.session_id=session_id
        #agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        self.agent_executor = create_react_agent(model=self.llm, tools=self.tools, checkpointer=self.memory)
       
    def get_agent(self):
        return self.agent_executor