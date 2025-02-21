#!/usr/bin/env python
import sys
import warnings
from datetime import datetime
import os
from mootcourt.mootcourt import Mootcourt

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
warnings.filterwarnings("ignore", category=DeprecationWarning)


def collect_multiline_input(prompt):
    """Collect multiline input until user enters 'END'"""
    print(prompt)
    lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)
    return "\n".join(lines)

def human_input_callback(task):
    """Callback function for human input tasks"""
    print("\n" + "=" * 50)
    print(f"🧑‍⚖️ MOOT COURT PROCEEDINGS - {task.description.splitlines()[0]}")
    print("=" * 50)
    
    print("\nGUIDELINES:")
    print("- Address the judge as 'Your Lordship'")
    print("- Use phrases like 'It is humbly submitted that...'")
    print("- Cite relevant case law and legal provisions")
    print("- Type 'END' on a new line when you've finished your argument")
    
    # Get human prosecutor's arguments
    prosecutor_arguments = collect_multiline_input("\nPresent your arguments (type 'END' when finished):")
    
    print("\nThank you. Your arguments have been recorded.")
    return prosecutor_arguments

def run():
    """
    Run the moot court simulation with human-in-loop as prosecutor.
    """
    # Get moot court problem details
    print("\n🏛️ INDIAN CONSTITUTIONAL MOOT COURT SIMULATION 🏛️\n")
    print("Current Working Directory:", os.getcwd())
    topic = input("Enter the moot court problem topic: ")
    facts = collect_multiline_input("\nEnter the key facts of the case (type 'END' when finished):")
    issues = collect_multiline_input("\nEnter the main legal issues (type 'END' when finished):")
    
    moot_court_problem = {
        'topic': topic,
        'jurisdiction': "Indian Constitution",
        'current_year': str(datetime.now().year),
        'facts': facts,
        'legal_issues': issues
    }
    
    print("\n--- MOOT COURT SIMULATION STARTING ---")
    print("You will play the role of the Prosecutor.")
    print("The simulation will proceed through arguments and evaluation.")
    print("You will be scored on a 100-point rubric by the Reviewer agent.")
    print("------------------------------------------\n")
    
    try:
        # Create the crew
        crew = Mootcourt().crew()
        
        # Register the human input callback
        # crew.human_input_callback = human_input_callback
        
        # Run the crew
        result = crew.kickoff(inputs=moot_court_problem)  #! Why is this moot_court_problem if not used ?
        
        print("\n--- MOOT COURT SIMULATION COMPLETE ---")
        print("Review and evaluation have been saved to 'moot_court_evaluation.md'")
        
    except Exception as e:
        raise Exception(f"An error occurred while running the moot court: {e}")



# def train():
#     """
#     Train the crew for a given number of iterations.
#     """
#     moot_court_problem = {
#         "topic": "Right to Privacy in Digital Surveillance",
#         "jurisdiction": "Indian Constitution",
#         "facts": "Government implemented mandatory digital ID scanning for all public services.",
#         "legal_issues": "Whether this violates Article 21 right to privacy; Proportionality of measures"
#     }
    
#     try:
#         Mootcourt().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=moot_court_problem)
#     except Exception as e:
#         raise Exception(f"An error occurred while training the crew: {e}")

# def replay():
#     """
#     Replay the crew execution from a specific task.
#     """
#     try:
#         Mootcourt().crew().replay(task_id=sys.argv[1])
#     except Exception as e:
#         raise Exception(f"An error occurred while replaying the crew: {e}")

# def test():
#     """
#     Test the crew execution and returns the results.
#     """
#     moot_court_problem = {
#         "topic": "Right to Freedom of Speech in Social Media Regulation",
#         "jurisdiction": "Indian Constitution",
#         "facts": "New legislation requiring social media platforms to filter content",
#         "legal_issues": "Whether this violates Article 19(1)(a); Reasonable restrictions under 19(2)"
#     }
    
#     try:
#         Mootcourt().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=moot_court_problem)
#     except Exception as e:
#         raise Exception(f"An error occurred while testing the crew: {e}")

# if __name__ == "__main__":
#     if len(sys.argv) > 1:
#         if sys.argv[1] == "train":
#             train()
#         elif sys.argv[1] == "replay":
#             replay()
#         elif sys.argv[1] == "test":
#             test()
#         else:
#             print(f"Unknown command: {sys.argv[1]}")
#     else:
#         run()
        




if __name__ == "__main__":
    run()