# Intro to OpenAI's Agents SDK

A beginner-friendly introduction to OpenAI's Agents SDK through one growing World Cup Matchday Agent.

Each lesson adds one new idea. Run them in order and read the comments as you go.

## What's inside

| # | Lesson | Topics |
|---|--------|--------|
| 01 | [`lessons/01_smallest_possible_agent.py`](lessons/01_smallest_possible_agent.py) | smallest World Cup helper with user input |
| 02 | [`lessons/02_agent_with_function_tool.py`](lessons/02_agent_with_function_tool.py) | one match-search tool |
| 03 | [`lessons/03_simple_handoff_triage.py`](lessons/03_simple_handoff_triage.py) | triage to match, travel, rules, or planner specialists |
| 04 | [`lessons/04_agent_with_guardrails.py`](lessons/04_agent_with_guardrails.py) | input, tool, and output guardrails |
| 05 | [`lessons/05_agent_and_tracing.py`](lessons/05_agent_and_tracing.py) | tracing a matchday run |
| 06 | [`lessons/06_simple_workflow.py`](lessons/06_simple_workflow.py) | Python-owned matchday workflow |
| 07 | [`lessons/07_single_agent_with_tools.py`](lessons/07_single_agent_with_tools.py) | one agent owns the loop and chooses tools |
| 08 | [`lessons/08_world_cup_agent_app.py`](lessons/08_world_cup_agent_app.py) | visual Streamlit app for the agent |

## Capstone

The capstone is a fuller visual World Cup Matchday Desk:

```bash
streamlit run capstone/world_cup_matchday_desk.py
```

It combines a fan profile, planning packet, tools, guardrails, traces, an action log, and a local data preview.

## Setup

Create a Conda environment from this folder:

```bash
conda env create -f environment.yml
conda activate intro-agent
```

If you created the environment before Streamlit was added, update it:

```bash
conda env update -f environment.yml --prune
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

The World Cup data in these lessons is a tiny local teaching dataset. For live tournament information, use FIFA's official [fixtures](https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/scores-fixtures) and [standings](https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/standings).

## Official docs used

- [Agents SDK guide](https://developers.openai.com/api/docs/guides/agents)
- [Agents SDK quickstart](https://developers.openai.com/api/docs/guides/agents/quickstart)
- [Using tools](https://developers.openai.com/api/docs/guides/tools#usage-in-the-agents-sdk)
- [Orchestration and handoffs](https://developers.openai.com/api/docs/guides/agents/orchestration)
- [Guardrails and human review](https://developers.openai.com/api/docs/guides/agents/guardrails-approvals)
- [Integrations and observability](https://developers.openai.com/api/docs/guides/agents/integrations-observability)
