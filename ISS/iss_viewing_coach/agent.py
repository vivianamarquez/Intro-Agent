"""Local ISS Viewing Coach agent.

Run from the repo root:

    python ISS/iss_viewing_coach/agent.py --place "San Francisco"

Or let the agent ask for the missing location:

    python ISS/iss_viewing_coach/agent.py

Requires:

    python -m pip install -r ISS/iss_viewing_coach/requirements.txt

Create a .env file with:

    OPENAI_API_KEY=your-key-here
    OPENAI_MODEL=gpt-4.1-mini
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests
from dotenv import load_dotenv

try:
    from agents import Agent, Runner, function_tool
except ModuleNotFoundError:
    Agent = None
    Runner = None

    def function_tool(func):
        return func


DEFAULT_TASK = "Help me plan a 15-minute ISS watch party for tonight."
DEFAULT_AUDIENCE = "curious beginners"
TOOLS_SUMMARY = [
    (
        "resolve_viewer_location(place_name)",
        "Turns a city or landmark into latitude, longitude, and timezone.",
    ),
    (
        "find_visible_iss_passes(latitude, longitude, timezone_name, hours)",
        "Computes ISS pass windows locally from public orbital data.",
    ),
    (
        "get_viewing_weather(latitude, longitude, timezone_name)",
        "Checks cloud cover and visibility near the viewer.",
    ),
    (
        "get_current_iss_location()",
        "Gets the station's current location for backup activities.",
    ),
]


@dataclass(frozen=True)
class Settings:
    model: str
    timeout_seconds: float
    pass_hours: int

    @classmethod
    def from_env(
        cls,
        model_override: str | None = None,
        require_api_key: bool = True,
    ) -> "Settings":
        load_dotenv()
        if require_api_key and not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("Set OPENAI_API_KEY in your .env file.")

        return cls(
            model=model_override or os.getenv("OPENAI_MODEL") or "gpt-4.1-mini",
            timeout_seconds=float(os.getenv("ISS_HTTP_TIMEOUT", "15")),
            pass_hours=int(os.getenv("ISS_PASS_HOURS", "24")),
        )


class ISSViewingClient:
    """Small data client for the agent's local tools."""

    def __init__(self, timeout_seconds: float) -> None:
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self.session.get(
            url,
            params=params,
            headers={"Accept": "application/json"},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()

    def resolve_location(self, place_name: str) -> dict[str, Any]:
        data = self.get_json(
            "https://geocoding-api.open-meteo.com/v1/search",
            {
                "name": place_name,
                "count": 1,
                "language": "en",
                "format": "json",
            },
        )
        results = data.get("results") or []
        if not results:
            return {
                "ok": False,
                "error": f"No location found for {place_name!r}.",
            }

        result = results[0]
        display_name = ", ".join(
            part
            for part in [
                result.get("name"),
                result.get("admin1"),
                result.get("country"),
            ]
            if part
        )

        return {
            "ok": True,
            "place_name": display_name,
            "latitude": round(result["latitude"], 4),
            "longitude": round(result["longitude"], 4),
            "timezone": result.get("timezone") or "UTC",
            "source": "open-meteo geocoding",
        }

    def get_weather(
        self,
        latitude: float,
        longitude: float,
        timezone_name: str,
    ) -> dict[str, Any]:
        data = self.get_json(
            "https://api.open-meteo.com/v1/forecast",
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": "cloud_cover",
                "hourly": "cloud_cover,visibility",
                "forecast_days": 2,
                "timezone": timezone_name or "auto",
            },
        )
        hourly = data.get("hourly", {})
        times = hourly.get("time") or []
        cloud_cover = hourly.get("cloud_cover") or []
        visibility = hourly.get("visibility") or []
        current_time = (data.get("current") or {}).get("time")
        start_index = 0
        if current_time:
            start_index = next(
                (
                    index
                    for index, time_value in enumerate(times)
                    if time_value >= current_time
                ),
                0,
            )
        next_hours = []

        for index in range(start_index, min(start_index + 12, len(times))):
            time_value = times[index]
            next_hours.append(
                {
                    "time": time_value,
                    "cloud_cover_percent": value_at(cloud_cover, index),
                    "visibility_km": meters_to_km(value_at(visibility, index)),
                }
            )

        return {
            "ok": True,
            "timezone": data.get("timezone") or timezone_name,
            "current_cloud_cover_percent": (data.get("current") or {}).get(
                "cloud_cover"
            ),
            "next_12_hours": next_hours,
            "source": "open-meteo forecast",
        }

    def get_current_iss_location(self) -> dict[str, Any]:
        data = self.get_json("https://api.wheretheiss.at/v1/satellites/25544")
        latitude = data["latitude"]
        longitude = data["longitude"]

        return {
            "ok": True,
            "place_name": self.reverse_place_name(latitude, longitude),
            "latitude": round(latitude, 2),
            "longitude": round(longitude, 2),
            "altitude_km": round(data["altitude"], 2),
            "velocity_km_per_hour": round(data["velocity"], 2),
            "source": "wheretheiss.at",
        }

    def reverse_place_name(self, latitude: float, longitude: float) -> str:
        try:
            data = self.get_json(
                "https://api.bigdatacloud.net/data/reverse-geocode-client",
                {
                    "latitude": latitude,
                    "longitude": longitude,
                    "localityLanguage": "en",
                },
            )
        except requests.RequestException:
            return "place lookup unavailable"

        parts = [
            data.get("locality") or data.get("city"),
            data.get("principalSubdivision"),
            data.get("countryName"),
        ]
        return ", ".join(part for part in parts if part) or "open ocean or remote region"


