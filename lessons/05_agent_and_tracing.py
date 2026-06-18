import asyncio
import os

from agents import Agent, Runner, function_tool, trace
from dotenv import load_dotenv

from world_cup_data import sample_question, search_matches


# Lesson 5:
# Tracing lets you inspect what happened during a run:
# model calls, tool calls, handoffs, guardrails, and custom workflow spans.

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")


@function_tool
def search_world_cup_matches(query: str) -> str:
    """Search the classroom World Cup match list."""
    print(f"Tool called: search_world_cup_matches(query={query!r})")
    return search_matches(query)


agent = Agent(
    name="Traceable matchday helper",
    instructions=(
        "You help fans answer World Cup match questions. "
        "Use search_world_cup_matches before answering. Keep answers short."
    ),
    model=MODEL,
    tools=[search_world_cup_matches],
)


async def main() -> None:
    user_question = input("Ask a World Cup match question to trace: ").strip()
    if not user_question:
        user_question = sample_question()
        print(f"Using sample question: {user_question}")

    print("Starting traced run...")
    with trace("World Cup matchday traced run"):
        result = await Runner.run(agent, user_question)

    print()
    print(result.final_output)
    print()
    print("Open traces here: https://platform.openai.com/traces")


if __name__ == "__main__":
    asyncio.run(main())
