# from langchain_community.vectorstores import FAISS
# from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain_community.document_loaders import PyPDFLoader
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from PyPDF2 import PdfReader
# import os

# # Set Google API Key (replace with actual key or use environment variable)
# os.environ["GOOGLE_API_KEY"] = "AIzaSyAys9j5WcbyzR-Xvn2Xb0QCpJft6BTkWjo"

# # Function to load and process PDF files
# def load_and_process_pdf(file_path):
#     document = PdfReader(file_path)
#     raw_text = ''.join(page.extract_text() for page in document.pages if page.extract_text())
#     text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=400)
#     split_docs = text_splitter.split_text(raw_text)
#     return split_docs

# # Load BNS and Constitution PDF files
# bns_docs = load_and_process_pdf("../../Processed_Data/Laws_Constitution/BNS.pdf")
# constitution_docs = load_and_process_pdf("../../Processed_Data/Laws_Constitution/constitution.pdf")

# # Initialize Gemini embeddings model
# embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# # Create FAISS stores
# bns_store = FAISS.from_texts(bns_docs, embeddings)
# constitution_store = FAISS.from_texts(constitution_docs, embeddings)

# # Save FAISS indexes locally
# bns_store.save_local("../../vector_database/faiss_bns")
# constitution_store.save_local("../../vector_database/faiss_constitution")

# print("FAISS stores for BNS and Constitution created successfully!")



from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader, CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
import os
import json
import pandas as pd
import docx
from typing import List, Dict, Any, Optional
import re

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
    
    def process_pdf(self, file_path: str) -> List[str]:
        """Process PDF files and return chunks of text."""
        print(f"Processing PDF: {file_path}")
        document = PdfReader(file_path)
        raw_text = ''.join(page.extract_text() for page in document.pages if page.extract_text())
        split_docs = self.text_splitter.split_text(raw_text)
        print(f"  Created {len(split_docs)} chunks from PDF")
        return split_docs
    
    def process_docx(self, file_path: str) -> List[str]:
        """Process DOCX files and return chunks of text."""
        print(f"Processing DOCX: {file_path}")
        doc = docx.Document(file_path)
        raw_text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        split_docs = self.text_splitter.split_text(raw_text)
        print(f"  Created {len(split_docs)} chunks from DOCX")
        return split_docs
    
    def process_json_landmark_cases(self, file_path: str) -> List[Dict[str, Any]]:
        """Process the landmark cases JSON file and treat each case as a document."""
        print(f"Processing JSON: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # For landmark cases, we want to keep each case as a whole
        formatted_cases = []
        for case in data:
            # Create a document dict with formatted text and metadata
            case_doc = {
                "text": self._format_case_text(case),
                "metadata": {
                    "topic": case.get("Topic", ""),
                    "part": case.get("Part", ""),
                    "part_name": case.get("Part_Name", ""),
                    "case_name": case.get("Name of the case", ""),
                    "source": "landmark_cases.json"
                }
            }
            formatted_cases.append(case_doc)
        
        print(f"  Created {len(formatted_cases)} case documents from JSON")
        return formatted_cases
    
    def _format_case_text(self, case: Dict[str, Any]) -> str:
        """Format the case text in a consistent way."""
        # Compile all available fields into a formatted string
        case_text = f"Case: {case.get('Name of the case', 'Unknown')}\n"
        if case.get("Topic"):
            case_text += f"Topic: {case['Topic']}\n"
        if case.get("Part") and case.get("Part_Name"):
            case_text += f"Constitutional Part: {case['Part']} ({case['Part_Name']})\n"
        if case.get("Bench"):
            case_text += f"Bench: {case['Bench']}\n"
        if case.get("Issue"):
            case_text += f"Issue: {case['Issue']}\n"
        if case.get("Fact of the Case"):
            case_text += f"Facts: {case['Fact of the Case']}\n"
        if case.get("Ratio"):
            case_text += f"Ratio: {case['Ratio']}\n"
        if case.get("Judgment"):
            case_text += f"Judgment: {case['Judgment']}\n"
        if case.get("case_details"):
            case_text += f"Additional Details: {case['case_details']}\n"
        
        return case_text
    
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
    
    def create_faiss_index_from_texts(self, texts: List[str], index_name: str) -> FAISS:
        """Create a FAISS index from text chunks."""
        print(f"Creating FAISS index: {index_name}")
        db = FAISS.from_texts(texts, self.embeddings)
        db.save_local(f"../../vector_database/faiss_{index_name}")
        print(f"  Saved FAISS index: faiss_{index_name}")
        return db

# Main execution
def main():
    # Initialize the processor
    processor = LegalDocumentProcessor(chunk_size=800, chunk_overlap=200)
    
    
    # Process BNS and Constitution PDF files (with metadata)
    bns_docs = processor.process_constitutional_docs("../../Processed_Data/Laws_Constitution/BNS.pdf", "BNS")
    processor.create_faiss_index(bns_docs, "bns")
    
    constitution_docs = processor.process_constitutional_docs("../../Processed_Data/Laws_Constitution/constitution.pdf", "Constitution")
    processor.create_faiss_index(constitution_docs, "constitution")

    # Process PDF files
    landmark_judgments_pdf = processor.process_pdf("../../Processed_Data/PreviousCases/LANDMARK_JUDGMENTS_OF_THE_SUPREME_COURT.pdf")
    processor.create_faiss_index_from_texts(landmark_judgments_pdf, "landmark_judgments_pdf")
    
    # Process DOCX files
    landmark_cases_docx = processor.process_docx("../../Processed_Data/PreviousCases/100LandmarkCases.docx")
    processor.create_faiss_index_from_texts(landmark_cases_docx, "landmark_cases_docx")
    
    # Process JSON landmark cases
    landmark_cases_json = processor.process_json_landmark_cases("../../Processed_Data/PreviousCases/landmark_cases.json")
    processor.create_faiss_index(landmark_cases_json, "landmark_cases_json")
    
    # Process Supreme Court CSV
    supreme_court_csv = processor.process_csv_supreme_court("../../Processed_Data/PreviousCases/supreme_court_judgments_cleaned.csv")
    processor.create_faiss_index(supreme_court_csv, "supreme_court_csv")
    
    print("All FAISS stores created successfully!")

if __name__ == "__main__":
    main()