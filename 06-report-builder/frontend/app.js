import { initClouds } from "/shared/clouds.js";
import { badge, danger, el, escape, fetchJson, number, render, table } from "/shared/api.js";

function lines(id) {
  return document.querySelector(id).value.split("\n").map((line) => line.trim()).filter(Boolean);
}

function pairs(id, keys) {
  return lines(id).map((line) => Object.fromEntries(line.split(",").map((part) => part.trim()).slice(0, keys.length).map((part, index) => [keys[index], part])));
}

function payload() {
  return {
    title: document.querySelector("#title").value.trim(),
    template: document.querySelector("#template").value,
    tlp: document.querySelector("#tlp").value,
    author: document.querySelector("#author").value.trim() || "analyst",
    summary: document.querySelector("#summary").value.trim(),
    iocs: pairs("#iocs", ["kind", "value"]).filter((item) => item.value),
    findings: pairs("#findings", ["severity", "title", "detail"]).filter((item) => item.title),
    recommendations: lines("#recommendations"),
  };
}

function fill(select, values, label) {
  select.replaceChildren(...values.map((value) => el("option", { value: value.id || value, text: value.title || value })));
  if (label) select.value = label;
}

async function loadTemplates() {
  const payload = await fetchJson("/api/templates");
  fill(document.querySelector("#template"), payload.items);
  fill(document.querySelector("#tlp"), payload.items[0].tlp);
  return payload;
}

async function preview() {
  const data = await fetchJson("/api/preview", { method: "POST", body: JSON.stringify(payload()) });
  show(data);
  return data;
}

function show(data) {
  document.querySelector("#preview-box").innerHTML = data.html;
  document.querySelector("#severity").textContent = Object.entries(data.severity).map(([key, value]) => `${key} ${value}`).join(" · ") || "без наблюдений";
  document.querySelector("#template-title").textContent = `${data.template} · ${data.tlp}`;
  document.querySelector("#status").textContent = "превью обновлено";
  return data;
}

async function save() {
  const data = await fetchJson("/api/reports", { method: "POST", body: JSON.stringify(payload()) });
  show(data);
  document.querySelector("#status").textContent = `сохранено · id ${data.id}`;
  await loadHistory();
  return data;
}

async function loadHistory() {
  const data = await fetchJson("/api/reports?limit=30");
  render(document.querySelector("#history-box"), [
    data.items.length
      ? table(
          [
            { title: "id", cell: (row) => escape(row.id) },
            { title: "Заголовок", cell: (row) => `<a href="/api/reports/${row.id}" target="_blank" rel="noreferrer">${escape(row.title)}</a>` },
            { title: "Шаблон", cell: (row) => escape(row.template) },
            { title: "TLP", cell: (row) => escape(row.tlp) },
            { title: "Создан", cell: (row) => escape(row.created_at) },
            { title: "Выгрузка", cell: (row) => `<a href="/api/reports/${row.id}/markdown" target="_blank" rel="noreferrer">.md</a>` },
          ],
          data.items,
        )
      : el("div", { class: "empty", text: "Отчётов пока нет" }),
  ]);
  return data;
}

async function loadSample() {
  const data = await fetchJson("/api/sample");
  document.querySelector("#title").value = data.title;
  document.querySelector("#summary").value = data.summary;
  document.querySelector("#author").value = data.author;
  document.querySelector("#template").value = data.template;
  document.querySelector("#tlp").value = data.tlp;
  document.querySelector("#iocs").value = data.iocs.map((item) => `${item.kind}, ${item.value}`).join("\n");
  document.querySelector("#findings").value = data.findings.map((item) => `${item.severity}, ${item.title}, ${item.detail}`).join("\n");
  document.querySelector("#recommendations").value = data.recommendations.join("\n");
  await preview();
  return data;
}

function bind() {
  document.querySelector("#preview").addEventListener("click", () => run(preview));
  document.querySelector("#save").addEventListener("click", () => run(save));
  document.querySelector("#reload").addEventListener("click", () => run(loadHistory));
  document.querySelector("#sample").addEventListener("click", () => run(loadSample));
}

async function run(action) {
  try {
    return await action();
  } catch (error) {
    render(document.querySelector("#preview-box"), [danger(error.message)]);
    return null;
  }
}

async function boot() {
  initClouds(document.querySelector("#clouds"));
  bind();
  await run(loadTemplates);
  await run(loadHistory);
  await run(loadSample);
}

boot();
