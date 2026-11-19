import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { classify } from "./mock-ai.mjs";

const html = await readFile(new URL("./index.html", import.meta.url));
const ALLOWED_TOPICS = new Set(["delivery", "pricing", "other"]);
const MODEL_TIMEOUT_MS = 300;

function json(response, status, body) {
  response.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
  response.end(JSON.stringify(body));
}

function manualReview(response) {
  return json(response, 200, {
    status: "manual_review",
    topic: null,
    draft: null,
  });
}

function isValidModelResult(value) {
  return (
    value !== null &&
    typeof value === "object" &&
    ALLOWED_TOPICS.has(value.topic) &&
    typeof value.draft === "string" &&
    value.draft.trim().length > 0
  );
}

async function readInput(request) {
  const chunks = [];
  for await (const chunk of request) chunks.push(chunk);

  let body;
  try {
    body = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  } catch {
    return null;
  }

  if (!body || typeof body.text !== "string" || body.text.trim().length === 0) {
    return null;
  }

  return body.text;
}

async function handleTriage(request, response) {
  const text = await readInput(request);
  if (text === null) {
    return json(response, 400, { status: "invalid_input" });
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), MODEL_TIMEOUT_MS);

  try {
    const raw = await classify(text, { signal: controller.signal });
    const result = JSON.parse(raw);

    if (!isValidModelResult(result)) {
      return manualReview(response);
    }

    return json(response, 200, {
      status: "ready",
      topic: result.topic,
      draft: result.draft.trim(),
    });
  } catch {
    return manualReview(response);
  } finally {
    clearTimeout(timeout);
  }
}

export function createAppServer() {
  return createServer(async (request, response) => {
    if (request.method === "GET" && request.url === "/") {
      response.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      response.end(html);
      return;
    }

    if (request.method !== "POST" || request.url !== "/api/triage") {
      return json(response, 404, { status: "not_found" });
    }

    try {
      await handleTriage(request, response);
    } catch {
      json(response, 500, { status: "server_error" });
    }
  });
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  createAppServer().listen(Number(process.env.PORT || 3000), "127.0.0.1");
}
