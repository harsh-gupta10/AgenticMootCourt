from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

class CourtAgentRunnable:
    def __init__(self, llm, role, case_details, constitution_store, bns_store, memory_store=None, max_iter=20):
        self.llm = llm
        self.role = role
        self.case_details = case_details
        self.constitution_store = constitution_store.as_retriever(k=4)
        self.bns_store = bns_store.as_retriever(k=4)
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
            print("Answer", answer)
            return answer

        @tool
        def search_bns_store(query: str) -> str:
            """Search the BNS store for relevant text using FAISS."""
            answer = self.bns_store.invoke(query)[2]
            print("Searching BNS store")
            return answer
        
        # Register tools
        self.tools = [search_constitution_store, search_bns_store]
        
        # Create BasePromptTemplate
        base_prompt = PromptTemplate.from_template(
             """{role}.
                These are the tools you can use:
                {tools}
                Use the following format:
                Input: The input question/statement
                Case details: The details of the case
                Thought: Use the chat history to determine the next argument/question/answer
                Action: One of the [{tool_names}] **only if you need to**.
                Action Input: the search query 
                Observation: Verifying the reasonability of the argument/question/answer
                ... (this Thought/Action/Action Input/Observation can repeat 3 times)
                Thought: I now know the final answer/argument/question
                Final Answer: the final argument that you want to make/ the final answer to the question/ the final question you want to ask

                Begin!

                Input: {input}
                Thought:{agent_scratchpad}
                Case Details:{case_details}"""
        )
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
        
        def prepare_inputs(input_dict):
            # For ReAct agents, the input is just the user query.
            print(input_dict)
            return {
                "input": input_dict.get("input", ""),
                "role": self.role,
                "case_details": self.case_details
            }
        

        return RunnableWithMessageHistory(
            runnable=self.agent_executor,
            get_session_history=self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
