from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableLambda, Runnable
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from Prompts_react import judge_prompt , defendant_prompt, reviewer_prompt , test_prompt, evaluation_prompt
from argsumm_test import LegalArgumentSummarizer


class CourtAgentRunnable:
    def __init__(self, llm, role, case_details, constitution_store, bns_store, Landmark_Cases_store, SC_Landmark_Cases_store ,  memory_store=None, max_iter=10):
        self.llm = llm
        self.role = role
        self.case_details = case_details
        self.constitution_store = constitution_store.as_retriever(k=4)
        self.bns_store = bns_store.as_retriever(k=4)
        self.Landmark_Cases_store = Landmark_Cases_store.as_retriever(k=4)
        self.SC_Landmark_Cases_store = SC_Landmark_Cases_store.as_retriever(k=4)
        self.max_iter = max_iter
        self.summarizer = LegalArgumentSummarizer()
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
        elif role=="evaluation":
            base_prompt=PromptTemplate.from_template(
                evaluation_prompt
            )
        else:
            raise ValueError("Invalid role. Please choose from 'judge', 'respondent', 'test' or 'reviewer' or 'evaluation'.")

        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=base_prompt
        )
        
        # Wrap the agent with an executor that integrates memory and sets max iterations
        self.agent_executor = AgentExecutor(agent=self.agent,tools=self.tools, max_execution_time=20,max_iterations=5,handle_parsing_errors=True
                                            ,verbose=True,return_intermediate_steps=True)

    def get_session_history(self, session_id):
        """Retrieve chat history."""
        print("Memory :", self.memory.chat_memory)
        return self.memory.chat_memory
    
    def normal_execute(self, input_data):
        """Custom function to handle the full execution flow with memory management"""
        # Extract the input message
        user_input = input_data["input"]
        chat_history = self.get_session_history("default")
        
        # Execute the agent with the input and history
        result = self.agent_executor.invoke({
            "input": user_input,
            "chat_history": chat_history,
            "case_details": self.case_details,
            "agent_scratchpad": []
        })
        
        # Get the raw response
        raw_response = result.get("output", "")
        
        processed_response = raw_response
        # Add the user input and processed response to memory
        self.memory.chat_memory.add_user_message(user_input)
        self.memory.chat_memory.add_ai_message(processed_response)
        
        # Return the result including both raw and processed outputs
        return {
            "raw_output": raw_response,
            "processed_output": processed_response,
            **result
        }


        
    def process_and_execute(self, input_data):
        """Custom function to handle the full execution flow with memory management"""
        # Extract the input message
        user_input = input_data["input"]
        chat_history =self.get_session_history("default")
        
        # Don't add to memory here - we'll use the history from the input
        # Execute the agent with the input and history
        result = self.agent_executor.invoke({
            "input": user_input,
            "chat_history": chat_history,
            "case_details": self.case_details,
        })
        
        # Get the raw response
        raw_response = result.get("output", "")
        
        # Process the response (summarize if needed)
        if self.role == "judge":
            processed_response = raw_response  # No summarization for judge
        else:
            processed_response = self.summarizer.summarize(raw_response, session_id="default")
            print("Processed response:", processed_response)
        
        # Add the user input and processed response to memory
        self.memory.chat_memory.add_user_message(user_input)
        self.memory.chat_memory.add_ai_message(processed_response)
       
        
        # Return the result including both raw and processed outputs
        return {
            "raw_output": raw_response,
            "processed_output": processed_response,
            **result
        }
    
    def create_runnable(self) -> Runnable:
        """Creates a custom runnable that manages memory explicitly"""
        return RunnableLambda(self.process_and_execute)
    # Ishan Insted of modifying here why dont you modify class so we just pass the Argument to summerise or not. 