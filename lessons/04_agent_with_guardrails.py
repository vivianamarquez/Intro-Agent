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
    ToolOutputGuardrailData,
    function_tool,
    input_guardrail,
    output_guardrail,
    tool_input_guardrail,
    tool_output_guardrail,
)
from dotenv import load_dotenv


# Lesson 4:
# Guardrails are checks around an agent workflow.
# This file shows three boundaries:
# 1. input guardrail: checks the user's request before the main agent runs
# 2. tool guardrail: checks a tool call before/after the Python function runs
# 3. output guardrail: checks the final answer before we print it

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")

COURSE_TERMS = {
    "agent": "An agent is a model plus instructions, tools, and runtime behavior.",
    "tool": "A tool is a capability the agent can call, like a Python function.",
    "handoff": "A handoff lets one agent pass control to another specialist agent.",
    "guardrail": "A guardrail checks input, tool behavior, or output before work continues.",
    "trace": "A trace is a record of what happened during an agent run.",
}

COURSE_WORDS = {"agent", "agents", "sdk", "tool", "tools", "handoff", "guardrail", "trace"}


def text_from_agent_input(agent_input: str | list[TResponseInputItem]) -> str:
    """Turn the possible SDK input shapes into text for this beginner example."""
    if isinstance(agent_input, str):
        return agent_input

    return " ".join(str(item) for item in agent_input)


@input_guardrail(name="course-topic-only", run_in_parallel=False)
async def course_topic_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    agent_input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Block requests that are not about this Agents SDK lesson."""
    text = text_from_agent_input(agent_input).lower()
    is_course_related = any(word in text for word in COURSE_WORDS)

    return GuardrailFunctionOutput(
        output_info={"course_related": is_course_related},
        tripwire_triggered=not is_course_related,
    )


@tool_input_guardrail(name="known-glossary-term-only")
def known_term_guardrail(data: ToolInputGuardrailData) -> ToolGuardrailFunctionOutput:
    """Reject unknown glossary terms before the tool function runs."""
    try:
        arguments = json.loads(data.context.tool_arguments)
    except json.JSONDecodeError:
        return ToolGuardrailFunctionOutput.reject_content(
            message="The glossary tool arguments were not valid JSON.",
            output_info={"tool_arguments": data.context.tool_arguments},
        )

    term = str(arguments.get("term", "")).strip().lower()

    if term not in COURSE_TERMS:
        return ToolGuardrailFunctionOutput.reject_content(
            message=(
                "That term is not in the classroom glossary. "
                "Choose one of: agent, tool, handoff, guardrail, trace."
            ),
            output_info={"term": term},
        )

    return ToolGuardrailFunctionOutput.allow(output_info={"term": term})


@tool_output_guardrail(name="public-glossary-output-only")
def public_glossary_output_guardrail(
    data: ToolOutputGuardrailData,
) -> ToolGuardrailFunctionOutput:
    """Reject a tool result if it accidentally includes instructor-only notes."""
    tool_output = str(data.output)

    if "INSTRUCTOR_ONLY" in tool_output:
        return ToolGuardrailFunctionOutput.reject_content(
            message="The glossary result included instructor-only notes, so do not use it.",
            output_info={"blocked": "instructor_only_note"},
        )

    return ToolGuardrailFunctionOutput.allow(output_info={"characters": len(tool_output)})


@function_tool(
    tool_input_guardrails=[known_term_guardrail],
    tool_output_guardrails=[public_glossary_output_guardrail],
)
def lookup_course_term(term: str) -> str:
    """Look up a short definition for a term from this course."""
    return COURSE_TERMS[term.strip().lower()]


@output_guardrail(name="short-final-answer")
async def short_final_answer_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    output: str,
) -> GuardrailFunctionOutput:
    """Stop the run if the final answer is too long for a beginner lesson."""
    character_count = len(str(output))

    return GuardrailFunctionOutput(
        output_info={"characters": character_count},
        tripwire_triggered=character_count > 900,
    )


agent = Agent(
    name="Guarded glossary coach",
    instructions=(
        "You teach the OpenAI Agents SDK. "
        "Use lookup_course_term when a student asks about a course term. "
        "Keep the final answer short, friendly, and concrete."
    ),
    model=MODEL,
    tools=[lookup_course_term],
    input_guardrails=[course_topic_guardrail],
    output_guardrails=[short_final_answer_guardrail],
)


async def main() -> None:
    # First, try a request that should be blocked before the main agent runs.
    try:
        await Runner.run(agent, "Can you plan a dinner menu for Friday?")
    except InputGuardrailTripwireTriggered:
        print("Input guardrail blocked the off-topic request.")

    print()

    # Now try an allowed request. This should pass the input guardrail, call the
    # glossary tool, pass the tool guardrails, and pass the output guardrail.
    try:
        result = await Runner.run(
            agent,
            "In the Agents SDK, what is a handoff?",
        )
        print(result.final_output)
    except OutputGuardrailTripwireTriggered:
        print("Output guardrail blocked an answer that was too long.")


if __name__ == "__main__":
    asyncio.run(main())
