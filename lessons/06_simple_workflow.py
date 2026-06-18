import asyncio
import os
from typing import Literal

from agents import Agent, Runner, trace
from dotenv import load_dotenv
from pydantic import BaseModel


# Lesson 6:
# A workflow is a process with steps.
# The important difference from a chatbot is that Python owns the order:
#
# 1. First agent: read the student's message and extract a small plan.
# 2. Plain Python: choose the right course note from that plan.
# 3. Second agent: write the final student-facing answer.
#
# This is intentionally small. The point is the shape, not complexity.

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")


class StudentRequest(BaseModel):
    topic: Literal["agent", "tool", "handoff", "guardrail", "trace", "unknown"]
    wants_code: bool
    question: str


course_notes = {
    "agent": "An agent is the model plus its job description and optional abilities.",
    "tool": "A tool lets an agent call real Python code instead of only writing text.",
    "handoff": "A handoff lets one agent transfer control to a better specialist.",
    "guardrail": "A guardrail checks inputs, tool behavior, or outputs before work continues.",
    "trace": "A trace shows what happened during a run, including model and tool steps.",
    "unknown": "Ask one clarifying question before trying to answer.",
}


extractor_agent = Agent(
    name="Request extractor",
    instructions=(
        "Read the student's message. "
        "Classify the main topic and whether they want code. "
        "Keep the question field short."
    ),
    model=MODEL,
    output_type=StudentRequest,
)


answer_agent = Agent(
    name="Teaching answer writer",
    instructions=(
        "Answer like a patient beginner-friendly teacher. "
        "Use the course note as your source of truth. "
        "If the student wants code, include one tiny Python snippet."
    ),
    model=MODEL,
)


async def run_teaching_workflow(student_message: str) -> str:
    # trace() groups the steps so you can inspect the workflow later.
    with trace("Simple teaching workflow"):
        # Step 1: use an agent to turn messy language into structured data.
        request_result = await Runner.run(extractor_agent, student_message)
        request = request_result.final_output

        # Step 2: use normal Python to make a deterministic workflow decision.
        note = course_notes[request.topic]

        # Step 3: give the second agent only the information it needs.
        answer_input = f"""
        Student question:
        {student_message}

        Extracted request:
        {request.model_dump_json(indent=2)}

        Course note:
        {note}
        """

        answer_result = await Runner.run(answer_agent, answer_input)

    return answer_result.final_output


async def main() -> None:
    student_message = (
        "I get that tools are functions, but when would I use a handoff instead? "
        "Can you show a tiny example?"
    )

    final_answer = await run_teaching_workflow(student_message)
    print(final_answer)
    print()
    print("Trace dashboard: https://platform.openai.com/traces")


if __name__ == "__main__":
    asyncio.run(main())
