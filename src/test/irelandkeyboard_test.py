"""Unit tests for the Ireland keyboard model (`src/irelandkeyboard.py`) and for `Starboard.getChordCost`."""

import itertools
import os
import unittest

from src.irelandkeyboard import KEYS, IrelandKeyboard, _shapeCost, parseChord, renderChord
from src.keyboard import FingerWeights, Starboard

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
FW = FingerWeights()


def loadBoard() -> Starboard:
    board = Starboard.fromJSONFile(os.path.join(ROOT, "starboard3h.json"))
    assert board is not None
    return board


class TestStarboardChordCost(unittest.TestCase):
    def test_equals_stroke_cost_per_part(self) -> None:
        board = loadBoard()
        for part, ids in (("onset", range(2, 10)), ("coda", range(16, 26)), ("nucleus", range(11, 15))):
            for n in (1, 2, 3):
                for combo in itertools.combinations(ids, n):
                    self.assertEqual(board.getChordCost(combo), board.getStrokeCost(combo, part), (part, combo))

    def test_mixed_chord_and_illegal(self) -> None:
        board = loadBoard()
        # onset k (2) + nucleus a (12) + coda t (20): three fingers, 125 + 100 + 125 = 350, discounted
        self.assertEqual(board.getChordCost((2, 12, 20)), int(350 * 0.85 ** 3))
        self.assertIsNone(board.getChordCost((2, 3, 4, 5, 22, 23, 24)))     # three pinky keys on the right
        self.assertEqual(board.getChordCost(()), 0)


class TestParse(unittest.TestCase):
    def test_parse_and_render(self) -> None:
        self.assertEqual(parseChord("STAR"), ["S", "T", "A", "-R"])
        self.assertEqual(parseChord("TSAR"), None)
        self.assertEqual(parseChord("-D"), ["-D"])
        self.assertEqual(parseChord("*S"), ["*", "-S"])
        self.assertEqual(renderChord({"-S", "-T"}), "-TS")
        self.assertEqual(renderChord({"T", "-R", "A"}), "TAR")
        self.assertEqual(renderChord({"S"}), "S")
        for text in ("STAR", "-TS", "PWA*EUFPLT"):
            keys = parseChord(text)
            assert keys is not None
            self.assertEqual(renderChord(keys), text)


class TestIrelandCost(unittest.TestCase):
    def setUp(self) -> None:
        self.kb = IrelandKeyboard()

    def one(self, keys: list[str]) -> int:
        cost = self.kb.getChordCost(keys)
        assert cost is not None
        return cost

    def test_single_keys_are_finger_weights(self) -> None:
        self.assertEqual(self.one(["S"]), int(FW.pinky1keyHome * 0.85))
        self.assertEqual(self.one(["T"]), int(FW.ringMid1key * 0.85))
        self.assertEqual(self.one(["H"]), int(FW.index1keyHome * 0.85))
        self.assertEqual(self.one(["*"]), int(FW.index1keyOffHome * 0.85))
        self.assertEqual(self.one(["A"]), int(FW.thumb1key * 0.85))
        self.assertEqual(self.one(["-D"]), int(FW.pinky1keyOffHome * 0.85))

    def test_two_and_three_keys_of_one_finger(self) -> None:
        self.assertEqual(self.one(["T", "K"]), int(FW.ringMid2keys * 0.85))
        self.assertEqual(self.one(["H", "R"]), int(FW.index2keysVert * 0.85))
        self.assertEqual(self.one(["H", "R", "*"]), int(FW.index3keys * 0.85))
        self.assertEqual(self.one(["A", "O"]), int(FW.thumb2keys * 0.85))
        self.assertEqual(self.one(["-T", "-S", "-D"]), int((FW.pinky4keys + _shapeCost((22, 23, 24))) * 0.85))   # three pinky keys: priced as four

    def test_star_goes_to_the_free_index(self) -> None:
        self.assertEqual(self.one(["*", "-F"]), self.one(["-F", "*"]))
        self.assertEqual(self.one(["*", "-F"]), int((FW.index2keysHorz) * 0.85))

    def test_order_matters_not_and_unknown_key(self) -> None:
        self.assertEqual(self.one(["-R", "A", "T"]), self.one(["T", "A", "-R"]))
        self.assertIsNone(self.kb.getChordCost(["Q"]))
        self.assertIsNone(self.kb.getStrokeCost("QX"))

    def test_shape_terms_and_outline(self) -> None:
        # S T: pinky 125 + ring 125 = 250 * 0.7225; S takes its top key, so no zig-zag with T
        self.assertEqual(self.one(["S", "T"]), int(250 * 0.85 ** 2))
        # S K: S takes its bottom key (no zig-zag with K); S P: a one-column gap on either row, +100
        self.assertEqual(self.one(["S", "K"]), int(250 * 0.85 ** 2))
        self.assertEqual(self.one(["S", "P"]), int((250 + 100) * 0.85 ** 2))
        # T (top, ring) with W (bottom, middle): zig-zag +100
        self.assertEqual(self.one(["T", "W"]), int((125 + 125 + 100) * 0.85 ** 2))
        self.assertEqual(self.kb.getOutlineCost("STAR/-D"), (self.kb.getStrokeCost("STAR") or 0) + (self.kb.getStrokeCost("-D") or 0))
        self.assertIsNone(self.kb.getOutlineCost("STAR/QQ"))

    def test_shape_helper_matches_starboard(self) -> None:
        board = loadBoard()
        for ids in (range(2, 10), range(16, 26)):
            for n in (2, 3, 4):
                for combo in itertools.combinations(ids, n):
                    self.assertEqual(_shapeCost(combo), board.getStrokeShapeCost(combo), combo)

    def test_keys_complete(self) -> None:
        self.assertEqual(len(KEYS), 22)


if __name__ == "__main__":
    unittest.main()
