"""Local visual UI for iss_mission_control_production.py.

Run from the repo root:

    python -m pip install -r ISS/iss_mission_control_visual/requirements.txt
    python ISS/iss_mission_control_visual/app.py

Then open:

    http://localhost:5050
"""

from __future__ import annotations

import asyncio
import os

from flask import Flask, jsonify, render_template, request

import agent_runtime


DEFAULT_TASK = "Give me a current ISS mission update."

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html", default_task=DEFAULT_TASK)


@app.post("/api/run")
def api_run():
    body = request.get_json(silent=True) or {}
    task = (body.get("task") or DEFAULT_TASK).strip() or DEFAULT_TASK
    tools_enabled = bool(body.get("tools_enabled", True))

    try:
        result = asyncio.run(agent_runtime.run_agent(task, tools_enabled=tools_enabled))
        return jsonify({"ok": True, **result})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 502


if __name__ == "__main__":
    agent_runtime.configure_logging()
    port = int(os.getenv("PORT", "5050"))
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
