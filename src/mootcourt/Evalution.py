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
import pandas as pd
from pathlib import Path

# Import your agent
from court_agent_react import CourtAgentRunnable
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

def calculate_bleu(generated, reference):
    """Calculate BLEU score"""
    if not generated or not reference:
        return 0
    reference_tokens = [word_tokenize(reference.lower())]
    generated_tokens = word_tokenize(generated.lower())
    return sentence_bleu(reference_tokens, generated_tokens)

def calculate_rouge(generated, reference):
    """Calculate ROUGE scores"""
    if not generated or not reference:
        return {'rouge-1': 0, 'rouge-2': 0, 'rouge-l': 0}
    try:
        scores = rouge.get_scores(generated, reference)[0]
        return {
            'rouge-1': scores['rouge-1']['f'],
            'rouge-2': scores['rouge-2']['f'],
            'rouge-l': scores['rouge-l']['f']
        }
    except:
        return {'rouge-1': 0, 'rouge-2': 0, 'rouge-l': 0}

def compute_embedding(text):
    """Compute embedding for a given text"""
    if not text:
        # Return a zero embedding for empty text
        return torch.zeros((1, 768), device=device)
    
    encoded_input = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    encoded_input = {k: v.to(device) for k, v in encoded_input.items()}
    
    with torch.no_grad():
        output = model(**encoded_input)
    
    # Extract CLS token embedding
    embedding = output.last_hidden_state[:, 0, :]  # Shape: (1, 768)
    return embedding

def calculate_embedding_similarity(generated, gold_answer):
    """Calculate cosine similarity between generated text and gold answer"""
    # Compute embeddings
    gen_embedding = compute_embedding(generated)
    gold_embedding = compute_embedding(gold_answer)
    
    # Normalize embeddings
    gen_embedding = F.normalize(gen_embedding, p=2, dim=1)
    gold_embedding = F.normalize(gold_embedding, p=2, dim=1)
    
    # Compute cosine similarity
    similarity = torch.mm(gen_embedding, gold_embedding.T).item()
    
    return similarity

def evaluate_legal_qa(questions, generated_answers, gold_answers, domain, question_ids=None):
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
        embedding_similarity = calculate_embedding_similarity(generated, gold)
        
        result = {
            'domain': domain,
            'question': question,
            'generated_answer': generated,
            'gold_answer': gold,
            'bleu': bleu_score,
            'rouge-1': rouge_scores['rouge-1'],
            'rouge-2': rouge_scores['rouge-2'],
            'rouge-l': rouge_scores['rouge-l'],
            'embedding_similarity': embedding_similarity
        }
        
        # Add question_id if provided
        if question_ids is not None:
            result['question_id'] = question_ids[i]
            
        results.append(result)
    
    return results

import csv
import os

def save_to_csv(results, output_file):
    """Save evaluation results to CSV inside the 'Results' folder with proper handling of newlines and special characters."""
    # Ensure the Results directory exists
    results_dir = "Results"
    os.makedirs(results_dir, exist_ok=True)

    # Construct the full file path
    output_path = os.path.join(results_dir, output_file)

    fieldnames = list(results[0].keys())  # Dynamically get all field names

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()

        # Clean rows before writing
        cleaned_results = []
        for row in results:
            cleaned_row = {key: (value.replace('\n', ' ').replace('\r', ' ') if isinstance(value, str) else value)
                           for key, value in row.items()}
            cleaned_results.append(cleaned_row)

        writer.writerows(cleaned_results)

    print(f"Results saved to {output_path}")


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

