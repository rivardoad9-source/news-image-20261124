# World news, 24 November 2026, in one image

`main.py` writes `entry.png` (1024x1024, under 1 MiB) for **Tuesday 24 November 2026**
to the output directory (`/output`, or `$MAKEFUN_OUTPUT_DIR`). It copies the image
drawn from `design/day.json` by `design/engine.py`; no network access, same bytes every run.

Rebuild the image from the story file:

    python design/engine.py design/day.json entry.png

Story-file format: see `design/engine.py` (`validate`) and `design/sample-day.json`.
The sample file contains invented placeholder stories only.
