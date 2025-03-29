from court_agent import CourtAgentRunnable
from Prompts import judge_prompt , defender_prompt, reviewer_prompt ,Defence_Outline_Prompt
from CaseDetails import case_details
from Initlise import initilise_llm_and_databases

llm,faiss_bns,faiss_constitution,faiss_lc,faiss_sc_lc = initilise_llm_and_databases()

# Initialize court agents with proper prompts
judge_agent = CourtAgentRunnable(llm, judge_prompt, case_details,faiss_constitution, faiss_bns,faiss_lc,faiss_sc_lc)
defense_agent = CourtAgentRunnable(llm, defender_prompt, case_details,faiss_constitution, faiss_bns,faiss_lc,faiss_sc_lc)
reviewer_agent = CourtAgentRunnable(llm, reviewer_prompt, case_details,faiss_constitution, faiss_bns,faiss_lc,faiss_sc_lc)

# Create runnables once
judge_runnable = judge_agent.create_runnable()
defense_runnable = defense_agent.create_runnable()
reviewer_runnable = reviewer_agent.create_runnable()

# File logging setup
LOG_FILE = "moot_court_log.txt"

def log_to_file(content):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(content + "\n")

# Agent functions
def judge_followup(argument):
    response = judge_runnable.invoke({"input": argument , "role": judge_prompt, "case_details":case_details},config={"configurable": {"session_id": "legal-session-123"}})
    response=response["output"]
    log_to_file(f"Judge: {response}")
    return response



def present_defense_argument(outline, argument_index):
    prompt = f"Based on the following outline, present argument {argument_index+1}:\n\n{outline}"
    response = defense_runnable.invoke({"input": prompt , "role": defender_prompt, "case_details":case_details},config={"configurable": {"session_id": "legal-session-123"}})
    response=response["output"]
    log_to_file(f"Defender: {response}")
    return response
  
def defender_reply_to_judge(judge_response):
    prompt = f"As the Respondent, answer the Judge's question: {judge_response}"
    response = defense_runnable.invoke({"input": prompt , "role": defender_prompt, "case_details":case_details},config={"configurable": {"session_id": "legal-session-123"}})
    response = response["output"]
    log_to_file(f"Defender Reply: {response}")
    return response

def defender_Reburtal_round(prosecutor_rebuttal):
    prompt = f"Present your rebuttal to the prosecutor's arguments: {prosecutor_rebuttal}"
    response = defense_runnable.invoke({"input": prompt , "role": defender_prompt, "case_details":case_details},config={"configurable": {"session_id": "legal-session-123"}})
    response = response["output"]
    log_to_file(f"Defender Reply: {response}")
    return response


def review_case(prosecutor_log, defender_log):
    full_log = f"Prosecutor:\n{prosecutor_log}\n\nDefender:\n{defender_log}"
    response = reviewer_runnable.invoke({"input": full_log , "role": reviewer_prompt, "case_details":case_details},config={"configurable": {"session_id": "legal-session-123"}})
    response = response["output"]
    log_to_file(f"Final Score Report: {response}")
    return response

def prosecutor_round():
    argument = input("\n🔹 Prosecutor, present your argument:\n>> ")
    log_to_file(f"Prosecutor: {argument}")
    return argument


def generate_defense_outline(prosecutor_log):
    global Defence_Outline_Prompt
    Defence_Outline_Prompt += f"\n\n{prosecutor_log}"  # Append prosecutor's log correctly

    response = defense_runnable.invoke(
        {"input": Defence_Outline_Prompt,
         "role": defender_prompt,
         "case_details": case_details},
        config={"configurable": {"session_id": "legal-session-123"}}
    )

    response=response["output"]
    log_to_file(f"Defense Outline: {response}")

    # Split response into argument paragraphs (expecting one argument per paragraph)
    defense_arguments = response.split("\n\n")
    defense_arguments = [arg.strip() for arg in defense_arguments if arg.strip()]
    
    # Fallback: If we have fewer than 4 arguments, try single newline splitting
    if len(defense_arguments) < 4:
        print("Warning: Not enough arguments found with paragraph splitting. Using single newline split as fallback.")
        defense_arguments = response.split("\n")
        defense_arguments = [arg.strip() for arg in defense_arguments if arg.strip()]
    
    return response, defense_arguments


