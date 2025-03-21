from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
import os
import pandas as pd
from typing import List, Dict, Any
import glob

# Set Google API Key (replace with actual key or use environment variable)
os.environ["GOOGLE_API_KEY"] = "AIzaSyAys9j5WcbyzR-Xvn2Xb0QCpJft6BTkWjo"  # Replace with environment variable in production

class LegalDocumentProcessor:
    def __init__(self, embedding_model="models/text-embedding-004", 
                 chunk_size=800, chunk_overlap=200):
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embeddings = GoogleGenerativeAIEmbeddings(model=self.embedding_model)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size, 
            chunk_overlap=self.chunk_overlap
        )
    
    def process_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Process PDF files and return chunks of text with metadata."""
        print(f"Processing PDF: {file_path}")
        # Extract filename without extension as case name
        file_name = os.path.basename(file_path)
        case_name = os.path.splitext(file_name)[0]
        
        document = PdfReader(file_path)
        raw_text = ''.join(page.extract_text() for page in document.pages if page.extract_text())
        chunks = self.text_splitter.split_text(raw_text)
        
        # Create documents with metadata
        documents = []
        for i, chunk in enumerate(chunks):
            doc = {
                "text": chunk,
                "metadata": {
                    "source": file_path,
                    "case_name": case_name,
                    "chunk_number": i+1,
                    "total_chunks": len(chunks)
                }
            }
            documents.append(doc)
        
        print(f"  Created {len(documents)} chunks from {file_name}")
        return documents
    
    def process_landmark_cases_directory(self, directory_path: str) -> List[Dict[str, Any]]:
        """Process all PDF files in the landmark cases directory."""
        print(f"Processing all PDFs in directory: {directory_path}")
        all_documents = []
        
        # Get all PDF files in the directory
        pdf_files = glob.glob(os.path.join(directory_path, "*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {directory_path}")
            return all_documents
        
        # Process each PDF file
        for pdf_file in pdf_files:
            documents = self.process_pdf(pdf_file)
            all_documents.extend(documents)
        
        print(f"Total documents from landmark cases directory: {len(all_documents)}")
        return all_documents
    
    def process_constitutional_docs(self, file_path: str, doc_type: str) -> List[Dict[str, Any]]:
        """Process constitutional documents like BNS and Constitution with appropriate metadata."""
        print(f"Processing {doc_type}: {file_path}")
        document = PdfReader(file_path)
        raw_text = ''.join(page.extract_text() for page in document.pages if page.extract_text())
        
        # Split text into chunks
        chunks = self.text_splitter.split_text(raw_text)
        
        # Add metadata to each chunk
        documents = []
        for i, chunk in enumerate(chunks):
            doc = {
                "text": chunk,
                "metadata": {
                    "source": doc_type,
                    "chunk_number": i+1,
                    "total_chunks": len(chunks)
                }
            }
            documents.append(doc)
        
        print(f"  Created {len(documents)} chunks from {doc_type}")
        return documents

    def process_csv_supreme_court(self, file_path: str) -> List[Dict[str, Any]]:
        """Process the Supreme Court CSV file handling longer entries appropriately."""
        print(f"Processing CSV: {file_path}")
        df = pd.read_csv(file_path)
        
        documents = []
        for _, row in df.iterrows():
            # Extract the case title/number for citation
            case_title = row.get('Cause Title/Case No.', '')
            
            # Format the full text
            full_text = f"Case: {case_title}\n"
            full_text += f"Date: {row.get('Date of Judgment', '')}\n"
            full_text += f"Subject: {row.get('Subject', '')}\n"
            full_text += f"Summary: {row.get('Judgment Summary', '')}\n"
            
            # Create metadata
            metadata = {
                "case_title": case_title,
                "date": row.get('Date of Judgment', ''),
                "subject": row.get('Subject', ''),
                "serial_number": row.get('Serial Number', ''),
                "source": "supreme_court_judgments_cleaned.csv"
            }
            
            # Check if the text is too long
            if len(full_text) > self.chunk_size:
                # Split the summary but keep the citation and essential info
                summary_text = row.get('Judgment Summary', '')
                summary_chunks = self.text_splitter.split_text(summary_text)
                
                # Create a document for each chunk, preserving the citation in each
                for i, chunk in enumerate(summary_chunks):
                    chunk_doc = {
                        "text": f"Case: {case_title} (Part {i+1}/{len(summary_chunks)})\n"
                               f"Date: {row.get('Date of Judgment', '')}\n"
                               f"Subject: {row.get('Subject', '')}\n"
                               f"Summary (Part {i+1}/{len(summary_chunks)}): {chunk}\n",
                        "metadata": {**metadata, "chunk_number": i+1, "total_chunks": len(summary_chunks)}
                    }
                    documents.append(chunk_doc)
            else:
                # If the text fits within our chunk size, keep it as is
                documents.append({
                    "text": full_text,
                    "metadata": metadata
                })
        
        print(f"  Created {len(documents)} documents from CSV")
        return documents

    def create_faiss_index(self, documents: List[Dict[str, Any]], index_name: str) -> FAISS:
        """Create a FAISS index from documents with metadata."""
        print(f"Creating FAISS index: {index_name}")
        
        # Extract texts and metadatas
        texts = [doc["text"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]
        
        # Create and save the FAISS index
        db = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)
        db.save_local(f"../../vector_database/faiss_{index_name}")
        print(f"  Saved FAISS index: faiss_{index_name}")
        return db

# Main execution
def main():
    # Initialize the processor
    processor = LegalDocumentProcessor(chunk_size=800, chunk_overlap=200)
    
    # # Process BNS and Constitution PDF files (with metadata)
    bns_docs = processor.process_constitutional_docs("../../Processed_Data/Laws_Constitution/BNS.pdf", "BNS")
    processor.create_faiss_index(bns_docs, "bns")
    
    constitution_docs = processor.process_constitutional_docs("../../Processed_Data/Laws_Constitution/constitution.pdf", "Constitution")
    processor.create_faiss_index(constitution_docs, "constitution")
    
    # Process Supreme Court CSV
    supreme_court_csv = processor.process_csv_supreme_court("../../Processed_Data/PreviousCases/supreme_court_judgments_cleaned.csv")
    processor.create_faiss_index(supreme_court_csv, "supreme_court_csv")
    
    # Process all PDFs in the 100LandmarkCases directory
    landmark_cases_directory = "../../Processed_Data/PreviousCases/landmark_cases"
    landmark_cases_docs = processor.process_landmark_cases_directory(landmark_cases_directory)
    processor.create_faiss_index(landmark_cases_docs, "landmark_cases")
    
    print("All FAISS stores created successfully!")

if __name__ == "__main__":
    main()