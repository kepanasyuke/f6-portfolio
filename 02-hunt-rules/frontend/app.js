import { initClouds } from "/shared/clouds.js";
import { badge, danger, el, escape, fetchJson, number, render, table } from "/shared/api.js";

const DETECTION_COLUMNS = [
  { title: "Правило", cell: (row) => escape(row.rule_id) },
  { title: "Событие", cell: (row) => escape(row.event_id) },
  { title: "Хост", cell: (row) => escape(row.host) },
  { title: "Время", cell: (row) => escape(row.occurred_at) },
  { title: "Суть", cell: (row) => escape(row.summary) },
];

function toneFor(severity) {
  return { critical: "accent", high: "warn", medium: "", low: "ok" }[severity] || "";
}

async function loadRules() {
  const payload = await fetchJson("/api/rules");
  render(document.querySelector("#rule-grid"), payload.items.map(ruleCard));
  document.querySelector("#events").textContent = `источники: ${payload.sources.length}`;
}

function ruleCard(rule) {
  return el("div", { class: "card" }, [
    el("span", { class: "card__index", text: `${rule.id} · ${rule.tactic || "—"}` }),
    el("h3", { class: "card__title", text: rule.title }),
    el("p", { class: "card__text mono", text: selectionText(rule.selection) }),
    el("div", { class: "card__foot" }, [
      badge(rule.severity, toneFor(rule.severity)),
      badge(rule.condition),
      rule.technique ? badge(rule.technique) : null,
      el("span", { class: "tag", text: rule.source }),
    ]),
  ]);
}

function selectionText(selection) {
  return Object.entries(selection)
    .map(([field, value]) => `${field} = ${Array.isArray(value) ? value.join(" | ") : value}`)
    .join("\n");
}

async function loadEvents() {
  const payload = await fetchJson("/api/events");
  document.querySelector("#events").textContent = `событий: ${number(payload.count)}`;
}

async function runAll() {
  const payload = await fetchJson("/api/evaluate", { method: "POST", body: JSON.stringify({ rule_ids: [] }) });
  showFindings(payload);
  return payload;
}

function showFindings(payload) {
  document.querySelector("#total").textContent = `${number(payload.total)} срабатываний`;
  render(
    document.querySelector("#findings"),
    payload.findings.map((item) =>
      el("div", { class: "panel stack" }, [
        el("div", { class: "between" }, [
          el("h3", { class: "card__title", text: `${item.id} · ${item.title}` }),
          el("div", { class: "row" }, [badge(item.severity, toneFor(item.severity)), badge(`срабатываний: ${item.hits}`)]),
        ]),
        item.hits
          ? table(
              [
                { title: "Событие", cell: (row) => escape(row.id) },
                { title: "Хост", cell: (row) => escape(row.host) },
                { title: "Тип", cell: (row) => escape(row["event.type"]) },
                { title: "Процесс", cell: (row) => escape(row["process.name"]) },
                { title: "Время", cell: (row) => escape(row.ts) },
              ],
              item.matches,
            )
          : el("div", { class: "empty", text: "Совпадений нет" }),
      ]),
    ),
  );
}

async function replay() {
  const payload = await fetchJson("/api/replay", { method: "POST", body: JSON.stringify({ rule_ids: [] }) });
  showFindings(payload);
  await loadDetections();
}

async function loadDetections() {
  const payload = await fetchJson("/api/detections");
  render(document.querySelector("#detection-table"), [
    payload.items.length ? table(DETECTION_COLUMNS, payload.items) : el("div", { class: "empty", text: "Детекций пока нет" }),
  ]);
}

async function validateRule() {
  const status = document.querySelector("#validate-status");
  const output = document.querySelector("#validate-output");
  try {
    const payload = await fetchJson("/api/validate", { method: "POST", body: JSON.stringify({ text: text() }) });
    status.textContent = "корректно";
    status.className = "badge badge--ok";
    output.textContent = JSON.stringify(payload.rule, null, 2);
  } catch (error) {
    status.textContent = "ошибка";
    status.className = "badge badge--accent";
    output.textContent = error.message;
  }
}

async function saveRule() {
  try {
    const payload = await fetchJson("/api/rules", { method: "POST", body: JSON.stringify({ text: text() }) });
    document.querySelector("#validate-status").textContent = `сохранено: ${payload.id}`;
    await loadRules();
  } catch (error) {
    document.querySelector("#validate-output").textContent = error.message;
  }
}

function text() {
  return document.querySelector("#yaml").value;
}

function bind() {
  document.querySelector("#run").addEventListener("click", () => guard(runAll));
  document.querySelector("#replay").addEventListener("click", () => guard(replay));
  document.querySelector("#reload").addEventListener("click", () => guard(loadDetections));
  document.querySelector("#validate").addEventListener("click", () => guard(validateRule));
  document.querySelector("#save-rule").addEventListener("click", () => guard(saveRule));
}

async function guard(action) {
  try {
    return await action();
  } catch (error) {
    render(document.querySelector("#findings"), [danger(error.message)]);
    return null;
  }
}

async function boot() {
  initClouds(document.querySelector("#clouds"));
  bind();
  await guard(loadRules);
  await guard(loadEvents);
  await guard(loadDetections);
  await guard(runAll);
}

boot();
