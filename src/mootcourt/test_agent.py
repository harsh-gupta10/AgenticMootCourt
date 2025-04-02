import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain.schema import HumanMessage
from mootcourt.court_agent import CourtAgentRunnable
import os
from langchain_groq import ChatGroq
from Initlise import initilise_llm_and_databases

# Create LLM instance
def create_llm( Provider , model , temprature):
    if Provider=="Google" and model=="gemini-1.5-flash":
       return ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=temprature)
    elif Provider=="Groq" and  model=="llama-3.3-70b-versatile":
      return ChatGroq( model="llama-3.3-70b-versatile", temperature=temprature)

os.environ["GROQ_API_KEY"] = "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"
#llm = create_llm(Provider="Groq" , model="llama-3.3-70b-versatile" , temprature=0.2)

def main():
    # Initialize Gemini model with proper API key
    os.environ["GOOGLE_API_KEY"] = "AIzaSyAys9j5WcbyzR-Xvn2Xb0QCpJft6BTkWjo"
    api_key=os.environ["GOOGLE_API_KEY"]
    if not api_key:
        print("WARNING: No API key found. Please set your GOOGLE_API_KEY environment variable.")
        return
    
    genai.configure(api_key=api_key)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.2)
    _,faiss_bns,faiss_constitution,faiss_lc,faiss_sc_lc = initilise_llm_and_databases()


    case_details="IGNORE LINE."
    # Initialize CourtAgentRunnable
    chatbot = CourtAgentRunnable(llm,"test",case_details,faiss_constitution,faiss_bns,faiss_lc,faiss_sc_lc,max_iter=5)

    # Create runnable agent
    chat_agent = chatbot.create_runnable()
    # Chat Loop
    print("Legal Assistant Chatbot (type 'exit' to stop)\n")
    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            break

        try:
            print("Passing input:", user_input)
            response = chat_agent.invoke(
                {"input": user_input,
                 "case_details": case_details},
                config={"configurable": {"session_id": "legal-session-123"}}
            )
            print("The bot will answer now.")
            print("\nBot:", response["output"])
        except Exception as e:
            import traceback    
            print("Error:", e)
            traceback.print_exc()

if __name__ == "__main__":
    main()