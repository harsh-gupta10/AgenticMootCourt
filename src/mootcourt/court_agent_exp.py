# This is an experimental version of court agent class with ReAct+IRAC prompting. Refer to google doc for more details.
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

class CourtAgentRunnable:
    def __init__(self, llm, role, case_details, constitution_store, bns_store, memory_store=None, max_iter=50):
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
            print("Searching constitution store.............")
            return answer

        @tool
        def search_BHARATIYA_NYAYA_SANHITA_store(query: str) -> str:
            """Search the BNS store for relevant text using FAISS."""
            answer = self.bns_store.invoke(query)[2]
            print("Searching BNS store.............")
            return answer
        
        # @tool
        # def Landmark_Cases(query: str) -> str:
        #     """Search the Landmark Cases for relevant text using FAISS."""
        #     answer = self.Landmark_Cases_store.invoke(query)[2]
        #     print("Searching Landmark Cases.............")
        #     return answer
          
        # @tool
        # def Supreme_Court_Landmark_Cases(query: str) -> str:
        #     """Search the Supreme Court Landmark Cases for relevant text using FAISS."""
        #     answer = self.SC_Landmark_Cases_store.invoke(query)[2]
        #     print("Searching Supreme Court Landmark Cases.............")
        #     return answer
        
        # Register tools
        self.tools = [search_constitution_store, search_BHARATIYA_NYAYA_SANHITA_store]
        
        # Create BasePromptTemplate
        base_prompt = PromptTemplate.from_template(
                """
                FOLLOW FORMAT STRICTLY.
                {role}
                These are the tools you can use: {tools}
                Use the following structured format for argumentation and questioning:

                Input: The input question/statement  
                Case Details: The details of the case  

                Thought: Use the chat history to determine the next argument/question/answer using IRAC framework:
                - Issue: Identify the key legal or logical issue in the argument.  
                - Rule: State the relevant legal principle, rule, or logical framework.  
                - Application: Apply the rule to the specific facts of the case.  
                - Conclusion: Provide a reasoned conclusion based on the analysis.  

                Action: One of the [{tool_names}] only if needed.  
                Action Input: The search query if using a tool.

                Observation: The result of the search. 

                (Repeat Thought/Action/Observation up to 3 times if necessary.)

                Thought: I now know the final answers/arguments/questions.  
                Final Answer: The arguments, questions, or answers.    


                Begin!

                Input: {input}  
                Thought: {agent_scratchpad}  
                Case Details: {case_details}
                Chat History: {chat_history}
                """
        )
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=base_prompt
        )
        
        # Wrap the agent with an executor that integrates memory and sets max iterations
        self.agent_executor = AgentExecutor(agent=self.agent,tools=self.tools, max_execution_time=20,max_iterations=10,handle_parsing_errors=True
                                            ,verbose=True,return_intermediate_steps=True)

    def get_session_history(self, session_id):
        """Retrieve chat history."""

        print("Retrieving chat history.............")
        print(self.memory.chat_memory)
        return self.memory.chat_memory

    def create_runnable(self) -> RunnableWithMessageHistory:
        """Creates a RunnableWithMessageHistory using the ReAct agent executor."""
    
        return RunnableWithMessageHistory(
            runnable=self.agent_executor,
            get_session_history=self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
