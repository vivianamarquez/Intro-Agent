import asyncio
import os

from agents import Agent, Runner, function_tool
from dotenv import load_dotenv

from world_cup_data import sample_question, search_matches


# Lesson 2:
# Now the agent gets one useful tool.
# The tool searches a tiny local World Cup match dataset.

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")


@function_tool
def search_world_cup_matches(query: str) -> str:
    """Search the classroom World Cup match list."""
    print(f"Tool called: search_world_cup_matches(query={query!r})")
    return search_matches(query)


agent = Agent(
    name="World Cup schedule helper",
    instructions=(
        "You help fans answer World Cup match questions. "
        "Use search_world_cup_matches when the user asks about teams, cities, "
        "dates, matches, scores, or schedules. Keep answers short."
    ),
    model=MODEL,
    tools=[search_world_cup_matches],
)


async def main() -> None:
    user_question = input("Ask about a World Cup match, team, city, or date: ").strip()
    if not user_question:
        user_question = sample_question()
        print(f"Using sample question: {user_question}")

    result = await Runner.run(agent, user_question)
    print()
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
