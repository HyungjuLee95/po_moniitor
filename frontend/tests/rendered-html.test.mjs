import assert from "node:assert/strict";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("server-renders the PO Monitor login page", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>PO Monitor Main \| SAP PO Operations<\/title>/i);
  assert.match(html, /MONITOR MAIN/);
  assert.match(html, /CONNECTED OPERATIONS/);
  assert.match(html, /운영 콘솔 로그인/);
  assert.match(html, /사용자 ID/);
  assert.match(html, /비밀번호/);
  assert.doesNotMatch(html, /Your site is taking shape/);
});
