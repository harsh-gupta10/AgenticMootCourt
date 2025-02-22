import os
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from dotenv import load_dotenv

# Set up API keys (Replace with actual key)
os.environ["GOOGLE_API_KEY"] = "AIzaSyDGl8KQuYU-QuD2TLdxIqFklMkxwdN60FQ"

# Initialize the Google Gemini API
# load_dotenv(".env")
# api_key=os.getenv["GOOGLE_API_KEY"]
# genai.configure(api_key=api_key)


# Initialize the Google Gemini API
api_key=os.environ["GOOGLE_API_KEY"]
genai.configure(api_key=api_key)


# -----------------------
#  LLM SETUP
# -----------------------

# Create LLM instances for different roles
def create_llm(role_instructions):
    """Creates a role-specific LLM instance"""
    llm = ChatGoogleGenerativeAI(
        model="gemini-pro",
        temperature=0.7,
        system=role_instructions
    )
    return llm

# Create role-specific LLMs
judge_llm = create_llm(
    "You are a fair and knowledgeable judge well-versed in constitutional law. "
    "Your goal is to evaluate arguments from both lawyers and ask clarification questions when necessary."
)

defender_llm = create_llm(
    "You are a skilled defense lawyer specializing in constitutional law. "
    "Your goal is to counter prosecutor arguments effectively using solid legal reasoning."
)

reviewer_llm = create_llm(
    "You are an expert legal analyst who scores performance based on a legal rubric. "
    "Your goal is to analyze debate logs and provide individual scores based on predefined criteria."
)

# -----------------------
#  FILE LOGGING SETUP
# -----------------------

LOG_FILE = "moot_court_log.txt"

