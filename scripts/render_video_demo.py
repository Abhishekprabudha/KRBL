#!/usr/bin/env python3
"""Capture the Streamlit demo end-to-end and mux it with narration into MP4."""

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from demo_media.storyboard import DEFAULT_NARRATION, DEFAULT_VIDEO, STORYBOARD_STEPS  # noqa: E402


def require_executable(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise RuntimeError(f"Required executable not found on PATH: {name}")
    return path


def wait_for_streamlit(url: str, timeout: float = 45.0) -> None:
    from urllib.request import urlopen

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=2) as response:  # noqa: S310 - local Streamlit health check
                if response.status < 500:
                    return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"Streamlit did not become ready at {url} within {timeout:.0f}s")


def start_streamlit(port: int) -> subprocess.Popen:
    streamlit = require_executable("streamlit")
    env = os.environ.copy()
    env.update(
        {
            "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
            "STREAMLIT_SERVER_HEADLESS": "true",
            "STREAMLIT_SERVER_PORT": str(port),
            "KRBL_RENDER_DEMO": "1",
        }
    )
    return subprocess.Popen(
        [streamlit, "run", "app.py", "--server.headless=true", f"--server.port={port}"],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )


def probe_media_duration(ffprobe: str, media_path: Path) -> float:
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(media_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def storyboard_durations(narration_duration: float, tail_padding: float) -> dict[str, float]:
    base_total = sum(step.duration for step in STORYBOARD_STEPS)
    target_total = max(base_total, narration_duration + tail_padding)
    scale = target_total / base_total if base_total else 1.0
    return {step.name: step.duration * scale for step in STORYBOARD_STEPS}


async def choose_selectbox_option(page, label: str, value: str) -> None:
    control = page.get_by_label(label)
    await control.click()
    option = page.get_by_role("option", name=value)
    if not await option.count():
        option = page.get_by_text(value, exact=True)
    await option.first.click()
    await page.wait_for_timeout(1400)


async def apply_step(page, step) -> None:
    if step.action == "advance_timeline":
        button = page.get_by_role("button", name="⏩ Advance 10 days")
        if await button.count():
            await button.first.click()
            await page.wait_for_timeout(1400)
    elif step.action == "select_flow" and step.flow:
        await choose_selectbox_option(page, "Select replenishment flow", step.flow)
    elif step.action == "open_live_timeline":
        await page.get_by_role("tab", name="📈 Live timeline").click()
        await page.wait_for_timeout(900)
    elif step.action == "open_agent_recommendation":
        await page.get_by_role("tab", name="🔮 Agent recommendation").click()
        await page.wait_for_timeout(900)
    elif step.action == "ask_genbi":
        await page.get_by_role("tab", name="🧠 KRBL GenBI").click()
        box = page.get_by_label("Your question")
        await box.fill(step.query or "What is KRBL's current stock?")
        await box.press("Enter")
        await page.wait_for_timeout(1500)


async def capture_storyboard(url: str, frame_dir: Path, width: int, height: int) -> list[Path]:
    from playwright.async_api import async_playwright

    frames: list[Path] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        await page.goto(url, wait_until="networkidle")
        await page.get_by_label("Autoplay telemetry").uncheck()
        await page.wait_for_timeout(1000)

        for step in STORYBOARD_STEPS:
            await apply_step(page, step)
            await page.evaluate(
                "caption => { document.body.dataset.demoCaption = caption; }",
                step.caption,
            )
            path = frame_dir / f"{step.name}.png"
            await page.screenshot(path=str(path), full_page=False)
            frames.append(path)

        await browser.close()
    return frames


def build_concat_file(frames: list[Path], concat_file: Path, durations: dict[str, float]) -> None:
    with concat_file.open("w", encoding="utf-8") as fh:
        for frame in frames:
            duration = durations[frame.stem]
            fh.write(f"file '{frame.as_posix()}'\n")
            fh.write(f"duration {duration:.3f}\n")
        if frames:
            fh.write(f"file '{frames[-1].as_posix()}'\n")


def mux_video(ffmpeg: str, concat_file: Path, narration: Path, output: Path) -> None:
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-i",
            str(narration),
            "-vf",
            "format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            str(output),
        ],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Streamlit screenshots plus narration into an MP4 demo.")
    parser.add_argument("--narration", type=Path, default=DEFAULT_NARRATION, help="Input narration MP3 path.")
    parser.add_argument("--output", type=Path, default=DEFAULT_VIDEO, help="Output MP4 path.")
    parser.add_argument("--port", type=int, default=8501, help="Local Streamlit port.")
    parser.add_argument("--width", type=int, default=1440, help="Browser capture width.")
    parser.add_argument("--height", type=int, default=1100, help="Browser capture height.")
    parser.add_argument(
        "--audio-tail-padding",
        type=float,
        default=1.25,
        help="Seconds to keep the final storyboard frame after narration ends.",
    )
    args = parser.parse_args()

    narration = args.narration.resolve()
    output = args.output.resolve()
    frame_dir = (output.parent / "frames").resolve()
    frame_dir.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)

    if not narration.exists():
        raise SystemExit(f"Narration MP3 not found: {narration}. Run scripts/render_narration.py first.")

    try:
        ffmpeg = require_executable("ffmpeg")
        ffprobe = require_executable("ffprobe")
        if importlib.util.find_spec("playwright.async_api") is None:
            raise RuntimeError("Python package not found: playwright")
    except Exception as exc:  # noqa: BLE001 - actionable CLI failure
        print(f"Cannot render video demo: {exc}", file=sys.stderr)
        print("Install ffmpeg and run `python -m playwright install chromium` after installing requirements.", file=sys.stderr)
        return 1

    url = f"http://localhost:{args.port}"
    proc = start_streamlit(args.port)
    try:
        wait_for_streamlit(url)
        import asyncio

        narration_duration = probe_media_duration(ffprobe, narration)
        durations = storyboard_durations(narration_duration, args.audio_tail_padding)
        frames = asyncio.run(capture_storyboard(url, frame_dir, args.width, args.height))
        concat_file = frame_dir / "frames.txt"
        build_concat_file(frames, concat_file, durations)
        mux_video(ffmpeg, concat_file, narration, output)
        print(f"Video demo rendered: {output}")
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
