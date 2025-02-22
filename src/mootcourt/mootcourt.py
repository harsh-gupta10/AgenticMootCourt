from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
import os
# from crewai_tools import tool
import yaml



class HumanProsecutorTool:
    name = "human_prosecutor_input"
    description = "Allows a human prosecutor to input their arguments manually."

    def func(self):
        return input("Enter prosecutor's argument: ")

human_prosecutor_tool = HumanProsecutorTool()

@CrewBase
class Mootcourt():
    """Indian Constitutional Moot Court simulation crew"""

    def __init__(self):
        load_dotenv(".env")
        self.GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
        self.llm = LLM(api_key=self.GOOGLE_API_KEY, model="gemini/gemini-1.5-flash")


    @agent
    def defender(self) -> Agent:
        return Agent(
            config=self.agents_config['defender'],
            llm=self.llm,
            verbose=True
        )

    @agent
    def judge(self) -> Agent:
        return Agent(
            config=self.agents_config['judge'],
            llm=self.llm,
            verbose=True
        )

    @agent
    def reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['reviewer'],
            llm=self.llm,
            verbose=True
        )

    @agent
    def prosecutor(self) -> Agent:
        return Agent(
            role="Prosecutor",
            backstory="A human law student acting as the prosecutor in the moot court.",
            goal="Take argument from human and output it.",
            description="A human law student acting as the prosecutor in the moot court.",
            tools=[human_prosecutor_tool],  # ✅ Fixed: Now a valid tool
            verbose=True
        )


    @task
    def prosecutor_task(self) -> Task:
        return Task(
            description="""You are a human law student acting as the prosecutor. Present your arguments 
            following proper court etiquette. Address the judge as 'Your Lordship' and use phrases like 
            'It is humbly submitted that...' Present your arguments in segments, with pauses for judicial questions.
            Cite relevant Indian case law to support your arguments.""",
            expected_output="Human prosecutor's arguments with proper legal reasoning and citations.",
            agent=self.prosecutor(),
            output_file='moot_court_prosecution.md'
        )
    @task
    def judge_followup_task(self) -> Task:
        return Task(
            description="Judge reviews the prosecutor's argument and provides follow-up questions.",
            expected_output="A list of follow-up questions or comments.",
            agent=self.judge()
        )
        
    @task
    def defense_task(self) -> Task:
        task_config = self.tasks_config['defense_task']
        return Task(
            description=task_config['description'],
            expected_output=task_config['expected_output'],
            agent=self.defender()
        )

    @task
    def judgment_task(self) -> Task:
        task_config = self.tasks_config['judgment_task']
        return Task(
            description=task_config['description'],
            expected_output=task_config['expected_output'],
            agent=self.judge()
        )

    @task
    def review_task(self) -> Task:
        task_config = self.tasks_config['review_task']
        return Task(
            description=task_config['description'],
            expected_output=task_config['expected_output'],
            agent=self.reviewer(),
            output_file='moot_court_evaluation.md'
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.prosecutor(),
                self.defender(),
                self.judge(),
                self.reviewer()
            ],
            tasks=[
                self.prosecutor_task(),
                self.defense_task(),
                self.judgment_task(),
                self.review_task()
            ],
            process=Process.sequential,
            verbose=True,
        )
