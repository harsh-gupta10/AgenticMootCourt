import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import os


os.environ["GOOGLE_API_KEY"] = "AIzaSyDGl8KQuYU-QuD2TLdxIqFklMkxwdN60FQ"
api_key=os.environ["GOOGLE_API_KEY"]
genai.configure(api_key=api_key)

# Initialize memory for each role
judge_memory = ConversationBufferMemory()
respondent_memory = ConversationBufferMemory()
reviewer_memory = ConversationBufferMemory()
petitioner_memory = ConversationBufferMemory()



# Initialize AI models
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.7)

# Define prompts
judge_prompt = PromptTemplate(
    input_variables=["history"],
    template="""
    You are a panel of judges in a moot court. Review the arguments presented so far:
    {history}
    Given the arguments, provide a logical judgment or ask for clarifications.
    """
)

respondent_prompt = PromptTemplate(
    input_variables=["history"],
    template="""
    You are the Respondent in a moot court. Here is the case history:
    {history}
    Based on the opponent's argument, present your response.
    """
)

reviewer_prompt = PromptTemplate(
    input_variables=["history"],
    template="""
    You are a Reviewer in a moot court. Summarize the discussion so far:
    {history}
    Provide an unbiased summary of the case progress.
    """
)

petitioner_prompt = PromptTemplate(
    input_variables=["history"],
    template="""
    You are the Petitioner in a moot court. Here is the case history:
    {history}
    Present your argument based on legal principles.
    """
)


# Define AI chains with memory
judge_chain = LLMChain(llm=llm, prompt=judge_prompt, memory=judge_memory)
respondent_chain = LLMChain(llm=llm, prompt=respondent_prompt, memory=respondent_memory)
reviewer_chain = LLMChain(llm=llm, prompt=reviewer_prompt, memory=reviewer_memory)
petitioner_chain = LLMChain(llm=llm, prompt=petitioner_prompt, memory=petitioner_memory)

def moot_court_simulation():
    print("Welcome to the Moot Court Simulation!")
    rounds = int(input("Enter the number of rounds (recommended: 2-3): "))
    
    for round_num in range(1, rounds + 1):
        print(f"\nRound {round_num} - Petitioner presents their argument:")
        user_argument = input("Petitioner: ")
        petitioner_memory.save_context({"input": user_argument}, {"output": "User provided an argument."})
        
        judge_followup = judge_chain.run(history=judge_memory.load_memory_variables({})["history"])
        print(f"Judge: {judge_followup}")
        judge_memory.save_context({"input": "Judge"}, {"output": judge_followup})
        
        print("\nRespondent presents their argument:")
        respondent_response = respondent_chain.run(history=respondent_memory.load_memory_variables({})["history"])
        print(f"Respondent: {respondent_response}")
        respondent_memory.save_context({"input": "Respondent"}, {"output": respondent_response})
        
        judge_followup = judge_chain.run(history=judge_memory.load_memory_variables({})["history"])
        print(f"Judge: {judge_followup}")
        judge_memory.save_context({"input": "Judge"}, {"output": judge_followup})
        
        # Rebuttal and Sur-rebuttal
        rebuttal_decision = input("\nDoes the Petitioner wish to present a rebuttal? (yes/no): ").strip().lower()
        if rebuttal_decision == "yes":
            petitioner_rebuttal = input("Petitioner Rebuttal: ")
            petitioner_memory.save_context({"input": "Petitioner Rebuttal"}, {"output": petitioner_rebuttal})
            
            print("\nRespondent presents Sur-rebuttal:")
            respondent_sur_rebuttal = respondent_chain.run(history=respondent_memory.load_memory_variables({})["history"])
            print(f"Respondent Sur-rebuttal: {respondent_sur_rebuttal}")
            respondent_memory.save_context({"input": "Respondent Sur-rebuttal"}, {"output": respondent_sur_rebuttal})
        
    # Final Review
    print("\nReviewing the Oral Round Performance:")
    review_response = reviewer_chain.run(history=reviewer_memory.load_memory_variables({})["history"])
    print(f"Final Review:\n{review_response}")
    reviewer_memory.save_context({"input": "Final Review"}, {"output": review_response})

    print("\nMoot Court Session Concluded!")

if __name__ == "__main__":
    moot_court_simulation()
