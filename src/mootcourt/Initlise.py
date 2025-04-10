from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_vertexai import ChatVertexAI
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
import google.generativeai as genai
from langchain_openai import ChatOpenAI
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
import getpass
from langchain_groq import ChatGroq
import os




def initilise_llm_and_databases():
    """ Its Used to initlise LLm and vector database
        Return:
          llm:
          faiss_bns:
          faiss_constitution:
          faiss_lc:
          faiss_sc_lc:
    """
    # Set up API keys
    os.environ["GOOGLE_API_KEY"] = "AIzaSyAys9j5WcbyzR-Xvn2Xb0QCpJft6BTkWjo"
    os.environ["GROQ_API_KEY"] = "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"
    os.environ["OPENROUTER_API_KEY"] = "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"
    os.environ["OPENROUTER_API_BASE"] = "https://openrouter.ai/api/v1"

    api_key = os.environ["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)

    # Initialize FAISS stores (Placeholder, replace with actual instances)
    embedding_model = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    faiss_bns = FAISS.load_local("../../vector_database/faiss_bns", embedding_model, allow_dangerous_deserialization=True)
    faiss_constitution = FAISS.load_local("../../vector_database/faiss_constitution", embedding_model, allow_dangerous_deserialization=True)
    faiss_lc = FAISS.load_local("../../vector_database/faiss_landmark_cases", embedding_model, allow_dangerous_deserialization=True)
    faiss_sc_lc = FAISS.load_local("../../vector_database/faiss_supreme_court_csv", embedding_model, allow_dangerous_deserialization=True)


    # Create LLM instance
    def create_llm( Provider , model , temprature):
        if Provider=="Google":
          return ChatVertexAI(model=model, temperature=temprature)
        elif Provider=="Groq":
          return ChatGroq(model, temperature=temprature)
        elif Provider=="OpenRouter":
          return ChatOpenAI(model=model,openai_api_key=os.environ["OPENROUTER_API_KEY"],openai_api_base=os.environ["OPENROUTER_API_BASE"],temperature=temprature)



    # llm = create_llm()
    llm = create_llm(Provider="Google" , model="gemini-2.5-pro-preview-03-25" , temprature=0.1)
    # llm = create_llm(Provider="Groq" , model="deepseek-r1-distill-llama-70b" , temprature=0.2)
    # llm = create_llm(Provider="OpenRouter" , model="google/gemini-2.5-pro-exp-03-25:free" , temprature=0.1)
    # llm = create_llm(Provider="OpenRouter" , model="google/gemini-2.0-flash-exp:free" , temprature=0.1)
    # faiss_sc_lc = FAISS.load_local("../../vector_database/faiss_supreme_court_csv", embedding_model, allow_dangerous_deserialization=True)
    return llm,faiss_bns,faiss_constitution,faiss_lc,faiss_sc_lc

