from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableLambda, Runnable
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool
from Prompts_normal import judge_prompt, defendant_prompt, reviewer_prompt, test_prompt
from argsumm_test import LegalArgumentSummarizer

class CourtAgentRunnable:
    def __init__(self, llm, role, case_details, constitution_store, bns_store, Landmark_Cases_store, SC_Landmark_Cases_store, memory_store=None, max_iter=20):
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
        

        # Tool implementation methods
        def _search_constitution_store(self, query):
            """Search the constitution store for relevant text"""
            docs = self.constitution_store.invoke(query)
            if docs and len(docs) > 0:
                answer = docs[0].page_content if hasattr(docs[0], 'page_content') else str(docs[0])
            else:
                answer = "No relevant constitutional provisions found."
            print("Searching constitution store.............")
            return answer
            
        def _search_bns_store(self, query):
            """Search the BNS store for relevant text"""
            docs = self.bns_store.invoke(query)
            if docs and len(docs) > 0:
                answer = docs[0].page_content if hasattr(docs[0], 'page_content') else str(docs[0])
            else:
                answer = "No relevant BNS provisions found."
            print("Searching BNS store.............")
            return answer
            
        def _search_landmark_cases(self, query):
            """Search the Landmark Cases for relevant text"""
            docs = self.Landmark_Cases_store.invoke(query)
            if docs and len(docs) > 0:
                answer = docs[0].page_content if hasattr(docs[0], 'page_content') else str(docs[0])
            else:
                answer = "No relevant landmark cases found."
            print("Searching Landmark Cases.............")
            return answer
            
        def _search_sc_landmark_cases(self, query):
            """Search the Supreme Court Landmark Cases for relevant text"""
            docs = self.SC_Landmark_Cases_store.invoke(query)
            if docs and len(docs) > 0:
                answer = docs[0].page_content if hasattr(docs[0], 'page_content') else str(docs[0])
            else:
                answer = "No relevant Supreme Court landmark cases found."
            print("Searching Supreme Court Landmark Cases.............")
            return answer

        # Add the methods to the instance
        self._search_constitution_store = _search_constitution_store.__get__(self)
        self._search_bns_store = _search_bns_store.__get__(self)
        self._search_landmark_cases = _search_landmark_cases.__get__(self)
        self._search_sc_landmark_cases = _search_sc_landmark_cases.__get__(self)



        # Define retrieval tools
        self.tools = [
            Tool(
                name="search_constitution_store",
                description="Search the constitution store for relevant text using FAISS",
                func=self._search_constitution_store
            ),
            Tool(
                name="search_BHARATIYA_NYAYA_SANHITA_store",
                description="Search the BNS store for relevant text using FAISS",
                func=self._search_bns_store
            ),
            Tool(
                name="Landmark_Cases",
                description="Search the Landmark Cases for relevant text using FAISS",
                func=self._search_landmark_cases
            ),
            Tool(
                name="Supreme_Court_Landmark_Cases",
                description="Search the Supreme Court Landmark Cases for relevant text using FAISS",
                func=self._search_sc_landmark_cases
            )
        ]

        # Select prompt based on role
        base_prompt_template = None
        if role == "judge":
            base_prompt_template = judge_prompt
        elif role == "respondent":
            base_prompt_template = defendant_prompt
        elif role == "reviewer":
            base_prompt_template = reviewer_prompt
        elif role == "test":
            base_prompt_template = test_prompt
        else:
            raise ValueError("Invalid role. Please choose from 'judge', 'respondent', 'test' or 'reviewer'.")


        # Create the StructuredChatAgent that works with any LLM
        chat_prompt = ChatPromptTemplate.from_messages([
            ("user", base_prompt_template)
        ])

        self.agent = create_tool_calling_agent(llm=self.llm, tools=self.tools, prompt=chat_prompt)
        
        # Create the agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            max_iterations=20,
            handle_parsing_errors=True,
            verbose=True,
            return_intermediate_steps=True
        )

    def get_session_history(self, session_id):
        """Retrieve chat history."""
        return self.memory.chat_memory.messages

    def process_and_execute(self, input_data):
        """Summarizes the output of the agent before storing it in memory."""
        # Extract the input message
        user_input = input_data["input"]
        chat_history = self.get_session_history("default")
        
        # Execute the agent with the input and history
        result = self.agent_executor.invoke({
            "input": user_input,
            "chat_history": chat_history,
            "case_details": self.case_details,
            "agent_scratchpad": ""
        })
        
        # Get the raw response
        raw_response = result.get("output", "")
        raw_response = result.get("output", "")
        raw_response = raw_response.split("Final Answer:")[-1].strip()
        result["output"] = raw_response
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
    
    def normal_execute(self, input_data):
        """Does not summarize the output"""
        # Extract the input message
        user_input = input_data["input"]
        chat_history = self.get_session_history("default")
        # Execute the agent with the input and history
        result = self.agent_executor.invoke({
            "input": user_input,
            "chat_history": chat_history,
            "case_details": self.case_details,
            "agent_scratchpad":[""]
        })
        
        raw_response = result.get("output", "")
        raw_response= raw_response.split("Final Answer:")[-1].strip()
        result["output"] = raw_response
        processed_response = raw_response
        self.memory.chat_memory.add_user_message(user_input)
        self.memory.chat_memory.add_ai_message(processed_response)
        
        # Return the result including both raw and processed outputs
        return {
            "raw_output": raw_response,
            "processed_output": processed_response,
            **result
        }

    def create_runnable(self) -> Runnable:
        # Create a simple runnable that calls our process_and_execute method
        return RunnableLambda(self.process_and_execute)