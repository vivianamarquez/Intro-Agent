import asyncio
import os

from agents import Agent, Runner, function_tool, trace
from dotenv import load_dotenv

from world_cup_data import (
    lookup_team_note,
    lookup_venue_note,
    sample_question,
    search_matches,
)


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


@function_tool
def search_world_cup_matches(query: str) -> str:
    """Search the classroom World Cup match list."""
    print(f"Tool called: search_world_cup_matches(query={query!r})")
    return search_matches(query)


@function_tool
def get_team_note(team: str) -> str:
    """Look up a short team note."""
    print(f"Tool called: get_team_note(team={team!r})")
    return lookup_team_note(team)


@function_tool
def get_venue_note(city: str) -> str:
    """Look up a short venue note for a host city."""
    print(f"Tool called: get_venue_note(city={city!r})")
    return lookup_venue_note(city)


matchday_agent = Agent(
    name="World Cup matchday agent",
    instructions=(
        "You help fans with World Cup matchday planning. "
        "Decide which tools you need. Use match search for fixtures, team notes "
        "for team context, and venue notes for city logistics. Keep answers short."
    ),
    model=MODEL,
    tools=[search_world_cup_matches, get_team_note, get_venue_note],
)


async def main() -> None:
    fan_message = input("Ask the one-run matchday agent a question: ").strip()
    if not fan_message:
        fan_message = sample_question()
        print(f"Using sample question: {fan_message}")

    print("Starting one agent run...")
    print("Python is not choosing steps now. The agent can choose tools inside the run.")
    print()

    with trace("Single World Cup agent with tools"):
        result = await Runner.run(matchday_agent, fan_message)

    print()
    print("Final answer:")
    print(result.final_output)
    print()
    print("Trace dashboard: https://platform.openai.com/traces")


if __name__ == "__main__":
    asyncio.run(main())
