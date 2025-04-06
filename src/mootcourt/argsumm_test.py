from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory
from langchain.schema import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import os
# Note: You should use environment variables for API keys in production
# import os
# os.environ["GOOGLE_API_KEY"] = "your-api-key"

class LegalArgumentSummarizer:
    def __init__(self, model="google/gemini-2.0-flash-exp:free", google_api_key="AIzaSyAys9j5WcbyzR-Xvn2Xb0QCpJft6BTkWjo", temperature=0.1):
        self.llm = ChatOpenAI(model=model,openai_api_key=os.environ["OPENROUTER_API_KEY"],openai_api_base=os.environ["OPENROUTER_API_BASE"],temperature=temperature)
        self.prompt = PromptTemplate(
            input_variables=["input"],
            template=(
                """ Summarize the input in the format (DO NOT ADD ANY EXTRA TEXT):
                    Key Points: [Summarize the input in 2-3 sentences, focusing on facts, claims, and reasoning related to legal principles or arguments.]
                    Precedents: [List relevant legal cases or statutes in this format: Case Name (Year) – Key principle or holding.]
                    Additional Instructions:
                    - A legal argument refers to any text presenting facts, claims, reasoning, or analysis related to legal principles, cases, statutes, or rights.
                    - If no precedents are explicitly mentioned in the input, return the precedents as none.
                    - If the input is not a legal argument (e.g., casual questions or unrelated content), return it as is without modification.

                    Example 1:
                    Input: "The accused acted in self-defense after being physically attacked. The accused reasonably believed that harm was imminent and used proportionate force."
                    Output:
                    Key Points: The accused acted in self-defense after being physically attacked. The accused reasonably believed that harm was imminent and used proportionate force.
                    Precedents: People v. Goetz (1986) – A defendant's belief in imminent danger must be reasonable.

                    Example 2:
                    Input: "The police conducted a search without a valid warrant, violating the accused's Fourth Amendment rights. The evidence obtained should be excluded from trial."
                    Output:
                    Key Points: The police conducted a search without a valid warrant, violating the accused's Fourth Amendment rights. The evidence obtained should be excluded from trial.
                    Precedents: Mapp v. Ohio (1961) – Illegally obtained evidence is inadmissible in court.

                    Example 3:
                    Input: "May I begin your Lordship?"
                    Output: "May I begin your Lordship?"

                    Input:
                    {input}
                """
            )
        )
        self.summarization_chain = self.prompt | self.llm | StrOutputParser()

    def summarize(self, legal_argument: str, session_id: str = "default") -> str:
        return self.summarization_chain.invoke(
            {"input": legal_argument},
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