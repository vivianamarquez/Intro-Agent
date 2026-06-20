"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type ISSLocation = {
  placeName: string;
  latitude: number;
  longitude: number;
  altitudeKm: number | null;
  velocityKmPerHour: number | null;
  source: string;
  timestamp: number;
};

type MissionResponse = {
  ok: boolean;
  mode?: string;
  location?: ISSLocation;
  answer?: string;
  error?: string;
};

const DEFAULT_PROMPT = "Where is the International Space Station right now?";

function formatNumber(value: number | null, suffix: string) {
  return value === null ? "Unavailable" : `${value.toLocaleString()} ${suffix}`;
}

function formatTime(timestamp?: number) {
  if (!timestamp) return "Unknown";
  return new Intl.DateTimeFormat(undefined, {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(timestamp * 1000));
}

function mapUrl(location: ISSLocation) {
  const lat = location.latitude;
  const lon = location.longitude;
  const span = 35;
  const bbox = [
    Math.max(-180, lon - span),
    Math.max(-85, lat - span),
    Math.min(180, lon + span),
    Math.min(85, lat + span),
  ].join("%2C");
  return `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${lat}%2C${lon}`;
}

export default function Home() {
  const [location, setLocation] = useState<ISSLocation | null>(null);
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT);
  const [answer, setAnswer] = useState("");
  const [status, setStatus] = useState("Loading live ISS signal...");
  const [mode, setMode] = useState("");
  const [isLoadingLocation, setIsLoadingLocation] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState("");

  async function loadLocation() {
    setIsLoadingLocation(true);
    setError("");
    setStatus("Fetching live ISS coordinates...");

    try {
      const response = await fetch("/api/iss", { cache: "no-store" });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.error || "ISS API request failed.");
      }
      setLocation(data.location);
      setStatus("Live ISS signal locked.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load ISS data.");
      setStatus("Live ISS signal failed.");
    } finally {
      setIsLoadingLocation(false);
    }
  }

  async function runMissionControl(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsRunning(true);
    setError("");
    setAnswer("");
    setMode("");
    setStatus("Fetching fresh ISS data for the narrator...");

    try {
      const response = await fetch("/api/mission-control", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const data = (await response.json()) as MissionResponse;
      if (!response.ok || !data.ok) {
        throw new Error(data.error || "Mission-control request failed.");
      }
      if (data.location) setLocation(data.location);
      setAnswer(data.answer || "");
      setMode(data.mode || "");
      setStatus("Mission-control update complete.");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Mission-control update failed.",
      );
      setStatus("Mission-control update failed.");
    } finally {
      setIsRunning(false);
    }
  }

  useEffect(() => {
    loadLocation();
  }, []);

  const map = useMemo(() => (location ? mapUrl(location) : ""), [location]);

  return (
    <main className="shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Live orbital operations</p>
          <h1>ISS Mission Control</h1>
          <p className="summary">
            Track the station in real time, then generate a factual
            mission-control update from server-verified coordinates.
          </p>
        </div>
        <div className="signal">
          <span className={error ? "dot error" : "dot"} />
          {status}
        </div>
      </section>

      <section className="grid">
        <div className="panel tracker">
          <div className="panelHeader">
            <div>
              <p className="kicker">Tracker</p>
              <h2>Current Signal</h2>
            </div>
            <button onClick={loadLocation} disabled={isLoadingLocation}>
              {isLoadingLocation ? "Refreshing..." : "Refresh"}
            </button>
          </div>

          {location ? (
            <>
              <div className="metrics">
                <div>
                  <span>Place</span>
                  <strong>{location.placeName}</strong>
                </div>
                <div>
                  <span>Altitude</span>
                  <strong>{formatNumber(location.altitudeKm, "km")}</strong>
                </div>
                <div>
                  <span>Speed</span>
                  <strong>
                    {formatNumber(location.velocityKmPerHour, "km/h")}
                  </strong>
                </div>
                <div>
                  <span>Coordinates</span>
                  <strong>
                    {location.latitude}, {location.longitude}
                  </strong>
                </div>
              </div>

              <iframe
                className="map"
                src={map}
                title="ISS position map"
                loading="lazy"
              />

              <div className="dataLine">
                Source: {location.source} · Updated {formatTime(location.timestamp)}
              </div>
            </>
          ) : (
            <div className="empty">Waiting for live ISS data.</div>
          )}
        </div>

        <div className="panel narrator">
          <div className="panelHeader">
            <div>
              <p className="kicker">Narrator</p>
              <h2>Mission Update</h2>
            </div>
          </div>

          <form onSubmit={runMissionControl}>
            <label htmlFor="prompt">Prompt</label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
            />
            <button type="submit" disabled={isRunning}>
              {isRunning ? "Running..." : "Generate update"}
            </button>
          </form>

          {answer ? (
            <div className="answer">
              <p>{answer}</p>
              <span>{mode === "template" ? "Template fallback" : "OpenAI"}</span>
            </div>
          ) : (
            <div className="empty">
              Generate a narrated update from the current live signal.
            </div>
          )}
        </div>
      </section>

      {error ? <div className="errorBox">{error}</div> : null}
    </main>
  );
}
