import os
from court_agent import CourtAgentRunnable
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
import google.generativeai as genai
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings

# Set up API keys
os.environ["GOOGLE_API_KEY"] = "AIzaSyAys9j5WcbyzR-Xvn2Xb0QCpJft6BTkWjo"
api_key = os.environ["GOOGLE_API_KEY"]
genai.configure(api_key=api_key)

# Initialize FAISS stores (Placeholder, replace with actual instances)
embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
faiss_store1 = FAISS.load_local("faiss_bns", embedding_model, allow_dangerous_deserialization=True)
faiss_store2 = FAISS.load_local("faiss_constitution", embedding_model, allow_dangerous_deserialization=True)

# Create LLM instance
def create_llm():
    return ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)

llm = create_llm()

# Define agent prompts
judge_prompt = "You are a fair and knowledgeable judge well-versed in constitutional law. Your goal is to evaluate arguments from both lawyers and ask clarification questions when necessary."
defense_prompt = "You are a skilled defense lawyer specializing in constitutional law. Your goal is to counter prosecutor arguments effectively using solid legal reasoning."
reviewer_prompt = "You are an expert legal analyst who scores performance based on a legal rubric. Your goal is to analyze debate logs and provide individual scores based on predefined criteria."

# Initialize court agents with proper prompts
judge_agent = CourtAgentRunnable(llm, "Judge", judge_prompt, faiss_store1, faiss_store2)
defense_agent = CourtAgentRunnable(llm, "Defense Lawyer", defense_prompt, faiss_store1, faiss_store2)
reviewer_agent = CourtAgentRunnable(llm, "Reviewer", reviewer_prompt, faiss_store1, faiss_store2)

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
    response = judge_runnable.invoke({"input": argument},config={"configurable": {"session_id": "legal-session-123"}})
    if hasattr(response, 'content'):
        response = response.content
    log_to_file(f"Judge: {response}")
    return response

def generate_defense_outline(prosecutor_log):
    response = defense_runnable.invoke({"input": prosecutor_log},config={"configurable": {"session_id": "legal-session-123"}})
    if hasattr(response, 'content'):
        response = response.content
    log_to_file(f"Defense Outline: {response}")
    return response

def present_defense_argument(outline, argument_index):
    prompt = f"Based on the following outline, present argument {argument_index+1}:\n\n{outline}"
    response = defense_runnable.invoke({"input": prompt},config={"configurable": {"session_id": "legal-session-123"}})
    if hasattr(response, 'content'):
        response = response.content
    log_to_file(f"Defender: {response}")
    return response

def review_case(prosecutor_log, defender_log):
    full_log = f"Prosecutor:\n{prosecutor_log}\n\nDefender:\n{defender_log}"
    response = reviewer_runnable.invoke({"input": full_log},config={"configurable": {"session_id": "legal-session-123"}})
    if hasattr(response, 'content'):
        response = response.content
    log_to_file(f"Final Score Report: {response}")
    return response

def prosecutor_round():
    argument = input("\n🔹 Prosecutor, present your argument:\n>> ")
    log_to_file(f"Prosecutor: {argument}")
    return argument

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
        while judge_response != "No Questions.":
            print(f"\n👨‍⚖️ Judge: {judge_response}")
            prosecutor_answer = prosecutor_round()
            prosecutor_log += f"Prosecutor Response: {prosecutor_answer}\n"
            judge_response = judge_followup(prosecutor_answer)
        
        if input("\nContinue with next argument? (yes/no): ").lower() != "yes":
            break
    
    print("\n🔶 Defender's Counter-Arguments:")
    defense_outline = generate_defense_outline(prosecutor_log)
    print(f"\n📝 Defense Outline:\n{defense_outline}\n")
    defense_arguments = defense_outline.split("\n")
    defense_arguments = [arg for arg in defense_arguments if arg.strip()]  # Filter empty strings
    
    for i in range(min(len(defense_arguments), 3)):  # Limit to prevent infinite loop, max 3 arguments
        defense_argument = present_defense_argument(defense_outline, i)
        print(f"\n👨‍⚖️ Defense Argument {i+1}:\n{defense_argument}")
        defender_log += f"Defender Argument {i+1}: {defense_argument}\n"
        
        judge_response = judge_followup(defense_argument)
        while judge_response != "No Questions.":
            print(f"\n👨‍⚖️ Judge: {judge_response}")
            defender_answer = input("\n🔸 Defender, respond to the judge:\n>> ")
            log_to_file(f"Defender Response: {defender_answer}")
            defender_log += f"Defender Response: {defender_answer}\n"
            judge_response = judge_followup(defender_answer)
        
        if i < len(defense_arguments) - 1:  # Don't ask after the last argument
            if input("\nContinue with next defense argument? (yes/no): ").lower() != "yes":
                break
    
    print("\n🔁 Rebuttal Round:")
    print("\nProsecutor, present your rebuttal to the defense arguments:")
    prosecutor_rebuttal = prosecutor_round()
    prosecutor_log += f"Prosecutor Rebuttal: {prosecutor_rebuttal}\n"
    
    judge_response = judge_followup(prosecutor_rebuttal)
    while judge_response != "No Questions.":
        print(f"\n👨‍⚖️ Judge: {judge_response}")
        prosecutor_answer = prosecutor_round()
        prosecutor_log += f"Prosecutor Response: {prosecutor_answer}\n"
        judge_response = judge_followup(prosecutor_answer)
    
    print("\nDefender, present your rebuttal:")
    defender_rebuttal = input("\n🔸 Defender, present your rebuttal:\n>> ")
    log_to_file(f"Defender Rebuttal: {defender_rebuttal}")
    defender_log += f"Defender Rebuttal: {defender_rebuttal}\n"
    
    judge_response = judge_followup(defender_rebuttal)
    if judge_response != "No Questions.":
        print(f"\n👨‍⚖️ Judge: {judge_response}")
        defender_answer = input("\n🔸 Defender, respond to the judge:\n>> ")
        log_to_file(f"Defender Response: {defender_answer}")
        defender_log += f"Defender Response: {defender_answer}\n"
    
    print("\nProsecutor, present your final response:")
    prosecutor_final = prosecutor_round()
    prosecutor_log += f"Prosecutor Final Response: {prosecutor_final}\n"
    
    print("\n🏆 Final Evaluation:")
    final_score = review_case(prosecutor_log, defender_log)
    print(f"\n📜 Final Score Report:\n{final_score}")
    print("\n🎤 Moot Court Session Concluded!")

if __name__ == "__main__":
    run_moot_court()