def value_at(values: list[Any], index: int) -> Any:
    return values[index] if index < len(values) else None


def meters_to_km(value: Any) -> float | None:
    if not isinstance(value, (int, float)):
        return None
    return round(value / 1000, 1)


def compass_direction(degrees: float) -> str:
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return directions[round(degrees / 45) % len(directions)]


def safe_timezone(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def local_time_string(skyfield_time: Any, timezone_name: str) -> str:
    dt = skyfield_time.utc_datetime()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(safe_timezone(timezone_name)).strftime("%Y-%m-%d %H:%M %Z")


def find_passes_with_skyfield(
    latitude: float,
    longitude: float,
    timezone_name: str,
    hours: int,
) -> dict[str, Any]:
    try:
        from skyfield.api import Loader, wgs84
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Install skyfield first: python -m pip install -r ISS/iss_viewing_coach/requirements.txt"
        ) from exc

    data_dir = Path(__file__).with_name(".skyfield-data")
    data_dir.mkdir(exist_ok=True)
    loader = Loader(str(data_dir))
    stations_url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle"
    satellites = loader.tle_file(stations_url, reload=False)
    satellites_by_name = {satellite.name: satellite for satellite in satellites}
    iss = satellites_by_name.get("ISS (ZARYA)")

    if iss is None:
        return {"ok": False, "error": "ISS TLE was not found in CelesTrak stations."}

    timescale = loader.timescale()
    now_utc = datetime.now(timezone.utc)
    t0 = timescale.from_datetime(now_utc)
    t1 = timescale.from_datetime(now_utc + timedelta(hours=max(1, min(hours, 72))))
    observer = wgs84.latlon(latitude, longitude)

    ephemeris = loader("de421.bsp")
    earth = ephemeris["earth"]
    sun = ephemeris["sun"]
    times, events = iss.find_events(observer, t0, t1, altitude_degrees=10.0)
    passes: list[dict[str, Any]] = []
    current_pass: dict[str, Any] | None = None

    for time_value, event in zip(times, events):
        if event == 0:
            current_pass = {"rise_time": local_time_string(time_value, timezone_name)}
            continue

        if current_pass is None:
            continue

        if event == 1:
            altitude, azimuth, _ = (iss - observer).at(time_value).altaz()
            sun_altitude, _, _ = (
                (earth + observer).at(time_value).observe(sun).apparent().altaz()
            )
            is_sunlit = bool(iss.at(time_value).is_sunlit(ephemeris))
            is_dark_enough = sun_altitude.degrees < -6
            likely_visible = bool(
                is_sunlit and is_dark_enough and altitude.degrees >= 10
            )

            current_pass.update(
                {
                    "peak_time": local_time_string(time_value, timezone_name),
                    "max_altitude_degrees": round(float(altitude.degrees), 1),
                    "look_direction": compass_direction(float(azimuth.degrees)),
                    "azimuth_degrees": round(float(azimuth.degrees), 1),
                    "sun_altitude_degrees": round(float(sun_altitude.degrees), 1),
                    "station_sunlit": is_sunlit,
                    "dark_enough": bool(is_dark_enough),
                    "likely_visible": likely_visible,
                }
            )
            continue

        if event == 2:
            current_pass["set_time"] = local_time_string(time_value, timezone_name)
            passes.append(current_pass)
            current_pass = None

    visible_passes = [candidate for candidate in passes if candidate.get("likely_visible")]

    return {
        "ok": True,
        "hours_checked": hours,
        "visible_passes": visible_passes[:3],
        "all_candidate_passes": passes[:5],
        "source": "CelesTrak TLE + Skyfield local pass calculation",
    }


def progress(message: str) -> None:
    print(f"[tool] {message}", file=sys.stderr, flush=True)


