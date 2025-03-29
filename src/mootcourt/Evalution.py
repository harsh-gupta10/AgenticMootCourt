import json
import csv
import os
from tqdm import tqdm
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.translate.bleu_score import sentence_bleu
from nltk.tokenize import word_tokenize
from rouge import Rouge
from sentence_transformers import SentenceTransformer
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

# Create a directory for storing embeddings
EMBEDDINGS_DIR = Path("cached_embeddings")
EMBEDDINGS_DIR.mkdir(exist_ok=True)

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

def get_embedding_path(text, dataset_name):
    """Generate a unique filename for the given text"""
    # Create a hash of the text to use as a filename
    import hashlib
    text_hash = hashlib.md5(text.encode()).hexdigest()
    return EMBEDDINGS_DIR / f"{dataset_name}_{text_hash}.pkl"

def get_cls_embedding(text, dataset_name=None):
    """Get the [CLS] token embedding for a given text, with disk caching."""
    if dataset_name:
        # Check if embedding is already cached
        embedding_path = get_embedding_path(text, dataset_name)
        
        if embedding_path.exists():
            try:
                with open(embedding_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Error loading cached embedding: {e}")
    
    # Calculate embedding if not cached or error loading
    encoded_input = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    
    # Move tensors to CPU
    encoded_input = {k: v.to(device) for k, v in encoded_input.items()}
    
    with torch.no_grad():  # Disable gradient computation
        output = model(**encoded_input)

    # Extract CLS token embedding (batch_size, hidden_dim)
    embedding = output.last_hidden_state[:, 0, :]  # Shape: (1, 768)
    
    # Cache the embedding if dataset_name is provided
    if dataset_name:
        with open(embedding_path, 'wb') as f:
            pickle.dump(embedding, f)
    
    return embedding

def calculate_embedding_similarity(generated, reference, dataset_name=None):
    """Calculate cosine similarity between embeddings of generated and reference texts."""
    gen_embedding = get_cls_embedding(generated, f"{dataset_name}_gen" if dataset_name else None)
    ref_embedding = get_cls_embedding(reference, f"{dataset_name}_ref" if dataset_name else None)

    # Normalize embeddings to unit vectors
    gen_embedding = F.normalize(gen_embedding, p=2, dim=1)
    ref_embedding = F.normalize(ref_embedding, p=2, dim=1)

    # Compute cosine similarity
    similarity = torch.mm(gen_embedding, ref_embedding.T).item()  # Single float value

    return similarity

def cache_gold_embeddings(dataset, domain):
    """Precompute and cache embeddings for gold standard answers"""
    print(f"Caching gold standard embeddings for {domain}...")
    for item in tqdm(dataset, desc=f"Caching {domain} embeddings"):
        question = item["question"]
        gold = item["answer"]
        
        # Cache the question and gold answer embeddings
        _ = get_cls_embedding(question, f"{domain}_question")
        _ = get_cls_embedding(gold, f"{domain}_gold")

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
    """Save evaluation results to CSV"""
    fieldnames = ['domain', 'question', 'generated_answer', 'gold_answer', 'bleu', 
                 'rouge-1', 'rouge-2', 'rouge-l', 'embedding_similarity']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

def run_evaluation(use_cached_datasets=True):
    # Initialize LLM and databases
    llm, faiss_bns, faiss_constitution, faiss_lc, faiss_sc_lc = initilise_llm_and_databases()
    
    # Base prompt for the judge agent
    Base_prompt = """
    **Role:** You are an Indian moot court **Judge**, responsible for questioning both the **Petitioner** and **Respondent**, testing their legal reasoning, accuracy, and argument strength.

    **Backstory:**  
    You are an **experienced legal authority**, ensuring **rigorous questioning and fair assessment**. correctly answer the asked Question.
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
    
    # Load datasets
    dataset_dir = "legal_dataset"
    # Create the directory if it doesn't exist
    os.makedirs(dataset_dir, exist_ok=True)
    
    dataset_files = {
        # "Constitution": os.path.join(dataset_dir, "constitution_qa.json"),
        # "CRPC": os.path.join(dataset_dir, "crpc_qa.json"),
        # "IPC": os.path.join(dataset_dir, "ipc_qa.json"),
        "TEST": os.path.join(dataset_dir, "test.json"),
    }
    
    # Create cached dataset path
    cached_datasets_path = Path("cached_datasets")
    cached_datasets_path.mkdir(exist_ok=True)
    
    all_results = []
    
    # Process each dataset
    for domain, file_path in dataset_files.items():
        print(f"Processing {domain} dataset...")
        
        # Check for cached processed dataset
        cached_file = cached_datasets_path / f"{domain}_processed.pkl"
        
        if use_cached_datasets and cached_file.exists():
            print(f"Loading cached processed dataset for {domain}...")
            with open(cached_file, 'rb') as f:
                cached_data = pickle.load(f)
                data = cached_data.get('data')
                questions = cached_data.get('questions')
                gold_answers = cached_data.get('gold_answers')
        else:
            if os.path.exists(file_path):
                data = load_json_data(file_path)
            else:
                print(f"Warning: Dataset file {file_path} does not exist. Creating a sample dataset.")
                # Create a sample dataset for testing
                data = [
                    {"question": "What is Article 14 of the Indian Constitution?", 
                     "answer": "Article 14 of the Indian Constitution ensures equality before law and equal protection of laws to all persons within the territory of India."}
                ]
                # Save the sample dataset
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
            
            # Limit the number of questions for faster evaluation (optional)
            # Remove this for full evaluation
            data = data[:10]  # First 10 questions for testing
            
            questions = [item["question"] for item in data]
            gold_answers = [item["answer"] for item in data]
            
            # Cache processed dataset
            with open(cached_file, 'wb') as f:
                pickle.dump({
                    'data': data,
                    'questions': questions,
                    'gold_answers': gold_answers
                }, f)
        
        # Cache gold standard embeddings
        cache_gold_embeddings(data, domain)
        
        # Cached responses path
        cached_responses_path = cached_datasets_path / f"{domain}_responses.pkl"
        
        if use_cached_datasets and cached_responses_path.exists():
            print(f"Loading cached responses for {domain}...")
            with open(cached_responses_path, 'rb') as f:
                generated_answers = pickle.load(f)
        else:
            generated_answers = []
            
            # Get generated answers
            for question in tqdm(questions, desc=f"Evaluating {domain} questions"):
                generated_answer = get_judge_response(question)
                generated_answers.append(generated_answer)
            
            # Cache generated responses
            with open(cached_responses_path, 'wb') as f:
                pickle.dump(generated_answers, f)
        
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
    # Set to False to recalculate everything, True to use cached data when available
    run_evaluation(use_cached_datasets=True)