def run_moot_court():
    print("\n🎓 Welcome to the AI Moot Court!\n")
    # Clear log file at the start
    open(LOG_FILE, "w").close()
    prosecutor_log, defender_log = "", ""
    
    print("\n🔷 Prosecutor's Opening Arguments:")
    while True:
        prosecutor_argument = prosecutor_round()
        prosecutor_log += f"Prosecutor: {prosecutor_argument}\n"
        
        judge_response = judge_followup(prosecutor_argument)
        while "No Questions" not in judge_response:
            print(f"\n👨‍⚖️ Judge: {judge_response}")
            prosecutor_answer = prosecutor_round()
            prosecutor_log += f"Judge: {judge_response}\nProsecutor Response: {prosecutor_answer}\n"
            judge_response = judge_followup(prosecutor_answer)
        
        if input("\nContinue with next argument? (yes/no): ").lower() != "yes":
            break
    
    print("\n🔶 Defender's Counter-Arguments:")
    defense_outline , defense_arguments  = generate_defense_outline(prosecutor_log)
    print(f"\n📝 Defense Outline:\n{defense_outline}\n")

    
    for i, argument in enumerate(defense_arguments[:5]):  # Limit to 5 arguments
        defense_argument = present_defense_argument(argument, i)
        print(f"\n👨‍⚖️ Defense Argument {i+1}:\n{defense_argument}")
        defender_log += f"Defender Argument {i+1}: {defense_argument}\n"
        
        judge_response = judge_followup(defense_argument)
        while "No Questions" not in judge_response:
            print(f"\n👨‍⚖️ Judge: {judge_response}")
            defender_answer = defender_reply_to_judge(judge_response=judge_response)
            print(f"\n🔸 Defender: {defender_answer}")
            defender_log += f"Judge: {judge_response}\nDefender Response: {defender_answer}\n"
            judge_response = judge_followup(defender_answer)
        
        # Below lines are only for testing if going in loop
        # if input("\nContinue with next defense argument? (yes/no): ").lower() != "yes":
        #     break

    #  Rebuttal flow 
    print("\n🔁 Rebuttal Round:")
    print("\nProsecutor, present your rebuttal to the defense arguments:")
    prosecutor_rebuttal = prosecutor_round()
    prosecutor_log += f"Prosecutor Rebuttal: {prosecutor_rebuttal}\n"
    prosecutor_rebuttal_log = f"Prosecutor Rebuttal: {prosecutor_rebuttal}\n"
    
    judge_response = judge_followup(prosecutor_rebuttal)
    while "No Questions" not in judge_response:
        print(f"\n👨‍⚖️ Judge: {judge_response}")
        prosecutor_answer = prosecutor_round()
        prosecutor_log += f"Judge: {judge_response}\nProsecutor Response: {prosecutor_answer}\n"
        prosecutor_rebuttal_log += f"Judge: {judge_response}\nProsecutor Response: {prosecutor_answer}\n"
        judge_response = judge_followup(prosecutor_answer)
    
    print("\nDefender, presenting rebuttal:")
    defender_rebuttal = defender_Reburtal_round(prosecutor_rebuttal_log)
    
        
    print(f"\n🔸 Defender Rebuttal: {defender_rebuttal}")
    defender_log += f"Defender Rebuttal: {defender_rebuttal}\n"
    
    judge_response = judge_followup(defender_rebuttal)
    while "No Questions" not in judge_response:
        print(f"\n👨‍⚖️ Judge: {judge_response}")
        # AI defender responds to judge's question
        defender_answer = defender_reply_to_judge(judge_response=judge_response)
        print(f"\n🔸 Defender: {defender_answer}")
        defender_log += f"Judge: {judge_response}\nDefender Response: {defender_answer}\n"
        judge_response = judge_followup(defender_answer)
    
    
    print("\n🏆 Final Evaluation:")
    final_score = review_case(prosecutor_log, defender_log)
    print(f"\n📜 Final Score Report:\n{final_score}")
    print("\n🎤 Moot Court Session Concluded!")

