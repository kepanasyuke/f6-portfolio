import { initClouds } from "/shared/clouds.js";
import { badge, danger, el, escape, fetchJson, number, render, table } from "/shared/api.js";

const state = { view: "overview", q: "", kind: "", severity: "", logQuery: "", brand: "f6security.example", node: "", depth: 2 };

const SEVERITY_TONE = { critical: "accent", high: "warn", medium: "", low: "ok" };
const TITLES = {
  overview: "Обзор",
  indicators: "Индикаторы",
  hunting: "Хантинг",
  logs: "Журналы",
  graph: "Инфраструктура",
  domains: "Домены",
  reports: "Отчёты",
  hosts: "Хосты",
};

function tone(value) {
  return SEVERITY_TONE[value] || "";
}

function field(label, control) {
  return el("label", { class: "field" }, [el("span", { text: label }), control]);
}

function input(id, value, placeholder = "") {
  return el("input", { id, value, placeholder });
}

function button(text, action, ghost = false) {
  return el("button", { class: ghost ? "btn btn--ghost" : "btn", type: "button", text, onclick: action });
}

function block(title, children) {
  return el("div", { class: "block" }, [el("p", { class: "block__title", text: title }), ...children]);
}

function kpi(item) {
  return el("div", { class: "kpi" }, [
    el("div", { class: "kpi__value", text: number(item.value) }),
    el("div", { class: "kpi__title", text: item.title }),
    el("div", { class: "kpi__hint", text: item.hint }),
  ]);
}

function kpiStrip(items) {
  return el("div", { class: "kpis" }, items.map(kpi));
}

function empty(text) {
  return el("div", { class: "empty", text });
}

function statusRow(service) {
  return el("div", { class: "status-row" }, [
    el("span", { text: service.title }),
    badge(service.online ? "online" : "offline", service.online ? "ok" : "accent"),
  ]);
}

function feedRow(item) {
  return el("div", { class: "feed-item" }, [el("b", { text: item.kind }), el("span", { text: item.text })]);
}

function head(title, subtitle, extra = []) {
  return el("div", { class: "view__head" }, [
    el("div", {}, [
      el("p", { class: "kicker", text: subtitle }),
      el("h2", { class: "display display--sm", text: title }),
    ]),
    el("div", { class: "row" }, extra),
  ]);
}

async function viewOverview() {
  const data = await fetchJson("/api/overview");
  return [
    head("Контроль контура", "Сводка всех сервисов"),
    kpiStrip(data.kpis),
    el("div", { class: "split" }, [
      block("Состояние сервисов", data.services.map(statusRow)),
      block("Лента", data.feed.length ? data.feed.map(feedRow) : [empty("Событий пока нет")]),
    ]),
  ];
}

async function viewIndicators() {
  const params = new URLSearchParams({ q: state.q, kind: state.kind, severity: state.severity });
  const data = await fetchJson(`/api/indicators?${params}`);
  const rows = data.items || [];
  return [
    head("Индикаторы компрометации", "Источник: Feed Harvester", [badge(`${number(rows.length)} записей`)]),
    el("div", { class: "form-row" }, [
      field("Значение", input("q", state.q, "example, 203.0.113")),
      field("Тип", select("kind", ["", "ipv4", "domain", "url", "sha256", "md5", "email"], state.kind)),
      field("Критичность", select("severity", ["", "critical", "high", "medium", "low"], state.severity)),
      button("Искать", () => apply({ kind: document.querySelector("#kind").value, severity: document.querySelector("#severity").value, q: document.querySelector("#q").value })),
    ]),
    el("div", { class: "scroller" }, [
      rows.length
        ? table(
            [
              { title: "Индикатор", cell: (row) => escape(row.value) },
              { title: "Тип", cell: (row) => escape(row.kind) },
              { title: "Критичность", cell: (row) => badge(row.severity, tone(row.severity)).outerHTML },
              { title: "Источник", cell: (row) => escape(row.source) },
              { title: "Уверенность", cell: (row) => escape(row.confidence) },
            ],
            rows,
          )
        : empty("Ничего не найдено — ослабьте фильтры"),
    ]),
  ];
}

function select(id, values, current) {
  const options = values.map((value) => el("option", { value, text: value || "все", selected: value === current ? "selected" : "" }));
  return el("select", { id }, options);
}

