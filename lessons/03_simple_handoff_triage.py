import asyncio
import os

from agents import Agent, Runner, function_tool, handoff
from dotenv import load_dotenv

from world_cup_data import (
    lookup_fan_policy,
    lookup_team_note,
    lookup_venue_note,
    sample_question,
    search_matches,
)


# Lesson 3:
# A handoff is useful when a different agent should take over the answer.
# Here the triage agent routes the fan to a match, travel, stadium-rules, or
# matchday-planning specialist.
#
# Handoffs are exposed to the model as tool calls behind the scenes.
# Tool names can only use letters, digits, and underscores, so we provide
# clean tool_name_override values below.

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


@function_tool
def get_fan_policy(topic: str) -> str:
    """Look up a short fan policy note."""
    print(f"Tool called: get_fan_policy(topic={topic!r})")
    return lookup_fan_policy(topic)


match_specialist = Agent(
    name="Match specialist",
    handoff_description="Use this for questions about fixtures, teams, groups, or scores.",
    instructions="Answer match questions. Use the match and team tools before answering.",
    model=MODEL,
    tools=[search_world_cup_matches, get_team_note],
)


travel_specialist = Agent(
    name="Travel specialist",
    handoff_description="Use this for questions about host cities, arrival timing, or venues.",
    instructions="Answer matchday travel questions. Use the venue tool before answering.",
    model=MODEL,
    tools=[get_venue_note],
)


rules_specialist = Agent(
    name="Stadium rules specialist",
    handoff_description="Use this for questions about tickets, bags, policies, or fan rules.",
    instructions="Answer stadium policy questions. Use the policy tool before answering.",
    model=MODEL,
    tools=[get_fan_policy],
)


matchday_planner = Agent(
    name="Matchday planner",
    handoff_description=(
        "Use this for mixed questions about attending, going to, planning for, "
        "or watching a specific team or match in person."
    ),
    instructions=(
        "Help the fan make a simple plan to attend a World Cup match. "
        "Use search_world_cup_matches to identify the match and city. "
        "Use get_venue_note for the host city. "
        "Use get_fan_policy for tickets and travel. "
        "Use get_team_note when a team is mentioned. "
        "Keep the answer practical and short."
    ),
    model=MODEL,
    tools=[
        search_world_cup_matches,
        get_team_note,
        get_venue_note,
        get_fan_policy,
    ],
)


triage_agent = Agent(
    name="World Cup triage",
    instructions=(
        "Route each fan question to the best specialist. "
        "Use Matchday planner for questions about attending, going to, "
        "planning for, or watching a specific team or match in person. "
        "Use Match specialist for teams and fixtures, Travel specialist for "
        "venues and arrival plans, and Stadium rules specialist for policies."
    ),
    model=MODEL,
    handoffs=[
        handoff(matchday_planner, tool_name_override="transfer_to_matchday_planner"),
        handoff(match_specialist, tool_name_override="transfer_to_match_specialist"),
        handoff(travel_specialist, tool_name_override="transfer_to_travel_specialist"),
        handoff(rules_specialist, tool_name_override="transfer_to_rules_specialist"),
    ],
)


async def main() -> None:
    user_question = input("Ask the World Cup triage agent a question: ").strip()
    if not user_question:
        user_question = sample_question()
        print(f"Using sample question: {user_question}")

    result = await Runner.run(triage_agent, user_question)
    print()
    print(result.final_output)
    print()
    print("Specialist that answered:", result.last_agent.name)


if __name__ == "__main__":
    asyncio.run(main())