def build_agent(settings: Settings, client: ISSViewingClient) -> Any:
    @function_tool
    def resolve_viewer_location(place_name: str) -> dict:
        """Resolve a viewer's city, town, or landmark into latitude, longitude, and timezone."""
        progress(f"resolve_viewer_location({place_name})")
        return client.resolve_location(place_name)

    @function_tool
    def find_visible_iss_passes(
        latitude: float,
        longitude: float,
        timezone_name: str = "UTC",
        hours: int = settings.pass_hours,
    ) -> dict:
        """Find ISS passes near a viewer and mark which ones are likely visible. Use at least 24 hours for tonight planning."""
        progress("find_visible_iss_passes(...)")
        hours_to_check = max(hours, settings.pass_hours)
        return find_passes_with_skyfield(
            latitude,
            longitude,
            timezone_name,
            hours_to_check,
        )

    @function_tool
    def get_viewing_weather(
        latitude: float,
        longitude: float,
        timezone_name: str = "auto",
    ) -> dict:
        """Get local cloud cover and visibility for the viewer's location."""
        progress("get_viewing_weather(...)")
        return client.get_weather(latitude, longitude, timezone_name)

    @function_tool
    def get_current_iss_location() -> dict:
        """Get the current place, coordinates, altitude, and speed of the ISS."""
        progress("get_current_iss_location()")
        return client.get_current_iss_location()

    return Agent(
        name="ISS Viewing Coach",
        model=settings.model,
        instructions=(
            "You help users accomplish a small real goal: planning a short ISS viewing session. "
            "If the user's location is missing, ask for their nearest city or landmark and stop. "
            "Once you have a location, use the tools instead of guessing. "
            "First resolve the viewer location, then check ISS passes and local weather. "
            "If a likely visible pass exists, recommend the best time, where to look, and a simple 15-minute plan. "
            "If no likely visible pass exists, say so and use the current ISS location tool to suggest a backup activity. "
            "Tailor the explanation to the audience. Be factual, practical, and concise."
        ),
        tools=[
            resolve_viewer_location,
            find_visible_iss_passes,
            get_viewing_weather,
            get_current_iss_location,
        ],
    )


def print_tool_summary() -> None:
    print("Tools available to this agent:")
    for name, description in TOOLS_SUMMARY:
        print(f"- {name}: {description}")
    print()


async def run_agent(agent: Any, task: str) -> str:
    result = await Runner.run(agent, task)
    print(result.final_output)
    return result.final_output


def build_task(task: str, place: str | None, audience: str) -> str:
    location_line = (
        f"Viewer location: {place}"
        if place
        else "Viewer location: not provided by the user yet."
    )
    return "\n".join(
        [
            task,
            location_line,
            f"Audience: {audience}",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a local ISS Viewing Coach agent.")
    parser.add_argument(
        "task",
        nargs="?",
        default=DEFAULT_TASK,
        help="Goal to send to the agent.",
    )
    parser.add_argument(
        "--place",
        default=None,
        help="Viewer city, town, or landmark. If omitted, the agent will ask.",
    )
    parser.add_argument(
        "--audience",
        default=DEFAULT_AUDIENCE,
        help="Audience to tailor the plan for, such as kids, adults, or classroom.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override OPENAI_MODEL for this run.",
    )
    parser.add_argument(
        "--dry-run-tools",
        metavar="PLACE",
        help="Run the local data tools for a place without calling OpenAI.",
    )
    parser.add_argument(
        "--hide-tools",
        action="store_true",
        help="Do not print the tool list before running.",
    )
    return parser.parse_args()


def run_tool_dry_run(place: str, settings: Settings, client: ISSViewingClient) -> None:
    location = client.resolve_location(place)
    if not location.get("ok"):
        print(json.dumps(location, indent=2))
        return

    passes = find_passes_with_skyfield(
        location["latitude"],
        location["longitude"],
        location["timezone"],
        settings.pass_hours,
    )
    weather = client.get_weather(
        location["latitude"],
        location["longitude"],
        location["timezone"],
    )
    iss_location = client.get_current_iss_location()

    print(
        json.dumps(
            {
                "viewer_location": location,
                "iss_passes": passes,
                "weather": weather,
                "current_iss_location": iss_location,
            },
            indent=2,
        )
    )


async def main() -> int:
    if Agent is None or Runner is None:
        raise RuntimeError(
            "Install the Agents SDK first: python -m pip install -r ISS/iss_viewing_coach/requirements.txt"
        )

    args = parse_args()
    settings = Settings.from_env(
        model_override=args.model,
        require_api_key=not args.dry_run_tools,
    )
    client = ISSViewingClient(timeout_seconds=settings.timeout_seconds)

    if args.dry_run_tools:
        run_tool_dry_run(args.dry_run_tools, settings, client)
        return 0

    if not args.hide_tools:
        print_tool_summary()

    agent = build_agent(settings, client)

    if args.place:
        await run_agent(agent, build_task(args.task, args.place, args.audience))
        return 0

    await run_agent(agent, build_task(args.task, None, args.audience))
    place = input("\nNearest city or landmark: ").strip()
    if not place:
        print("No location provided. Stopping.")
        return 0

    print()
    await run_agent(agent, build_task(args.task, place, args.audience))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        raise SystemExit(130)