def evaluate_previous_datasets():
    """Evaluate the original datasets from the previous code"""
    dataset_dir = "../../EvalutionDataset"
    os.makedirs(dataset_dir, exist_ok=True)
    
    dataset_files = {
        "Constitution": os.path.join(dataset_dir, "constitution_qa.json"),
        "CRPC": os.path.join(dataset_dir, "crpc_qa.json"),
        "IPC": os.path.join(dataset_dir, "ipc_qa.json"),
        # "TEST": os.path.join(dataset_dir, "test.json"),
    }
    
    all_results = []
    
    for domain, file_path in dataset_files.items():
        print(f"Processing {domain} dataset...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            questions = [item["question"] for item in data]
            gold_answers = [item["answer"] for item in data]
            
            generated_answers = []
            
            for question in tqdm(questions, desc=f"Evaluating {domain} questions"):
                generated_answer = get_judge_response(question)
                generated_answers.append(generated_answer)
            
            domain_results = evaluate_legal_qa(questions, generated_answers, gold_answers, domain)
            all_results.extend(domain_results)
            
            # Save domain results
            save_to_csv(domain_results, f"{domain.lower()}_evaluation_results.csv")
            
            # Print domain summary
            print_evaluation_summary(domain_results, domain)
            
        except FileNotFoundError:
            print(f"Warning: {file_path} not found. Skipping {domain} dataset.")
    
    # Save overall results
    if all_results:
        save_to_csv(all_results, "original_datasets_evaluation_results.csv")
        print_evaluation_summary(all_results, "All Original Datasets")

def evaluate_articles_constitution_dataset():
    """Evaluate the Articles Constitution dataset (Dataset 1)"""
    try:
        print("\nProcessing Articles Constitution dataset...")
        # df = pd.read_json("hf://datasets/nisaar/Articles_Constitution_3300_Instruction_Set/Article_12_14_15_19_21_Instructionset_train.jsonl", lines=True)
        df = pd.read_json("Articles_Constitution_3300_Instruction_Set.jsonl", lines=True)
        
        
        questions = []
        gold_answers = []
        
        for _, row in df.iterrows():
            # Format the question using both instruction and input
            question = f"{row['instruction']}\n\nCase: {row['input']}"
            questions.append(question)
            gold_answers.append(row['output'])
        
        generated_answers = []
        
        for question in tqdm(questions, desc="Evaluating Articles Constitution questions"):
            generated_answer = get_judge_response(question)
            generated_answers.append(generated_answer)
        
        results = evaluate_legal_qa(questions, generated_answers, gold_answers, "ArticlesConstitution")
        
        # Save results
        save_to_csv(results, "articles_constitution_evaluation_results.csv")
        
        # Print summary
        print_evaluation_summary(results, "Articles Constitution Dataset")
        
        return results
    except Exception as e:
        print(f"Error processing Articles Constitution dataset: {str(e)}")
        return []

def evaluate_lawyer_gpt_dataset():
    """Evaluate the Lawyer GPT dataset (Dataset 2)"""
    try:
        print("\nProcessing Lawyer GPT dataset...")
        # df = pd.read_json("hf://datasets/nisaar/Lawyer_GPT_India/150_lawergpt_dataset_qna_v1_train.jsonl", lines=True)
        df = pd.read_json("150_lawergpt_dataset_qna_v1_train.jsonl", lines=True)
        
        
        questions = df['question'].tolist()
        gold_answers = df['answer'].tolist()
        
        generated_answers = []
        
        for question in tqdm(questions, desc="Evaluating Lawyer GPT questions"):
            generated_answer = get_judge_response(question)
            generated_answers.append(generated_answer)
        
        results = evaluate_legal_qa(questions, generated_answers, gold_answers, "LawyerGPT")
        
        # Save results
        save_to_csv(results, "lawyer_gpt_evaluation_results.csv")
        
        # Print summary
        print_evaluation_summary(results, "Lawyer GPT Dataset")
        
        return results
    except Exception as e:
        print(f"Error processing Lawyer GPT dataset: {str(e)}")
        return []

def evaluate_indian_constitution_dataset():
    """Evaluate the Indian Constitution dataset (Dataset 3)"""
    try:
        # dataset_dir = "../../EvalutionDataset"
        # os.makedirs(dataset_dir, exist_ok=True)
        print("\nProcessing Indian Constitution dataset...")
        df = pd.read_csv("../../EvalutionDataset/indian_constitution.csv")
        
        questions = []
        gold_answers = []
        article_ids = []
        
        for _, row in df.iterrows():
            article_id = f"Part {row['Part No.']} - Article {row['Article No.']}"
            question = f"What is the description of {article_id} - {row['Article Heading']}? Please provide the full text of this article."
            
            questions.append(question)
            gold_answers.append(row['Article Description'])
            article_ids.append(article_id)
        
        generated_answers = []
        
        for question in tqdm(questions, desc="Evaluating Indian Constitution questions"):
            generated_answer = get_judge_response(question)
            generated_answers.append(generated_answer)
        
        results = evaluate_legal_qa(questions, generated_answers, gold_answers, "IndianConstitution", article_ids)
        
        # Save results
        save_to_csv(results, "indian_constitution_evaluation_results.csv")
        
        # Print summary
        print_evaluation_summary(results, "Indian Constitution Dataset")
        
        return results
    except Exception as e:
        print(f"Error processing Indian Constitution dataset: {str(e)}")
        return []

def evaluate_ipc_sections_dataset():
    """Evaluate the IPC Sections dataset (Dataset 4)"""
    try:
        print("\nProcessing IPC Sections dataset...")
        df = pd.read_csv("../../EvalutionDataset/ipc_sections.csv")
        
        # For description evaluations
        desc_questions = []
        desc_gold_answers = []
        
        # For offense evaluations
        offense_questions = []
        offense_gold_answers = []
        
        # For punishment evaluations
        punishment_questions = []
        punishment_gold_answers = []
        
        section_ids = []
        
        for _, row in df.iterrows():
            section_id = f"IPC Section {row['Section']}"
            section_ids.append(section_id)
            
            # Description question
            desc_question = f"What is the full description of {section_id}?"
            desc_questions.append(desc_question)
            desc_gold_answers.append(row['Description'])
            
            # Offense question
            offense_question = f"What offense is covered under {section_id}?"
            offense_questions.append(offense_question)
            offense_gold_answers.append(row['Offense'])
            
            # Punishment question
            punishment_question = f"What is the punishment specified under {section_id}?"
            punishment_questions.append(punishment_question)
            punishment_gold_answers.append(row['Punishment'])
        
        # Evaluate descriptions
        desc_generated_answers = []
        for question in tqdm(desc_questions, desc="Evaluating IPC Section Descriptions"):
            generated_answer = get_judge_response(question)
            desc_generated_answers.append(generated_answer)
        
        desc_results = evaluate_legal_qa(desc_questions, desc_generated_answers, desc_gold_answers, 
                                         "IPC_Description", section_ids)
        
        # Evaluate offenses
        offense_generated_answers = []
        for question in tqdm(offense_questions, desc="Evaluating IPC Section Offenses"):
            generated_answer = get_judge_response(question)
            offense_generated_answers.append(generated_answer)
        
        offense_results = evaluate_legal_qa(offense_questions, offense_generated_answers, offense_gold_answers, 
                                           "IPC_Offense", section_ids)
        
        # Evaluate punishments
        punishment_generated_answers = []
        for question in tqdm(punishment_questions, desc="Evaluating IPC Section Punishments"):
            generated_answer = get_judge_response(question)
            punishment_generated_answers.append(generated_answer)
        
        punishment_results = evaluate_legal_qa(punishment_questions, punishment_generated_answers, punishment_gold_answers, 
                                              "IPC_Punishment", section_ids)
        
        # Save results separately
        save_to_csv(desc_results, "ipc_description_evaluation_results.csv")
        save_to_csv(offense_results, "ipc_offense_evaluation_results.csv")
        save_to_csv(punishment_results, "ipc_punishment_evaluation_results.csv")
        
        # Combined results
        all_ipc_results = desc_results + offense_results + punishment_results
        save_to_csv(all_ipc_results, "ipc_all_evaluation_results.csv")
        
        # Print summaries
        print_evaluation_summary(desc_results, "IPC Section Descriptions")
        print_evaluation_summary(offense_results, "IPC Section Offenses")
        print_evaluation_summary(punishment_results, "IPC Section Punishments")
        print_evaluation_summary(all_ipc_results, "All IPC Evaluations")
        
        return all_ipc_results
    except Exception as e:
        print(f"Error processing IPC Sections dataset: {str(e)}")
        return []

def print_evaluation_summary(results, dataset_name):
    """Print evaluation summary for a dataset"""
    if not results:
        print(f"\n{dataset_name}: No results to summarize")
        return
    
    avg_bleu = np.mean([r['bleu'] for r in results])
    avg_rouge_1 = np.mean([r['rouge-1'] for r in results])
    avg_rouge_2 = np.mean([r['rouge-2'] for r in results])
    avg_rouge_l = np.mean([r['rouge-l'] for r in results])
    avg_embedding_sim = np.mean([r['embedding_similarity'] for r in results])
    
    print(f"\n{dataset_name} Summary:")
    print(f"  Number of questions: {len(results)}")
    print(f"  Average BLEU: {avg_bleu:.4f}")
    print(f"  Average ROUGE-1: {avg_rouge_1:.4f}")
    print(f"  Average ROUGE-2: {avg_rouge_2:.4f}")
    print(f"  Average ROUGE-L: {avg_rouge_l:.4f}")
    print(f"  Average Embedding Similarity: {avg_embedding_sim:.4f}")

def run_complete_evaluation():
    """Run evaluation on all datasets"""
    print("Starting comprehensive legal evaluation...")
    
    all_results = []
    
    # Evaluate original datasets
    print("\n==== Evaluating Original Datasets ====")
    evaluate_previous_datasets()
    
    # Evaluate new datasets
    print("\n==== Evaluating New Datasets ====")
    
    # Dataset 1: Articles Constitution
    print("\n==== Evaluating Articles Constitution ====")
    articles_results = evaluate_articles_constitution_dataset()
    all_results.extend(articles_results)
    
    # Dataset 2: Lawyer GPT
    print("\n==== Evaluating Lawyer GPT ====")
    lawyer_results = evaluate_lawyer_gpt_dataset()
    all_results.extend(lawyer_results)
    
    # Dataset 3: Indian Constitution
    print("\n==== Evaluating Indian Constitution ====")
    constitution_results = evaluate_indian_constitution_dataset()
    all_results.extend(constitution_results)
    
    # Dataset 4: IPC Sections
    print("\n==== Evaluating IPC Sections ====")
    ipc_results = evaluate_ipc_sections_dataset()
    all_results.extend(ipc_results)
    
    # Save combined results from all new datasets
    if all_results:
        save_to_csv(all_results, "all_new_datasets_evaluation_results.csv")
        print_evaluation_summary(all_results, "All New Datasets Combined")
    
    print("\nEvaluation complete. Results saved to CSV files.")

if __name__ == "__main__":
    run_complete_evaluation()