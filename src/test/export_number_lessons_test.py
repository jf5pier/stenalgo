"""Unit tests for the number lessons exporter (`util/export_number_lessons.py`): both theories, the strokes, the Definitions entries."""

import json
import os
import sys
import unittest
from typing import Any

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "plover_stenalgo"))

from plover_stenalgo._generated_keys import KEYS  # type: ignore[import-not-found]  # noqa: E402
from src.keyboard import Starboard  # noqa: E402
from util.export_number_lessons import NUMBER_DATA, NUMBER_FILES, build  # noqa: E402
from util.export_punctuation_lessons import PLOVER_FILES, PLUVIER_FILE, PRACTICE_WORDS, loadChords, loadWords  # noqa: E402


class TestNumberLessons(unittest.TestCase):
    document: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        needed = [PRACTICE_WORDS, NUMBER_DATA, PLUVIER_FILE, *PLOVER_FILES, *NUMBER_FILES.values()]
        if not all(os.path.exists(os.path.join(ROOT, p)) for p in needed):
            raise unittest.SkipTest("generated inputs not built")
        os.chdir(ROOT)
        board = Starboard.fromJSONFile("starboard3h.json")
        assert board is not None
        with open(NUMBER_DATA, encoding="utf-8") as fh:
            data = json.load(fh)
        numberChords = {theory: loadChords((file,)) for theory, file in NUMBER_FILES.items()}
        cls.document = build(data, numberChords, loadChords(PLOVER_FILES), loadChords((PLUVIER_FILE,)), loadWords(), board, KEYS)

    def lessons(self, style: str, punctuation: str = "plover") -> list[dict[str, Any]]:
        return self.document["lessons"][style][punctuation]

    def test_both_styles_have_the_same_chiffres_lessons_and_the_track_is_listed(self) -> None:
        self.assertEqual([t["id"] for t in self.document["tracks"]], ["chiffres"])
        self.assertEqual([l["id"] for l in self.lessons("lapwing")], [l["id"] for l in self.lessons("pluvier")])


    def test_every_item_types_the_digits_of_its_number(self) -> None:
        for style in ("lapwing", "pluvier"):
            for lesson in self.lessons(style):
                for item in lesson["words"]:
                    digits = "".join(c for c in item["ortho"] if c.isdigit())
                    shown = "".join(c for seg in item["segments"] for c in seg["text"] if c.isdigit())
                    self.assertEqual(digits, shown, (style, item["ortho"]))

    def test_the_styles_split_a_number_into_their_own_strokes(self) -> None:
        def item(style: str, ortho: str) -> dict[str, Any]:
            return next(w for l in self.lessons(style) for w in l["words"] if w["ortho"] == ortho)
        self.assertEqual(len(item("pluvier", "12346789")["strokes"]), 1)           # one stroke in the keyboard order
        self.assertEqual(len(item("lapwing", "12346789")["strokes"]), 8)           # the numpad: one stroke per digit
        self.assertEqual(len(item("lapwing", "1000")["strokes"]), 1)               # the thousands vowels
        self.assertEqual(len(item("pluvier", "21")["strokes"]), 2)                 # 2 then 1 goes back down the keyboard

    def test_the_glued_comma_comes_from_the_punctuation_style_not_the_number_theory(self) -> None:
        def decimal(theory: str, punctuation: str) -> dict[str, Any]:
            return next(w for l in self.lessons(theory, punctuation) for w in l["words"] if w["ortho"] == "3,14")
        self.assertIn("v-l", decimal("pluvier", "plover")["steno"].split())          # Plover punctuation: v-l, whatever the numbers
        self.assertIn("v-l", decimal("lapwing", "plover")["steno"].split())
        self.assertIn("-jsdRl", decimal("pluvier", "pluvier")["steno"].split())      # Pluvier punctuation: its own -FRBGS
        self.assertIn("-jsdRl", decimal("lapwing", "pluvier")["steno"].split())

    def test_a_multi_stroke_number_is_spaced_before_its_first_stroke_only(self) -> None:
        lesson = next(l for l in self.lessons("pluvier") if "plusieurs frappes" in l["title"])
        item = next(w for w in lesson["words"] if w["ortho"] == "2025")
        self.assertEqual([s["text"] for s in item["segments"]], ["20", "25"])
        self.assertEqual([s["spaceBefore"] for s in item["segments"]], [False, False])      # alone: the first has no space before it
        sentence = next(w for l in self.lessons("pluvier") if "phrases" in l["title"] for w in l["words"] if w["ortho"] == "Il a 25 ans")
        self.assertEqual([s["spaceBefore"] for s in sentence["segments"]], [False, True, True, True])

    def test_the_bar_one_is_the_k_key(self) -> None:
        one = next(w for w in self.lessons("pluvier")[0]["words"] if w["ortho"] == "1")
        self.assertEqual(one["steno"], "k-#")

    def test_definitions_list_every_single_stroke_number_of_each_theory(self) -> None:
        digits = {theory: {e["glyph"] for e in self.document["entries"][theory]} for theory in ("lapwing", "pluvier")}
        for theory in digits:
            self.assertTrue(digits[theory] >= set("0123456789"), theory)
        self.assertEqual(len(digits["pluvier"]), 1023)                       # every subset of the ten bar keys
        self.assertTrue({"12346789", "123", "2468"} <= digits["pluvier"])
        self.assertTrue({"10", "300", "9000"} <= digits["lapwing"])           # the numpad: a digit with its zeros
