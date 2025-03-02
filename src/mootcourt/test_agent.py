import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain.schema import HumanMessage
from court_agent import CourtAgentRunnable
import os

def main():
    # Initialize Gemini model with proper API key
    os.environ["GOOGLE_API_KEY"] = "AIzaSyAys9j5WcbyzR-Xvn2Xb0QCpJft6BTkWjo"
    api_key=os.environ["GOOGLE_API_KEY"]
    if not api_key:
        print("WARNING: No API key found. Please set your GOOGLE_API_KEY environment variable.")
        return
    
    genai.configure(api_key=api_key)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)

    # Load FAISS stores
    try:
        embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        faiss_store1 = FAISS.load_local("faiss_bns", embedding_model, allow_dangerous_deserialization=True)
        faiss_store2 = FAISS.load_local("faiss_constitution", embedding_model, allow_dangerous_deserialization=True)
        
        print("FAISS stores loaded successfully")
    except Exception as e:
        print(f"Error loading FAISS stores: {e}")
        return

    # Initialize CourtAgentRunnable
    chatbot = CourtAgentRunnable(
        llm=llm,
        role="Legal Assistant specialized in constitutional law",
        case_details="The case involves constitutional law disputes regarding rights and freedoms.",
        faiss_store1=faiss_store1,
        faiss_store2=faiss_store2
    )

    # Create runnable agent
    chat_agent = chatbot.create_runnable()

    # Chat Loop
    print("Legal Assistant Chatbot (type 'exit' to stop)\n")
    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            break

        try:
            # Run the chatbot with FAISS retrieval
            print("Passing input:", user_input)
            response = chat_agent.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": "legal-session-123"}}
            )
            print("The bot will answer now.")
            print("\nBot:", response.content)
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()