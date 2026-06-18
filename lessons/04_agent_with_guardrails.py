import asyncio
import json
import os

from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    ToolGuardrailFunctionOutput,
    ToolInputGuardrailData,
    function_tool,
    input_guardrail,
    output_guardrail,
    tool_input_guardrail,
)
from dotenv import load_dotenv

from world_cup_data import VENUE_NOTES, lookup_venue_note, sample_question


# Lesson 4:
# Guardrails are checks around an agent workflow.
# This World Cup agent has:
# 1. an input guardrail that blocks betting/scalping/emergency requests
# 2. a tool guardrail that only allows known classroom host cities
# 3. an output guardrail that keeps the final answer short

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")


def text_from_agent_input(agent_input: str | list[TResponseInputItem]) -> str:
    if isinstance(agent_input, str):
        return agent_input

    return " ".join(str(item) for item in agent_input)


@input_guardrail(name="safe-fan-request", run_in_parallel=False)
async def safe_fan_request_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    agent_input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Block requests this matchday helper should not handle."""
    text = text_from_agent_input(agent_input).lower()
    blocked_terms = {
        "bet",
        "bets",
        "odds",
        "parlay",
        "scalp",
        "fake ticket",
        "emergency",
        "medical",
    }
    blocked = any(term in text for term in blocked_terms)

    return GuardrailFunctionOutput(
        output_info={"blocked": blocked},
        tripwire_triggered=blocked,
    )


@tool_input_guardrail(name="known-host-city-only")
def known_host_city_guardrail(data: ToolInputGuardrailData) -> ToolGuardrailFunctionOutput:
    """Reject venue lookups outside the classroom dataset."""
    try:
        arguments = json.loads(data.context.tool_arguments)
    except json.JSONDecodeError:
        return ToolGuardrailFunctionOutput.reject_content(
            message="The venue lookup arguments were not valid JSON.",
            output_info={"tool_arguments": data.context.tool_arguments},
        )

    city = str(arguments.get("city", "")).strip().lower()
    if city not in VENUE_NOTES:
        return ToolGuardrailFunctionOutput.reject_content(
            message=(
                "That city is not in the classroom venue dataset. "
                "Use one of: Dallas, Los Angeles, Mexico City, Philadelphia, Toronto."
            ),
            output_info={"city": city},
        )

    return ToolGuardrailFunctionOutput.allow(output_info={"city": city})


@function_tool(tool_input_guardrails=[known_host_city_guardrail])
def get_venue_note(city: str) -> str:
    """Look up a short venue note for a host city."""
    print(f"Tool called: get_venue_note(city={city!r})")
    return lookup_venue_note(city)


@output_guardrail(name="short-matchday-answer")
async def short_answer_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    output: str,
) -> GuardrailFunctionOutput:
    """Keep the final answer short enough for the terminal."""
    character_count = len(str(output))

    return GuardrailFunctionOutput(
        output_info={"characters": character_count},
        tripwire_triggered=character_count > 900,
    )


agent = Agent(
    name="Guarded matchday helper",
    instructions=(
        "You help fans with safe World Cup venue and arrival questions. "
        "Use get_venue_note for host-city questions. Keep answers short."
    ),
    model=MODEL,
    tools=[get_venue_note],
    input_guardrails=[safe_fan_request_guardrail],
    output_guardrails=[short_answer_guardrail],
)


async def main() -> None:
    user_question = input("Ask a safe World Cup venue question: ").strip()
    if not user_question:
        user_question = sample_question()
        print(f"Using sample question: {user_question}")

    try:
        result = await Runner.run(agent, user_question)
        print()
        print(result.final_output)
    except InputGuardrailTripwireTriggered:
        print("Input guardrail blocked this request.")
        print("Try a matchday logistics question instead.")
    except OutputGuardrailTripwireTriggered:
        print("Output guardrail blocked an answer that was too long.")


if __name__ == "__main__":
    asyncio.run(main())
