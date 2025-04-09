import json
from tqdm import tqdm
import numpy as np
import pandas as pd
import os
import csv
import mlcroissant as mlc
import pandas as pd


from EvalutionMatrices import *
from  EvalutionInitilise import *

import json
from tqdm import tqdm
import numpy as np
import pandas as pd
import os
import csv
import mlcroissant as mlc
import pandas as pd
from datetime import datetime


from EvalutionMatrices import *
from  EvalutionInitilise import *

def save_evaluation_summary(results, dataset_name, output_file="evaluation_summaries.txt"):
    """Save evaluation summary for a dataset to a file"""
    results_dir = "../../Results"
    os.makedirs(results_dir, exist_ok=True)
    
    # Construct the full file path
    output_path = os.path.join(results_dir, output_file)
    
    if not results:
        summary = f"\n{dataset_name}: No results to summarize\n"
    else:
        avg_bleu = np.mean([r['bleu'] for r in results])
        avg_rouge_1 = np.mean([r['rouge-1'] for r in results])
        avg_rouge_2 = np.mean([r['rouge-2'] for r in results])
        avg_rouge_l = np.mean([r['rouge-l'] for r in results])
        avg_embedding_sim = np.mean([r['embedding_similarity'] for r in results])
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary = f"\n=== {dataset_name} Summary (completed at {timestamp}) ===\n"
        summary += f"  Number of questions: {len(results)}\n"
        summary += f"  Average BLEU: {avg_bleu:.4f}\n"
        summary += f"  Average ROUGE-1: {avg_rouge_1:.4f}\n"
        summary += f"  Average ROUGE-2: {avg_rouge_2:.4f}\n"
        summary += f"  Average ROUGE-L: {avg_rouge_l:.4f}\n"
        summary += f"  Average Embedding Similarity: {avg_embedding_sim:.4f}\n"
        summary += "=" * 50 + "\n"
    
    # Append to the summaries file
    with open(output_path, 'a', encoding='utf-8') as f:
        f.write(summary)
    
    print(f"Summary for {dataset_name} saved to {output_path}")

