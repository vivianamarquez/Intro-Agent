# Intro to OpenAI's Agents SDK

A beginner-friendly introduction to OpenAI's Agents SDK with small Python scripts.

Each lesson adds one new idea. Run them in order and read the comments as you go.

## What's inside

| # | Lesson | Topics |
|---|--------|--------|
| 01 | [`lessons/01_smallest_possible_agent.py`](lessons/01_smallest_possible_agent.py) | `Agent`, `Runner.run`, `final_output` |
| 02 | [`lessons/02_agent_with_function_tool.py`](lessons/02_agent_with_function_tool.py) | `@function_tool`, local Python functions as tools |
| 03 | [`lessons/03_simple_handoff_triage.py`](lessons/03_simple_handoff_triage.py) | triage agent, specialist agents, handoffs |
| 04 | [`lessons/04_agent_with_guardrails.py`](lessons/04_agent_with_guardrails.py) | input guardrail, tool guardrail, output guardrail |
| 05 | [`lessons/05_agent_and_tracing.py`](lessons/05_agent_and_tracing.py) | tracing one workflow across multiple agent runs |
| 06 | [`lessons/06_simple_workflow.py`](lessons/06_simple_workflow.py) | a tiny app-owned workflow with structured output and tracing |
| 07 | [`lessons/07_single_agent_with_tools.py`](lessons/07_single_agent_with_tools.py) | one agent owns the loop and decides when to call tools |

## Setup

Create a Conda environment from this folder:

```bash
conda env create -f environment.yml
conda activate intro-agent
```

Create a local `.env` file:

```text
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-5.5
```

Do not commit `.env`. Use `.env.example` as the shareable template.

## Running a lesson

```bash
python lessons/01_smallest_possible_agent.py
```

The lessons default to `gpt-5.5`, matching the OpenAI Agents SDK quickstart. To use a different model, change `OPENAI_MODEL` in your `.env` file.

## Official docs used

- [Agents SDK guide](https://developers.openai.com/api/docs/guides/agents)
- [Agents SDK quickstart](https://developers.openai.com/api/docs/guides/agents/quickstart)
- [Using tools](https://developers.openai.com/api/docs/guides/tools#usage-in-the-agents-sdk)
- [Orchestration and handoffs](https://developers.openai.com/api/docs/guides/agents/orchestration)
- [Guardrails and human review](https://developers.openai.com/api/docs/guides/agents/guardrails-approvals)
- [Integrations and observability](https://developers.openai.com/api/docs/guides/agents/integrations-observability)
