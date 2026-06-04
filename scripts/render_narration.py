#!/usr/bin/env python3
"""Render the KRBL demo narration MP3 before video capture.

The script prefers gTTS because it writes MP3 directly. If gTTS is not
available, it falls back to pyttsx3 and converts the generated audio to MP3
with ffmpeg when ffmpeg is installed.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from demo_media.storyboard import DEFAULT_NARRATION, NARRATION_TEXT  # noqa: E402


def render_with_gtts(text: str, output: Path, language: str) -> bool:
    try:
        from gtts import gTTS
    except ImportError:
        return False

    tts = gTTS(text=text, lang=language, slow=False)
    tts.save(str(output))
    return True


def render_with_pyttsx3(text: str, output: Path) -> bool:
    try:
        import pyttsx3
    except ImportError:
        return False

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("pyttsx3 fallback requires ffmpeg to convert WAV output to MP3.")

    with tempfile.TemporaryDirectory() as tmp:
        wav_path = Path(tmp) / "narration.wav"
        engine = pyttsx3.init()
        engine.setProperty("rate", 168)
        engine.save_to_file(text, str(wav_path))
        engine.runAndWait()
        subprocess.run(
            [ffmpeg, "-y", "-i", str(wav_path), "-codec:a", "libmp3lame", "-q:a", "4", str(output)],
            check=True,
        )
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the KRBL demo narration as MP3.")
    parser.add_argument("--output", type=Path, default=DEFAULT_NARRATION, help="Output MP3 path.")
    parser.add_argument("--language", default="en", help="gTTS language code.")
    parser.add_argument("--text", default=NARRATION_TEXT, help="Narration text to synthesize.")
    args = parser.parse_args()

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        if render_with_gtts(args.text, output, args.language):
            print(f"Narration MP3 rendered with gTTS: {output}")
            return 0
        if render_with_pyttsx3(args.text, output):
            print(f"Narration MP3 rendered with pyttsx3: {output}")
            return 0
    except Exception as exc:  # noqa: BLE001 - provide actionable CLI failure
        print(f"Failed to render narration: {exc}", file=sys.stderr)
        return 1

    print(
        "No supported TTS backend is installed. Install gTTS, or install pyttsx3 plus ffmpeg, "
        "then rerun this command.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
