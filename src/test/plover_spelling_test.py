"""Unit tests for the spelling theory (`util/export_plover_spelling.py`)."""

import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "plover_stenalgo"))

from src.keyboard import Starboard  # noqa: E402
from util._stenorender import renderFinalStrokesToRTFCRE  # noqa: E402
from util.export_plover_spelling import (ACCENTED, ENDINGS, LETTERS, SPELLING_OUT, build, letterChords, reservedSpellingStrokes,  # noqa: E402
                                         strokes, translation)


class TestSpellingDesign(unittest.TestCase):
    def test_every_character_has_four_distinct_strokes(self) -> None:
        chords = letterChords()
        self.assertEqual(len(chords), 26 + len(ACCENTED))
        self.assertEqual(len(strokes()), len(chords) * 4)

    def test_plain_letters_are_the_a_to_z(self) -> None:
        self.assertEqual("".join(sorted(LETTERS)), "abcdefghijklmnopqrstuvwxyz")

    def test_an_accent_is_one_shared_key(self) -> None:
        chords = letterChords()
        for char, (base, _accent) in ACCENTED.items():
            self.assertEqual(len(set(chords[char]) - set(LETTERS[base])), 1, char)
        graveKeys = {tuple(set(chords[c]) - set(LETTERS[ACCENTED[c][0]])) for c in "àèù"}
        self.assertEqual(len(graveKeys), 1)

    def test_translations(self) -> None:
        self.assertEqual(translation("é", "lower"), "{&é}")
        self.assertEqual(translation("é", "upper"), "{&É}")
        self.assertEqual(translation("a", "lowerSpace"), "{&a}{^ ^}")
        self.assertEqual(translation("a", "upperSpace"), "{&A}{^ ^}")

    def test_endings_are_a_row_and_the_index_key_adds_the_space(self) -> None:
        self.assertEqual(set(ENDINGS["lowerSpace"]) - set(ENDINGS["lower"]), {16})
        self.assertEqual(set(ENDINGS["upperSpace"]) - set(ENDINGS["upper"]), {17})

    def test_reserved_strokes_hold_a_mark_key(self) -> None:
        reserved = reservedSpellingStrokes()
        self.assertTrue(reserved)
        self.assertTrue(all(10 in stroke or 15 in stroke for stroke in reserved))


class TestSpellingBuild(unittest.TestCase):
    def setUp(self) -> None:
        os.chdir(ROOT)
        self.starboard = Starboard.fromJSONFile("starboard3h.json")
        assert self.starboard is not None

    def test_a_collision_is_reported(self) -> None:
        assert self.starboard is not None
        first = next(iter(strokes()))
        chord = renderFinalStrokesToRTFCRE(self.starboard, (first,))
        with self.assertRaises(ValueError):
            build(self.starboard, {chord}, set(), set())
        with self.assertRaises(ValueError):
            build(self.starboard, set(), {chord}, set())
        with self.assertRaises(ValueError):
            build(self.starboard, set(), set(), {frozenset(first)})

    def test_the_shipped_file_is_collision_free_against_the_theory(self) -> None:
        theory, spelling = ROOT / "plover_stenalgo_dictionary.json", ROOT / SPELLING_OUT
        if not (theory.exists() and spelling.exists()):
            self.skipTest("generated data not built")
        with open(theory, encoding="utf-8") as f:
            words = json.load(f)
        with open(spelling, encoding="utf-8") as f:
            entries = json.load(f)
        self.assertEqual(len(entries), 156)
        firsts = {o.split("/")[0] for o in words}
        self.assertFalse(set(entries) & firsts)
