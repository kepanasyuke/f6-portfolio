import { initClouds } from "/shared/clouds.js";
import { badge, danger, el, escape, fetchJson, number, render, table } from "/shared/api.js";

function tone(verdict) {
  return { critical: "accent", high: "warn", medium: "", low: "ok" }[verdict] || "";
}

function stat(value, label) {
  return el("div", { class: "stat" }, [
    el("div", { class: "stat__value", text: number(value) }),
    el("div", { class: "stat__label", text: label }),
  ]);
}

function card(item) {
  return el("div", { class: "card" }, [
    el("span", { class: "card__index", text: `риск ${item.risk} · дистанция ${item.distance}` }),
    el("h3", { class: "card__title", text: item.domain }),
    el("div", { class: "meter" }, [el("i", { style: `width:${item.risk}%` })]),
    el("div", { class: "row" }, [
      badge(item.verdict, tone(item.verdict)),
      item.signals.registered ? badge("зарегистрирован", "accent") : badge("свободен"),
      item.signals.mx ? badge("MX есть", "warn") : badge("без MX"),
      badge(`HTTP ${item.signals.http_status}`),
      badge(`${item.signals.created_days_ago} дн.`),
    ]),
    el("button", { class: "btn btn--ghost", type: "button", text: "В наблюдение", onclick: () => watch(item.domain) }),
  ]);
}

async function loadStats() {
  const payload = await fetchJson("/api/stats");
  render(document.querySelector("#stats"), [
    stat(payload.scanned, "доменов в базе"),
    ...Object.entries(payload.verdicts).map(([key, value]) => stat(value, key)),
  ]);
  return payload;
}

async function scan() {
  const brand = document.querySelector("#brand").value.trim() || "f6security.example";
  const limit = Number(document.querySelector("#limit").value) || 40;
  const payload = await fetchJson("/api/scan", { method: "POST", body: JSON.stringify({ brand, limit }) });
  document.querySelector("#summary").textContent = `${number(payload.generated)} вариантов · топ ${payload.items.length}`;
  render(document.querySelector("#cards"), payload.items.map(card));
  await loadStats();
  return payload;
}

async function check() {
  const domain = document.querySelector("#domain").value.trim();
  const brand = document.querySelector("#brand").value.trim() || "f6security.example";
  const verdictNode = document.querySelector("#check-verdict");
  if (!domain) {
    verdictNode.textContent = "пусто";
    return null;
  }
  const item = await fetchJson(`/api/check?domain=${encodeURIComponent(domain)}&brand=${encodeURIComponent(brand)}`);
  verdictNode.textContent = item.verdict;
  verdictNode.className = `badge badge--${tone(item.verdict) || "accent"}`;
  render(document.querySelector("#check-result"), [
    el("div", { class: "between" }, [
      el("span", { class: "mono", text: item.domain }),
      badge(`риск ${item.risk}`, tone(item.verdict)),
    ]),
    el("div", { class: "mono muted", text: `дистанция: ${item.distance} · HTTP ${item.signals.http_status} · регистрация ${item.signals.registered ? "есть" : "нет"}` }),
  ]);
  return item;
}

async function watch(domain) {
  await fetchJson("/api/watchlist", { method: "POST", body: JSON.stringify({ domain, note: "найден радаром" }) });
  await loadWatchlist();
  return domain;
}

async function loadWatchlist() {
  const payload = await fetchJson("/api/watchlist");
  render(document.querySelector("#watch-table"), [
    payload.items.length
      ? table(
          [
            { title: "Домен", cell: (row) => escape(row.domain) },
            { title: "Заметка", cell: (row) => escape(row.note) },
            { title: "Добавлен", cell: (row) => escape(row.created_at) },
          ],
          payload.items,
        )
      : el("div", { class: "empty", text: "Список пуст" }),
  ]);
  return payload;
}

function bind() {
  document.querySelector("#scan-btn").addEventListener("click", () => run(scan));
  document.querySelector("#check-btn").addEventListener("click", () => run(check));
  document.querySelector("#reload-watch").addEventListener("click", () => run(loadWatchlist));
  document.querySelector("#domain").addEventListener("keydown", (event) => event.key === "Enter" && run(check));
}

async function run(action) {
  try {
    return await action();
  } catch (error) {
    render(document.querySelector("#cards"), [danger(error.message)]);
    return null;
  }
}

async function boot() {
  initClouds(document.querySelector("#clouds"));
  bind();
  const health = await fetchJson("/api/health").catch(() => null);
  document.querySelector("#health").textContent = health ? `${health.service} · ${health.version}` : "API недоступен";
  await run(scan);
  await run(loadWatchlist);
}

boot();
