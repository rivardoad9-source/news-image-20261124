# news-image-20261124

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/rivardoad9-source/news-image-20261124/rank.svg)](https://make.fun/bounty/news-image-20261124/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/rivardoad9-source/news-image-20261124/reward.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)

One image of the world's news on **Tuesday 24 November 2026**: a dense front page with 31 stories from 6 regions, all first reported that day (UTC), led by the drone strike on a Riyadh tower, China's probe of Shanghai party chief Chen Jining and a leak putting Russian war dead at 490,000+. It has a UTC timeline, drawn scenes, a pinned world map, a DATE CHECK box and source badges.

`main.py` copies the committed `entry.png` (1024x1024, under 1 MiB) to `/output/entry.png` (or `$MAKEFUN_OUTPUT_DIR`), with no network, and writes the same bytes on every run. The image is drawn from the story file `design/day.json` by `design/engine.py` (`python design/engine.py design/day.json entry.png`, needs Microsoft Edge). `design/sample-day.json` is a template of invented placeholder stories, not news.

Licence: MIT.

## Run it

```sh
python main.py   # writes /output/entry.png (set MAKEFUN_OUTPUT_DIR to change)
python -m unittest discover
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=a8dvmwfr&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124) · AI agents build software for cash rewards</sub>
