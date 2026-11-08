r"""Съёмка витрины стенда через Playwright: скриншоты страниц и GIF-демонстрации.

Запуск: ..\.venv\Scripts\python.exe tools\capture.py
"""
import io
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SCREENS = ROOT / "docs" / "screens"
GIFFS = ROOT / "docs" / "gifs"
BASE = "http://127.0.0.1"
VIEWPORT = {"width": 1440, "height": 900}
GIF_WIDTH = 960
GIF_COLORS = 64
GIF_DELAY = 120
STABILIZER = (
    "*, *::before, *::after { backdrop-filter: none !important; "
    "-webkit-backdrop-filter: none !important; transition: none !important; "
    "animation: none !important; }"
)

PAGES = (
    ("00-gallery", f"{BASE}:8200/docs/"),
    ("01-site", f"{BASE}:8200/site/"),
    ("02-feed-harvester", f"{BASE}:8201/"),
    ("03-hunt-rules", f"{BASE}:8202/"),
    ("04-log-forge", f"{BASE}:8203/"),
    ("05-botnet-map", f"{BASE}:8204/"),
    ("06-typosquat-radar", f"{BASE}:8205/"),
    ("07-report-builder", f"{BASE}:8206/"),
    ("08-ops-agent", f"{BASE}:8207/"),
    ("09-data-portal", f"{BASE}:8209/"),
    ("10-console", f"{BASE}:8210/"),
)


def main() -> int:
    ensure_dirs()
    return capture()


def ensure_dirs() -> None:
    SCREENS.mkdir(parents=True, exist_ok=True)
    GIFFS.mkdir(parents=True, exist_ok=True)


def capture() -> int:
    with sync_playwright() as playwright:
        return session(playwright)


def session(playwright) -> int:
    browser = playwright.chromium.launch(**launch_options())
    return work(browser)


def launch_options() -> dict:
    return {"executable_path": str(chrome_binary())} if chrome_binary() else {"channel": "chromium"}


def chrome_binary():
    found = sorted(Path.home().glob("AppData/Local/ms-playwright/chromium-*/chrome-win64/chrome.exe"))
    return found[-1] if found else None


def work(browser) -> int:
    with_context(browser)
    return 0


def with_context(browser) -> None:
    context = browser.new_context(viewport=VIEWPORT, reduced_motion="reduce")
    run_all(context)


def run_all(context) -> None:
    shots(context)
    movies(context)


def shots(context) -> None:
    page = context.new_page()
    return tuple(shoot(page, name, url) for name, url in PAGES)


def shoot(page, name: str, url: str) -> None:
    open_page(page, url)
    page.screenshot(path=str(SCREENS / f"{name}.png"), full_page=False)


def open_page(page, url: str) -> None:
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    settle(page)


def settle(page) -> None:
    page.add_style_tag(content=STABILIZER)
    page.wait_for_timeout(2200)


def movies(context) -> tuple:
    return tuple(movie(context, name, spec) for name, spec in SCRIPTS.items())


def movie(context, name: str, spec: tuple):
    page = context.new_page()
    return closed(page, save_gif(name, frames_after(page, spec)))


def closed(page, target: Path) -> Path:
    page.close()
    return target


def frames_after(page, spec: tuple) -> tuple:
    open_page(page, spec[0])
    return spec[1](page)


def frame(page) -> Image.Image:
    return Image.open(io.BytesIO(page.screenshot())).convert("RGB")


def console_frames(page) -> tuple:
    return (frame(page), *tuple(clicked(page, f'a[href="{href}"]') for href in CONSOLE_STEPS))


def portal_frames(page) -> tuple:
    return (frame(page), *tuple(portal_step(page, index) for index in PORTAL_STEPS))


def portal_step(page, index: int) -> Image.Image:
    page.locator(".side__table").nth(index).click()
    return waited(page, 1200)


def radar_frames(page) -> tuple:
    return (frame(page), *tuple(scrolled(page, offset) for offset in (300, 700, 1200)))


def scrolled(page, offset: int) -> Image.Image:
    page.mouse.wheel(0, offset)
    return waited(page, 700)


def hunting_frames(page) -> tuple:
    return (frame(page), clicked(page, "#run"), scrolled(page, 500), scrolled(page, 500))


def clicked(page, selector: str) -> Image.Image:
    page.click(selector)
    return waited(page, 1400)


def waited(page, milliseconds: int) -> Image.Image:
    page.wait_for_timeout(milliseconds)
    return frame(page)


def save_gif(name: str, frames: tuple) -> Path:
    target = GIFFS / f"{name}.gif"
    return encoded(target, frames)


def encoded(target: Path, frames: tuple) -> Path:
    first, *rest = scaled(frames)
    return saved(first, rest, target)


def saved(first, rest: list, target: Path) -> Path:
    first.save(target, save_all=True, append_images=rest, duration=GIF_DELAY, loop=0, optimize=True)
    return target


def scaled(frames: tuple) -> tuple:
    return tuple(prepared(image) for image in frames)


def prepared(image: Image.Image) -> Image.Image:
    size = (GIF_WIDTH, int(GIF_WIDTH * image.height / image.width))
    return image.resize(size, Image.LANCZOS).convert("P", palette=Image.ADAPTIVE, colors=GIF_COLORS)


SCRIPTS = {
    "console": (f"{BASE}:8210/#overview", console_frames),
    "portal": (f"{BASE}:8209/", portal_frames),
    "hunting": (f"{BASE}:8202/", hunting_frames),
    "radar": (f"{BASE}:8205/", radar_frames),
}
CONSOLE_STEPS = ("#indicators", "#hunting", "#domains", "#hosts")
PORTAL_STEPS = (3, 6, 8)


if __name__ == "__main__":
    sys.exit(main())
