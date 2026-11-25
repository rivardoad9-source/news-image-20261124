"""One-day world-news front page, driven entirely by a JSON story file.

Everything on the page comes from the file: masthead date, tagline, region
chips and counts (computed), UTC timeline, 3 leads, 10 illustrated stories,
briefs, map pins (from lat/lon), DATE CHECK box. Nothing else is date-specific.

usage:  python design/engine.py design/sample-day.json out.png
        (prints the overflow report; exits 1 if anything overflows or is invalid)
"""

import html
import json
import math
import os
import pathlib
import re
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from icons import KINDS, banner  # noqa: E402
from scenes import SCENES  # noqa: E402

EDGE = os.environ.get("EDGE_PATH", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")

BADGE = {"REPORTED": "#2e7d32", "OFFICIAL": "#1d4e89", "CONFIRMED": "#2e7d32",
         "CLAIM": "#b26a00", "ONGOING": "#1d6fa3", "PROVISIONAL": "#6a4c93"}
REGION = {"EUROPE": "#2563c9", "MIDDLE EAST": "#c62828", "AFRICA": "#2e7d32", "ASIA": "#ef6c00",
          "AMERICAS": "#7b3fa0", "OCEANIA": "#00897b", "WORLD": "#37474f"}
STORY_FIELDS = ["place", "region", "field", "headline", "dek", "source", "badge", "scene", "lat", "lon"]
BRIEF_MAX = 18
MAX_SCENE_REPEATS = 2

# Coarse land mask on a 60x26 grid: column = 6 deg of longitude from -180,
# row = 5 deg of latitude from 75N. Boxes are (col0, col1, row0, row1), inclusive.
LAND = [
    (2, 6, 1, 3), (6, 14, 1, 4), (17, 20, 1, 4), (15, 16, 1, 1), (15, 16, 4, 4), (21, 26, 0, 2),
    (9, 18, 5, 8), (10, 16, 9, 9), (17, 17, 9, 9), (11, 14, 10, 10), (13, 15, 11, 11), (15, 16, 12, 12),
    (17, 21, 12, 13), (16, 23, 14, 15), (17, 24, 16, 16), (17, 23, 17, 19), (18, 22, 20, 21),
    (18, 20, 22, 23), (18, 19, 24, 25),
    (30, 34, 1, 3), (28, 29, 3, 4), (29, 35, 4, 5), (28, 34, 6, 6), (28, 30, 7, 7), (32, 33, 7, 7),
    (34, 37, 6, 7), (35, 59, 0, 3), (36, 55, 4, 4), (37, 49, 5, 5), (37, 52, 6, 6), (51, 52, 6, 7),
    (53, 54, 6, 8), (42, 50, 7, 9), (38, 40, 7, 9), (35, 39, 9, 11), (41, 44, 9, 11), (42, 43, 12, 12),
    (45, 48, 10, 13), (50, 50, 11, 12), (45, 47, 14, 14), (49, 53, 14, 15), (48, 50, 16, 16),
    (28, 35, 7, 8), (27, 36, 9, 12), (37, 38, 11, 12), (29, 38, 13, 13), (31, 37, 14, 15),
    (32, 37, 16, 19), (38, 38, 17, 19), (33, 35, 20, 21),
    (49, 54, 17, 18), (48, 55, 19, 20), (49, 55, 21, 21), (53, 54, 22, 22), (57, 58, 22, 24),
]
COLS, ROWS = 60, 26


# ---------- story file: checks and derived values ----------

def load_day(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def every(day):
    return day["leads"] + day["stories"]


def region_counts(day):
    counts = {}
    for s in every(day):
        counts[s["region"]] = counts.get(s["region"], 0) + 1
    for a in day["also"]:
        counts[a[1]] = counts.get(a[1], 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def total_stories(day):
    return len(every(day)) + len(day["also"])


def short_day(day):
    """'Tuesday 24 November 2026' -> 'TUESDAY 24 NOVEMBER'."""
    return re.sub(r"\s+\d{4}$", "", day["day"]).upper()


def scene_ok(name):
    return name in SCENES or name in KINDS


def validate(day):
    problems = []
    for key in ("day", "tagline", "timeline", "numbers", "leads", "stories", "also", "left_out", "not_yet", "foot"):
        if key not in day:
            problems.append(f"missing top-level field: {key}")
    if problems:
        return problems
    if not re.match(r"^[A-Za-z]+ \d{1,2} [A-Za-z]+ \d{4}$", day["day"]):
        problems.append(f"day should look like 'Tuesday 24 November 2026', got {day['day']!r}")
    if len(day["leads"]) != 3:
        problems.append(f"need exactly 3 leads, got {len(day['leads'])}")
    if len(day["stories"]) != 10:
        problems.append(f"need exactly 10 stories, got {len(day['stories'])}")
    if len(day["numbers"]) != 4:
        problems.append(f"need exactly 4 numbers, got {len(day['numbers'])}")
    if not 8 <= len(day["also"]) <= BRIEF_MAX:
        problems.append(f"need 8..{BRIEF_MAX} briefs, got {len(day['also'])}")
    use = {}
    for kind, items in (("lead", day["leads"]), ("story", day["stories"])):
        for i, s in enumerate(items, 1):
            for f in STORY_FIELDS:
                if f not in s:
                    problems.append(f"{kind} {i} missing {f}")
            if s.get("region") not in REGION:
                problems.append(f"{kind} {i}: unknown region {s.get('region')!r}")
            if s.get("badge") not in BADGE:
                problems.append(f"{kind} {i}: unknown badge {s.get('badge')!r}")
            if "scene" in s:
                if not scene_ok(s["scene"]):
                    problems.append(f"{kind} {i}: unknown scene {s['scene']!r}")
                use[s["scene"]] = use.get(s["scene"], 0) + 1
    for name, n in use.items():
        if n > MAX_SCENE_REPEATS:
            problems.append(f"scene {name!r} used {n} times (max {MAX_SCENE_REPEATS}); pick other scenes")
    for i, a in enumerate(day["also"], 1):
        if len(a) < 4:
            problems.append(f"brief {i} needs [place, region, headline, source(, badge)]")
        elif a[1] not in REGION:
            problems.append(f"brief {i}: unknown region {a[1]!r}")
    return problems


# ---------- world map ----------

def land_cells():
    return {(c, r) for c0, c1, r0, r1 in LAND for c in range(c0, c1 + 1) for r in range(r0, r1 + 1)}


def world_map(pins, w=300, h=104):
    sx, sy = w / COLS, h / ROWS
    out = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">']
    for c, r in sorted(land_cells()):
        out.append(f'<circle cx="{(c + .5) * sx:.1f}" cy="{(r + .5) * sy:.1f}" r="1.9" fill="#a9b4c2"/>')
    placed, marks, lines = [], [], []
    for n, lat, lon, col in pins:
        x0 = min(max((lon + 180) / 360 * w, 9), w - 9)
        y0 = (75 - lat) / 130 * h
        spot = None
        for ring in (0, 11, 15, 19, 23, 27, 31):
            for k in range(12 if ring else 1):
                a_ = math.pi * 2 * k / 12 + 0.4
                x, y = x0 + ring * math.cos(a_), y0 + ring * math.sin(a_)
                if 8 <= x <= w - 8 and 8 <= y <= h - 8 and not any(abs(x - px) < 12 and abs(y - py) < 12 for px, py in placed):
                    spot = (x, y)
                    break
            if spot:
                break
        x, y = spot or (x0, y0)
        placed.append((x, y))
        if (x, y) != (x0, y0):
            lines.append(f'<path d="M{x0:.1f},{y0:.1f} L{x:.1f},{y:.1f}" stroke="{col}" stroke-width="1.2"/>'
                         f'<circle cx="{x0:.1f}" cy="{y0:.1f}" r="1.8" fill="{col}"/>')
        marks.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.6" fill="{col}" stroke="#fff" stroke-width="1"/>'
                     f'<text x="{x:.1f}" y="{y + 2.9:.1f}" font-family="Arial" font-weight="700" font-size="7.6" '
                     f'fill="#fff" text-anchor="middle">{n}</text>')
    out.extend(lines)
    out.extend(marks)
    out.append("</svg>")
    return "".join(out)


# ---------- page ----------

def esc(s):
    return html.escape(str(s), quote=False)


def pic(s, variant, lead):
    if s["scene"] in SCENES:
        return SCENES[s["scene"]]()
    text = s.get("text")
    if text and not lead and len(s["place"]) > 14:
        text = None  # a long place chip would sit on top of the corner figure
    return banner(s["scene"], text, variant)


def card(n, s, variant, lead=False):
    col = REGION.get(s["region"], "#37474f")
    bcol = BADGE.get(s["badge"], "#2e7d32")
    cls = "card lead" if lead else "card"
    # leads carry the badge on the picture; small cards put it on the source line,
    # so a short picture is never covered by a badge and a place chip at once
    badge = f'<span class="badge" style="background:{bcol}">{s["badge"]}</span>'
    pic_badge, src_badge = (badge, "") if lead else ("", badge)
    return (f'<div class="{cls}" style="--rc:{col}"><div class="pic">{pic(s, variant, lead)}'
            f'<div class="place"><i>{n}</i>{esc(s["place"])}</div>'
            f'{pic_badge}</div>'
            f'<div class="tx"><div class="kick">{esc(s["region"])} · {esc(s["field"])}</div>'
            f'<h2>{esc(s["headline"])}</h2><p>{esc(s["dek"])}</p><div class="src">{src_badge}{esc(s["source"])}</div></div></div>')


CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 1024px; height: 1024px; overflow: hidden; }
body { background: #f7f3ea; color: #15181d; font-family: 'Segoe UI', Arial, sans-serif; -webkit-font-smoothing: antialiased;
       display: flex; flex-direction: column; }
body > * { flex: none; }
svg { display: block; width: 100%; height: 100%; }
.bar { background: #15181d; color: #fff; display: flex; justify-content: space-between; padding: 2px 12px;
       font: 700 13px Bahnschrift, Arial; letter-spacing: 1.5px; height: 20px; align-items: center; }
.bar b { color: #ffcc33; }
.mast { height: 76px; padding: 0 10px; }
.mast svg text { font: 700 80px Georgia, 'Times New Roman', serif; fill: #15181d; }
.tag { text-align: center; font: italic 700 21px Georgia, serif; color: #b3001b; white-space: nowrap; overflow: hidden;
       height: 26px; padding: 0 10px; }
.chips { display: flex; justify-content: center; gap: 6px; margin: 3px 0 4px; height: 22px; }
.chips span { font: 700 14px Bahnschrift, Arial; color: #fff; padding: 1px 9px; border-radius: 3px; letter-spacing: .6px; }
.utc { margin: 0 10px; background: #15181d; color: #f0f0f0; border-radius: 4px; padding: 0 8px; font: 12.5px 'Segoe UI', Arial;
       white-space: nowrap; overflow: hidden; height: 22px; line-height: 22px; }
.utc b { color: #ff5a6e; margin-right: 7px; }
.utc span { margin-right: 9px; }
.utc em { color: #ffcc33; font-style: normal; font-weight: 700; margin-right: 3px; }
.leads { display: grid; grid-template-columns: 1fr 1fr 1fr 170px; gap: 8px; margin: 5px 10px 0; height: 252px; }
.rows { display: grid; grid-template-columns: repeat(5, 1fr); gap: 7px; margin: 5px 10px 0; height: 172px; }
.card { background: #fff; border: 1px solid #d8d2c4; border-top: 5px solid var(--rc); display: flex; flex-direction: column;
        min-height: 0; overflow: hidden; }
.card .pic { position: relative; flex: 0 1 52px; min-height: 26px; }
.card.lead .pic { flex: 0 1 100px; min-height: 56px; }
.place { position: absolute; left: 4px; top: 4px; background: rgba(255,255,255,.95); color: #15181d; padding: 1px 6px 1px 2px;
         border-radius: 3px; font: 700 12px Bahnschrift, Arial; letter-spacing: .3px; display: flex; align-items: center; gap: 4px;
         max-width: calc(100% - 8px); white-space: nowrap; overflow: hidden; }
.place i { font-style: normal; background: var(--rc); color: #fff; border-radius: 50%; width: 17px; height: 17px; flex: none;
           display: inline-flex; align-items: center; justify-content: center; font-size: 11px; }
.src .badge { position: static; display: inline-block; margin-right: 3px; padding: 0 3px; font-size: 8.5px; letter-spacing: .2px; vertical-align: 1px; }
.badge { position: absolute; right: 4px; bottom: 4px; color: #fff; font: 700 10px Arial; letter-spacing: .7px;
         padding: 2px 5px; border-radius: 2px; }
.tx { padding: 3px 7px 2px; display: flex; flex-direction: column; flex: 1 0 auto; }
.kick { flex: none; font: 700 10.5px Arial; letter-spacing: .6px; color: var(--rc); text-transform: uppercase; white-space: nowrap; overflow: hidden; }
.card h2 { flex: none; font: 700 17px/1.06 Georgia, serif; margin-top: 2px; text-wrap: balance; }
.card.lead h2 { font-size: 23px; line-height: 1.04; }
.card p { font-size: 12px; line-height: 1.18; color: #2b2b2b; margin-top: 2px; }
.card.lead p { font-size: 12.5px; line-height: 1.2; }
.src { margin-top: auto; font-size: 9.5px; line-height: 1.1; color: #6b6b6b; padding-top: 1px; flex: none; white-space: nowrap; overflow: hidden; }
.nums { background: #15253d; color: #fff; padding: 6px 9px; display: flex; flex-direction: column; gap: 3px; }
.nums h3 { font: 700 13px Bahnschrift, Arial; letter-spacing: 1px; border-bottom: 1px solid #3b4d6b; padding-bottom: 2px; }
.nums div b { display: block; font: 700 26px/1 Bahnschrift, Arial; color: #ffcc33; }
.nums div span { font-size: 11px; color: #d6e0ee; line-height: 1.12; display: block; }
.bottom { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 8px; margin: 5px 10px 0; height: 108px; }
.also { min-width: 0; }
.also h3, .map h3 { font: 700 13.5px Bahnschrift, Arial; letter-spacing: 1px; border-bottom: 2px solid #15181d; padding-bottom: 1px; margin-bottom: 2px; }
.also ol { list-style: none; columns: 3; column-gap: 10px; }
.also li { font-size: 11.5px; line-height: 1.2; break-inside: avoid; white-space: nowrap; overflow: hidden; }
.also li b { font-weight: 700; }
.also li i { font-style: normal; color: #b3001b; font-weight: 700; margin-right: 3px; }
.lab { color: #fff; font: 700 8.5px Arial; padding: 0 3px; border-radius: 2px; margin-right: 3px; vertical-align: 1px; }
.map { background: #fff; border: 1px solid #d8d2c4; padding: 3px 6px; display: flex; flex-direction: column; }
.map .m { flex: 1; min-height: 0; position: relative; }
.map .m svg { position: absolute; inset: 0; }
.check { margin: 5px 10px 0; border: 2px solid #c62828; background: #fff; padding: 2px 8px; font-size: 11px; line-height: 1.2; height: 78px;
         overflow: hidden; }
.check .h { display: flex; gap: 8px; align-items: center; font-weight: 700; font-size: 13px; white-space: nowrap; }
.check .h span { background: #c62828; color: #fff; padding: 0 7px; font: 700 13px Bahnschrift, Arial; letter-spacing: 1px; }
.check u { text-decoration: none; color: #c62828; font-weight: 700; }
.foot { text-align: center; font-size: 10px; color: #555; padding: 2px 10px 0; height: 26px; overflow: hidden; line-height: 1.15; }
"""


def brief(i, a):
    badge = a[4] if len(a) > 4 else "REPORTED"
    lab = f'<span class="lab" style="background:{BADGE[badge]}">{badge}</span>' if badge != "REPORTED" else ""
    return f'<li><i>{i}</i>{lab}<b>{esc(a[2])}</b></li>'


def build(day, probe=False):
    items = every(day)
    seen = {}
    cards = []
    for i, s in enumerate(items):
        v = seen.get(s["scene"], 0)
        seen[s["scene"]] = v + 1
        cards.append(card(i + 1, s, v, lead=i < len(day["leads"])))
    counts = region_counts(day)
    total = total_stories(day)
    chips = "".join(f'<span style="background:{REGION.get(r, "#37474f")}">{esc(r)} {n}</span>' for r, n in counts.items())
    utc = "".join(f'<span><em>{esc(t)}</em>{esc(x)}</span>' for t, x in day["timeline"])
    nums = "".join(f'<div><b>{esc(v)}</b><span>{esc(t)}</span></div>' for v, t in day["numbers"])
    n0 = len(items) + 1
    also = "".join(brief(n0 + i, a) for i, a in enumerate(day["also"]))
    pins = [(i + 1, s["lat"], s["lon"], REGION.get(s["region"], "#37474f")) for i, s in enumerate(items)]
    left = " · ".join(f'{esc(t)} <u>{esc(d)}</u>' for t, d in day["left_out"])
    check = day.get("check") or f"Every story on this page happened or was first reported on {day['day']} (UTC)."
    short = day.get("short") or short_day(day)
    d = esc(day["day"])
    body = f"""
<div class="bar"><span>THE WORLD IN ONE DAY</span><span><b>{total} STORIES · {len(counts)} REGIONS</b> · ALL FROM THIS ONE DAY</span></div>
<div class="mast"><svg viewBox="0 0 1004 76" preserveAspectRatio="none"><text x="2" y="62" textLength="1000" lengthAdjust="spacingAndGlyphs">{d}</text></svg></div>
<div class="tag">{esc(day["tagline"])}</div>
<div class="chips">{chips}</div>
<div class="utc"><b>UTC</b>{utc}</div>
<div class="leads">{"".join(cards[:3])}<div class="nums"><h3>THE DAY IN NUMBERS</h3>{nums}</div></div>
<div class="rows">{"".join(cards[3:8])}</div>
<div class="rows">{"".join(cards[8:13])}</div>
<div class="bottom"><div class="also"><h3>ALSO ON {esc(short)}</h3><ol>{also}</ol></div>
<div class="map"><h3>WHERE IT HAPPENED</h3><div class="m">{world_map(pins)}</div></div></div>
<div class="check"><div class="h"><span>DATE CHECK</span>{esc(check)}</div>Left out on purpose (first reported earlier): {left}<br><b>Not yet:</b> {esc(day["not_yet"])}</div>
<div class="foot">{esc(day["foot"])}</div>
"""
    script = CHECK_JS if probe else ""
    return (f'<!doctype html><html><head><meta charset="utf-8"><title>{d}</title><style>{CSS}</style></head>'
            f'<body>{body}{script}</body></html>')


# Reports every element whose content is clipped, plus anything past the 1024 box.
CHECK_JS = """<script>addEventListener('load',()=>{const bad=[];
document.querySelectorAll('.card p,.card h2,.also li,.kick,.src,.utc,.tx,.also,.map,.bottom,.foot,.check,.tag,.place,.mast,.nums,.leads,.rows').forEach(e=>{
 if(e.scrollHeight>e.clientHeight+1||e.scrollWidth>e.clientWidth+1)bad.push((e.className||e.tagName)+':'+e.textContent.slice(0,24)+' '+e.scrollWidth+'x'+e.scrollHeight+' vs '+e.clientWidth+'x'+e.clientHeight);});
document.querySelectorAll('body *').forEach(e=>{const r=e.getBoundingClientRect();
 if(r.width&&(r.bottom>1024.5||r.right>1024.5||r.left<-0.5))bad.push('outside:'+(e.className||e.tagName)+' '+Math.round(r.bottom)+','+Math.round(r.right));});
const pre=document.createElement('pre');pre.id='overflow';pre.textContent='OVERFLOW '+JSON.stringify(bad)+' END';document.body.appendChild(pre);});</script>"""


def _edge(*args):
    return subprocess.run([EDGE, "--headless", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                           "--window-size=1024,1024", *args], capture_output=True, text=True, encoding="utf-8", timeout=120)


def overflow_report(day):
    with tempfile.TemporaryDirectory() as t:
        p = pathlib.Path(t) / "probe.html"
        p.write_text(build(day, probe=True), encoding="utf-8")
        r = _edge("--dump-dom", p.as_uri())
    m = re.search(r"OVERFLOW (\[.*?\]) END", r.stdout, re.S)
    if not m:
        raise RuntimeError("overflow probe did not run")
    return json.loads(html.unescape(m.group(1)))


def render(src, out_png):
    """Render a story file (path or dict) to a 1024x1024 PNG. Returns the overflow list."""
    day = src if isinstance(src, dict) else load_day(src)
    problems = validate(day)
    if problems:
        raise ValueError("invalid story file:\n  " + "\n  ".join(problems))
    report = overflow_report(day)
    out_png = pathlib.Path(out_png).resolve()
    with tempfile.TemporaryDirectory() as t:
        p = pathlib.Path(t) / "page.html"
        p.write_text(build(day), encoding="utf-8")
        _edge(f"--screenshot={out_png}", p.as_uri())
    return report


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    day = load_day(sys.argv[1])
    for p in validate(day):
        print("PROBLEM", p)
    rep = render(day, sys.argv[2]) if not validate(day) else ["invalid"]
    print("overflow:", rep)
    print(sys.argv[2], pathlib.Path(sys.argv[2]).stat().st_size, "bytes")
    sys.exit(1 if rep or validate(day) else 0)
