import { initClouds } from "/shared/clouds.js";
import { badge, danger, el, escape, fetchJson, number, render, table } from "/shared/api.js";

const COLUMNS = [
  { title: "Индикатор", cell: (row) => escape(row.value) },
  { title: "Тип", cell: (row) => `<span class="muted">${escape(row.kind)}</span>` },
  { title: "Критичность", cell: (row) => severityBadge(row.severity) },
  { title: "Источник", cell: (row) => escape(row.source) },
  { title: "Уверенность", cell: (row) => meter(row.confidence) },
  { title: "Впервые", cell: (row) => escape(row.first_seen) },
  { title: "Теги", cell: (row) => tags(row.tags) },
];

function severityBadge(severity) {
  const tone = { critical: "accent", high: "warn", medium: "", low: "ok" }[severity];
  return `<span class="badge ${tone ? `badge--${tone}` : ""}">${escape(severity)}</span>`;
}

function meter(value) {
  return `<div class="row" style="gap:8px"><span class="mono">${number(value)}</span>
    <span class="meter" style="flex:1;min-width:60px"><i style="width:${Number(value) || 0}%"></i></span></div>`;
}

function tags(value) {
  return String(value || "")
    .split(",")
    .filter(Boolean)
    .map((item) => `<span class="tag">${escape(item)}</span>`)
    .join(" ");
}

function stat(value, label) {
  return el("div", { class: "stat" }, [
    el("div", { class: "stat__value", text: number(value) }),
    el("div", { class: "stat__label", text: label }),
  ]);
}

function fillSelect(select, values, placeholder) {
  select.replaceChildren(el("option", { value: "", text: placeholder }));
  values.forEach((value) => select.append(el("option", { value, text: value })));
}

async function loadStats() {
  const stats = await fetchJson("/api/stats");
  render(document.querySelector("#stats-grid"), [
    stat(stats.total, "всего индикаторов"),
    ...Object.entries(stats.by_kind).map(([key, value]) => stat(value, key)),
    ...Object.entries(stats.by_severity).map(([key, value]) => stat(value, key)),
  ]);
  fillSelect(document.querySelector("#kind"), Object.keys(stats.by_kind), "любой тип");
  fillSelect(document.querySelector("#severity"), Object.keys(stats.by_severity), "любая");
  return stats;
}

async function loadIocs() {
  const params = new URLSearchParams({ limit: "100" });
  const kind = document.querySelector("#kind").value;
  const severity = document.querySelector("#severity").value;
  const query = document.querySelector("#query").value.trim();
  if (kind) params.set("kind", kind);
  if (severity) params.set("severity", severity);
  if (query) params.set("q", query);
  const payload = await fetchJson(`/api/iocs?${params}`);
  document.querySelector("#count").textContent = `${number(payload.count)} записей`;
  const body = payload.items.length ? table(COLUMNS, payload.items) : el("div", { class: "empty", text: "Ничего не найдено" });
  render(document.querySelector("#results"), [body]);
  return payload;
}

async function loadFeeds() {
  const payload = await fetchJson("/api/feeds");
  render(
    document.querySelector("#feeds"),
    payload.items.map((name) => badge(name, "ok")),
  );
}

async function loadHealth() {
  const health = await fetchJson("/api/health");
  const node = document.querySelector("#health");
  node.textContent = `${health.service} · ${health.version}`;
  return health;
}

async function ingest() {
  const target = document.querySelector("#ingest-result");
  try {
    const payload = await fetchJson("/api/ingest", {
      method: "POST",
      body: JSON.stringify({
        format: document.querySelector("#format").value,
        content: document.querySelector("#content").value,
      }),
    });
    target.textContent = `разобрано ${payload.parsed} · сохранено ${payload.stored} · отброшено ${payload.rejected}`;
    await refresh();
  } catch (error) {
    target.textContent = `ошибка: ${error.message}`;
  }
}

async function loadAll() {
  const payload = await fetchJson("/api/ingest/all", { method: "POST", body: "{}" });
  const total = payload.results.reduce((sum, item) => sum + item.stored, 0);
  document.querySelector("#ingest-result").textContent = `файлов ${payload.results.length} · сохранено ${total}`;
  await refresh();
}

async function refresh() {
  try {
    await loadStats();
    await loadIocs();
  } catch (error) {
    render(document.querySelector("#results"), [danger(`API недоступен: ${error.message}`)]);
  }
}

function bind() {
  document.querySelector("#apply").addEventListener("click", refresh);
  document.querySelector("#reload").addEventListener("click", refresh);
  document.querySelector("#ingest-run").addEventListener("click", ingest);
  document.querySelector("#load-all").addEventListener("click", loadAll);
  document.querySelector("#query").addEventListener("keydown", (event) => event.key === "Enter" && refresh());
}

async function boot() {
  initClouds(document.querySelector("#clouds"));
  bind();
  await loadHealth().catch((error) => (document.querySelector("#health").textContent = error.message));
  await loadFeeds().catch(() => {});
  await refresh();
}

boot();
