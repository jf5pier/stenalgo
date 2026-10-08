"""Unit tests for the spelling lessons exporter (`util/export_spelling_lessons.py`)."""

import json
import os
import sys
import unittest
from typing import Any

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "plover_stenalgo"))

from plover_stenalgo._generated_keys import KEYS  # type: ignore[import-not-found]  # noqa: E402
from src.keyboard import Starboard  # noqa: E402
from util.export_plover_spelling import SPELLING_OUT  # noqa: E402
from util.export_spelling_lessons import SPELLING_DATA, build, slugOf, spell  # noqa: E402


class TestSpell(unittest.TestCase):
    def test_letters_and_case(self) -> None:
        self.assertEqual(spell("Paris"), ["@p_upper", "@a_lower", "@r_lower", "@i_lower", "@s_lower"])

    def test_a_space_is_the_space_after_ending(self) -> None:
        self.assertEqual(spell("A b"), ["@a_upperSpace", "@b_lower"])

    def test_accented_capital(self) -> None:
        self.assertEqual(spell("É"), ["@é_upper"])
        self.assertEqual(slugOf("É", "upper"), "é_upper")

    def test_bad_examples(self) -> None:
        for bad in (" a", "a ", "a-b", "a  b'"):
            with self.assertRaises(ValueError, msg=bad):
                spell(bad)


class TestSpellingLessons(unittest.TestCase):
    document: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        if not all(os.path.exists(os.path.join(ROOT, p)) for p in (SPELLING_OUT, SPELLING_DATA)):
            raise unittest.SkipTest("generated inputs not built")
        os.chdir(ROOT)
        board = Starboard.fromJSONFile("starboard3h.json")
        assert board is not None
        with open(SPELLING_DATA, encoding="utf-8") as fh:
            data = json.load(fh)
        with open(SPELLING_OUT, encoding="utf-8") as fh:
            dictionary = json.load(fh)
        cls.document = build(data, dictionary, board, KEYS)

    def test_entries_are_the_156_strokes(self) -> None:
        self.assertEqual(len(self.document["entries"]), 156)
        self.assertEqual(len({e["primary"] for e in self.document["entries"]}), 156)

    def test_every_example_is_typed_as_written(self) -> None:
        for lesson in self.document["lessons"]:
            for item in lesson["words"]:
                self.assertTrue(item["strokes"])
                self.assertEqual(len(item["strokes"]), len(item["segments"]))
                self.assertEqual("".join(s["text"] for s in item["segments"]), item["ortho"])

    def test_a_stale_dictionary_is_refused(self) -> None:
        board = Starboard.fromJSONFile("starboard3h.json")
        assert board is not None
        with self.assertRaises(ValueError):
            build({"families": []}, {"x": "{&x}"}, board, KEYS)
