from EvalutionHelper import *

# ? Going forward with Articles_Constitution_3300_Instruction_Set ,  indian_constitution.csv , ipc_qa.json
def run_complete_evaluation():
    """Run evaluation on all datasets"""
    print("Starting comprehensive legal evaluation...")
    
    all_results = []
    
    # Evaluate original datasets
    print("\n==== Evaluating ipc_qa Dataset ====")
    evaluate_previous_datasets()
    
    # Evaluate new datasets
    # print("\n==== Evaluating New Datasets ====")
    
    # Dataset 1: Articles Constitution
    print("\n==== Evaluating Articles_Constitution_3300_Instruction_Set Dataset  ====")
    articles_results = evaluate_articles_constitution_dataset()
    all_results.extend(articles_results)
    
    # # Dataset 2: Lawyer GPT
    # print("\n==== Evaluating Lawyer GPT ====")
    # lawyer_results = evaluate_lawyer_gpt_dataset()
    # all_results.extend(lawyer_results)
    
    # Dataset 3: Indian Constitution
    print("\n==== Evaluating indian_constitution.csv Dataset ====")
    constitution_results = evaluate_indian_constitution_dataset()
    all_results.extend(constitution_results)
    
    # Dataset 4: IPC Sections
    # print("\n==== Evaluating IPC Sections ====")
    # ipc_results = evaluate_ipc_sections_dataset()
    # all_results.extend(ipc_results)
    
    # Save combined results from all new datasets
    # if all_results:
    #     save_to_csv(all_results, "all_new_datasets_evaluation_results.csv")
    #     print_evaluation_summary(all_results, "All New Datasets Combined")
    
    print("\nEvaluation complete. Results saved to CSV files.")


if __name__ == "__main__":
    run_complete_evaluation()