async function viewHunting() {
  const data = await fetchJson("/api/hunting");
  const rules = data.rules?.items || [];
  const detections = data.detections?.items || [];
  return [
    head("Правила хантинга", "Источник: Hunt Rules", [button("Прогнать библиотеку", runHunting)]),
    el("div", { class: "split" }, [
      block(
        "Правила",
        rules.length
          ? [
              table(
                [
                  { title: "ID", cell: (row) => escape(row.id) },
                  { title: "Название", cell: (row) => escape(row.title) },
                  { title: "Критичность", cell: (row) => badge(row.severity, tone(row.severity)).outerHTML },
                ],
                rules,
              ),
            ]
          : [empty("Правила недоступны")],
      ),
      block(
        "Детекции",
        detections.length
          ? [
              table(
                [
                  { title: "Правило", cell: (row) => escape(row.rule_id) },
                  { title: "Хост", cell: (row) => escape(row.host) },
                  { title: "Время", cell: (row) => escape(row.occurred_at) },
                ],
                detections.slice(0, 40),
              ),
            ]
          : [empty("Детекций пока нет")],
      ),
    ]),
    el("div", { id: "hunt-result" }),
  ];
}

async function runHunting() {
  const payload = await fetchJson("/api/hunting/run", { method: "POST", body: "{}" });
  const findings = payload.findings || [];
  render(document.querySelector("#hunt-result"), [
    el("p", { class: "block__title", text: `Прогон: ${number(payload.total || 0)} срабатываний` }),
    findings.length
      ? table(
          [
            { title: "Правило", cell: (row) => escape(row.id) },
            { title: "Название", cell: (row) => escape(row.title) },
            { title: "Срабатываний", cell: (row) => escape(row.hits) },
          ],
          findings,
        )
      : empty("Совпадений нет"),
  ]);
}

async function viewLogs() {
  const data = state.logQuery ? await fetchJson(`/api/logs?q=${encodeURIComponent(state.logQuery)}`) : { items: [], count: 0 };
  const items = data.items || [];
  return [
    head("Поиск по журналам", "Источник: Log Forge", [badge(`${number(items.length)} совпадений`)]),
    el("div", { class: "form-row" }, [
      field("Запрос", input("logQuery", state.logQuery, "failed root 203.0.113.*")),
      button("Искать", () => apply({ logQuery: document.querySelector("#logQuery").value })),
    ]),
    el("div", { class: "split" }, items.length ? items.map(logCard) : [empty("Введите запрос — поиск идёт по словам и маскам")]),
  ];
}

function logCard(doc) {
  return el("div", { class: "block" }, [
    el("div", { class: "between" }, [
      el("span", { class: "mono muted", text: `${doc["@timestamp"] || "—"} · ${doc.host || "—"}` }),
      badge(doc["event.category"] || "log"),
    ]),
    el("p", { class: "mono", style: "margin:10px 0 0;font-size:12px;word-break:break-all", text: doc.message || "" }),
  ]);
}

async function viewGraph() {
  const query = state.node ? `node=${encodeURIComponent(state.node)}&depth=${state.depth}` : "";
  const data = await fetchJson(`/api/graph?${query}`);
  const nodes = data.nodes || [];
  const edges = data.edges || [];
  return [
    head("Инфраструктура злоумышленника", "Источник: Botnet Map", [badge(`${number(nodes.length)} узлов`)]),
    el("div", { class: "form-row" }, [
      field("Узел для пивота", input("node", state.node, "ip-203-0-113-24")),
      field("Глубина", select("depth", ["1", "2", "3", "4"], String(state.depth))),
      button("Пивот", () => apply({ node: document.querySelector("#node").value, depth: Number(document.querySelector("#depth").value) })),
      button("Весь граф", () => apply({ node: "", depth: 2 }), true),
    ]),
    el("div", { class: "split" }, [
      block(
        "Узлы",
        nodes.length
          ? [
              table(
                [
                  { title: "ID", cell: (row) => escape(row.id) },
                  { title: "Тип", cell: (row) => escape(row.kind) },
                  { title: "Значение", cell: (row) => escape(row.value) },
                  { title: "Риск", cell: (row) => escape(row.risk) },
                ],
                nodes,
              ),
            ]
          : [empty("Пусто")],
      ),
      block(
        "Связи",
        edges.length
          ? [
              table(
                [
                  { title: "Откуда", cell: (row) => escape(row.src) },
                  { title: "Куда", cell: (row) => escape(row.dst) },
                  { title: "Тип", cell: (row) => escape(row.relation) },
                  { title: "Уверенность", cell: (row) => escape(row.confidence) },
                ],
                edges,
              ),
            ]
          : [empty("Пусто")],
      ),
    ]),
  ];
}

async function viewDomains() {
  const data = await fetchJson(`/api/domains?brand=${encodeURIComponent(state.brand)}`);
  const items = data.items || [];
  return [
    head("Похожие домены", "Источник: Typosquat Radar", [badge(`${number(items.length)} вариантов`)]),
    el("div", { class: "form-row" }, [
      field("Бренд-домен", input("brand", state.brand, "f6security.example")),
      button("Сканировать", () => apply({ brand: document.querySelector("#brand").value })),
    ]),
    el("div", { class: "scroller" }, [
      items.length
        ? table(
            [
              { title: "Домен", cell: (row) => escape(row.domain) },
              { title: "Риск", cell: (row) => escape(row.risk) },
              { title: "Вердикт", cell: (row) => badge(row.verdict, tone(row.verdict)).outerHTML },
              { title: "Дистанция", cell: (row) => escape(row.distance) },
            ],
            items,
          )
        : empty("Сканирование недоступно"),
    ]),
  ];
}

