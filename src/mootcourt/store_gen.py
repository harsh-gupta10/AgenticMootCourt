from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

# Set Google API Key (replace with actual key or use environment variable)
os.environ["GOOGLE_API_KEY"] = "AIzaSyAys9j5WcbyzR-Xvn2Xb0QCpJft6BTkWjo"

# Function to load and process PDF files
def load_and_process_pdf(file_path):
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = text_splitter.split_documents(documents)
    return split_docs

# Load BNS and Constitution PDF files
bns_docs = load_and_process_pdf("BNS.pdf")
constitution_docs = load_and_process_pdf("constitution.pdf")

# Initialize Gemini embeddings model
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Create FAISS stores
bns_store = FAISS.from_documents(bns_docs, embeddings)
constitution_store = FAISS.from_documents(constitution_docs, embeddings)

# Save FAISS indexes locally
bns_store.save_local("faiss_bns")
constitution_store.save_local("faiss_constitution")

print("FAISS stores for BNS and Constitution created successfully!")