def log_to_file(content):
    """Logs the debate transcript to a file."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(content + "\n")

# -----------------------
#  AGENT FUNCTIONS
# -----------------------

def judge_followup(argument):
    """Judge evaluates an argument and may ask a clarification question"""
    print("Judge is Judging The Argument Presented")
    prompt = f"""
    You are a judge in a moot court. Review the following argument:

    "{argument}"

    If necessary, ask a clarification question. Otherwise, respond with "No Questions."
    """
    response = judge_llm.invoke([HumanMessage(content=prompt)]).content
    log_to_file(f"Judge: {response}")
    return response

def generate_defense_outline(prosecutor_log):
    """Generate a structured defense outline based on prosecutor arguments"""
    prompt = f"""
    You are a defense lawyer preparing for a moot court.

    Based on the prosecutor's full log of arguments and replies to the judge below,
    create a structured outline of key points for your defense:

    "{prosecutor_log}"

    Ensure logical flow, case law citations, and factual rebuttals.
    """
    response = defender_llm.invoke([HumanMessage(content=prompt)]).content
    log_to_file(f"Defense Outline: {response}")
    return response

def present_defense_argument(outline, argument_index):
    """Present a specific defense argument based on the outline"""
    prompt = f"""
    You are a defense lawyer presenting an argument in a moot court.

    Follow the structured defense outline and present the next argument (point {argument_index + 1}) 
    in a clear and legally backed manner.

    Outline reference:
    "{outline}"
    """
    response = defender_llm.invoke([HumanMessage(content=prompt)]).content
    log_to_file(f"Defender: {response}")
    return response

def review_case(prosecutor_log, defender_log):
    """Review and score both lawyers based on the debate logs"""
    rubric = """
    Evaluate the arguments based on these criteria:

    1. Recognition of Issues (10)
    2. Identification of Legal Principles (15)
    3. Use of Authorities (15)
    4. Application of Facts (15)
    5. Clarity, Logic, and Structure (10)
    6. Response to Questions (15)
    7. Communication with Judges (10)
    8. Overall Presentation (10)

    Score the Prosecutor and Defender separately based on their respective logs.
    """

    prompt = f"""
    You are an expert moot court evaluator.

    Using the scoring rubric below, analyze the logs for both lawyers and provide a detailed score breakdown:

    {rubric}

    Prosecutor's Debate Log:
    "{prosecutor_log}"

    Defender's Debate Log:
    "{defender_log}"
    """
    response = reviewer_llm.invoke([HumanMessage(content=prompt)]).content
    log_to_file(f"\n🏆 Final Score Report:\n{response}")
    return response

# -----------------------
#  PROSECUTOR FUNCTIONS
# -----------------------

def prosecutor_round():
    """Get input from the human prosecutor"""
    argument = input("\n🔹 Prosecutor, present your argument:\n>> ")
    log_to_file(f"Prosecutor: {argument}")
    return argument

# -----------------------
#  MAIN CLI FLOW
# -----------------------

def run_moot_court():
    print("\n🎓 Welcome to the AI Moot Court!\n")

    # Clear log file at the start
    open(LOG_FILE, "w").close()

    prosecutor_log = ""
    defender_log = ""

    # **Prosecutor's Turn**
    print("\n🔷 Prosecutor's Opening Arguments:")
    
    while True:
        prosecutor_argument = prosecutor_round()
        prosecutor_log += f"Prosecutor: {prosecutor_argument}\n"

        while True:
            judge_response = judge_followup(prosecutor_argument)
            # print(judge_response)
            if judge_response == "No Questions.":
                break
            prosecutor_answer = prosecutor_round()
            prosecutor_log += f"Prosecutor Response: {prosecutor_answer}\n"
        print("nContinue with next argument? ")
        if input("\nContinue with next argument? (yes/no): ").lower() != "yes":
            break

    # **Defender's Turn**
    print("\n🔶 Defender's Counter-Arguments:")
    defense_outline = generate_defense_outline(prosecutor_log)

    defense_arguments = defense_outline.split("\n")

    for i, argument in enumerate(defense_arguments):
        if i >= len(defense_arguments) - 1:
            break
            
        defense_argument = present_defense_argument(defense_outline, i)
        defender_log += f"Defender: {defense_argument}\n"

        while True:
            judge_response = judge_followup(defense_argument)
            if judge_response == "No Questions.":
                break
            defender_answer = present_defense_argument(defense_outline, i)
            defender_log += f"Defender Response: {defender_answer}\n"

        if input("\nContinue with next defense argument? (yes/no): ").lower() != "yes":
            break

    # **Rebuttal Round**
    print("\n🔁 Rebuttal Round:")
    
    prosecutor_rebuttal = prosecutor_round()
    prosecutor_log += f"Prosecutor Rebuttal: {prosecutor_rebuttal}\n"

    while True:
        judge_response = judge_followup(prosecutor_rebuttal)
        if judge_response == "No Questions.":
            break
        prosecutor_answer = prosecutor_round()
        prosecutor_log += f"Prosecutor Response: {prosecutor_answer}\n"

    # Defender Response to Prosecutor's Rebuttal
    defender_response = present_defense_argument(prosecutor_rebuttal, 0)
    defender_log += f"Defender Response: {defender_response}\n"

    # Defender Rebuttal Based on **Full Prosecutor Log**
    defender_rebuttal = present_defense_argument(prosecutor_log, 1)
    defender_log += f"Defender Rebuttal: {defender_rebuttal}\n"

    while True:
        judge_response = judge_followup(defender_rebuttal)
        if judge_response == "No Questions.":
            break
        break  # Added to prevent infinite loop if judge has questions

    prosecutor_final = prosecutor_round()
    prosecutor_log += f"Prosecutor Final Response: {prosecutor_final}\n"

    # **Final Score**
    print("\n🏆 Final Evaluation:")
    final_score = review_case(prosecutor_log, defender_log)
    print(f"\n📜 Final Score Report:\n{final_score}")

    print("\n🎤 Moot Court Session Concluded!")

# -----------------------
#  RUN THE COURT SIMULATION
# -----------------------

if __name__ == "__main__":
    run_moot_court()