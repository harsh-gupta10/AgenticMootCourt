from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
from langchain.schema import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Note: You should use environment variables for API keys in production
# import os
# os.environ["GOOGLE_API_KEY"] = "your-api-key"

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    google_api_key="AIzaSyAys9j5WcbyzR-Xvn2Xb0QCpJft6BTkWjo",  
    temperature=0.2
)

# Create prompt template
prompt = PromptTemplate(
    input_variables=["legal_argument"],
    template=(
        """Summarize the following Indian legal argument in the format(DO NOT ADD ANY EXTRA TEXT):
            Label: [Argument Label(of form A1,A2,..)]
            Key Points: [Brief description of the argument, including facts, claims, and reasoning]
            Precedents: [List of relevant legal cases or statutes]
            Supporting/Answering: [List of argument labels that support or answer this argument]
            Opposing/Questioning: [List of argument labels that challenge or question this argument]
            
            Answer **None** for any missing information. Use previous argument summaries for connecting arguments.
            Below are some examples:
            Example 1:
                Label: A1
                Key Points: The accused acted in self-defense after being physically attacked. The accused reasonably believed that harm was imminent and used proportionate force.
                Precedents: People v. Goetz (1986) – A defendant's belief in imminent danger must be reasonable.
                Supporting/Answering: A4, A7
                Opposing/Questioning: A2, A6
                
            Example 2:
                Label: A2
                Key Points: The police conducted a search without a valid warrant, violating the accused's Fourth Amendment rights. The evidence obtained should be excluded from trial.
                Precedents: Mapp v. Ohio (1961) – Illegally obtained evidence is inadmissible in court.
                Supporting/Answering: A5, A6
                Opposing/Questioning: A1, A8
                
            Example 3:
                Label: A3
                Key Points: The defendant knowingly misrepresented financial statements to deceive investors, constituting securities fraud.
                Precedents: United States v. O'Hagan (1997) – Misrepresentation in financial markets constitutes fraud.
                Supporting/Answering: A2, A9
                Opposing/Questioning: A8, A10

            Legal Argument:
            {legal_argument}
            Chat history: {history}
        """
    )
)

# Build the chain
chain = prompt | llm | StrOutputParser()

# Setup message history
chat_memory = ChatMessageHistory()

# Setup message history
def get_session_history(session_id: str) -> ChatMessageHistory:
    return chat_memory

# Create the RunnableWithMessageHistory
summarization_chain = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_message_key="legal_argument",
    history_messages_key="history"
)

def summarize_legal_argument(legal_argument: str, session_id: str = "default") -> str:
    return summarization_chain.invoke(
        {"legal_argument": legal_argument},
        config={"configurable": {"session_id": session_id}}
    )

if __name__ == "__main__":
    user_input = ""
    session_id = "user_session_1"  
    
    while user_input != "exit":
        user_input = input("Enter the legal argument to summarize:\n")
        if user_input == "exit":
            break
        
        summary = summarize_legal_argument(user_input, session_id)
        chat_memory.add_message(summary)
        print("\nSummary:\n", summary)