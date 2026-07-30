import assert from "node:assert/strict";
import { createServer } from "node:http";
import { fileURLToPath } from "node:url";
import test from "node:test";
import next from "next";

async function render() {
  const directory = fileURLToPath(new URL("..", import.meta.url));
  const application = next({ dev: false, dir: directory });
  await application.prepare();
  const handler = application.getRequestHandler();
  const server = createServer((request, response) => handler(request, response));
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  assert.ok(address && typeof address !== "string");

  try {
    const response = await fetch(`http://127.0.0.1:${address.port}/`, {
      headers: { accept: "text/html" },
    });
    return {
      status: response.status,
      contentType: response.headers.get("content-type") ?? "",
      html: await response.text(),
    };
  } finally {
    await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
    await application.close();
  }
}

test("server-renders the PO Monitor login page", async () => {
  const { status, contentType, html } = await render();
  assert.equal(status, 200);
  assert.match(contentType, /^text\/html\b/i);
  assert.match(html, /<title>PO Monitor Main \| SAP PO Operations<\/title>/i);
  assert.match(html, /MONITOR MAIN/);
  assert.match(html, /CONNECTED OPERATIONS/);
  assert.match(html, /운영 콘솔 로그인/);
  assert.match(html, /사용자 ID/);
  assert.match(html, /비밀번호/);
  assert.doesNotMatch(html, /Your site is taking shape/);
});
