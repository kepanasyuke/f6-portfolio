import { initClouds } from "/shared/clouds.js";
import { badge, danger, el, escape, fetchJson, number, render, table } from "/shared/api.js";

const TONES = { ok: "ok", warn: "warn", critical: "accent", unknown: "" };
const state = { selected: null };

function tone(status) {
  return TONES[status] || "";
}

function stat(value, label) {
  return el("div", { class: "stat" }, [
    el("div", { class: "stat__value", text: number(value) }),
    el("div", { class: "stat__label", text: label }),
  ]);
}

function hostRow(item) {
  return [
    `<button class="node-chip" data-host="${escape(item.name)}">${escape(item.name)}</button>`,
    escape(item.role),
    escape(item.os),
    escape(item.ip),
    escape(item.owner),
    badge(item.status, tone(item.status)).outerHTML,
    String(item.checks.filter((check) => check.status !== "ok").length),
  ];
}

const COLUMNS = [
  { title: "Хост", cell: (row) => row[0] },
  { title: "Роль", cell: (row) => row[1] },
  { title: "ОС", cell: (row) => row[2] },
  { title: "IP", cell: (row) => row[3] },
  { title: "Владелец", cell: (row) => row[4] },
  { title: "Статус", cell: (row) => row[5] },
  { title: "Проблем", cell: (row) => row[6] },
];

async function loadOverview() {
  const payload = await fetchJson("/api/overview");
  render(document.querySelector("#stats"), [
    stat(payload.stats.total, "хостов"),
    ...Object.entries(payload.stats.by_status).map(([key, value]) => stat(value, key)),
    ...Object.entries(payload.stats.by_os).map(([key, value]) => stat(value, key)),
  ]);
  const box = document.querySelector("#host-table");
  render(box, [table(COLUMNS, payload.hosts.map((item) => hostRow(item)))]);
  box.querySelectorAll("[data-host]").forEach((button) => button.addEventListener("click", () => select(button.dataset.host)));
  return payload;
}

function checkRow(check) {
  return el("div", { class: "between" }, [
    el("span", { class: "mono muted", text: check.title }),
    el("div", { class: "row" }, [
      el("span", { class: "mono", text: `${number(check.value)} ${check.unit}`.trim() }),
      badge(check.status, tone(check.status)),
    ]),
  ]);
}

async function select(name) {
  state.selected = name;
  const payload = await fetchJson(`/api/hosts/${encodeURIComponent(name)}`);
  document.querySelector("#selected").textContent = `${payload.name} · ${payload.status}`;
  render(document.querySelector("#host-card"), [
    el("div", { class: "between" }, [
      el("h3", { class: "card__title", text: payload.name }),
      badge(payload.status, tone(payload.status)),
    ]),
    el("div", { class: "mono muted", text: `${payload.os} · ${payload.role} · ${payload.ip} · ${payload.owner}` }),
    el("div", { class: "stack", style: "gap:10px" }, payload.checks.map(checkRow)),
    el("button", {
      class: "btn btn--ghost",
      type: "button",
      text: "Прогнать проверки",
      onclick: () => run(() => checkHost(name)),
    }),
  ]);
  return payload;
}

async function checkHost(name) {
  await fetchJson(`/api/hosts/${encodeURIComponent(name)}/check`, { method: "POST", body: "{}" });
  await loadOverview();
  await loadJournal();
  return select(name);
}

async function checkAll() {
  await fetchJson("/api/check-all", { method: "POST", body: "{}" });
  await loadOverview();
  await loadJournal();
  return state.selected ? select(state.selected) : null;
}

async function loadJournal() {
  const payload = await fetchJson("/api/journal?limit=12");
  render(
    document.querySelector("#journal"),
    payload.items.map((item) =>
      el("div", { class: "mono muted", style: "font-size:12px", text: `${item.created_at} · ${item.action} · ${item.target} ${item.detail}` }),
    ),
  );
  return payload;
}

async function loadPlaybook(osName) {
  const payload = await fetchJson(`/api/playbook?os=${encodeURIComponent(osName)}`);
  render(
    document.querySelector("#checklist"),
    payload.items.map((item) =>
      el("div", { class: "card" }, [
        el("span", { class: "card__index", text: item.id }),
        el("h3", { class: "card__title", text: item.title }),
        el("p", { class: "card__text mono", text: item.how }),
      ]),
    ),
  );
  return payload;
}

function bind() {
  document.querySelector("#check-all").addEventListener("click", () => run(checkAll));
  document.querySelector("#linux").addEventListener("click", () => run(() => loadPlaybook("linux")));
  document.querySelector("#windows").addEventListener("click", () => run(() => loadPlaybook("windows")));
}

async function run(action) {
  try {
    return await action();
  } catch (error) {
    render(document.querySelector("#host-card"), [danger(error.message)]);
    return null;
  }
}

async function boot() {
  initClouds(document.querySelector("#clouds"));
  bind();
  const health = await fetchJson("/api/health").catch(() => null);
  document.querySelector("#health").textContent = health ? `${health.service} · ${health.version}` : "API недоступен";
  const overview = await run(loadOverview);
  await run(loadJournal);
  await run(() => loadPlaybook("linux"));
  const worst = overview?.stats?.problems?.[0] || overview?.hosts?.[0]?.name;
  if (worst) await run(() => select(worst));
}

boot();
