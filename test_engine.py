"""Tests for the story-file engine in design/engine.py (layout checks that
need a browser are skipped when Edge is not installed)."""

import json
import os
import pathlib
import struct
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "design"))

import engine  # noqa: E402
import icons  # noqa: E402

SAMPLE = ROOT / "design" / "sample-day.json"
NEW_KINDS = ["wildfire", "heatwave", "migrants", "satellite", "oil", "train", "election", "concert"]
NEEDED_TOPICS = ["sport", "market", "quake", "flood", "storm", "diplomacy", "court", "health", "tech",
                 "space", "protest", "wildfire", "heatwave"]


def sample():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


class ValidateTest(unittest.TestCase):
    def test_sample_is_valid(self):
        self.assertEqual(engine.validate(sample()), [])

    def test_missing_field_is_reported(self):
        day = sample()
        del day["stories"][0]["headline"]
        self.assertTrue(any("headline" in p for p in engine.validate(day)))

    def test_wrong_lead_count_is_reported(self):
        day = sample()
        day["leads"] = day["leads"][:2]
        self.assertTrue(any("3 leads" in p for p in engine.validate(day)))

    def test_unknown_scene_is_reported(self):
        day = sample()
        day["stories"][1]["scene"] = "no-such-scene"
        self.assertTrue(any("no-such-scene" in p for p in engine.validate(day)))

    def test_scene_used_three_times_is_reported(self):
        day = sample()
        for s in day["stories"][:3]:
            s["scene"] = "fire"
        self.assertTrue(any("fire" in p and "times" in p for p in engine.validate(day)))


class DerivedTextTest(unittest.TestCase):
    def test_region_counts_add_up(self):
        day = sample()
        counts = engine.region_counts(day)
        self.assertEqual(sum(counts.values()), engine.total_stories(day))
        self.assertGreaterEqual(len(counts), 6)

    def test_masthead_and_short_date(self):
        page = engine.build(sample())
        self.assertIn("Tuesday 24 November 2026", page)
        self.assertIn("TUESDAY 24 NOVEMBER", page)
        self.assertNotIn("23 Nov", page)

    def test_chips_show_computed_counts(self):
        day = sample()
        page = engine.build(day)
        for region, n in engine.region_counts(day).items():
            self.assertIn(f"{region} {n}", page)

    def test_total_in_top_bar(self):
        day = sample()
        self.assertIn(f"{engine.total_stories(day)} STORIES", engine.build(day))


class LeadTest(unittest.TestCase):
    def test_lead_without_photo_like_art_still_has_a_picture(self):
        day = sample()
        day["leads"][0].update(region="AFRICA", scene="court", place="NAIROBI, KENYA")
        day["leads"][0].pop("text", None)
        page = engine.build(day)
        self.assertEqual(engine.validate(day), [])
        self.assertIn("NAIROBI, KENYA", page)
        self.assertIn('class="card lead"', page)


class IconsTest(unittest.TestCase):
    def test_every_kind_is_wellformed_svg(self):
        for kind in icons.KINDS:
            svg = icons.banner(kind, "7")
            root = ET.fromstring(svg)
            self.assertTrue(root.tag.endswith("svg"), kind)

    def test_new_scene_kinds_exist(self):
        for kind in NEW_KINDS + NEEDED_TOPICS:
            self.assertIn(kind, icons.KINDS)

    def test_variants_change_the_drawing(self):
        self.assertNotEqual(icons.banner("strike", None, 0), icons.banner("strike", None, 1))


@unittest.skipUnless(os.path.exists(engine.EDGE), "Edge not installed")
class RenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.a = pathlib.Path(cls.tmp.name) / "a.png"
        cls.b = pathlib.Path(cls.tmp.name) / "b.png"
        cls.report = engine.render(SAMPLE, cls.a)
        engine.render(SAMPLE, cls.b)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_png_is_1024_square_and_under_1mib(self):
        data = self.a.read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", data[16:24]), (1024, 1024))
        self.assertLessEqual(len(data), 1048576)

    def test_two_renders_are_identical(self):
        self.assertEqual(self.a.read_bytes(), self.b.read_bytes())

    def test_no_overflow(self):
        self.assertEqual(self.report, [])


if __name__ == "__main__":
    unittest.main()
