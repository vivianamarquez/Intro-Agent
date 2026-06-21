"""Agent runtime used only by the local visual demo.

This intentionally lives beside the Flask app so the production script can stay
unchanged while the UI demonstrates running with and without tools.
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from typing import Any

import requests
from agents import Agent, Runner, function_tool
from dotenv import load_dotenv


DEFAULT_MODEL = "gpt-4.1-mini"
TOOL_NAME = "get_iss_location"

logger = logging.getLogger("iss_mission_control_visual")


@dataclass(frozen=True)
class Settings:
    model: str
    timeout_seconds: float

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()

        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("Set OPENAI_API_KEY in your .env file.")

        return cls(
            model=os.getenv("OPENAI_MODEL") or DEFAULT_MODEL,
            timeout_seconds=float(os.getenv("ISS_HTTP_TIMEOUT", "15")),
        )


class ISSLocationClient:
    """Small client for the external APIs this agent depends on."""

    def __init__(self, timeout_seconds: float) -> None:
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    def get_place_name(self, latitude: float, longitude: float) -> str:
        response = self.session.get(
            "https://api.bigdatacloud.net/data/reverse-geocode-client",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "localityLanguage": "en",
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()

        place_parts = [
            data.get("locality") or data.get("city"),
            data.get("principalSubdivision"),
            data.get("countryName"),
        ]
        place_name = ", ".join(part for part in place_parts if part)
        return place_name or "an area with no nearby place name"

    def get_location(self) -> dict[str, Any]:
        response = self.session.get(
            "https://api.wheretheiss.at/v1/satellites/25544",
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()

        latitude = data["latitude"]
        longitude = data["longitude"]

        return {
            "place_name": self.get_place_name(latitude, longitude),
            "latitude": round(latitude, 2),
            "longitude": round(longitude, 2),
            "altitude_km": round(data["altitude"], 2),
            "velocity_km_per_hour": round(data["velocity"], 2),
        }


def configure_logging() -> None:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def progress(message: str) -> None:
    print(f"[progress] {message}", file=sys.stderr, flush=True)


def build_agent(
    settings: Settings,
    iss_client: ISSLocationClient,
    tools_enabled: bool,
) -> Agent:
    @function_tool
    def get_iss_location() -> dict:
        """Get the current place name, latitude, longitude, altitude, and speed of the International Space Station."""
        progress("Calling get_iss_location tool")
        logger.info("Fetching live ISS location")

        try:
            location = iss_client.get_location()
        except requests.RequestException as exc:
            logger.exception("ISS location lookup failed")
            raise RuntimeError("Could not fetch live ISS location data.") from exc

        logger.info("ISS location lookup succeeded")
        progress("ISS data received")
        return location

    if tools_enabled:
        tool_instructions = (
            "You have access to get_iss_location. "
            "Use it before answering live ISS location questions. "
        )
        tools = [get_iss_location]
    else:
        tool_instructions = ""
        tools = []

    return Agent(
        name="ISS Mission Control",
        instructions=(
            "You are a concise mission-control communicator. "
            f"{tool_instructions}"
            "Make the update exciting but factual."
        ),
        model=settings.model,
        tools=tools,
    )


async def run_agent(task: str, tools_enabled: bool) -> dict[str, Any]:
    settings = Settings.from_env()
    client = ISSLocationClient(timeout_seconds=settings.timeout_seconds)
    agent = build_agent(settings, client, tools_enabled=tools_enabled)
    result = await Runner.run(agent, task)

    return {
        "answer": result.final_output or "",
        "model": settings.model,
        "tools_enabled": tools_enabled,
        "available_tools": [TOOL_NAME] if tools_enabled else [],
    }
