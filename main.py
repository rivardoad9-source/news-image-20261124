"""Entry for make.fun's news-image-20261124: the world's news of 24 November 2026 in one image.

The picture is already drawn (design/engine.py renders design/day.json to entry.png), so at
run time this only copies those exact bytes to the output folder: no network, same file every run.
"""

import os
from pathlib import Path

IMAGE = Path(__file__).resolve().with_name("entry.png")


def write_entry(folder):
    target = Path(folder)
    target.mkdir(parents=True, exist_ok=True)
    (target / "entry.png").write_bytes(IMAGE.read_bytes())
    return target / "entry.png"


if __name__ == "__main__":
    write_entry(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
