import { initClouds } from "/shared/clouds.js";
import { danger, el, escape, fetchJson, number, render } from "/shared/api.js";

const HIGHLIGHTS = ["@timestamp", "host", "event.category", "event.outcome", "user.name", "source.ip", "process.name", "http.response.status_code", "url.path"];

function stat(value, label) {
  return el("div", { class: "stat" }, [
    el("div", { class: "stat__value", text: number(value) }),
    el("div", { class: "stat__label", text: label }),
  ]);
}

function kv(field, value) {
  return el("div", { class: "row", style: "gap:8px" }, [
    el("span", { class: "muted mono", style: "min-width:190px", text: field }),
    el("span", { class: "mono", text: String(value) }),
  ]);
}

function documentCard(doc) {
  return el("div", { class: "panel stack" }, [
    el("div", { class: "between" }, [
      el("span", { class: "mono muted", text: `${doc.id || "—"} · ${doc["event.dataset"] || "raw"}` }),
      el("span", { class: "badge badge--accent", text: `score ${doc._score}` }),
    ]),
    el("div", { class: "stack", style: "gap:6px" }, HIGHLIGHTS.filter((field) => doc[field] !== undefined).map((field) => kv(field, doc[field]))),
    el("div", { class: "mono muted", style: "font-size:12px;word-break:break-all", text: doc.message || "" }),
  ]);
}

async function stats() {
  const payload = await fetchJson("/api/stats");
  render(document.querySelector("#stats"), [
    stat(payload.documents, "документов"),
    stat(payload.terms, "термов в индексе"),
    ...Object.entries(payload.categories).map(([key, value]) => stat(value, key)),
  ]);
  return payload;
}

async function search(query) {
  const payload = await fetchJson("/api/search", { method: "POST", body: JSON.stringify({ query, limit: 25 }) });
  document.querySelector("#hits").textContent = `${number(payload.count)} совпадений`;
  render(
    document.querySelector("#results"),
    payload.items.length ? payload.items.map(documentCard) : [el("div", { class: "empty", text: "Совпадений нет — попробуйте другой запрос или маску 203.0.113.*" })],
  );
  return payload;
}

async function recent() {
  const payload = await fetchJson("/api/logs?limit=12");
  document.querySelector("#hits").textContent = `${number(payload.items.length)} последних событий`;
  render(document.querySelector("#results"), payload.items.map(documentCard));
  return payload;
}

async function reindex() {
  const payload = await fetchJson("/api/reindex", { method: "POST", body: "{}" });
  document.querySelector("#ingest-status").textContent = `переиндексировано: ${payload.documents}`;
  await stats();
  return payload;
}

async function ingest() {
  const status = document.querySelector("#ingest-status");
  try {
    const payload = await fetchJson("/api/ingest", {
      method: "POST",
      body: JSON.stringify({
        format: document.querySelector("#format").value,
        content: document.querySelector("#content").value,
        prefix: "manual",
      }),
    });
    status.textContent = `сохранено ${payload.stored} · в базе ${payload.documents}`;
    await stats();
    await recent();
  } catch (error) {
    status.textContent = `ошибка: ${error.message}`;
  }
}

async function loadMapping() {
  const payload = await fetchJson("/api/mapping");
  const fields = Object.entries(payload.mappings.properties).map(([name, spec]) => `${name.padEnd(30)} ${spec.type}`);
  render(document.querySelector("#mapping"), [el("span", { text: fields.join("\n") })]);
}

function bind() {
  document.querySelector("#go").addEventListener("click", () => run(() => search(document.querySelector("#query").value)));
  document.querySelector("#all").addEventListener("click", () => run(recent));
  document.querySelector("#reindex").addEventListener("click", () => run(reindex));
  document.querySelector("#ingest-run").addEventListener("click", ingest);
  document.querySelector("#query").addEventListener("keydown", (event) => event.key === "Enter" && run(() => search(document.querySelector("#query").value)));
}

async function run(action) {
  try {
    return await action();
  } catch (error) {
    render(document.querySelector("#results"), [danger(error.message)]);
    return null;
  }
}

async function boot() {
  initClouds(document.querySelector("#clouds"));
  bind();
  await run(stats);
  await run(loadMapping);
  await run(() => search(document.querySelector("#query").value));
}

boot();
