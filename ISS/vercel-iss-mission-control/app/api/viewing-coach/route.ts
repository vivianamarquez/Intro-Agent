import OpenAI from "openai";
import { getISSLocation } from "@/lib/iss";
import {
  buildRunSteps,
  deterministicViewingPlan,
  getViewerContext,
} from "@/lib/viewing";

export const dynamic = "force-dynamic";

type ViewingCoachRequest = {
  audience?: string;
  goal?: string;
  prompt?: string;
  viewerPlace?: string;
};

const DEFAULT_GOAL =
  "Help me decide whether it is worth planning a short ISS viewing session tonight.";
const DEFAULT_AUDIENCE = "casual stargazers";
const DEFAULT_MAX_OUTPUT_TOKENS = 700;

function outputTokenLimit(): number {
  const configured = Number(process.env.OPENAI_MAX_OUTPUT_TOKENS);

  if (Number.isFinite(configured) && configured > 0) {
    return Math.floor(configured);
  }

  return DEFAULT_MAX_OUTPUT_TOKENS;
}

export async function POST(request: Request) {
  const body = (await request.json().catch(() => ({}))) as ViewingCoachRequest;
  const goal = body.goal?.trim() || body.prompt?.trim() || DEFAULT_GOAL;
  const viewerPlace = body.viewerPlace?.trim() || "";
  const audience = body.audience?.trim() || DEFAULT_AUDIENCE;

  try {
    const [location, viewerContext] = await Promise.all([
      getISSLocation(),
      getViewerContext(viewerPlace),
    ]);
    const steps = buildRunSteps(location, viewerContext);

    if (!process.env.OPENAI_API_KEY) {
      return Response.json({
        ok: true,
        mode: "template",
        location,
        viewerContext,
        steps,
        tokenLimitHit: false,
        incompleteReason: null,
        tokenLimitNotice: null,
        answer: deterministicViewingPlan(location, viewerContext, goal, audience),
      });
    }

    const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
    const response = await client.responses.create({
      model: process.env.OPENAI_MODEL || "gpt-4.1-mini",
      instructions:
        "You are an ISS Viewing Coach. Help the user decide what to do next using only the verified context provided by the server. Do not invent exact local pass times. If pass windows are not in the provided data, say that a pass-prediction source still needs to be connected for exact timing. Do not reveal hidden reasoning; give a concise decision, the evidence, a short plan, and a backup.",
      input: [
        {
          role: "user",
          content: [
            {
              type: "input_text",
              text: [
                `Viewer goal: ${goal}`,
                `Audience: ${audience}`,
                `Viewer place request: ${viewerPlace || "not provided"}`,
                "",
                "Verified live ISS data:",
                JSON.stringify(location, null, 2),
                "",
                "Verified viewer context:",
                JSON.stringify(viewerContext, null, 2),
                "",
                "Return a practical coach-style answer with these parts:",
                "Decision:",
                "Evidence:",
                "Plan:",
                "Backup:",
                "Ask for one missing detail only if it would materially improve the recommendation.",
              ].join("\n"),
            },
          ],
        },
      ],
      max_output_tokens: outputTokenLimit(),
    });
    const answer = response.output_text?.trim();
    const incompleteReason = response.incomplete_details?.reason ?? null;
    const tokenLimitHit =
      response.status === "incomplete" &&
      incompleteReason === "max_output_tokens";

    return Response.json({
      ok: true,
      mode: "openai",
      location,
      viewerContext,
      steps,
      tokenLimitHit,
      incompleteReason,
      tokenLimitNotice: tokenLimitHit
        ? answer
          ? "The model reached the output token limit, so the coach answer may be partial."
          : "The model reached the output token limit before producing visible text. Increase OPENAI_MAX_OUTPUT_TOKENS or shorten the request."
        : null,
      answer:
        answer || deterministicViewingPlan(location, viewerContext, goal, audience),
    });
  } catch (error) {
    return Response.json(
      {
        ok: false,
        error:
          error instanceof Error
            ? error.message
            : "Viewing coach request failed.",
      },
      { status: 502 },
    );
  }
}
