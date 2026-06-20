import OpenAI from "openai";
import { deterministicMissionUpdate, getISSLocation } from "@/lib/iss";

export const dynamic = "force-dynamic";

type MissionRequest = {
  prompt?: string;
};

export async function POST(request: Request) {
  const body = (await request.json().catch(() => ({}))) as MissionRequest;
  const prompt =
    body.prompt?.trim() || "Where is the International Space Station right now?";

  try {
    const location = await getISSLocation();

    if (!process.env.OPENAI_API_KEY) {
      return Response.json({
        ok: true,
        mode: "template",
        location,
        answer: deterministicMissionUpdate(location),
      });
    }

    const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
    const response = await client.responses.create({
      model: process.env.OPENAI_MODEL || "gpt-4.1-mini",
      instructions:
        "You are a concise mission-control communicator. Use the provided live ISS data. Do not claim the data is unavailable unless the provided data says so.",
      input: [
        {
          role: "user",
          content: [
            {
              type: "input_text",
              text: [
                prompt,
                "",
                "Live ISS data:",
                JSON.stringify(location, null, 2),
                "",
                "Give a short, exciting, factual mission-control update.",
              ].join("\n"),
            },
          ],
        },
      ],
      max_output_tokens: 250,
    });

    return Response.json({
      ok: true,
      mode: "openai",
      location,
      answer: response.output_text || deterministicMissionUpdate(location),
    });
  } catch (error) {
    return Response.json(
      {
        ok: false,
        error:
          error instanceof Error
            ? error.message
            : "Mission-control update failed.",
      },
      { status: 502 },
    );
  }
}
