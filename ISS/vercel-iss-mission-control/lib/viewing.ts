import type { ISSLocation } from "@/lib/iss";

export type ViewingReadinessLevel =
  | "needs_location"
  | "good"
  | "mixed"
  | "poor"
  | "unknown";

export type ViewingReadiness = {
  level: ViewingReadinessLevel;
  label: string;
  reasons: string[];
};

export type ViewerContext = {
  requestedPlace: string;
  placeName: string | null;
  latitude: number | null;
  longitude: number | null;
  timezone: string | null;
  localTime: string | null;
  cloudCoverPercent: number | null;
  visibilityMeters: number | null;
  readiness: ViewingReadiness;
  source: string[];
  status:
    | "missing_location"
    | "ready"
    | "place_not_found"
    | "weather_unavailable"
    | "lookup_failed";
};

type GeocodeResponse = {
  results?: Array<{
    name: string;
    latitude: number;
    longitude: number;
    country?: string;
    admin1?: string;
    timezone?: string;
  }>;
};

type ForecastResponse = {
  timezone?: string;
  current?: {
    time?: string;
    cloud_cover?: number;
  };
  hourly?: {
    time?: string[];
    visibility?: number[];
  };
};

const GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search";
const FORECAST_URL = "https://api.open-meteo.com/v1/forecast";

function round(value: number, places = 2): number {
  const multiplier = 10 ** places;
  return Math.round(value * multiplier) / multiplier;
}

async function fetchJson(url: string): Promise<unknown> {
  const response = await fetch(url, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(`${url} returned ${response.status}`);
  }

  return response.json();
}

function placeNameFor(
  result: NonNullable<GeocodeResponse["results"]>[number],
): string {
  return [result.name, result.admin1, result.country].filter(Boolean).join(", ");
}

function nearestVisibility(forecast: ForecastResponse): number | null {
  const times = forecast.hourly?.time;
  const visibility = forecast.hourly?.visibility;
  const currentTime = forecast.current?.time;

  if (!times?.length || !visibility?.length || !currentTime) return null;

  const index = times.findIndex((time) => time >= currentTime);
  const safeIndex = index >= 0 ? index : 0;
  const value = visibility[safeIndex];

  return typeof value === "number" ? Math.round(value) : null;
}

function readinessFromWeather(
  status: ViewerContext["status"],
  cloudCoverPercent: number | null,
  visibilityMeters: number | null,
): ViewingReadiness {
  if (status === "missing_location") {
    return {
      level: "needs_location",
      label: "Needs viewer location",
      reasons: ["Add a nearest city or landmark so the coach can check local sky conditions."],
    };
  }

  if (status === "place_not_found") {
    return {
      level: "unknown",
      label: "Place not found",
      reasons: ["Try a nearby city, town, or landmark."],
    };
  }

  if (status === "lookup_failed") {
    return {
      level: "unknown",
      label: "Lookup failed",
      reasons: ["The viewer-side lookup did not return usable data."],
    };
  }

  if (cloudCoverPercent === null && visibilityMeters === null) {
    return {
      level: "unknown",
      label: "Conditions unknown",
      reasons: ["Weather data was not available for this location."],
    };
  }

  const reasons: string[] = [];
  if (cloudCoverPercent !== null) {
    reasons.push(`${cloudCoverPercent}% cloud cover`);
  }
  if (visibilityMeters !== null) {
    reasons.push(`${round(visibilityMeters / 1000, 1)} km visibility`);
  }

  if (
    (cloudCoverPercent !== null && cloudCoverPercent > 70) ||
    (visibilityMeters !== null && visibilityMeters < 8000)
  ) {
    return {
      level: "poor",
      label: "Poor viewing odds",
      reasons,
    };
  }

  if (
    (cloudCoverPercent !== null && cloudCoverPercent > 35) ||
    (visibilityMeters !== null && visibilityMeters < 16000)
  ) {
    return {
      level: "mixed",
      label: "Mixed viewing odds",
      reasons,
    };
  }

  return {
    level: "good",
    label: "Good viewing odds",
    reasons,
  };
}