def append_incremental_results(new_result, dataset_name):
    """Append a single result to the incremental results file"""
    results_dir = "../../Results"
    os.makedirs(results_dir, exist_ok=True)
    
    # Create a consistent filename for the incremental results
    output_file = f"{dataset_name}_incremental_results.csv"
    output_path = os.path.join(results_dir, output_file)
    
    # Clean the result before writing
    cleaned_result = {key: (value.replace('\n', ' ').replace('\r', ' ') if isinstance(value, str) else value)
                     for key, value in new_result.items()}
    
    # Check if file exists to determine if we need to write headers
    file_exists = os.path.isfile(output_path)
    
    with open(output_path, 'a', newline='', encoding='utf-8') as f:
        fieldnames = list(cleaned_result.keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        
        # Write header only if file is newly created
        if not file_exists:
            writer.writeheader()
        
        # Append the single row
        writer.writerow(cleaned_result)
    
    # No print statement to avoid cluttering the console during frequent appends

def evaluate_previous_datasets():
    """Evaluate the original datasets from the previous code"""
    dataset_dir = "../../EvalutionDataset"  
    os.makedirs(dataset_dir, exist_ok=True)
    
    dataset_files = {
        # "Constitution": os.path.join(dataset_dir, "constitution_qa.json"),
        # "CRPC": os.path.join(dataset_dir, "crpc_qa.json"),
        "IPC": os.path.join(dataset_dir, "ipc_qa.json"),
        # "TEST": os.path.join(dataset_dir, "test.json"),
    }
    
    for domain, file_path in dataset_files.items():
        print(f"Processing {domain} dataset...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            questions = [item["question"] for item in data]
            gold_answers = [item["answer"] for item in data]
            
            generated_answers = []
            domain_results = []
            
            # Clear the incremental results file at the start for this domain
            results_dir = "../../Results"
            os.makedirs(results_dir, exist_ok=True)
            output_file = f"{domain}_incremental_results.csv"
            output_path = os.path.join(results_dir, output_file)
            if os.path.exists(output_path):
                os.remove(output_path)
            
            for i, question in enumerate(tqdm(questions, desc=f"Evaluating {domain} questions")):
                generated_answer = get_judge_response(question)
                generated_answers.append(generated_answer)
                
                # Evaluate current question
                current_result = evaluate_legal_qa(
                    [questions[i]], 
                    [generated_answer], 
                    [gold_answers[i]], 
                    domain
                )[0]  # Just get the first (only) result
                
                # Append this single result to the incremental file
                append_incremental_results(current_result, domain)
                
                # Also keep track of all results for final evaluation
                domain_results.append(current_result)
            
            # Save final domain results (this is the complete set)
            # save_to_csv(domain_results, f"{domain.lower()}_evaluation_results.csv")
            
            # Print and save domain summary
            print_evaluation_summary(domain_results, domain)
            save_evaluation_summary(domain_results, domain)
            
        except FileNotFoundError:
            print(f"Warning: {file_path} not found. Skipping {domain} dataset.")

def evaluate_articles_constitution_dataset():
    """Evaluate the Articles Constitution dataset (Dataset 1)"""
    try:
        print("\nProcessing Articles Constitution dataset...")
        df = pd.read_json("../../EvalutionDataset/Articles_Constitution_3300_Instruction_Set.jsonl", lines=True)
        
        questions = []
        gold_answers = []
        
        for _, row in df.iterrows():
            # Format the question using both instruction and input
            question = f"{row['instruction']}\n\nCase: {row['input']}"
            questions.append(question)
            gold_answers.append(row['output'])
        
        # Clear the incremental results file at the start
        domain = "ArticlesConstitution"
        results_dir = "../../Results"
        os.makedirs(results_dir, exist_ok=True)
        output_file = f"{domain}_incremental_results.csv"
        output_path = os.path.join(results_dir, output_file)
        if os.path.exists(output_path):
            os.remove(output_path)
        
        generated_answers = []
        all_results = []
        
        for i, question in enumerate(tqdm(questions, desc="Evaluating Articles Constitution questions")):
            generated_answer = get_judge_response(question)
            generated_answers.append(generated_answer)
            
            # Evaluate current question
            current_result = evaluate_legal_qa(
                [questions[i]], 
                [generated_answer], 
                [gold_answers[i]], 
                domain
            )[0]  # Just get the first (only) result
            
            # Append this single result to the incremental file
            append_incremental_results(current_result, domain)
            
            # Also keep track of all results for final evaluation
            all_results.append(current_result)
        
        # Save final results
        # save_to_csv(all_results, "articles_constitution_evaluation_results.csv")
        
        # Print and save summary
        print_evaluation_summary(all_results, "Articles Constitution Dataset")
        save_evaluation_summary(all_results, "Articles Constitution Dataset")
        
        return all_results
    except Exception as e:
        print(f"Error processing Articles Constitution dataset: {str(e)}")
        return []

def evaluate_indian_constitution_dataset():
    """Evaluate the Indian Constitution dataset (Dataset 3)"""
    try:
        print("\nProcessing Indian Constitution dataset...")
        df = pd.read_csv("../../EvalutionDataset/indian_constitution.csv")
        
        questions = []
        gold_answers = []
        article_ids = []
        
        for _, row in df.iterrows():
            article_id = f"Part {row['Part+No.']} - Article {row['Article+No.']}"
            question = f"What is the description of {article_id} - {row['Article+Heading']}? Please provide the full text of this article."
            
            questions.append(question)
            gold_answers.append(row['Article+Description'])
            article_ids.append(article_id)
        
        # Clear the incremental results file at the start
        domain = "IndianConstitution"
        results_dir = "../../Results"
        os.makedirs(results_dir, exist_ok=True)
        output_file = f"{domain}_incremental_results.csv"
        output_path = os.path.join(results_dir, output_file)
        if os.path.exists(output_path):
            os.remove(output_path)
        
        generated_answers = []
        all_results = []
        
        for i, question in enumerate(tqdm(questions, desc="Evaluating Indian Constitution questions")):
            generated_answer = get_judge_response(question)
            generated_answers.append(generated_answer)
            
            # Evaluate current question with its article ID
            current_result = evaluate_legal_qa(
                [questions[i]], 
                [generated_answer], 
                [gold_answers[i]], 
                domain,
                [article_ids[i]] if article_ids else None
            )[0]  # Just get the first (only) result
            
            # Append this single result to the incremental file
            append_incremental_results(current_result, domain)
            
            # Also keep track of all results for final evaluation
            all_results.append(current_result)
        
        # Save final results
        # save_to_csv(all_results, "indian_constitution_evaluation_results.csv")
        
        # Print and save summary
        print_evaluation_summary(all_results, "Indian Constitution Dataset")
        save_evaluation_summary(all_results, "Indian Constitution Dataset")
        
        return all_results
    except Exception as e:
        print(f"Error processing Indian Constitution dataset: {str(e)}")
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

def save_to_csv(results, output_file):
    """Save evaluation results to CSV inside the 'Results' folder with proper handling of newlines and special characters."""
    # Ensure the Results directory exists
    results_dir = "../../Results"
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


# def evaluate_lawyer_gpt_dataset():
#     """Evaluate the Lawyer GPT dataset (Dataset 2)"""
#     try:
#         print("\nProcessing Lawyer GPT dataset...")
#         # df = pd.read_json("hf://datasets/nisaar/Lawyer_GPT_India/150_lawergpt_dataset_qna_v1_train.jsonl", lines=True)
#         df = pd.read_json("../../EvalutionDataset/150_lawergpt_dataset_qna_v1_train.jsonl", lines=True)
        
        
#         questions = df['question'].tolist()
#         gold_answers = df['answer'].tolist()
        
#         generated_answers = []
        
#         for question in tqdm(questions, desc="Evaluating Lawyer GPT questions"):
#             generated_answer = get_judge_response(question)
#             generated_answers.append(generated_answer)
        
#         results = evaluate_legal_qa(questions, generated_answers, gold_answers, "LawyerGPT")
        
#         # Save results
#         save_to_csv(results, "lawyer_gpt_evaluation_results.csv")
        
#         # Print summary
#         print_evaluation_summary(results, "Lawyer GPT Dataset")
        
#         return results
#     except Exception as e:
#         print(f"Error processing Lawyer GPT dataset: {str(e)}")
#         return []


# def evaluate_ipc_sections_dataset():
  
  
  
    """Evaluate the IPC Sections dataset (Dataset 4)"""
    try:
        print("\nProcessing IPC Sections dataset...")
        df = pd.read_csv("../../EvalutionDataset/ipc_sections.csv")
        
        
        # Fetch the Croissant JSON-LD
        # croissant_dataset = mlc.Dataset('https://www.kaggle.com/datasets/kanishhkaa/legal-analysis-using-ipc-dataset/croissant/download')
        # # Check what record sets are in the dataset
        # record_sets = croissant_dataset.metadata.record_sets
        # # Fetch the records and put them in a DataFrame
        # record_set_df = pd.DataFrame(croissant_dataset.records(record_set=record_sets[0].uuid))

        
        # For description evaluations
        desc_questions = []
        desc_gold_answers = []
        
        # For offense evaluations
        offense_questions = []
        offense_gold_answers = []
        
        # # For punishment evaluations
        # punishment_questions = []
        # punishment_gold_answers = []
        
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
            
            # # Punishment question
            # punishment_question = f"What is the punishment specified under {section_id}?"
            # punishment_questions.append(punishment_question)
            # punishment_gold_answers.append(row['Punishment'])
        
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
        
        # # Evaluate punishments
        # punishment_generated_answers = []
        # for question in tqdm(punishment_questions, desc="Evaluating IPC Section Punishments"):
        #     generated_answer = get_judge_response(question)
        #     punishment_generated_answers.append(generated_answer)
        
        # punishment_results = evaluate_legal_qa(punishment_questions, punishment_generated_answers, punishment_gold_answers, 
                                              # "IPC_Punishment", section_ids)
        
        # Save results separately
        save_to_csv(desc_results, "ipc_description_evaluation_results.csv")
        save_to_csv(offense_results, "ipc_offense_evaluation_results.csv")
        # save_to_csv(punishment_results, "ipc_punishment_evaluation_results.csv")
        
        # Combined results
        # all_ipc_results = desc_results + offense_results + punishment_results
        all_ipc_results = desc_results + offense_results
        save_to_csv(all_ipc_results, "ipc_all_evaluation_results.csv")
        
        # Print summaries
        print_evaluation_summary(desc_results, "IPC Section Descriptions")
        print_evaluation_summary(offense_results, "IPC Section Offenses")
        # print_evaluation_summary(punishment_results, "IPC Section Punishments")
        print_evaluation_summary(all_ipc_results, "All IPC Evaluations")
        
        return all_ipc_results
    except Exception as e:
        print(f"Error processing IPC Sections dataset: {str(e)}")
        return []