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

class LegalArgumentSummarizer:
    def __init__(self, model="gemini-1.5-pro", google_api_key="AIzaSyAys9j5WcbyzR-Xvn2Xb0QCpJft6BTkWjo", temperature=0.1):
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=google_api_key,
            temperature=temperature
        )
        self.prompt = PromptTemplate(
            input_variables=["input"],
            template=(
                """Summarize the input in the format(DO NOT ADD ANY EXTRA TEXT):
                    Key Points: [Brief description of the input, including facts, claims, and reasoning]
                    Precedents: [List of relevant legal cases or statutes]
                    
                    Answer **None** for any missing information. Return the input as is if it is not a legal argument.
                    Below are some examples:
                    Example 1:
                        Key Points: The accused acted in self-defense after being physically attacked. The accused reasonably believed that harm was imminent and used proportionate force.
                        Precedents: People v. Goetz (1986) – A defendant's belief in imminent danger must be reasonable.
                        
                    Example 2:
                        Key Points: The police conducted a search without a valid warrant, violating the accused's Fourth Amendment rights. The evidence obtained should be excluded from trial.
                        Precedents: Mapp v. Ohio (1961) – Illegally obtained evidence is inadmissible in court.
                        
                    Example 3:
                        Key Points: The defendant knowingly misrepresented financial statements to deceive investors, constituting securities fraud.
                        Precedents: United States v. O'Hagan (1997) – Misrepresentation in financial markets constitutes fraud.
                    Example 4:
                        May I begin your Lordship?
                    Input:
                    {input}
                    Chat history: {history}
                """
            )
        )
        self.chain = self.prompt | self.llm | StrOutputParser()
        self.chat_memory = ChatMessageHistory()
        self.summarization_chain = RunnableWithMessageHistory(
            self.chain,
            self.get_session_history,
            input_message_key="legal_argument",
            history_messages_key="history"
        )

    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        return self.chat_memory

    def summarize(self, legal_argument: str, session_id: str = "default") -> str:
        return self.summarization_chain.invoke(
            {"input": legal_argument},
            config={"configurable": {"session_id": session_id}}
        )

# if __name__ == "__main__":
#     summarizer = LegalArgumentSummarizer()
#     user_input = ""
#     session_id = "user_session_1"  
    
#     while user_input != "exit":
#         user_input = input("Enter the legal argument to summarize:\n")
#         if user_input == "exit":
#             break
        
#         summary = summarizer.summarize(user_input, session_id)
#         summarizer.chat_memory.add_message({"role": "assistant", "content": summary})
#         print("\nSummary:\n", summary)