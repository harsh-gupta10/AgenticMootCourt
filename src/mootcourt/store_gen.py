from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
import os

# Set Google API Key (replace with actual key or use environment variable)
os.environ["GOOGLE_API_KEY"] = "AIzaSyAys9j5WcbyzR-Xvn2Xb0QCpJft6BTkWjo"

# Function to load and process PDF files
def load_and_process_pdf(file_path):
    document = PdfReader(file_path)
    raw_text = ''.join(page.extract_text() for page in document.pages if page.extract_text())
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=400)
    split_docs = text_splitter.split_text(raw_text)
    return split_docs

# Load BNS and Constitution PDF files
bns_docs = load_and_process_pdf("BNS.pdf")
constitution_docs = load_and_process_pdf("constitution.pdf")

# Initialize Gemini embeddings model
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# Create FAISS stores
bns_store = FAISS.from_texts(bns_docs, embeddings)
constitution_store = FAISS.from_texts(constitution_docs, embeddings)

# Save FAISS indexes locally
bns_store.save_local("faiss_bns")
constitution_store.save_local("faiss_constitution")

print("FAISS stores for BNS and Constitution created successfully!")