export async function getViewerContext(placeQuery: string): Promise<ViewerContext> {
  const requestedPlace = placeQuery.trim();

  if (!requestedPlace) {
    return {
      requestedPlace,
      placeName: null,
      latitude: null,
      longitude: null,
      timezone: null,
      localTime: null,
      cloudCoverPercent: null,
      visibilityMeters: null,
      readiness: readinessFromWeather("missing_location", null, null),
      source: [],
      status: "missing_location",
    };
  }

  try {
    const geocodeUrl = `${GEOCODE_URL}?name=${encodeURIComponent(
      requestedPlace,
    )}&count=1&language=en&format=json`;
    const geocode = (await fetchJson(geocodeUrl)) as GeocodeResponse;
    const result = geocode.results?.[0];

    if (!result) {
      return {
        requestedPlace,
        placeName: null,
        latitude: null,
        longitude: null,
        timezone: null,
        localTime: null,
        cloudCoverPercent: null,
        visibilityMeters: null,
        readiness: readinessFromWeather("place_not_found", null, null),
        source: ["open-meteo geocoding"],
        status: "place_not_found",
      };
    }

    const latitude = round(result.latitude, 4);
    const longitude = round(result.longitude, 4);

    try {
      const forecastUrl = `${FORECAST_URL}?latitude=${latitude}&longitude=${longitude}&current=cloud_cover&hourly=visibility&forecast_days=1&timezone=auto`;
      const forecast = (await fetchJson(forecastUrl)) as ForecastResponse;
      const cloudCoverPercent =
        typeof forecast.current?.cloud_cover === "number"
          ? forecast.current.cloud_cover
          : null;
      const visibilityMeters = nearestVisibility(forecast);
      const status: ViewerContext["status"] =
        cloudCoverPercent === null && visibilityMeters === null
          ? "weather_unavailable"
          : "ready";

      return {
        requestedPlace,
        placeName: placeNameFor(result),
        latitude,
        longitude,
        timezone: forecast.timezone || result.timezone || null,
        localTime: forecast.current?.time || null,
        cloudCoverPercent,
        visibilityMeters,
        readiness: readinessFromWeather(status, cloudCoverPercent, visibilityMeters),
        source: ["open-meteo geocoding", "open-meteo forecast"],
        status,
      };
    } catch {
      return {
        requestedPlace,
        placeName: placeNameFor(result),
        latitude,
        longitude,
        timezone: result.timezone || null,
        localTime: null,
        cloudCoverPercent: null,
        visibilityMeters: null,
        readiness: readinessFromWeather("weather_unavailable", null, null),
        source: ["open-meteo geocoding"],
        status: "weather_unavailable",
      };
    }
  } catch {
    return {
      requestedPlace,
      placeName: null,
      latitude: null,
      longitude: null,
      timezone: null,
      localTime: null,
      cloudCoverPercent: null,
      visibilityMeters: null,
      readiness: readinessFromWeather("lookup_failed", null, null),
      source: [],
      status: "lookup_failed",
    };
  }
}

export function deterministicViewingPlan(
  location: ISSLocation,
  viewerContext: ViewerContext,
  goal: string,
  audience: string,
): string {
  const altitude =
    location.altitudeKm === null
      ? "altitude unavailable"
      : `${location.altitudeKm.toLocaleString()} km altitude`;
  const speed =
    location.velocityKmPerHour === null
      ? "speed unavailable"
      : `${location.velocityKmPerHour.toLocaleString()} km/h`;

  if (viewerContext.status === "missing_location") {
    return [
      "ISS Viewing Coach:",
      `I have the live station signal over ${location.placeName} at ${location.latitude}, ${location.longitude}, with ${altitude} and ${speed}.`,
      "To plan a real viewing session, add your nearest city or landmark so I can check local sky conditions before recommending the next move.",
    ].join(" ");
  }

  const place = viewerContext.placeName || viewerContext.requestedPlace;
  const conditions = viewerContext.readiness.reasons.length
    ? viewerContext.readiness.reasons.join(", ")
    : "local viewing conditions unavailable";
  const decision =
    viewerContext.readiness.level === "poor"
      ? "make this a backup-plan night"
      : viewerContext.readiness.level === "mixed"
        ? "prepare, but keep expectations flexible"
        : viewerContext.readiness.level === "good"
          ? "it is worth preparing a short viewing session"
          : "collect one more reliable viewing signal before committing";

  return [
    "ISS Viewing Coach:",
    `For this audience (${audience}): ${decision}.`,
    `Your goal is: ${goal}`,
    `Viewer context: ${place} has ${conditions}.`,
    `Live station context: the ISS is over ${location.placeName} at ${location.latitude}, ${location.longitude}, with ${altitude} and ${speed}.`,
    "Exact local pass windows are not connected yet, so verify the pass time with a pass-prediction source before sending people outside.",
  ].join(" ");
}

export function buildRunSteps(
  location: ISSLocation,
  viewerContext: ViewerContext,
): string[] {
  const steps = [
    `Checked live ISS telemetry from ${location.source}.`,
    `Resolved current station place as ${location.placeName}.`,
  ];

  if (viewerContext.status === "missing_location") {
    steps.push("Paused local planning until the viewer provides a city or landmark.");
  } else if (viewerContext.placeName) {
    steps.push(`Resolved viewer location as ${viewerContext.placeName}.`);
    steps.push(`Evaluated viewing conditions: ${viewerContext.readiness.label}.`);
  } else {
    steps.push(`Viewer location lookup returned: ${viewerContext.readiness.label}.`);
  }

  steps.push("Prepared a recommendation without inventing exact pass times.");
  return steps;
}
