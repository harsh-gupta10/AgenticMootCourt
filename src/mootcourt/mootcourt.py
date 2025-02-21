from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from langchain_community.agent_toolkits.load_tools import load_tools
from dotenv import load_dotenv
import os

@CrewBase
class Mootcourt():
    """Indian Constitutional Moot Court simulation crew"""

    def __init__(self):
        # Load GOOGLE_API_KEY from .env file
        load_dotenv(".env")
        self.GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
        self.llm = LLM(api_key=self.GOOGLE_API_KEY,model="gemini/gemini-1.5-flash")
        self.tools = load_tools(["human"])

    @agent
    def defender(self) -> Agent:
        print(self.agents_config['defender'])
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
        """Human prosecutor agent (acts as a placeholder for human input)."""
        return Agent(
            role="Prosecutor",
            backstory="A human law student acting as the prosecutor in the moot court.",
            goal="Take argument from human and output it.",
            description="A human law student acting as the prosecutor in the moot court.",
            tools=self.tools,
            llm=self.llm # This marks the agent as a human
        )

    @task
    def prosecutor_task(self) -> Task:
        """Task for human prosecutor to present arguments."""
        return Task(
            description="""You are a human law student acting as the prosecutor. Present your arguments 
            following proper court etiquette. Address the judge as 'Your Lordship' and use phrases like 
            'It is humbly submitted that...' Present your arguments in segments, with pauses for judicial questions.
            Cite relevant Indian case law to support your arguments.
            
            This task will be handled by a human user providing input through the command line.""",
            expected_output="Human prosecutor's arguments with proper legal reasoning and citations.",
            agent=self.prosecutor(),
            output_file='moot_court_prosecution.md'
        )

    @task
    def defense_task(self) -> Task:
        return Task(
            config=self.tasks_config['defense_task']
            #context=[self.prosecutor_task()]
        )

    @task
    def judgment_task(self) -> Task:
        return Task(
            config=self.tasks_config['judgment_task']
        )

    @task
    def review_task(self) -> Task:
        return Task(
            config=self.tasks_config['review_task'],
            #context=[self.prosecutor_task(),self.defense_task(), self.judgment_task()],
            output_file='moot_court_evaluation.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Indian Moot Court crew with human-in-the-loop functionality"""

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