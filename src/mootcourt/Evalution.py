import json
import csv
import os
from tqdm import tqdm
import numpy as np
import nltk
from nltk.translate.bleu_score import sentence_bleu
from nltk.tokenize import word_tokenize
from rouge import Rouge
from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F
import pickle
from pathlib import Path

# Import your agent
from court_agent import CourtAgentRunnable
from Initlise import initilise_llm_and_databases

# Initialize NLTK components
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Set device to CPU explicitly
device = torch.device("cpu")

# Initialize sentence transformer model for semantic similarity
tokenizer = AutoTokenizer.from_pretrained("law-ai/InLegalBERT")
model = AutoModel.from_pretrained("law-ai/InLegalBERT").to(device)

rouge = Rouge()

# Create a directory for storing gold answer embeddings
EMBEDDINGS_DIR = Path("gold_answer_embeddings")
EMBEDDINGS_DIR.mkdir(exist_ok=True)

# Dictionary to store gold answer embeddings in memory
gold_answer_embeddings = {}

def load_json_data(file_path):
    """Load JSON data from file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def calculate_bleu(generated, reference):
    """Calculate BLEU score"""
    reference_tokens = [word_tokenize(reference.lower())]
    generated_tokens = word_tokenize(generated.lower())
    return sentence_bleu(reference_tokens, generated_tokens)

def calculate_rouge(generated, reference):
    """Calculate ROUGE scores"""
    try:
        scores = rouge.get_scores(generated, reference)[0]
        return {
            'rouge-1': scores['rouge-1']['f'],
            'rouge-2': scores['rouge-2']['f'],
            'rouge-l': scores['rouge-l']['f']
        }
    except:
        return {'rouge-1': 0, 'rouge-2': 0, 'rouge-l': 0}

def get_embedding_filename(text, domain):
    """Generate a unique filename for the given text"""
    import hashlib
    text_hash = hashlib.md5(text.encode()).hexdigest()
    return f"{domain}_gold_{text_hash}.pkl"

def compute_embedding(text):
    """Compute embedding for a given text"""
    encoded_input = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    encoded_input = {k: v.to(device) for k, v in encoded_input.items()}
    
    with torch.no_grad():
        output = model(**encoded_input)
    
    # Extract CLS token embedding
    embedding = output.last_hidden_state[:, 0, :]  # Shape: (1, 768)
    return embedding

def load_gold_embeddings(gold_answers, domain):
    """Load or compute embeddings for gold answers"""
    if domain not in gold_answer_embeddings:
        gold_answer_embeddings[domain] = {}
    
    print(f"Loading gold answer embeddings for {domain}...")
    for gold_answer in tqdm(gold_answers, desc=f"Processing {domain} gold embeddings"):
        if gold_answer in gold_answer_embeddings[domain]:
            continue  # Already loaded
            
        embedding_filename = get_embedding_filename(gold_answer, domain)
        embedding_path = EMBEDDINGS_DIR / embedding_filename
        
        if embedding_path.exists():
            # Load from disk
            with open(embedding_path, 'rb') as f:
                embedding = pickle.load(f)
        else:
            # Compute and save
            embedding = compute_embedding(gold_answer)
            with open(embedding_path, 'wb') as f:
                pickle.dump(embedding, f)
        
        # Store in memory
        gold_answer_embeddings[domain][gold_answer] = embedding
    
    print(f"Loaded {len(gold_answer_embeddings[domain])} gold answer embeddings for {domain}")

def calculate_embedding_similarity(generated, gold_answer, domain):
    """Calculate cosine similarity between generated text and gold answer"""
    # Get gold answer embedding
    if domain not in gold_answer_embeddings or gold_answer not in gold_answer_embeddings[domain]:
        # Compute on the fly if not available
        gold_embedding = compute_embedding(gold_answer)
    else:
        gold_embedding = gold_answer_embeddings[domain][gold_answer]
    
    # Compute embedding for generated text (not cached)
    gen_embedding = compute_embedding(generated)
    
    # Normalize embeddings
    gen_embedding = F.normalize(gen_embedding, p=2, dim=1)
    gold_embedding = F.normalize(gold_embedding, p=2, dim=1)
    
    # Compute cosine similarity
    similarity = torch.mm(gen_embedding, gold_embedding.T).item()
    
    return similarity

def evaluate_legal_qa(questions, generated_answers, gold_answers, domain):
    """Evaluate legal QA performance"""
    results = []
    
    for i in range(len(questions)):
        question = questions[i]
        generated = generated_answers[i]
        gold = gold_answers[i]
        
        # Calculate lexical similarity
        bleu_score = calculate_bleu(generated, gold)
        
        # Calculate ROUGE scores
        rouge_scores = calculate_rouge(generated, gold)
        
        # Calculate semantic similarity
        embedding_similarity = calculate_embedding_similarity(generated, gold, domain)
        
        # Store results
        results.append({
            'domain': domain,
            'question': question,
            'generated_answer': generated,
            'gold_answer': gold,
            'bleu': bleu_score,
            'rouge-1': rouge_scores['rouge-1'],
            'rouge-2': rouge_scores['rouge-2'],
            'rouge-l': rouge_scores['rouge-l'],
            'embedding_similarity': embedding_similarity
        })
    
    return results

def save_to_csv(results, output_file):
    """Save evaluation results to CSV with proper handling of newlines and special characters"""
    fieldnames = ['domain', 'question', 'generated_answer', 'gold_answer', 'bleu', 
                 'rouge-1', 'rouge-2', 'rouge-l', 'embedding_similarity']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        
        # Clean rows before writing
        cleaned_results = []
        for row in results:
            cleaned_row = {}
            for key, value in row.items():
                if isinstance(value, str):
                    # Replace newlines and other problematic characters
                    cleaned_value = value.replace('\n', ' ').replace('\r', ' ')
                    cleaned_row[key] = cleaned_value
                else:
                    cleaned_row[key] = value
            cleaned_results.append(cleaned_row)
            
        writer.writerows(cleaned_results)

# Initialize LLM and databases
llm, faiss_bns, faiss_constitution, faiss_lc, faiss_sc_lc = initilise_llm_and_databases()

# Base prompt for the judge agent
Base_prompt = """
**Role:** You are an Indian moot court **Judge**, responsible for questioning both the **Petitioner** and **Respondent**, testing their legal reasoning, accuracy, and argument strength.

