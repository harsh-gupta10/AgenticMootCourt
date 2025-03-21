import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain.schema import HumanMessage
from court_agent_exp import CourtAgentRunnable
import os

def main():
    # Initialize Gemini model with proper API key
    os.environ["GOOGLE_API_KEY"] = "AIzaSyAys9j5WcbyzR-Xvn2Xb0QCpJft6BTkWjo"
    api_key=os.environ["GOOGLE_API_KEY"]
    if not api_key:
        print("WARNING: No API key found. Please set your GOOGLE_API_KEY environment variable.")
        return
    
    genai.configure(api_key=api_key)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.2)

    # Load FAISS stores
    try:
        embedding_model = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        faiss_store1 = FAISS.load_local("../../vector_database/faiss_bns", embedding_model, allow_dangerous_deserialization=True)
        faiss_store2 = FAISS.load_local("../../vector_database/faiss_constitution", embedding_model, allow_dangerous_deserialization=True)
        
        print("FAISS stores loaded successfully")
    except Exception as e:
        print(f"Error loading FAISS stores: {e}")
        return
    

    # Role and case details
    role  = """You are a legal professional well versed in Indian constitutional law. You are tasked with answering legal questions of the user.
    You are to provide legal advice and information based on the Indian Constitution and the Bhartiya Nyay Sanhita(BNS)"""

    case_details="THIS IS A PLACEHOLDER. IGNORE THIS LINE."
    # Initialize CourtAgentRunnable
    chatbot = CourtAgentRunnable(llm,role,case_details,faiss_store2,faiss_store1,max_iter=3)

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
                 "role": role,
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