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

type ViewerContext = {
  requestedPlace: string;
  placeName: string | null;
  latitude: number | null;
  longitude: number | null;
  timezone: string | null;
  localTime: string | null;
  cloudCoverPercent: number | null;
  visibilityMeters: number | null;
  readiness: {
    level: "needs_location" | "good" | "mixed" | "poor" | "unknown";
    label: string;
    reasons: string[];
  };
  source: string[];
  status:
    | "missing_location"
    | "ready"
    | "place_not_found"
    | "weather_unavailable"
    | "lookup_failed";
};

type MissionResponse = {
  ok: boolean;
  mode?: string;
  location?: ISSLocation;
  viewerContext?: ViewerContext;
  steps?: string[];
  answer?: string;
  tokenLimitHit?: boolean;
  incompleteReason?: string | null;
  tokenLimitNotice?: string | null;
  error?: string;
};

const DEFAULT_GOAL =
  "Help me decide whether it is worth planning a short ISS viewing session tonight.";

function formatNumber(value: number | null, suffix: string) {
  return value === null ? "Unavailable" : `${value.toLocaleString()} ${suffix}`;
}

function formatPercent(value: number | null) {
  return value === null ? "Unavailable" : `${value}%`;
}

function formatVisibility(value: number | null) {
  if (value === null) return "Unavailable";
  return `${(value / 1000).toLocaleString(undefined, {
    maximumFractionDigits: 1,
  })} km`;
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

function contextPlace(viewerContext: ViewerContext) {
  return viewerContext.placeName || viewerContext.requestedPlace || "Not set";
}

export default function Home() {
  const [location, setLocation] = useState<ISSLocation | null>(null);
  const [viewerPlace, setViewerPlace] = useState("");
  const [audience, setAudience] = useState("casual stargazers");
  const [goal, setGoal] = useState(DEFAULT_GOAL);
  const [viewerContext, setViewerContext] = useState<ViewerContext | null>(null);
  const [steps, setSteps] = useState<string[]>([]);
  const [answer, setAnswer] = useState("");
  const [status, setStatus] = useState("Loading live ISS signal...");
  const [mode, setMode] = useState("");
  const [tokenLimitHit, setTokenLimitHit] = useState(false);
  const [tokenLimitNotice, setTokenLimitNotice] = useState<string | null>(null);
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

  async function runViewingCoach(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsRunning(true);
    setError("");
    setAnswer("");
    setMode("");
    setSteps([]);
    setTokenLimitHit(false);
    setTokenLimitNotice(null);
    setStatus("Checking ISS signal and local viewing conditions...");

    try {
      const response = await fetch("/api/viewing-coach", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ audience, goal, viewerPlace }),
      });
      const data = (await response.json()) as MissionResponse;
      if (!response.ok || !data.ok) {
        throw new Error(data.error || "Viewing coach request failed.");
      }
      if (data.location) setLocation(data.location);
      setViewerContext(data.viewerContext || null);
      setSteps(data.steps || []);
      setAnswer(data.answer || "");
      setMode(data.mode || "");
      setTokenLimitHit(Boolean(data.tokenLimitHit));
      setTokenLimitNotice(data.tokenLimitNotice || null);
      setStatus(
        data.tokenLimitHit
          ? "Coach stopped at the output token limit."
          : "Viewing plan ready.",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Viewing coach failed.");
      setStatus("Viewing coach failed.");
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
          <p className="eyebrow">Live orbital planning</p>
          <h1>ISS Viewing Coach</h1>
          <p className="summary">
            Turn live station telemetry and local sky conditions into a concrete
            viewing decision.
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

        <div className="panel coach">
          <div className="panelHeader">
            <div>
              <p className="kicker">Coach</p>
              <h2>Viewing Plan</h2>
            </div>
          </div>

          <form onSubmit={runViewingCoach}>
            <div className="formRow">
              <div className="field">
                <label htmlFor="viewerPlace">Nearest place</label>
                <input
                  id="viewerPlace"
                  placeholder="Los Angeles"
                  value={viewerPlace}
                  onChange={(event) => setViewerPlace(event.target.value)}
                />
              </div>
              <div className="field">
                <label htmlFor="audience">Audience</label>
                <select
                  id="audience"
                  value={audience}
                  onChange={(event) => setAudience(event.target.value)}
                >
                  <option>casual stargazers</option>
                  <option>classroom learners</option>
                  <option>family watch party</option>
                  <option>first-time skywatchers</option>
                </select>
              </div>
            </div>

            <label htmlFor="goal">Goal</label>
            <textarea
              id="goal"
              value={goal}
              onChange={(event) => setGoal(event.target.value)}
            />
            <button type="submit" disabled={isRunning}>
              {isRunning ? "Planning..." : "Plan viewing session"}
            </button>
          </form>

          {viewerContext ? (
            <div className="viewerContext">
              <div>
                <span>Viewer</span>
                <strong>{contextPlace(viewerContext)}</strong>
              </div>
              <div>
                <span>Readiness</span>
                <strong className={`readiness ${viewerContext.readiness.level}`}>
                  {viewerContext.readiness.label}
                </strong>
              </div>
              <div>
                <span>Cloud cover</span>
                <strong>{formatPercent(viewerContext.cloudCoverPercent)}</strong>
              </div>
              <div>
                <span>Visibility</span>
                <strong>{formatVisibility(viewerContext.visibilityMeters)}</strong>
              </div>
            </div>
          ) : null}

          {tokenLimitHit ? (
            <div className="warningBox" role="alert">
              {tokenLimitNotice ||
                "The model ran out of output tokens before finishing."}
            </div>
          ) : null}

          {steps.length ? (
            <div className="steps">
              <span>Run trace</span>
              <ol>
                {steps.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ol>
            </div>
          ) : null}

          {answer ? (
            <div className="answer">
              <p>{answer}</p>
              <span>{mode === "template" ? "Template fallback" : "OpenAI"}</span>
            </div>
          ) : (
            <div className="empty">
              Add a place and goal to produce a viewing recommendation.
            </div>
          )}
        </div>
      </section>

      {error ? <div className="errorBox">{error}</div> : null}
    </main>
  );
}
