# ISS Viewing Coach

Vercel-ready Next.js app for a live International Space Station tracker plus a viewing coach.

The app does more than narrate an API response:

- checks the current ISS position on the server
- resolves the viewer's nearest place when provided
- checks local cloud cover and visibility
- asks OpenAI for a practical viewing recommendation from those verified facts
- shows a visible warning if the OpenAI response runs out of output tokens

## Local Setup

```bash
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:3000`.

## Vercel Deployment

Deploy the `ISS/vercel-iss-mission-control` directory as the Vercel project root.

Set these environment variables in Vercel Project Settings:

```text
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4.1-mini
OPENAI_MAX_OUTPUT_TOKENS=700
```

`OPENAI_MAX_OUTPUT_TOKENS` is optional. Set it lower if you want to test the token-limit warning state.

## Why This Shape

- `app/api/iss/route.ts` fetches live ISS data on the server.
- `app/api/viewing-coach/route.ts` gathers ISS, viewer, and weather context before calling OpenAI.
- `lib/viewing.ts` keeps the place lookup, weather lookup, readiness scoring, run trace, and fallback answer separate from the UI.
- The browser never receives `OPENAI_API_KEY`.
- If OpenAI is not configured, the app still returns a deterministic viewing plan.