async function viewReports() {
  const data = await fetchJson("/api/reports");
  const items = data.items || [];
  return [
    head("Отчёты для портала", "Источник: Report Builder", [badge(`${number(items.length)} отчётов`)]),
    el("div", { class: "split" }, [
      block(
        "История",
        items.length
          ? [
              table(
                [
                  { title: "ID", cell: (row) => escape(row.id) },
                  { title: "Заголовок", cell: (row) => escape(row.title) },
                  { title: "TLP", cell: (row) => escape(row.tlp) },
                ],
                items,
              ),
            ]
          : [empty("Отчётов пока нет")],
      ),
      block("Новый отчёт", [reportForm()]),
    ]),
  ];
}

function reportForm() {
  return el("div", { class: "stack" }, [
    field("Заголовок", input("reportTitle", "", "Кампания Gatekeeper")),
    field("Шаблон", select("reportTemplate", ["threat", "incident", "actor"], "threat")),
    field("Резюме", el("textarea", { id: "reportSummary", placeholder: "Кратко о чём отчёт" })),
    button("Создать", createReport),
    el("div", { id: "report-result", class: "mono muted" }),
  ]);
}

async function createReport() {
  const payload = {
    title: document.querySelector("#reportTitle").value,
    template: document.querySelector("#reportTemplate").value,
    summary: document.querySelector("#reportSummary").value,
  };
  const created = await fetchJson("/api/reports", { method: "POST", body: JSON.stringify(payload) });
  render(document.querySelector("#report-result"), [
    el("span", { text: created.id ? `сохранено: id ${created.id}` : "сервис отчётов недоступен" }),
  ]);
  return created;
}

async function viewHosts() {
  const data = await fetchJson("/api/hosts");
  const hosts = data.hosts || [];
  return [
    head("Парк серверов", "Источник: Ops Agent", [badge(`${number(hosts.length)} хостов`)]),
    el("div", { class: "scroller" }, [
      hosts.length
        ? table(
            [
              { title: "Хост", cell: (row) => escape(row.name) },
              { title: "Роль", cell: (row) => escape(row.role) },
              { title: "ОС", cell: (row) => escape(row.os) },
              { title: "IP", cell: (row) => escape(row.ip) },
              { title: "Статус", cell: (row) => badge(row.status, tone(row.status)).outerHTML },
              { title: "", cell: (row) => `<button class="btn btn--ghost" data-check="${escape(row.name)}" type="button">Проверить</button>` },
            ],
            hosts,
          )
        : empty("Инвентарь недоступен"),
    ]),
    el("div", { id: "host-result" }),
  ];
}

const VIEWS = {
  overview: viewOverview,
  indicators: viewIndicators,
  hunting: viewHunting,
  logs: viewLogs,
  graph: viewGraph,
  domains: viewDomains,
  reports: viewReports,
  hosts: viewHosts,
};

function apply(patch) {
  Object.assign(state, patch);
  return renderView();
}

async function renderView() {
  document.querySelector("#section-title").textContent = TITLES[state.view] || "Обзор";
  document.querySelectorAll("#menu a").forEach((link) => link.classList.toggle("active", link.dataset.view === state.view));
  try {
    const nodes = await VIEWS[state.view]();
    render(document.querySelector("#view"), nodes);
    bind();
  } catch (error) {
    render(document.querySelector("#view"), [danger(error.message)]);
  }
}

function bind() {
  document.querySelectorAll("[data-check]").forEach((node) =>
    node.addEventListener("click", () => checkHost(node.dataset.check)),
  );
}

async function checkHost(name) {
  const payload = await fetchJson(`/api/hosts/${encodeURIComponent(name)}/check`, { method: "POST", body: "{}" });
  render(document.querySelector("#host-result"), [
    el("p", { class: "mono muted", text: payload.status ? `${payload.host}: ${payload.status}` : "проверка недоступна" }),
  ]);
  return payload;
}

function route() {
  const name = location.hash.replace("#", "") || "overview";
  state.view = VIEWS[name] ? name : "overview";
  return renderView();
}

async function boot() {
  initClouds(document.querySelector("#clouds"));
  window.addEventListener("hashchange", route);
  document.querySelector("#refresh").addEventListener("click", route);
  const health = await fetchJson("/api/health").catch(() => null);
  document.querySelector("#status").textContent = health ? `${health.service} · ${health.version}` : "API недоступен";
  await route();
}

boot();
