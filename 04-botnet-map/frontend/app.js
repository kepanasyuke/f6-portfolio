import { initClouds } from "/shared/clouds.js";
import { badge, el, escape, fetchJson, number, render } from "/shared/api.js";

const COLORS = {
  ip: "#ff3b2f",
  domain: "#ffffff",
  hash: "#ffc53d",
  cert: "#35d39b",
  email: "#8fb3ff",
  asn: "#b98cff",
  host: "#ff8a5c",
};
const state = { nodes: [], edges: [], selected: null, view: { scale: 1, x: 0, y: 0 } };

function radius(node) {
  return 6 + Math.min(10, Number(node.risk || 0) / 12);
}

function seedPositions(nodes, width, height) {
  return nodes.map((node, index) => ({
    ...node,
    x: width / 2 + Math.cos((index / nodes.length) * Math.PI * 2) * width * 0.3,
    y: height / 2 + Math.sin((index / nodes.length) * Math.PI * 2) * height * 0.32,
    vx: 0,
    vy: 0,
  }));
}

function simulate(nodes, edges, width, height) {
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const links = edges.map((edge) => [byId.get(edge.src), byId.get(edge.dst)]).filter(([a, b]) => a && b);
  return runSteps(nodes, links, width, height, 320);
}

function runSteps(nodes, links, width, height, steps) {
  return steps === 0 ? nodes : runSteps(stepOnce(nodes, links, width, height), links, width, height, steps - 1);
}

function stepOnce(nodes, links, width, height) {
  const moved = nodes.map((node) => ({ ...node, vx: node.vx * 0.82, vy: node.vy * 0.82 }));
  applyRepulsion(moved);
  applySprings(moved, links);
  applyGravity(moved, width, height);
  return moved.map((node) => ({ ...node, x: node.x + node.vx, y: node.y + node.vy }));
}

function applyRepulsion(nodes) {
  nodes.forEach((a, i) => nodes.forEach((b, j) => {
    const dx = a.x - b.x;
    const dy = a.y - b.y;
    const distance = Math.max(Math.hypot(dx, dy), 1);
    const force = 900 / (distance * distance);
    a.vx += (dx / distance) * force;
    a.vy += (dy / distance) * force;
    if (i === j) return;
  }));
}

function applySprings(nodes, links) {
  links.forEach(([a, b]) => {
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const distance = Math.max(Math.hypot(dx, dy), 1);
    const force = (distance - 130) * 0.0045;
    a.vx += (dx / distance) * force;
    a.vy += (dy / distance) * force;
    b.vx -= (dx / distance) * force;
    b.vy -= (dy / distance) * force;
  });
}

function applyGravity(nodes, width, height) {
  nodes.forEach((node) => {
    node.vx += (width / 2 - node.x) * 0.0016;
    node.vy += (height / 2 - node.y) * 0.0016;
  });
}

function layout() {
  const canvas = document.querySelector("#graph");
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.floor(width * ratio);
  canvas.height = Math.floor(height * ratio);
  canvas.getContext("2d").setTransform(ratio, 0, 0, ratio, 0, 0);
  if (!state.nodes.length) return;
  const seeded = seedPositions(state.nodes, width, height);
  state.nodes = simulate(seeded, state.edges, width, height);
  draw();
}

function draw() {
  const canvas = document.querySelector("#graph");
  const ctx = canvas.getContext("2d");
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  ctx.clearRect(0, 0, width, height);
  const byId = new Map(state.nodes.map((node) => [node.id, node]));
  drawEdges(ctx, byId);
  state.nodes.forEach((node) => drawNode(ctx, node, node.id === state.selected));
}

function drawEdges(ctx, byId) {
  state.edges.forEach((edge) => {
    const a = byId.get(edge.src);
    const b = byId.get(edge.dst);
    if (!a || !b) return;
    ctx.strokeStyle = state.selected && (edge.src === state.selected || edge.dst === state.selected) ? "rgba(255,59,47,0.75)" : "rgba(255,255,255,0.16)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.stroke();
    if (state.selected && (edge.src === state.selected || edge.dst === state.selected)) {
      label(ctx, edge.relation, (a.x + b.x) / 2, (a.y + b.y) / 2, "rgba(255,59,47,0.85)", 9);
    }
  });
}

