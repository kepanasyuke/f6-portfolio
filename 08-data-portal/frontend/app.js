import { initClouds } from "/shared/clouds.js";
import { badge, danger, el, escape, fetchJson, number, render } from "/shared/api.js";

const state = { sources: [], source: "", table: "", sort: "", direction: "asc", q: "", limit: 50, offset: 0, total: 0 };

function param(name, value) {
  return value ? `${name}=${encodeURIComponent(value)}` : "";
}

function query() {
  return ["source", "table", "sort", "direction", "q", "limit", "offset"].map((key) => param(key, state[key])).filter(Boolean).join("&");
}

async function loadSummary() {
  const data = await fetchJson("/api/summary");
  state.sources = data.sources;
  render(document.querySelector("#kpis"), data.kpis.map(kpiCard));
  renderSidebar();
  return data;
}

function kpiCard(item) {
  return el("div", { class: "kpi" }, [
    el("div", { class: "kpi__value", text: number(item.value) }),
    el("div", { class: "kpi__title", text: item.title }),
    el("div", { class: "kpi__hint", text: item.hint }),
  ]);
}

function renderSidebar() {
  render(document.querySelector("#sidebar"), state.sources.map(sourceGroup));
}

function sourceGroup(source) {
  return el("div", { class: "side__group" }, [
    el("div", { class: "side__title" }, [
      el("span", { text: source.title }),
      el("span", { text: source.available ? `${number(tableRows(source))} строк` : "нет базы" }),
    ]),
    el("div", { class: "side__tables" }, source.tables.map((table) => tableButton(source, table))),
  ]);
}

function tableRows(source) {
  return source.tables.reduce((sum, table) => sum + table.rows, 0);
}

function tableButton(source, table) {
  const active = state.source === source.key && state.table === table.name;
  return el("button", {
    class: `side__table${active ? " side__table--active" : ""}`,
    type: "button",
    onclick: () => select(source.key, table.name),
  }, [
    el("span", { text: table.name }),
    el("b", { text: number(table.rows) }),
  ]);
}

async function select(sourceKey, tableName) {
  Object.assign(state, { source: sourceKey, table: tableName, sort: "", direction: "asc", offset: 0 });
  document.querySelector("#current").textContent = `${sourceKey} / ${tableName}`;
  renderSidebar();
  await loadPage();
  return state;
}

async function loadPage() {
  const data = await fetchJson(`/api/rows?${query()}`);
  state.total = data.total;
  if (!state.sort && data.columns.length) state.sort = data.columns[0].name;
  renderTable(data);
  renderSchema(data.columns);
  document.querySelector("#page-info").textContent = `${number(state.offset + 1)}–${number(Math.min(state.offset + state.limit, data.total))} из ${number(data.total)}`;
  document.querySelector("#export").href = `/api/export.csv?${query()}`;
  return data;
}

function renderTable(data) {
  const rows = data.rows.map((row) => el("tr", {}, data.columns.map((column) => cell(row, column))));
  const head = el("tr", {}, data.columns.map((column) => headerCell(column)));
  render(document.querySelector("#table-wrap"), [
    el("table", { class: "grid-table" }, [el("thead", {}, [head]), el("tbody", {}, rows)]),
  ]);
  if (!data.rows.length) {
    render(document.querySelector("#table-wrap"), [el("div", { class: "empty", style: "border:0", text: "Пусто — ослабьте фильтр или выберите другую таблицу" })]);
  }
  return data;
}

function headerCell(column) {
  const sorted = column.name === state.sort;
  const mark = sorted ? (state.direction === "asc" ? " ↑" : " ↓") : "";
  return el("th", {
    class: sorted ? "is-sorted" : "",
    title: `${column.type}${column.pk ? " · primary key" : ""}`,
    text: `${column.name}${mark}`,
    onclick: () => sortBy(column.name),
  });
}

function sortBy(name) {
  state.direction = name === state.sort && state.direction === "asc" ? "desc" : "asc";
  state.sort = name;
  run(loadPage);
}

function cell(row, column) {
  const value = row[column.name];
  if (value === null || value === undefined) return el("td", { class: "muted", text: "—" });
  return el("td", { text: String(value) });
}

function renderSchema(columns) {
  document.querySelector("#schema").hidden = false;
  render(
    document.querySelector("#schema-body"),
    columns.map((column) =>
      el("div", { class: "schema__row" }, [
        el("span", { text: column.name }),
        el("span", { class: "schema__type", text: `${column.type}${column.pk ? " · pk" : ""}${column.notnull ? " · not null" : ""}` }),
      ]),
    ),
  );
  return columns;
}

function paginate(step) {
  const next = state.offset + step * state.limit;
  state.offset = Math.max(0, Math.min(next, Math.max(state.total - 1, 0)));
  run(loadPage);
}

function search() {
  state.q = document.querySelector("#search").value.trim();
  state.offset = 0;
  run(loadPage);
}

function bind() {
  document.querySelector("#search").addEventListener("keydown", (event) => event.key === "Enter" && search());
  document.querySelector("#reload").addEventListener("click", search);
  document.querySelector("#limit").addEventListener("change", (event) => {
    state.limit = Number(event.target.value);
    state.offset = 0;
    run(loadPage);
  });
  document.querySelector("#prev").addEventListener("click", () => paginate(-1));
  document.querySelector("#next").addEventListener("click", () => paginate(1));
}

async function run(action) {
  try {
    return await action();
  } catch (error) {
    render(document.querySelector("#table-wrap"), [danger(error.message)]);
    return null;
  }
}

async function boot() {
  initClouds(document.querySelector("#clouds"));
  bind();
  const health = await fetchJson("/api/health").catch(() => null);
  document.querySelector("#health").textContent = health ? `${health.service} · ${health.version}` : "API недоступен";
  const data = await run(loadSummary);
  const first = data?.sources?.find((source) => source.available && source.tables.length);
  if (first) await run(() => select(first.key, first.tables[0].name));
}

boot();
