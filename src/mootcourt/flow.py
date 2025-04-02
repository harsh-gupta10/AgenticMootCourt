#from mootcourt.court_agent import CourtAgentRunnable
from court_agent_normal import CourtAgentRunnable
from CaseDetails import case_details
from Initlise import initilise_llm_and_databases

llm,faiss_bns,faiss_constitution,faiss_lc,faiss_sc_lc = initilise_llm_and_databases()

# Initialize court agents with proper prompts
judge_agent = CourtAgentRunnable(llm, "judge", case_details,faiss_constitution, faiss_bns,faiss_lc,faiss_sc_lc,max_iter=5)
defense_agent = CourtAgentRunnable(llm, "respondent", case_details,faiss_constitution, faiss_bns,faiss_lc,faiss_sc_lc,max_iter=5)
reviewer_agent = CourtAgentRunnable(llm, "reviewer", case_details,faiss_constitution, faiss_bns,faiss_lc,faiss_sc_lc,max_iter=5)

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
    response = judge_runnable.invoke({"input": argument , "case_details":case_details},config={"configurable": {"session_id": "legal-session-123"}})
    response=response["output"]
    log_to_file(f"Judge: {response}")
    return response

def review_case(prosecutor_log, defender_log):
    full_log = f"Petitioner:\n{prosecutor_log}\n\nDefendant:\n{defender_log}"
    response = reviewer_runnable.invoke({"input": full_log , "case_details":case_details},config={"configurable": {"session_id": "legal-session-123"}})
    response = response["output"]
    log_to_file(f"Final Score Report: {response}")
    return response

def prosecutor_round():
    argument = input("\n🔹 Petitioner, present your argument:\n>> ")
    log_to_file(f"Petitioner: {argument}")
    return argument

def defender_round(input="<None>"):
    argument = defense_runnable.invoke({"input": input, "case_details": case_details}, config={"configurable": {"session_id": "legal-session-123"}})
    argument = argument["output"]
    log_to_file(f"Respondent: {argument}")
    return argument


def run_moot_court():
    print("\n🎓 Welcome to the AI Moot Court!\n")
    # Clear log file at the start
    open(LOG_FILE, "w").close()
    prosecutor_log, defender_log = "", ""
    
    print("\n🔷 Petitioner's Arguments:")
    while True:
        prosecutor_argument = prosecutor_round()
        prosecutor_log += f"Petitioner: {prosecutor_argument}\n"
        
        judge_response = judge_followup(prosecutor_argument)
        while "<None>" not in judge_response:
            print(f"\n👨‍⚖️ Judge: {judge_response}")
            prosecutor_answer = prosecutor_round()
            prosecutor_log += f"Judge: {judge_response}\nPetitioner Response: {prosecutor_answer}\n"
            judge_response = judge_followup(prosecutor_answer)
        
        if input("\nContinue with next argument? (yes/no): ").lower() != "yes":
            break
    log_to_file("The respondent's arguments will now begin.")
    # Provide <Switch> token to judge to let them know the prosecution is done
    judge_followup("<Switch>")
    print("\n🔶 Respondent's Arguments:")
    while True:
        # Add delay of 0.5 seconds
        import time
        time.sleep(0.5)
        defender_argument = defender_round()
        if defender_argument == "<END>":
            break
        print("\n🔸 Respondent: ", defender_argument)
        defender_log += f"Respondent: {defender_argument}\n"
        judge_response = judge_followup(defender_argument)
        question_counter = 0
        while "<None>" not in judge_response and question_counter <= 3:
            # Add delay of 0.5 seconds
            time.sleep(0.5)
            print(f"\n👨‍⚖️ Judge: {judge_response}")
            defender_answer = defender_round(judge_response)
            defender_log += f"Judge: {judge_response}\nDefender Response: {defender_answer}\n"
            if question_counter == 3:
                judge_response = judge_followup("<LIMIT>")
            else:
                judge_response = judge_followup(defender_answer)
            question_counter +=1
        
        
        # Below lines are only for testing if going in loop
        # if input("\nContinue with next defense argument? (yes/no): ").lower() != "yes":
        #     break

    # #  Rebuttal flow 
    # print("\n🔁 Rebuttal Round:")
    # print("\nProsecutor, present your rebuttal to the defense arguments:")
    # prosecutor_rebuttal = prosecutor_round()
    # prosecutor_log += f"Prosecutor Rebuttal: {prosecutor_rebuttal}\n"
    # prosecutor_rebuttal_log = f"Prosecutor Rebuttal: {prosecutor_rebuttal}\n"
    
    # judge_response = judge_followup(prosecutor_rebuttal)
    # while "No Questions" not in judge_response:
    #     print(f"\n👨‍⚖️ Judge: {judge_response}")
    #     prosecutor_answer = prosecutor_round()
    #     prosecutor_log += f"Judge: {judge_response}\nProsecutor Response: {prosecutor_answer}\n"
    #     prosecutor_rebuttal_log += f"Judge: {judge_response}\nProsecutor Response: {prosecutor_answer}\n"
    #     judge_response = judge_followup(prosecutor_answer)
    
    # print("\nDefender, presenting rebuttal:")
    # defender_rebuttal = defender_Reburtal_round(prosecutor_rebuttal_log)
    
        
    # print(f"\n🔸 Defender Rebuttal: {defender_rebuttal}")
    # defender_log += f"Defender Rebuttal: {defender_rebuttal}\n"
    
    # judge_response = judge_followup(defender_rebuttal)
    # while "No Questions" not in judge_response:
    #     print(f"\n👨‍⚖️ Judge: {judge_response}")
    #     # AI defender responds to judge's question
    #     defender_answer = defender_reply_to_judge(judge_response=judge_response)
    #     print(f"\n🔸 Defender: {defender_answer}")
    #     defender_log += f"Judge: {judge_response}\nDefender Response: {defender_answer}\n"
    #     judge_response = judge_followup(defender_answer)
    
    
    print("\n🏆 Final Evaluation:")
    final_score = review_case(prosecutor_log, defender_log)
    print(f"\n📜 Final Score Report:\n{final_score}")
    print("\n🎤 Moot Court Session Concluded!")

