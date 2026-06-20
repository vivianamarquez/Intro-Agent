export type ISSLocation = {
  placeName: string;
  latitude: number;
  longitude: number;
  altitudeKm: number | null;
  velocityKmPerHour: number | null;
  source: string;
  timestamp: number;
};

const ISS_URL = "https://api.wheretheiss.at/v1/satellites/25544";
const OPEN_NOTIFY_URL = "http://api.open-notify.org/iss-now.json";
const REVERSE_GEOCODE_URL =
  "https://api.bigdatacloud.net/data/reverse-geocode-client";

function round(value: number, places = 2): number {
  const multiplier = 10 ** places;
  return Math.round(value * multiplier) / multiplier;
}

async function fetchJson(url: string, init?: RequestInit): Promise<unknown> {
  const response = await fetch(url, {
    ...init,
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`${url} returned ${response.status}`);
  }

  return response.json();
}

async function getPlaceName(
  latitude: number,
  longitude: number,
): Promise<string> {
  try {
    const data = (await fetchJson(
      `${REVERSE_GEOCODE_URL}?latitude=${latitude}&longitude=${longitude}&localityLanguage=en`,
    )) as {
      locality?: string;
      city?: string;
      principalSubdivision?: string;
      countryName?: string;
    };

    const parts = [
      data.locality || data.city,
      data.principalSubdivision,
      data.countryName,
    ].filter(Boolean);

    return parts.length ? parts.join(", ") : "open ocean or remote region";
  } catch {
    return "place lookup unavailable";
  }
}

export async function getISSLocation(): Promise<ISSLocation> {
  try {
    const data = (await fetchJson(ISS_URL)) as {
      latitude: number;
      longitude: number;
      altitude: number;
      velocity: number;
      timestamp?: number;
    };

    const latitude = data.latitude;
    const longitude = data.longitude;

    return {
      placeName: await getPlaceName(latitude, longitude),
      latitude: round(latitude),
      longitude: round(longitude),
      altitudeKm: round(data.altitude),
      velocityKmPerHour: round(data.velocity),
      source: "wheretheiss.at",
      timestamp: data.timestamp ?? Math.floor(Date.now() / 1000),
    };
  } catch {
    const fallback = (await fetchJson(OPEN_NOTIFY_URL)) as {
      timestamp: number;
      iss_position: {
        latitude: string;
        longitude: string;
      };
    };

    const latitude = Number(fallback.iss_position.latitude);
    const longitude = Number(fallback.iss_position.longitude);

    return {
      placeName: await getPlaceName(latitude, longitude),
      latitude: round(latitude),
      longitude: round(longitude),
      altitudeKm: null,
      velocityKmPerHour: null,
      source: "open-notify.org",
      timestamp: fallback.timestamp,
    };
  }
}

export function deterministicMissionUpdate(location: ISSLocation): string {
  const altitude =
    location.altitudeKm === null
      ? "altitude currently unavailable"
      : `altitude ${location.altitudeKm.toLocaleString()} kilometers`;
  const speed =
    location.velocityKmPerHour === null
      ? "speed currently unavailable"
      : `speed ${location.velocityKmPerHour.toLocaleString()} kilometers per hour`;

  return [
    "Mission Control update:",
    `The International Space Station is currently over ${location.placeName}.`,
    `Current coordinates are ${location.latitude}, ${location.longitude}, with ${altitude} and ${speed}.`,
    "Live signal confirmed.",
  ].join(" ");
}
