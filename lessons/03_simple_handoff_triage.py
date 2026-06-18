import asyncio
import os

from agents import Agent, Runner, handoff
from dotenv import load_dotenv


# Lesson 3:
# A handoff is useful when a different agent should take over the answer.
# The triage agent decides who should respond, then the specialist continues.
#
# Handoffs are exposed to the model as tool calls behind the scenes.
# Tool names can only use letters, digits, and underscores, so we provide
# clean tool_name_override values below.

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")


concept_coach = Agent(
    name="Concept coach",
    handoff_description="Use this agent for plain-language explanations of Agent SDK concepts.",
    instructions=(
        "Explain Agent SDK concepts for beginners. "
        "Use short examples and avoid jargon when possible. "
        "When comparing two concepts, explain the difference directly."
    ),
    model=MODEL,
)


code_coach = Agent(
    name="Code coach",
    handoff_description="Use this agent for Python code examples and debugging help.",
    instructions=(
        "Help students read and write small Python examples for the Agents SDK. "
        "Keep code short and explain each important line."
    ),
    model=MODEL,
)


triage_agent = Agent(
    name="Agent SDK triage",
    instructions=(
        "Route each student question to the best specialist. "
        "Use Concept coach for explanations. Use Code coach for code."
    ),
    model=MODEL,
    handoffs=[
        handoff(concept_coach, tool_name_override="transfer_to_concept_coach"),
        handoff(code_coach, tool_name_override="transfer_to_code_coach"),
    ],
)


async def main() -> None:
    result = await Runner.run(
        triage_agent,
        "I keep mixing up tools and handoffs. Can you explain the difference?",
    )

    print(result.final_output)
    print()
    print("Specialist that answered:", result.last_agent.name)


if __name__ == "__main__":
    asyncio.run(main())
