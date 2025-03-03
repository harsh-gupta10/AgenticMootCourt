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
    return ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.7)

llm = create_llm()

# Define agent prompts
judge_prompt = """
**Role:** You are an Indian moot court **Judge**, responsible for questioning both the **Petitioner** and **Respondent**, testing their legal reasoning, accuracy, and argument strength.

**Backstory:**  
You are an **experienced legal authority**, ensuring **rigorous questioning and fair assessment**. Your task is to **challenge arguments, clarify legal points, and expose weaknesses** in both sides' reasoning.

### **Questioning Process**
- **Ask critical questions** after each argument section.
- You can ask a maximum of **5 questions**.  
- **Types of questions:**  
  - **Clarifications** (e.g., “Can you define this legal principle?”)  
  - **Fact-checking** (e.g., “What case supports this?”)  
  - **Logical inconsistencies** (e.g., “Doesn’t this contradict X?”)  
  - **Hypotheticals** (e.g., “How would this apply in Y scenario?”)  
- **Can interrupt** if needed, but allow structured responses.  
- **Follow-up** if answers are weak or unclear. 
- Reply with **No Questions.** if you don't have any or the participant finishes his argument. 
- Complete the hearing in **one** session.

You ensure a fair and intellectually rigorous courtroom environment.
"""

defender_prompt = """
**Role:** You are the **Respondent**, arguing against the **Prosecutor (Human)** and refuting their legal claims in a structured, logical manner.

**Backstory:**  
You are a **highly skilled constitutional lawyer**, trained to **defend laws, policies, or PILs**. Your goal is to **undermine the Prosecutor’s case through precise legal counterarguments**.

### **Defense Strategy**
- **Present counterarguments** in structured parts.  
- **Cite relevant case law and legal principles.**  
- **Refute the Prosecutor’s claims** using logic, precedent, and legal interpretation.  
- **Engage with the Judge’s questions**, defending your stance effectively.  
- **Maintain professionalism** while persuasively arguing your case.  
- Conclude your argument in 5-10 responses.

You ensure a strong legal defense, making your case **clear, logical, and well-supported**.
"""

reviewer_prompt = """
### Reviewer Agent

**Role:** You objectively score the **Prosecutor (Human)** and **Defender (AI)** in a moot court based on legal reasoning, presentation, and conduct.

**Backstory:**  
You are an impartial **legal evaluator** trained in **moot court procedures and constitutional law**. Your job is to **assess arguments using a strict rubric**.

### Scoring Criteria (Total: 100 Points)

1. **Recognition of Issues (10 pts)** – Identifies and weighs legal issues correctly.  
2. **Legal Principles (15 pts)** – Applies relevant laws accurately.  
3. **Use of Authorities (15 pts)** – Cites case law, statutes, and references effectively.  
4. **Application of Facts (15 pts)** – Uses case facts logically.  
5. **Clarity & Structure (10 pts)** – Organizes arguments coherently.  
6. **Response to Questions (15 pts)** – Answers judges effectively.  
7. **Communication (10 pts)** – Engages with judges clearly.  
8. **Presentation & Poise (10 pts)** – Shows confidence and professionalism.  

### Review Process
- **Observe** the entire session.  
- **Score each participant** using the rubric.  
- **Justify deductions** concisely (e.g., “Weak case law application”).  
- **Ensure fairness**, applying the same standard to both sides.  
- **Provide a final comparative analysis**, noting strengths and areas for improvement.  

You **evaluate, not judge**, ensuring objective assessment based on advocacy quality.
"""

case_details="""
**PQR & Ors v. State of Mahadpur**  
The State of Mahadpur amended the Mahadpur Preservation of Animals Act, 1976, imposing a **total ban on transportation, slaughter, import, and possession** of cow, bull, and bullock flesh. Sections 9A & 9B place the burden of proof on the accused. The petitioners challenge the amendments as violating:  
- **Article 21** (Right to Privacy & Personal Choice).  
- **Article 19(1)(g)** (Freedom of Trade).  
- **Article 25 & 29** (Religious & Cultural Rights).  
The State defends the law, citing **reasonable restrictions, Directive Principles, and animal rights**. The Supreme Court must decide the constitutional validity of the ban.
"""

# Initialize court agents with proper prompts
judge_agent = CourtAgentRunnable(llm, judge_prompt, case_details,faiss_store1, faiss_store2)
defense_agent = CourtAgentRunnable(llm, defender_prompt, case_details,faiss_store1, faiss_store2)
reviewer_agent = CourtAgentRunnable(llm, reviewer_prompt, case_details,faiss_store1, faiss_store2)

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
        while  "No Questions" not in judge_response:
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
    
    for i in range(min(len(defense_arguments), 5)):  # Limit to prevent infinite loop, max 3 arguments
        defense_argument = present_defense_argument(defense_outline, i)
        print(f"\n👨‍⚖️ Defense Argument {i+1}:\n{defense_argument}")
        defender_log += f"Defender Argument {i+1}: {defense_argument}\n"
        
        judge_response = judge_followup(defense_argument)
        # Make this use defender AI, not human input
        while  "No Questions" not in judge_response:
            print(f"\n👨‍⚖️ Judge: {judge_response}")
            defender_answer = input("\n🔸 Defender, respond to the judge:\n>> ")
            log_to_file(f"Defender Response: {defender_answer}")
            defender_log += f"Defender Response: {defender_answer}\n"
            judge_response = judge_followup(defender_answer)
        
        if i < len(defense_arguments) - 1:  
            if input("\nContinue with next defense argument? (yes/no): ").lower() != "yes":
                break
    # TODO: FIX Rebuttal flow
    # print("\n🔁 Rebuttal Round:")
    # print("\nProsecutor, present your rebuttal to the defense arguments:")
    # prosecutor_rebuttal = prosecutor_round()
    # prosecutor_log += f"Prosecutor Rebuttal: {prosecutor_rebuttal}\n"
    
    # judge_response = judge_followup(prosecutor_rebuttal)
    # while  "No Questions" not in judge_response:
    #     print(f"\n👨‍⚖️ Judge: {judge_response}")
    #     prosecutor_answer = prosecutor_round()
    #     prosecutor_log += f"Prosecutor Response: {prosecutor_answer}\n"
    #     judge_response = judge_followup(prosecutor_answer)
    
    # print("\nDefender, present your rebuttal:")
    # defender_rebuttal = present_defense_argument()
    # log_to_file(f"Defender Rebuttal: {defender_rebuttal}")
    # defender_log += f"Defender Rebuttal: {defender_rebuttal}\n"
    
    # judge_response = judge_followup(defender_rebuttal)
    # if judge_response != "No Questions.":
    #     print(f"\n👨‍⚖️ Judge: {judge_response}")
    #     defender_answer = input("\n🔸 Defender, respond to the judge:\n>> ")
    #     log_to_file(f"Defender Response: {defender_answer}")
    #     defender_log += f"Defender Response: {defender_answer}\n"
    
    # print("\nProsecutor, present your final response:")
    # prosecutor_final = prosecutor_round()
    # prosecutor_log += f"Prosecutor Final Response: {prosecutor_final}\n"
    
    print("\n🏆 Final Evaluation:")
    final_score = review_case(prosecutor_log, defender_log)
    print(f"\n📜 Final Score Report:\n{final_score}")
    print("\n🎤 Moot Court Session Concluded!")

if __name__ == "__main__":
    run_moot_court()