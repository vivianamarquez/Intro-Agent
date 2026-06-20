# ISS Mission Control

Vercel-ready Next.js app for a live International Space Station tracker plus a mission-control narrator.

## Local Setup

```bash
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:3000`.

## Vercel Deployment

Set these environment variables in Vercel Project Settings:

```text
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4.1-mini
```

Deploy the `ISS/vercel-iss-mission-control` directory as the Vercel project root.

## Why This Shape

- `app/api/iss/route.ts` fetches live ISS data on the server.
- `app/api/mission-control/route.ts` sends verified ISS data to OpenAI for narration.
- The browser never receives `OPENAI_API_KEY`.
- If OpenAI is not configured, the app still returns a deterministic template update.
