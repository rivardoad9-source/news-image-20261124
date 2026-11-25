"""An invented placeholder day for testing the layout. Nothing here is news:
every headline says SAMPLE and every place, figure and badge is made up."""

# (place, region, field, scene, badge, lat, lon, corner figure)
LEADS = [
    ("PORT HARCOURT, NIGERIA", "AFRICA", "Disaster", "flood", "CONFIRMED", 4.8, 7.0, "9k"),
    ("CEBU, PHILIPPINES", "ASIA", "Disaster", "quake", "CONFIRMED", 10.3, 123.9, "M5.9"),
    ("VIENNA, AUSTRIA", "EUROPE", "Diplomacy", "diplomacy", "OFFICIAL", 48.2, 16.4, None),
]
CARDS = [
    ("DOHA", "MIDDLE EAST", "Sport", "sport", "REPORTED", 25.3, 51.5, "3-0"),
    ("OSAKA", "ASIA", "Markets", "market", "REPORTED", 34.7, 135.5, "-1%"),
    ("PERTH", "OCEANIA", "Weather", "wildfire", "OFFICIAL", -31.9, 115.9, None),
    ("ACCRA", "AFRICA", "Court", "court", "REPORTED", 5.6, -0.2, None),
    ("RECIFE", "AMERICAS", "Health", "health", "CLAIM", -8.1, -34.9, None),
    ("KOUROU", "WORLD", "Space", "satellite", "ONGOING", 5.2, -52.7, None),
    ("QUITO", "AMERICAS", "Protest", "protest", "REPORTED", -0.2, -78.5, None),
    ("PUNE", "ASIA", "Transport", "train", "REPORTED", 18.5, 73.9, None),
    ("PORTO", "EUROPE", "Weather", "storm", "CONFIRMED", 41.2, -8.6, None),
    ("TUNIS", "MIDDLE EAST", "Politics", "election", "PROVISIONAL", 36.8, 10.2, None),
]
BRIEF_PLACES = [("Lome", "AFRICA"), ("Busan", "ASIA"), ("Bergen", "EUROPE"), ("Cusco", "AMERICAS"),
                ("Muscat", "MIDDLE EAST"), ("Hobart", "OCEANIA"), ("Banjul", "AFRICA"), ("Hue", "ASIA"),
                ("Turin", "EUROPE"), ("Cali", "AMERICAS"), ("Aqaba", "MIDDLE EAST"), ("Suva", "OCEANIA")]


def story(i, row, lead):
    place, region, field, scene, badge, lat, lon, figure = row
    s = {"place": place, "region": region, "field": field, "badge": badge, "scene": scene,
         "lat": lat, "lon": lon, "source": "SAMPLE placeholder",
         "headline": f"SAMPLE: {field} story number {i}" + (" leads the page" if lead else ""),
         "dek": "Invented text that only tests how the layout holds a short explainer."}
    if figure:
        s["text"] = figure
    return s


def sample_day():
    briefs = [[p, r, f"SAMPLE: brief number {n}", "SAMPLE"] for n, (p, r) in enumerate(BRIEF_PLACES, 1)]
    briefs[2].append("CLAIM")
    briefs[4].append("OFFICIAL")
    return {
        "day": "Tuesday 24 November 2026",
        "tagline": "SAMPLE LAYOUT, NOT NEWS · invented stories that only test the page",
        "timeline": [[f"{h:02d}:00", f"SAMPLE event {h}"] for h in (1, 5, 9, 13, 17, 21)],
        "numbers": [["9k", "SAMPLE figure (invented)"], ["M5.9", "SAMPLE figure (invented)"],
                    ["3-0", "SAMPLE score (invented)"], ["-1%", "SAMPLE move (invented)"]],
        "leads": [story(i, row, True) for i, row in enumerate(LEADS, 1)],
        "stories": [story(i, row, False) for i, row in enumerate(CARDS, 4)],
        "also": briefs,
        "left_out": [["SAMPLE earlier story", "Sun 22"]],
        "not_yet": "SAMPLE items due on later days.",
        "foot": "SAMPLE PAGE: every story is invented to test the layout. Scenes are drawn illustrations.",
    }
