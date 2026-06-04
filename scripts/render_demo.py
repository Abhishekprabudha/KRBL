#!/usr/bin/env python3
"""Render the KRBL MP3 narration first, then the Streamlit MP4 video demo."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Render narration MP3 first, then Streamlit MP4 demo.")
    parser.add_argument("--output-dir", type=Path, default=Path("rendered_demo"), help="Directory for rendered media.")
    args = parser.parse_args()

    output_dir = args.output_dir
    narration = output_dir / "krbl_narration.mp3"
    video = output_dir / "krbl_streamlit_demo.mp4"

    subprocess.run([sys.executable, "scripts/render_narration.py", "--output", str(narration)], cwd=REPO_ROOT, check=True)
    subprocess.run(
        [sys.executable, "scripts/render_video_demo.py", "--narration", str(narration), "--output", str(video)],
        cwd=REPO_ROOT,
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
