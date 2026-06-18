import asyncio
import os

from agents import Agent, Runner, trace
from dotenv import load_dotenv


# Lesson 5:
# Tracing lets you inspect what happened during a workflow:
# model calls, tool calls, handoffs, guardrails, and custom spans.
# The normal Agents SDK path traces runs by default, and trace() lets us group
# related runs under one workflow name.

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")


agent = Agent(
    name="Traceable coach",
    instructions="Teach the OpenAI Agents SDK with short, beginner-friendly answers.",
    model=MODEL,
)


async def main() -> None:
    with trace("Intro Agents SDK lesson workflow"):
        first = await Runner.run(
            agent,
            "Explain handoffs in one sentence.",
        )

        second = await Runner.run(
            agent,
            f"Write one short quiz question about this explanation: {first.final_output}",
        )

    print("Explanation:")
    print(first.final_output)
    print()
    print("Quiz question:")
    print(second.final_output)
    print()
    print("Open traces here: https://platform.openai.com/traces")


if __name__ == "__main__":
    asyncio.run(main())
