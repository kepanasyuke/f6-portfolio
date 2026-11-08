const DENSITY = 0.00008;
const MIN_CLOUDS = 7;
const MAX_CLOUDS = 18;
const SPEED = 0.06;

export function initClouds(canvas, options = {}) {
  const ctx = canvas.getContext("2d");
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const state = { clouds: [], width: 0, height: 0, drift: 0 };

  const resize = () => {
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    state.width = canvas.clientWidth;
    state.height = canvas.clientHeight;
    canvas.width = Math.floor(state.width * ratio);
    canvas.height = Math.floor(state.height * ratio);
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    state.clouds = buildClouds(state.width, state.height);
  };

  const frame = () => {
    draw(ctx, state);
    step(state);
    requestAnimationFrame(frame);
  };

  canvas.addEventListener("pointermove", (event) => {
    state.drift = (event.clientX / Math.max(state.width, 1) - 0.5) * 26;
  });

  window.addEventListener("resize", resize);
  resize();
  draw(ctx, state);

  if (!reduced && !options.static) {
    requestAnimationFrame(frame);
  }

  return state;
}

function buildClouds(width, height) {
  const count = clamp(Math.round(width * height * DENSITY), MIN_CLOUDS, MAX_CLOUDS);
  return Array.from({ length: count }, (_, index) => spawn(width, height, index / count));
}

function spawn(width, height, offset) {
  const radius = 120 + Math.random() * 260;
  return {
    x: width * offset + Math.random() * width * 0.2,
    y: height * (0.08 + Math.random() * 0.8),
    radius,
    alpha: 0.05 + Math.random() * 0.11,
    speed: SPEED * (0.35 + Math.random() * 1.4),
    squash: 0.45 + Math.random() * 0.3,
  };
}

function step(state) {
  state.clouds = state.clouds.map((cloud) => ({
    ...cloud,
    x: cloud.x + cloud.speed + state.drift * 0.01,
    y: cloud.y - cloud.speed * 0.06,
    life: ((cloud.x + cloud.radius) / state.width > 1.15 ? "respawn" : "keep"),
  })).map((cloud) => (cloud.life === "respawn"
    ? spawn(state.width, state.height, -0.2)
    : cloud));
}

function draw(ctx, state) {
  ctx.clearRect(0, 0, state.width, state.height);
  ctx.globalCompositeOperation = "lighter";
  state.clouds.forEach((cloud) => paint(ctx, cloud));
  ctx.globalCompositeOperation = "source-over";
}

function paint(ctx, cloud) {
  const gradient = ctx.createRadialGradient(cloud.x, cloud.y, 0, cloud.x, cloud.y, cloud.radius);
  gradient.addColorStop(0, `rgba(255,255,255,${cloud.alpha})`);
  gradient.addColorStop(0.45, `rgba(190,200,255,${cloud.alpha * 0.5})`);
  gradient.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.ellipse(cloud.x, cloud.y, cloud.radius, cloud.radius * cloud.squash, 0, 0, Math.PI * 2);
  ctx.fill();
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}