**Backstory:**  
You are an **experienced legal authority**, ensuring **rigorous questioning and fair assessment**. correctly answer the asked Question.

** Answer The asked Question **
Eg:
  {
    "question": "Where are the terms 'Man', 'Woman', 'Person', and 'Public' defined in the Indian Penal Code?",
    "answer": "These terms are defined in the 'General Explanations' section of the Indian Penal Code."
  },
  {
    "question": "Is it permitted for a person accused of an offence to be forced to be a witness against himself?",
    "answer": "No, a person accused of an offence shall not be compelled to be a witness against himself."
  },
  {
    "question": "What is the right to life and personal liberty?",
    "answer": "The right to life and personal liberty means that no person shall be deprived of his life or personal liberty except according to procedure established by law."
  }
"""

# Initialize judge agent
case_details = ""
judge_agent = CourtAgentRunnable(llm, Base_prompt, case_details, faiss_constitution, faiss_bns, faiss_lc, faiss_sc_lc)
judge_runnable = judge_agent.create_runnable()

# Function to get response from judge agent
def get_judge_response(question):
    response = judge_runnable.invoke(
        {"input": question, "role": Base_prompt, "case_details": case_details},
        config={"configurable": {"session_id": "legal-session-123"}}
    )
    return response["output"]

def run_evaluation(use_cached_embeddings=True):
    # Load datasets
    dataset_dir = "../../EvalutionDataset"
    # Create the directory if it doesn't exist
    os.makedirs(dataset_dir, exist_ok=True)
    
    dataset_files = {
        # "Constitution": os.path.join(dataset_dir, "constitution_qa.json"),
        # "CRPC": os.path.join(dataset_dir, "crpc_qa.json"),
        # "IPC": os.path.join(dataset_dir, "ipc_qa.json"),
        "TEST": os.path.join(dataset_dir, "test.json"),
    }
    
    all_results = []
    
    # Process each dataset
    for domain, file_path in dataset_files.items():
        print(f"Processing {domain} dataset...")
        
        # Load the dataset directly (no caching of dataset)
        data = load_json_data(file_path)
        questions = [item["question"] for item in data]
        gold_answers = [item["answer"] for item in data]
        
        # Only cache gold answer embeddings
        if use_cached_embeddings:
            load_gold_embeddings(gold_answers, domain)
        
        generated_answers = []
        
        # Generate answers (no caching of responses)
        for question in tqdm(questions, desc=f"Evaluating {domain} questions"):
            generated_answer = get_judge_response(question)
            generated_answers.append(generated_answer)
        
        # Evaluate answers
        domain_results = evaluate_legal_qa(questions, generated_answers, gold_answers, domain)
        all_results.extend(domain_results)
        
        # Save intermediate results
        save_to_csv(domain_results, f"{domain.lower()}_evaluation_results.csv")
        
    # Save combined results
    save_to_csv(all_results, "combined_evaluation_results.csv")
    
    # Calculate and print summary statistics
    print("\nEvaluation Summary:")
    for domain in dataset_files.keys():
        domain_results = [r for r in all_results if r['domain'] == domain]
        avg_bleu = np.mean([r['bleu'] for r in domain_results])
        avg_rouge_l = np.mean([r['rouge-l'] for r in domain_results])
        avg_embedding_sim = np.mean([r['embedding_similarity'] for r in domain_results])
        
        print(f"\n{domain} Dataset:")
        print(f"  Average BLEU: {avg_bleu:.4f}")
        print(f"  Average ROUGE-L: {avg_rouge_l:.4f}")
        print(f"  Average Embedding Similarity: {avg_embedding_sim:.4f}")
    
    # Overall statistics
    avg_bleu = np.mean([r['bleu'] for r in all_results])
    avg_rouge_l = np.mean([r['rouge-l'] for r in all_results])
    avg_embedding_sim = np.mean([r['embedding_similarity'] for r in all_results])
    
    print("\nOverall:")
    print(f"  Average BLEU: {avg_bleu:.4f}")
    print(f"  Average ROUGE-L: {avg_rouge_l:.4f}")
    print(f"  Average Embedding Similarity: {avg_embedding_sim:.4f}")

if __name__ == "__main__":
    # Set to False to not use cached embeddings, True to use cached embeddings when available
    run_evaluation(use_cached_embeddings=True)