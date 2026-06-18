import asyncio
import os

import streamlit as st
from agents import Agent, Runner, function_tool, trace
from dotenv import load_dotenv

from world_cup_data import (
    lookup_team_note,
    lookup_venue_note,
    search_matches,
)


# Lesson 8:
# Same agent idea, but now it lives behind a tiny visual interface.
# Run it with:
#
# streamlit run lessons/08_world_cup_agent_app.py

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")
ACTION_LOG: list[str] = []


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


agent = Agent(
    name="World Cup matchday app agent",
    instructions=(
        "You help fans plan around World Cup matches. "
        "Use tools for match, team, and venue questions. "
        "Keep the response practical and short."
    ),
    model=MODEL,
    tools=[search_world_cup_matches, get_team_note, get_venue_note],
)


async def ask_agent(question: str) -> str:
    ACTION_LOG.clear()
    with trace("World Cup visual app"):
        result = await Runner.run(agent, question)
    return result.final_output


st.set_page_config(page_title="World Cup Matchday Agent")
st.title("World Cup Matchday Agent")

question = st.text_input(
    "Ask about a match, team, or host city",
    placeholder="Example: What should I know about England vs Croatia in Dallas?",
)

if st.button("Ask agent", type="primary"):
    if not question.strip():
        st.warning("Ask a World Cup matchday question first.")
    elif not os.getenv("OPENAI_API_KEY"):
        st.error("Set OPENAI_API_KEY in your .env file before running the app.")
    else:
        with st.spinner("The agent is thinking and may call tools..."):
            answer = asyncio.run(ask_agent(question.strip()))

        st.subheader("Answer")
        st.write(answer)

        st.subheader("What happened")
        if ACTION_LOG:
            for action in ACTION_LOG:
                st.write(f"- {action}")
        else:
            st.write("- The agent answered without calling a tool.")

        st.caption("Inspect full traces at https://platform.openai.com/traces")
