"""Unit tests for the number dictionaries (`util/export_plover_numbers.py`): the Pluvier number-bar strokes and the French hours."""

import os
import sys
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "plover_stenalgo"))

from util.export_plover_complements import parseIreland  # noqa: E402
from util.export_plover_numbers import BAR_KEYS, barStroke, frenchHours, pluvierEntries, reservedNumberStrokes  # noqa: E402


class TestPluvierNumbers(unittest.TestCase):
    def test_bar_strokes(self) -> None:
        by = dict(BAR_KEYS)
        self.assertEqual(barStroke((("S", by["S"]),)), "#S")
        self.assertEqual(barStroke(tuple(k for k in BAR_KEYS if k[0] in "STPH")), "#STPH")
        self.assertEqual(barStroke((("S", "1"), ("-F", "6"))), "#S-F")
        self.assertEqual(barStroke((("A", "5"), ("O", "0"))), "#AO")

    def test_every_entry_is_a_parsable_stroke_with_digits_in_keyboard_order(self) -> None:
        entries = pluvierEntries()
        self.assertEqual(len(entries), 1023)
        for outline, translation in entries.items():
            self.assertIsNotNone(parseIreland(outline), outline)
        self.assertEqual(entries["#STPH"], "{&1234}")
        self.assertEqual(entries["#AO"], "{&50}")
        self.assertEqual(entries["#-FPLT"], "{&6789}")
        self.assertNotIn("-FRBGS", entries)                    # the glued comma / period belong to the Pluvier punctuation set

    def test_french_hours(self) -> None:
        self.assertEqual(frenchHours("10 o'clock"), "10 h")
        self.assertEqual(frenchHours("13:00"), "13 h")
        self.assertEqual(frenchHours("{&7}"), "{&7}")


class TestReservedStrokes(unittest.TestCase):
    def test_every_reserved_stroke_holds_the_hash_key_and_the_digits_are_in(self) -> None:
        from util.export_plover_system import GEMINI_PR_LABELS
        hashKey = GEMINI_PR_LABELS.index("*4")
        reserved = reservedNumberStrokes()
        self.assertTrue(all(hashKey in stroke for stroke in reserved))
        self.assertGreaterEqual(len(reserved), 1023)            # the Pluvier bar chords alone are 1023
        # the Pluvier 1 is the `k-` key (the Gemini #C button), not `s-`: `k-#` is reserved and `s-#` is not
        self.assertIn(frozenset({2, hashKey}), reserved)
        self.assertNotIn(frozenset({3, hashKey}), reserved)
        # `@#` (5) and `a#` (0) are numbers, so reserved: the keys 11 (A) and 12 (O) of the layout
        self.assertIn(frozenset({11, hashKey}), reserved)
        self.assertIn(frozenset({12, hashKey}), reserved)


if __name__ == "__main__":
    unittest.main()
