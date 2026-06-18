import asyncio
import os
import sys
from pathlib import Path

import streamlit as st
from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    function_tool,
    input_guardrail,
    trace,
)
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1] / "lessons"))

from world_cup_data import (  # noqa: E402
    FAN_POLICIES,
    MATCHES,
    TEAM_NOTES,
    VENUE_NOTES,
    lookup_fan_policy,
    lookup_team_note,
    lookup_venue_note,
    match_to_text,
    search_matches,
)


# Capstone:
# A visual World Cup Matchday Desk.
#
# This is intentionally different from Lesson 8.
# Lesson 8 is a tiny chat wrapper around one agent.
# The capstone is a fuller desk:
# - fan profile inputs
# - a generated planning packet
# - an agent response
# - visible action log
# - local data preview
# - safety guardrail

# python -m streamlit run capstone/world_cup_matchday_desk.py

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")
ACTION_LOG: list[str] = []


def text_from_agent_input(agent_input: str | list[TResponseInputItem]) -> str:
    if isinstance(agent_input, str):
        return agent_input
    return " ".join(str(item) for item in agent_input)


def build_planning_packet(team: str, city: str, priorities: list[str], fan_request: str) -> str:
    priority_text = ", ".join(priorities) if priorities else "general matchday help"
    return f"""
    Fan profile:
    - Team or match interest: {team}
    - Host city: {city}
    - Priorities: {priority_text}

    Fan request:
    {fan_request}
    """


def local_preview(team: str, city: str) -> dict[str, str]:
    return {
        "matches": search_matches(f"{team} {city}"),
        "team_note": lookup_team_note(team),
        "venue_note": lookup_venue_note(city),
        "ticket_policy": lookup_fan_policy("tickets"),
        "travel_policy": lookup_fan_policy("travel"),
    }


@input_guardrail(name="matchday-desk-safety", run_in_parallel=False)
async def matchday_safety_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    agent_input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Block requests this fan desk should not handle."""
    text = text_from_agent_input(agent_input).lower()
    blocked_terms = {"bet", "odds", "parlay", "scalp", "fake ticket", "medical emergency"}
    blocked = any(term in text for term in blocked_terms)

    return GuardrailFunctionOutput(
        output_info={"blocked": blocked},
        tripwire_triggered=blocked,
    )


@function_tool
def search_world_cup_matches(query: str) -> str:
    """Search the classroom World Cup match list."""
    ACTION_LOG.append(f"Searched matches for: {query}")
    return search_matches(query)


@function_tool
def get_team_note(team: str) -> str:
    """Look up a short team note."""
    ACTION_LOG.append(f"Looked up team note: {team}")
    return lookup_team_note(team)


@function_tool
def get_venue_note(city: str) -> str:
    """Look up a short venue note for a host city."""
    ACTION_LOG.append(f"Looked up venue note: {city}")
    return lookup_venue_note(city)


@function_tool
def get_fan_policy(topic: str) -> str:
    """Look up a fan policy note."""
    ACTION_LOG.append(f"Looked up fan policy: {topic}")
    return lookup_fan_policy(topic)


desk_agent = Agent(
    name="World Cup Matchday Desk",
    instructions=(
        "You are a concise World Cup matchday concierge. "
        "Use tools before giving factual matchday advice. "
        "Return a practical plan with these headings: Match, Arrival, Stadium, "
        "Fan checklist, Next step. "
        "Do not help with betting, ticket scalping, or medical emergencies."
    ),
    model=MODEL,
    tools=[
        search_world_cup_matches,
        get_team_note,
        get_venue_note,
        get_fan_policy,
    ],
    input_guardrails=[matchday_safety_guardrail],
)


async def ask_desk(planning_packet: str) -> tuple[str, bool]:
    ACTION_LOG.clear()
    try:
        with trace("World Cup Matchday Desk capstone"):
            result = await Runner.run(desk_agent, planning_packet)
        return result.final_output, False
    except InputGuardrailTripwireTriggered:
        return (
            "I cannot help with betting, ticket scalping, or medical emergencies. "
            "Try a match, venue, ticket, bag, or travel question instead.",
            True,
        )


st.set_page_config(page_title="World Cup Matchday Desk", layout="wide")
st.title("World Cup Matchday Desk")
st.write("Build a practical fan plan from a tiny classroom World Cup dataset.")

team_options = sorted(TEAM_NOTES.keys(), key=str.title)
city_options = sorted(VENUE_NOTES.keys(), key=str.title)

with st.sidebar:
    st.header("Fan Profile")
    team = st.selectbox(
        "Team or match interest",
        options=team_options,
        index=team_options.index("colombia"),
        format_func=str.title,
    )
    city = st.selectbox(
        "Host city",
        options=city_options,
        index=city_options.index("mexico city"),
        format_func=str.title,
    )
    priorities = st.multiselect(
        "Planning priorities",
        options=["match", "arrival", "tickets", "bags", "travel", "weather"],
        default=["match", "arrival", "tickets"],
    )

    st.divider()
    st.write("Run with:")
    st.code("python -m streamlit run capstone/world_cup_matchday_desk.py")

default_request = (
    "I want to attend Colombia's match. Help me understand the match, "
    "arrival plan, and ticket safety basics."
)

left, right = st.columns([1, 1])

with left:
    st.subheader("Fan Request")
    fan_request = st.text_area(
        "What does the fan need?",
        value=default_request,
        height=150,
    )

    planning_packet = build_planning_packet(team, city, priorities, fan_request)

    with st.expander("Planning packet sent to the agent"):
        st.code(planning_packet.strip())

    run_button = st.button("Build matchday plan", type="primary")

with right:
    st.subheader("Local Data Preview")
    preview = local_preview(team, city)
    st.write("Matches")
    st.code(preview["matches"])
    st.write("Venue")
    st.write(preview["venue_note"])
    st.write("Policies")
    st.write(f"- Tickets: {preview['ticket_policy']}")
    st.write(f"- Travel: {preview['travel_policy']}")

if run_button:
    if not fan_request.strip():
        st.warning("Enter a fan request first.")
    elif not os.getenv("OPENAI_API_KEY"):
        st.error("Set OPENAI_API_KEY in your .env file before running the app.")
    else:
        with st.spinner("Running the matchday desk agent..."):
            answer, blocked = asyncio.run(ask_desk(planning_packet))

        answer_tab, log_tab, data_tab = st.tabs(["Plan", "Action log", "Dataset"])

        with answer_tab:
            if blocked:
                st.warning(answer)
            else:
                st.subheader("Matchday Plan")
                st.write(answer)

        with log_tab:
            st.subheader("What the agent did")
            if ACTION_LOG:
                for step_number, action in enumerate(ACTION_LOG, start=1):
                    st.write(f"{step_number}. {action}")
            else:
                st.write("No tools were called.")
            st.caption("Inspect full traces at https://platform.openai.com/traces")

        with data_tab:
            st.subheader("Classroom Dataset")
            st.write("Matches")
            for match in MATCHES:
                st.write(f"- {match_to_text(match)}")

            st.write("Fan Policies")
            for topic, policy in FAN_POLICIES.items():
                st.write(f"- {topic}: {policy}")
