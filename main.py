"""Write the 24 November 2026 world-news image to /output/entry.png."""

import os
import pathlib
import shutil

SOURCE = pathlib.Path(__file__).resolve().parent / "entry.png"  # drawn by design/engine.py from design/day.json


def main():
    out = pathlib.Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE, out / "entry.png")


if __name__ == "__main__":
    main()
