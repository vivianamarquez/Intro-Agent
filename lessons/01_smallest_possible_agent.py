import asyncio
import os

from agents import Agent, Runner
from dotenv import load_dotenv


# Lesson 1:
# The smallest agent has three pieces:
# 1. a name, so it is easy to recognize in traces
# 2. instructions, so the model knows its job
# 3. a model, so the SDK knows what to call
#
# This is not very "agentic" yet.
# It has no tools, no handoffs, no guardrails, and no memory.
# It is mostly here so we can learn the basic SDK shape before adding power.

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")


agent = Agent(
    name="Tiny explainer",
    instructions="Explain technical ideas in one clear beginner-friendly sentence.",
    model=MODEL,
)


async def main() -> None:
    # Runner.run sends one turn to the agent.
    # The result object contains the final answer and details about the run.
    result = await Runner.run(
        agent,
        "What is an AI agent?",
    )

    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
