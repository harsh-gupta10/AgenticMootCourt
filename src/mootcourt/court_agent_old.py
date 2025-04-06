from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from Prompts_react import judge_prompt , defendant_prompt, reviewer_prompt , test_prompt

class CourtAgentRunnable:
    def __init__(self, llm, role, case_details, constitution_store, bns_store, Landmark_Cases_store, SC_Landmark_Cases_store ,  memory_store=None, max_iter=20):
        self.llm = llm
        self.role = role
        self.case_details = case_details
        self.constitution_store = constitution_store.as_retriever(k=4)
        self.bns_store = bns_store.as_retriever(k=4)
        self.Landmark_Cases_store = Landmark_Cases_store.as_retriever(k=4)
        self.SC_Landmark_Cases_store = SC_Landmark_Cases_store.as_retriever(k=4)
        self.max_iter = max_iter

        # Initialize persistent memory
        self.memory = memory_store if memory_store else ConversationBufferMemory(
            chat_memory=ChatMessageHistory(),
            return_messages=True
        )

        # Define retrieval tools
        @tool
        def search_constitution_store(query: str) -> str:
            """Search the constitution store for relevant text using FAISS"""
            answer = self.constitution_store.invoke(query)[2]
            print("Searching constitution store.............")
            return answer

        @tool
        def search_BHARATIYA_NYAYA_SANHITA_store(query: str) -> str:
            """Search the BNS store for relevant text using FAISS."""
            answer = self.bns_store.invoke(query)[2]
            print("Searching BNS store.............")
            return answer
        
        @tool
        def Landmark_Cases(query: str) -> str:
            """Search the Landmark Cases for relevant text using FAISS."""
            answer = self.Landmark_Cases_store.invoke(query)[2]
            print("Searching Landmark Cases.............")
            return answer
          
        @tool
        def Supreme_Court_Landmark_Cases(query: str) -> str:
            """Search the Supreme Court Landmark Cases for relevant text using FAISS."""
            answer = self.SC_Landmark_Cases_store.invoke(query)[2]
            print("Searching Supreme Court Landmark Cases.............")
            return answer
        
        # @tool
        # def No_Op(query: str) -> str:
        #     """Call when no action is needed. Provide action input as No Op"""
        #     return "Nop"
        
        # Register tools
        self.tools = [search_constitution_store, search_BHARATIYA_NYAYA_SANHITA_store , Landmark_Cases , Supreme_Court_Landmark_Cases]


        base_prompt = None
        # Add more roles as needed
        if role=="judge":
            base_prompt=PromptTemplate.from_template(
                judge_prompt
            )
        elif role=="respondent":
            base_prompt=PromptTemplate.from_template(
                defendant_prompt
            )
        
        elif role=="reviewer":
            base_prompt=PromptTemplate.from_template(
                reviewer_prompt
            )

        elif role=="test":
            base_prompt=PromptTemplate.from_template(
                test_prompt
            )
        else:
            raise ValueError("Invalid role. Please choose from 'judge', 'respondent', 'test' or 'reviewer'.")

        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=base_prompt
        )
        
        # Wrap the agent with an executor that integrates memory and sets max iterations
        self.agent_executor = AgentExecutor(agent=self.agent,tools=self.tools, max_execution_time=20,max_iterations=100,handle_parsing_errors=True
                                            ,verbose=True,return_intermediate_steps=True)

    def get_session_history(self, session_id):
        """Retrieve chat history."""
        return self.memory.chat_memory

    def create_runnable(self) -> RunnableWithMessageHistory:
        """Creates a RunnableWithMessageHistory using the ReAct agent executor."""

        return RunnableWithMessageHistory(
            runnable=self.agent_executor,
            get_session_history=self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )


