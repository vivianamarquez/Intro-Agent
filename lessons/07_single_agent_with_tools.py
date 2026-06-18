import asyncio
import os

from agents import Agent, Runner, function_tool, trace
from dotenv import load_dotenv


# Lesson 7:
# This is the contrast with Lesson 6.
#
# Lesson 6 was a workflow:
# - Python chose Step 1, then Step 2, then Step 3.
#
# This file is one agent:
# - Python gives the agent tools.
# - Python calls Runner.run once.
# - The SDK agent loop lets the agent decide which tools to call before answering.

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")


course_notes = {
    "agent": "An agent is a model plus instructions, tools, and runtime behavior.",
    "tool": "A tool is a Python function the agent can call when it needs more help.",
    "handoff": "A handoff transfers control from one agent to another specialist agent.",
    "workflow": "A workflow is an app-owned process where Python decides the steps.",
}


@function_tool
def lookup_course_note(topic: str) -> str:
    """Look up a short course note by topic."""
    clean_topic = topic.strip().lower()
    print(f"Tool called: lookup_course_note(topic={clean_topic!r})")
    return course_notes.get(clean_topic, f"No course note found for {topic!r}.")


@function_tool
def get_tiny_example(topic: str) -> str:
    """Return one tiny Python example for a course topic."""
    clean_topic = topic.strip().lower()
    print(f"Tool called: get_tiny_example(topic={clean_topic!r})")

    if clean_topic == "handoff":
        return (
            "triage_agent = Agent(\n"
            '    name="Triage",\n'
            "    handoffs=[billing_agent, tech_agent],\n"
            ")"
        )

    if clean_topic == "tool":
        return (
            "@function_tool\n"
            "def lookup_course_note(topic: str) -> str:\n"
            "    return course_notes[topic]"
        )

    return "No tiny example is available for that topic yet."


tutor_agent = Agent(
    name="Agent SDK tutor",
    instructions=(
        "You teach the OpenAI Agents SDK to beginners. "
        "Always call lookup_course_note before answering. "
        "If the student asks for an example or code, call get_tiny_example too. "
        "Keep the final answer short and concrete."
    ),
    model=MODEL,
    tools=[lookup_course_note, get_tiny_example],
)


async def main() -> None:
    student_message = (
        "What is a handoff, and can you show me a tiny Python example?"
    )

    print("Starting one agent run...")
    print("Python is not choosing steps now. The agent can choose tools inside the run.")
    print()

    with trace("Single agent with tools"):
        result = await Runner.run(tutor_agent, student_message)

    print()
    print("Final answer:")
    print(result.final_output)
    print()
    print("Trace dashboard: https://platform.openai.com/traces")


if __name__ == "__main__":
    asyncio.run(main())
