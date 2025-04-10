# Import your agent
# import sys
# import os

# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# from court_agent_react import CourtAgentRunnable
from court_agent_react import CourtAgentRunnable
from Initlise import initilise_llm_and_databases
import time




# Initialize LLM and databases
llm, faiss_bns, faiss_constitution, faiss_lc, faiss_sc_lc = initilise_llm_and_databases()

# Base prompt for the judge agent
Base_prompt = """
You are an **experienced legal authority**, ensuring **Correct answering to the asked question about indian law**.
"""

# Initialize judge agent
case_details = ""
judge_agent = CourtAgentRunnable(llm, "evaluation", case_details, faiss_constitution, faiss_bns, faiss_lc, faiss_sc_lc)
judge_runnable = judge_agent.create_runnable()

# Function to get response from judge agent
def get_judge_response(question):
    time.sleep(1)
    response = judge_runnable.invoke(
        {"input": question, "role": "evaluation", },
        config={"configurable": {"session_id": "legal-session-123"}}
    )
    return response["output"]
  
 
 
# print("===========Response==================") 
# print(get_judge_response("What does the territory of a country, such as India, comprise of, according to their constitutional provisions?"))
