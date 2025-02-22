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


def interactive_prosecutor_input(task, crew):
    """
    Iterative process where Prosecutor presents arguments in steps, and Judge follows up.
    """
    print("\n" + "=" * 50)
    print(f"🧑‍⚖️ PROSECUTOR'S ARGUMENT - {task.description.splitlines()[0]}")
    print("=" * 50)

    arguments = []
    while True:
        argument = collect_multiline_input("\nEnter a segment of your argument (type 'END' to finish this round):")
        if not argument:
            break
        arguments.append(argument)

        # ✅ FIX: Run the Judge's task separately without passing it in inputs
        judge_response = crew.kickoff(inputs={"argument": argument})  # ⚡ Removed "task" key
        print("\n👨‍⚖️ Judge's Response:")
        print(judge_response)

        follow_up = input("\nDoes the judge have more follow-ups? (yes/no): ").strip().lower()
        if follow_up != "yes":
            break  # Move to the next argument

    return "\n".join(arguments)


def run():
    """
    Run the moot court simulation with an interactive argument process.
    """
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
        moot_court = Mootcourt()
        crew = moot_court.crew()

        # Get prosecutor task
        prosecutor_task = crew.tasks[0]  # Prosecutor task

        # Interactive argument process
        prosecutor_arguments = interactive_prosecutor_input(prosecutor_task, crew)

        # Start the AI part (Defender, Judge, and Review)
        result = crew.kickoff(inputs={'prosecutor_arguments': prosecutor_arguments, **moot_court_problem})

        print("\n--- MOOT COURT SIMULATION COMPLETE ---")
        print("Review and evaluation have been saved to 'moot_court_evaluation.md'")

    except Exception as e:
        raise Exception(f"An error occurred while running the moot court: {e}")



if __name__ == "__main__":
    run()
