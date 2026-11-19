import test from "node:test";
import assert from "node:assert/strict";
import { once } from "node:events";
import { createAppServer } from "./server.mjs";

async function withServer(run) {
  const server = createAppServer();
  server.listen(0, "127.0.0.1");
  await once(server, "listening");

  const { port } = server.address();
  try {
    await run(`http://127.0.0.1:${port}`);
  } finally {
    server.close();
    await once(server, "close");
  }
}

async function triage(baseUrl, body, raw = false) {
  return fetch(`${baseUrl}/api/triage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: raw ? body : JSON.stringify(body),
  });
}

test("returns ready for a valid model response", async () => {
  await withServer(async (baseUrl) => {
    const response = await triage(baseUrl, { text: "Когда будет доставка?" });
    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), {
      status: "ready",
      topic: "delivery",
      draft: "Спасибо за обращение. Уточним детали заявки.",
    });
  });
});

test("returns invalid_input for empty or broken input", async () => {
  await withServer(async (baseUrl) => {
    for (const body of [{}, { text: "   " }, { text: 123 }]) {
      const response = await triage(baseUrl, body);
      assert.equal(response.status, 400);
      assert.deepEqual(await response.json(), { status: "invalid_input" });
    }

    const brokenJson = await triage(baseUrl, "{", true);
    assert.equal(brokenJson.status, 400);
    assert.deepEqual(await brokenJson.json(), { status: "invalid_input" });
  });
});

test("falls back to manual review for model failures", async () => {
  await withServer(async (baseUrl) => {
    for (const marker of ["[error]", "[bad-json]", "[bad-topic]", "[empty-draft]"]) {
      const response = await triage(baseUrl, { text: `Заявка ${marker}` });
      assert.equal(response.status, 200);
      assert.deepEqual(await response.json(), {
        status: "manual_review",
        topic: null,
        draft: null,
      });
    }
  });
});

test("cuts off a slow model after 300 ms and returns manual review", async () => {
  await withServer(async (baseUrl) => {
    const started = Date.now();
    const response = await triage(baseUrl, { text: "Заявка [timeout]" });
    const elapsed = Date.now() - started;

    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), {
      status: "manual_review",
      topic: null,
      draft: null,
    });
    assert.ok(elapsed < 900, `expected timeout well below mock's 1200ms, got ${elapsed}ms`);
  });
});
