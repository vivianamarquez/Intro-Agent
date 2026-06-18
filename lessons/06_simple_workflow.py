import asyncio
import os
from typing import Literal

from agents import Agent, Runner, trace
from dotenv import load_dotenv
from pydantic import BaseModel

from world_cup_data import (
    lookup_venue_note,
    sample_question,
    search_matches,
)


# Lesson 6:
# A workflow is a process with steps.
# The important difference from a single agent run is that Python owns the order:
#
# 1. First agent: read the fan's request and extract a small plan.
# 2. Plain Python: choose which local data lookups to run.
# 3. Second agent: write the final fan-facing answer.
#
# This is intentionally small. The point is the shape, not complexity.

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")


class FanRequest(BaseModel):
    topic: Literal["match", "venue", "both", "unknown"]
    query: str
    city: str | None


extractor_agent = Agent(
    name="Fan request extractor",
    instructions=(
        "Read the fan's message. Classify whether they need match info, "
        "venue info, both, or unknown. Extract the most likely city if one appears."
    ),
    model=MODEL,
    output_type=FanRequest,
)


answer_agent = Agent(
    name="Matchday answer writer",
    instructions=(
        "Answer like a helpful World Cup matchday concierge. "
        "Use only the provided lookup notes. Keep the answer short and practical."
    ),
    model=MODEL,
)


async def run_matchday_workflow(fan_message: str) -> str:
    # trace() groups the steps so you can inspect the workflow later.
    with trace("Simple World Cup workflow"):
        # Step 1: use an agent to turn messy language into structured data.
        print("Step 1: extracting the fan request...")
        request_result = await Runner.run(extractor_agent, fan_message)
        request = request_result.final_output
        print(f"Step 1 done: topic={request.topic}, city={request.city}")

        # Step 2: use normal Python to decide which lookups to run.
        print("Step 2: running local lookups...")
        lookup_notes = []
        if request.topic in {"match", "both"}:
            lookup_notes.append(search_matches(request.query))
        if request.topic in {"venue", "both"} and request.city:
            lookup_notes.append(lookup_venue_note(request.city))
        if not lookup_notes:
            lookup_notes.append("No specific match or venue lookup was selected.")
        print("Step 2 done: lookup notes ready")

        # Step 3: give the second agent only the information it needs.
        print("Step 3: drafting the final answer...")
        answer_input = f"""
        Fan question:
        {fan_message}

        Extracted request:
        {request.model_dump_json(indent=2)}

        Lookup notes:
        {chr(10).join(lookup_notes)}
        """

        answer_result = await Runner.run(answer_agent, answer_input)
        print("Step 3 done: final answer drafted")

    return answer_result.final_output


async def main() -> None:
    fan_message = input("What are you trying to plan for the World Cup? ").strip()
    if not fan_message:
        fan_message = sample_question()
        print(f"Using sample question: {fan_message}")

    final_answer = await run_matchday_workflow(fan_message)
    print()
    print(final_answer)
    print()
    print("Trace dashboard: https://platform.openai.com/traces")


if __name__ == "__main__":
    asyncio.run(main())
