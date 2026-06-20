import { getISSLocation } from "@/lib/iss";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const location = await getISSLocation();
    return Response.json({ ok: true, location });
  } catch (error) {
    return Response.json(
      {
        ok: false,
        error:
          error instanceof Error ? error.message : "Unable to fetch ISS data.",
      },
      { status: 502 },
    );
  }
}
