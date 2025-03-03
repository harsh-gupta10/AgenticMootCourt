from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.vectorstores import FAISS
from langchain.tools import Tool

class CourtAgentRunnable:
    def __init__(self, llm, role, case_details, faiss_store1, faiss_store2, memory_store=None):
        self.llm = llm
        self.role = role
        self.case_details = case_details
        self.faiss_store1 = faiss_store1
        self.faiss_store2 = faiss_store2

        # Use persistent memory
        self.memory = memory_store if memory_store else ConversationBufferMemory(
            chat_memory=ChatMessageHistory(),
            return_messages=True
        )

    def retrieve_from_law_doc(self, query, k=3):
        """Retrieve relevant documents from both FAISS stores."""
        docs1 = self.faiss_store1.similarity_search(query, k=k)
        docs2 = self.faiss_store2.similarity_search(query, k=k)
        merged_docs = docs1 + docs2  # Merge results
        
        # Return document content as a string
        retrieved_content = "\n\n".join([doc.page_content for doc in merged_docs])
        print(f"Retrieved content: {retrieved_content[:100]}...")  # Debug print
        return retrieved_content

    def get_session_history(self, session_id):
        """Retrieve chat history."""
        return self.memory.chat_memory

    def create_runnable(self) -> RunnableWithMessageHistory:
        """Creates a RunnableWithMessageHistory with FAISS retrieval properly integrated."""
        
        # Create a more comprehensive prompt that uses only HumanMessage and AIMessage
        # instead of SystemMessage which might be causing compatibility issues
        prompt = ChatPromptTemplate.from_messages([
            # Convert system messages to AI messages for compatibility
            ("ai", "{role}"),
            ("ai", "Case Details: {case_details}"),
            ("ai", "I've retrieved these relevant legal documents: {retrieved_docs}"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])

        # Define a function to prepare context with retrieved documents
        def prepare_inputs(input_dict):
            query = input_dict.get("input", "")
            # Include chat_history in the prepared inputs
            chat_history = input_dict.get("chat_history", [])
            
            retrieved_docs = self.retrieve_from_law_doc(query)
            
            return {
                "input": query,
                "retrieved_docs": retrieved_docs,
                "case_details": self.case_details,
                "role": self.role,
                "chat_history": chat_history
            }

        # Define the improved chain that includes retrieval
        chain = (
            RunnableLambda(prepare_inputs)
            | prompt
            | self.llm
        )

        # Wrap with message history
        return RunnableWithMessageHistory(
            runnable=chain,
            get_session_history=self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history"
        )