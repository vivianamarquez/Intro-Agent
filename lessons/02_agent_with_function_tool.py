import asyncio
import os

from agents import Agent, Runner, function_tool
from dotenv import load_dotenv


# Lesson 2:
# A function tool is a normal Python function the agent is allowed to call.
# The SDK reads the function name, type hints, and docstring to describe the tool
# to the model.

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")


@function_tool
def lookup_course_term(term: str) -> str:
    """Look up a short definition for a term from this course."""
    glossary = {
        "agent": "An agent is a model plus instructions, tools, and runtime behavior.",
        "tool": "A tool is a capability the agent can call, like a Python function.",
        "handoff": "A handoff lets one agent pass control to another specialist agent.",
        "guardrail": "A guardrail checks input, tool behavior, or output before work continues.",
        "trace": "A trace is a record of what happened during an agent run.",
    }

    # Keep the tool deterministic so students can predict what it returns.
    clean_term = term.strip().lower()
    return glossary.get(clean_term, f"No course definition found for {term!r}.")


agent = Agent(
    name="Glossary coach",
    instructions=(
        "You teach the OpenAI Agents SDK. "
        "When the user asks about a course term, call lookup_course_term first. "
        "Then explain the term in plain language."
    ),
    model=MODEL,
    tools=[lookup_course_term],
)


async def main() -> None:
    result = await Runner.run(
        agent,
        "In this course, what does handoff mean?",
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
