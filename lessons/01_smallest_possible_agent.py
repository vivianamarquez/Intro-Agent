import asyncio
import os

from agents import Agent, Runner
from dotenv import load_dotenv

from world_cup_data import sample_question


# Lesson 1:
# The smallest agent has three pieces:
# 1. a name, so it is easy to recognize in traces
# 2. instructions, so the model knows its job
# 3. a model, so the SDK knows what to call
#
# This is not very powerful yet.
# It has no tools, no handoffs, no guardrails, and no memory.
# It is a World Cup helper in personality, but it cannot look up real data yet.

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")


agent = Agent(
    name="World Cup matchday helper",
    instructions=(
        "You help fans understand the World Cup matchday experience. "
        "Be clear about uncertainty. If you need live match data, say that "
        "this first lesson does not have tools yet."
    ),
    model=MODEL,
)


async def main() -> None:
    user_question = input("Ask the World Cup helper a question: ").strip()
    if not user_question:
        user_question = sample_question()
        print(f"Using sample question: {user_question}")

    result = await Runner.run(agent, user_question)
    print()
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
