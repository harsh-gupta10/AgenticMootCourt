from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.agents import create_tool_calling_agent
from langchain_core.tools import tool

class CourtAgentRunnable:
    def __init__(self, llm, role, case_details, constitution_store, bns_store, memory_store=None, max_iter=3):
        self.llm = llm
        self.role = role
        self.case_details = case_details
        self.constitution_store = constitution_store
        self.bns_store = bns_store
        self.max_iter = max_iter

        # Use persistent memory
        self.memory = memory_store if memory_store else ConversationBufferMemory(
            chat_memory=ChatMessageHistory(),
            return_messages=True
        )

        # Define retrieval tools
        @tool
        def search_constitution_store(query: str, k: int = 3) -> str:
            """Search the constitution store for relevant documents."""
            docs = self.constitution_store.similarity_search(query, k=k)
            return "\n\n".join([doc.page_content for doc in docs])

        @tool
        def search_bns_store(query: str, k: int = 3) -> str:
            """Search the BNS store for relevant documents."""
            docs = self.bns_store.similarity_search(query, k=k)
            return "\n\n".join([doc.page_content for doc in docs])
        
        # Register tools
        self.tools = [search_constitution_store, search_bns_store]

        # Create the agent
        self.agent = create_tool_calling_agent(self.llm, self.tools)

    def get_session_history(self, session_id):
        """Retrieve chat history."""
        return self.memory.chat_memory

    def create_runnable(self) -> RunnableWithMessageHistory:
        """Creates an agent-based RunnableWithMessageHistory."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("ai", "{role}"),
            ("ai", "Case Details: {case_details}"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])

        def prepare_inputs(input_dict):
            query = input_dict.get("input", "")
            chat_history = input_dict.get("chat_history", [])
            return {
                "input": query,
                "case_details": self.case_details,
                "role": self.role,
                "chat_history": chat_history
            }
        
        chain = RunnableLambda(prepare_inputs) | prompt | self.agent

        return RunnableWithMessageHistory(
            runnable=chain,
            get_session_history=self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history"
        )