function drawNode(ctx, node, active) {
  ctx.beginPath();
  ctx.fillStyle = COLORS[node.kind] || "#9a9aa2";
  ctx.arc(node.x, node.y, radius(node) + (active ? 4 : 0), 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = active ? "#ff3b2f" : "rgba(0,0,0,0.6)";
  ctx.lineWidth = active ? 2 : 1;
  ctx.stroke();
  label(ctx, short(node.value), node.x, node.y + radius(node) + 13, active ? "#ffffff" : "rgba(255,255,255,0.55)", 10);
}

function label(ctx, text, x, y, color, size) {
  ctx.fillStyle = color;
  ctx.font = `${size}px Consolas, monospace`;
  ctx.textAlign = "center";
  ctx.fillText(text, x, y);
}

function short(value) {
  const text = String(value);
  return text.length > 26 ? `${text.slice(0, 24)}…` : text;
}

function pick(event) {
  const canvas = document.querySelector("#graph");
  const rect = canvas.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  const nearest = state.nodes.reduce((best, node) => {
    const distance = Math.hypot(node.x - x, node.y - y);
    return distance < best.distance ? { node, distance } : best;
  }, { node: null, distance: 24 });
  return nearest.node;
}

async function select(nodeId) {
  state.selected = nodeId;
  draw();
  const payload = await fetchJson(`/api/pivot?node=${encodeURIComponent(nodeId)}&depth=1`);
  const center = payload.nodes.find((node) => node.id === nodeId) || {};
  document.querySelector("#selected").textContent = center.value || nodeId;
  render(document.querySelector("#node-card"), [
    el("div", { class: "between" }, [
      el("h3", { class: "card__title", text: center.value || nodeId }),
      badge(`${center.kind || "?"} · риск ${number(center.risk)}`, "accent"),
    ]),
    el("div", { class: "mono muted", text: `id: ${center.id} · первые данные: ${center.first_seen || "—"}` }),
    el("div", { class: "row" }, String(center.tags || "").split(",").filter(Boolean).map((tag) => badge(tag))),
    el("div", { class: "stack", style: "gap:8px" }, payload.edges.map((edge) => el("div", { class: "mono muted", text: `${edge.src} → ${edge.dst} · ${edge.relation} · ${edge.confidence}%` }))),
  ]);
  return payload;
}

async function loadGraph() {
  const payload = await fetchJson("/api/graph");
  state.nodes = payload.nodes;
  state.edges = payload.edges;
  document.querySelector("#counts").textContent = `${number(payload.stats.nodes)} узлов · ${number(payload.stats.edges)} связей`;
  render(
    document.querySelector("#legend"),
    Object.entries(COLORS).map(([kind, color]) => el("span", {}, [el("i", { style: `background:${color}` }), `${kind}: ${number(payload.stats.by_kind[kind] || 0)}`])),
  );
  layout();
  return payload;
}

async function searchNodes(needle) {
  const payload = await fetchJson(`/api/nodes?q=${encodeURIComponent(needle)}`);
  render(
    document.querySelector("#node-list"),
    payload.items.slice(0, 40).map((node) =>
      el("button", { class: "node-chip", type: "button", text: `${node.kind}: ${short(node.value)}`, onclick: () => select(node.id) }),
    ),
  );
  return payload;
}

async function loadSchema() {
  const payload = await fetchJson("/api/schema");
  document.querySelector("#schema-box").textContent = payload.sql;
  return payload;
}

function bind() {
  const canvas = document.querySelector("#graph");
  canvas.addEventListener("click", (event) => {
    const node = pick(event);
    if (node) select(node.id);
  });
  canvas.addEventListener("mousemove", (event) => {
    canvas.style.cursor = pick(event) ? "pointer" : "default";
  });
  window.addEventListener("resize", layout);
  document.querySelector("#reset").addEventListener("click", layout);
  document.querySelector("#search").addEventListener("input", (event) => searchNodes(event.target.value.trim()));
  document.querySelector("#load-schema").addEventListener("click", loadSchema);
}

async function boot() {
  initClouds(document.querySelector("#clouds"));
  bind();
  await loadGraph();
  await searchNodes("");
  const first = state.nodes.find((node) => node.kind === "domain") || state.nodes[0];
  if (first) await select(first.id);
  await loadSchema();
}

boot();
