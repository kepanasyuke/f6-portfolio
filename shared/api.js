export async function fetchJson(url, options = {}) {
  const res = await fetch(url, { headers: { "Content-Type": "application/json" }, ...options });
  const payload = await res.json().catch(() => ({ detail: res.statusText }));
  return res.ok ? payload : Promise.reject(new Error(payload.detail || res.statusText));
}

export function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  Object.entries(attrs).forEach(([key, value]) => setAttr(node, key, value));
  children.forEach((child) => node.append(child instanceof Node ? child : document.createTextNode(String(child))));
  return node;
}

function setAttr(node, key, value) {
  if (key === "class") return node.setAttribute("class", value);
  if (key === "text") return (node.textContent = value);
  if (key.startsWith("on")) return node.addEventListener(key.slice(2), value);
  if (key === "html") return (node.innerHTML = value);
  node.setAttribute(key, value);
}

export function render(target, nodes) {
  target.replaceChildren(...nodes.filter(Boolean));
}

export function clear(target) {
  target.replaceChildren();
}

export function badge(text, tone = "") {
  return el("span", { class: `badge ${tone ? `badge--${tone}` : ""}`, text });
}

export function tag(text) {
  return el("span", { class: "tag", text });
}

export function number(value) {
  return new Intl.NumberFormat("ru-RU").format(value ?? 0);
}

export function date(value) {
  return value ? new Date(value).toLocaleString("ru-RU") : "—";
}

export function table(columns, rows) {
  const head = el("tr", {}, columns.map((column) => el("th", { text: column.title })));
  const body = rows.map((row) => el("tr", {}, columns.map((column) => el("td", { html: column.cell(row) }))));
  return el("table", {}, [el("thead", {}, [head]), el("tbody", {}, body)]);
}

export function escape(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => `&#${char.charCodeAt(0)};`);
}

export function danger(message) {
  return el("div", { class: "empty error", text: message });
}
