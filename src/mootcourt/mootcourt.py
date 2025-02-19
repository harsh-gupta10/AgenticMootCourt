from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class Mootcourt():
    """Mootcourt crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def prosecutor(self) -> Agent:
        return Agent(
            config=self.agents_config['prosecutor'],
            verbose=True
        )

    @agent
    def judge(self) -> Agent:
        return Agent(
            config=self.agents_config['judge'],
            verbose=True
        )

    @agent
    def reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['reviewer'],
            verbose=True
        )

    @task
    def prosecution_task(self) -> Task:
        return Task(
            config=self.tasks_config['prosecution_task'],
        )

    @task
    def judgment_task(self) -> Task:
        return Task(
            config=self.tasks_config['judgment_task'],
        )

    @task
    def review_task(self) -> Task:
        return Task(
            config=self.tasks_config['review_task'],
            output_file='review_feedback.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Mootcourt crew"""

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,  # Agents execute tasks in sequence
            verbose=True,
        )
