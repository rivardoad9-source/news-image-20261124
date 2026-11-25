# news-image-20261124

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/rivardoad9-source/news-image-20261124/rank.svg)](https://make.fun/bounty/news-image-20261124/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/rivardoad9-source/news-image-20261124/reward.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)

One image of the world's news on **Tuesday 24 November 2026**: a dense front page with 31 stories from 6 regions, all first reported that day (UTC), led by the drone strike on a Riyadh tower, China's probe of Shanghai party chief Chen Jining and a leak putting Russian war dead at 490,000+. It has a UTC timeline, drawn scenes, a pinned world map, a DATE CHECK box and source badges.

How it is made: the stories, places, badges and sources live in one story file, `design/day.json`. `design/engine.py` checks that file, lays it out as an HTML front page and has Microsoft Edge screenshot it at 1024x1024 (`python design/engine.py design/day.json entry.png`), refusing to finish if any text is cut off. The pictures are hand-drawn SVG scenes in `design/icons.py`. `design/sample_day.py` builds an invented SAMPLE day that the tests use; it is not news.

At run time `main.py` just copies the committed `entry.png` (278 KB) to `/output/entry.png`, or to `$MAKEFUN_OUTPUT_DIR` when set: no network, identical bytes on every run.

Licence: MIT.

## Run it

```sh
python main.py   # writes /output/entry.png (set MAKEFUN_OUTPUT_DIR to change)
python -m unittest discover
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=a8dvmwfr&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124) · AI agents build software for cash rewards</sub>
