"""Unit tests for the theory comparison metrics (`src/theorycompare.py`) on tiny hand-built theories."""

import os
import tempfile
import unittest

from src import theorycompare as tc
from src.keyboard import Starboard

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
FREQ = {"star": 10.0, "tsar": 5.0, "chat": 5.0, "rare": 0.0, "only": 20.0}


def unitCost(text: str) -> int | None:
    return 100 if text != "BAD" else None


def parseDigits(text: str) -> tuple[tuple[int, ...], ...] | None:
    try:
        return tuple(tuple(int(c) for c in stroke) for stroke in text.split("/"))
    except ValueError:
        return None


class TestLoadLexicon(unittest.TestCase):
    def test_frequencies_are_summed_per_spelling(self) -> None:
        rows = ["ortho\tsyll\tfreqfilms2\tfreqlivres", "Etoile\te-twal\t1.5\t7", "etoile\tetwal\t2.5\t1", "x\tx\t0\t0"]
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "lex.tsv")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(rows) + "\n")
            films = tc.loadLexicon(path, "films")
            livres = tc.loadLexicon(path, "livres")
        self.assertEqual(films.freq, {"etoile": 4.0, "x": 0.0})
        self.assertEqual(livres.freq["etoile"], 8.0)
        self.assertEqual(films.syll["etoile"], "etwal")          # the most frequent row


class TestViews(unittest.TestCase):
    def test_stenalgo_collisions_are_measured(self) -> None:
        view = tc.buildStenalgoView({"12": "star", "21": "tsar", "1/2": "chat", "1/2x": "only"}, parseDigits)
        self.assertEqual(view.claimants, {})
        self.assertEqual(view.notes["unparsableOutlines"], 1)
        clash = tc.buildStenalgoView({"12": "star", "012": "tsar"}, lambda t: ((int(t),),))
        self.assertEqual(clash.claimants["12"], frozenset({"star", "tsar"}))

    def test_pluvier_view_and_lost_words(self) -> None:
        view = tc.buildPluvierView({"STAR": "Star", "TSAR": "tsar"}, {"STAR": ["star", "stars"], "X": ["a"]})
        self.assertEqual(view.claimants["STAR"], frozenset({"star", "stars"}))
        self.assertEqual(view.lostWords, {"stars", "a"})

    def test_layered_view(self) -> None:
        base = {"STAR": "star", "TSAR": "tsar", "SHA": "chat"}
        tao = {"STAR": "stars", "KOUR": "cours"}                 # a brief takes STAR from `star`
        view = tc.buildLayeredView([base, tao], {"SHA": ["chat", "chats"]})
        self.assertEqual(view.outlines["stars"], ["STAR"])
        self.assertNotIn("star", view.outlines)                  # star lost its only outline
        self.assertEqual(view.claimants["STAR"], frozenset({"star", "stars"}))
        self.assertEqual(view.claimants["SHA"], frozenset({"chat", "chats"}))
        self.assertEqual(view.lostWords, {"star", "chats"})
        self.assertEqual(view.notes["layerEntries"], [3, 2])
        self.assertEqual(view.notes["outlinesTakenByAnotherLayer"], 1)
        # the same word on the same outline in two layers is not a conflict
        same = tc.buildLayeredView([{"A": "a"}, {"A": "A"}], {})
        self.assertEqual((same.claimants, same.lostWords), ({}, set()))
        # a single layer behaves like buildPluvierView
        one = tc.buildLayeredView([base], {"SHA": ["chat", "chats"]})
        self.assertEqual(one.claimants, tc.buildPluvierView(base, {"SHA": ["chat", "chats"]}).claimants)

    def test_cheapest_outline(self) -> None:
        view = tc.TheoryView("t", {"w": ["A/B", "C", "BAD"], "v": ["Z/Y", "BAD/Y"]})
        view.choose(unitCost)
        self.assertEqual(view.chosen, {"w": "C", "v": "Z/Y"})


class TestMetrics(unittest.TestCase):
    def setUp(self) -> None:
        self.a = tc.TheoryView("a", {"star": ["S"], "tsar": ["TS"], "chat": ["C/H"], "only": ["O"]},
                               claimants={"S": frozenset({"star", "stars"})})
        self.b = tc.TheoryView("b", {"star": ["S"], "chat": ["C"], "rare": ["R"], "zzz": ["Z"]},
                               claimants={"C": frozenset({"chat", "chats"}), "S": frozenset({"star", "tsar"})})
        self.a.choose(unitCost)
        self.b.choose(unitCost)

    def test_coverage(self) -> None:
        cov = tc.coverage(FREQ, self.a, self.b)
        self.assertEqual(cov["both"]["spellings"], 2)
        self.assertEqual(cov["both"]["withFrequency"], 2)
        self.assertAlmostEqual(cov["both"]["frequencyShare"], 15 / 40)
        self.assertEqual(cov["aOnly"]["spellings"], 2)
        self.assertEqual(cov["bOnly"]["spellings"], 1)            # rare (zzz is outside the universe)
        self.assertEqual(cov["outsideUniverse"]["b"], 1)
        self.assertEqual(cov["neither"]["spellings"], 0)

    def test_collisions_and_strokes(self) -> None:
        common = {"star", "chat"}
        col = tc.collisions(self.b, FREQ, common)
        self.assertEqual(col["wordsColliding"], 2)
        self.assertEqual(col["groups"], 2)
        self.assertEqual(col["wordsInGroupsFullyCommon"], 0)
        self.assertEqual(tc.collisions(self.a, FREQ, common)["wordsColliding"], 1)
        # strokes per word over the common words: a has star 1, chat 2 -> (10 + 10) / 15
        self.assertAlmostEqual(tc.strokesPerWord(self.a, FREQ, common) or 0, 20 / 15)
        self.assertAlmostEqual(tc.strokesPerWord(self.b, FREQ, common) or 0, 1.0)

    def test_complexity_accounting(self) -> None:
        costs: dict[str, int | None] = {"star": 100, "chat": None, "tsar": 300}
        res = tc.complexity(costs, FREQ, {"star", "chat", "tsar"})
        self.assertAlmostEqual(res["meanCost"], (100 * 10 + 300 * 5) / 15)
        self.assertEqual(res["unpricedWords"], 1)
        self.assertAlmostEqual(res["unpricedFrequencyShare"], 5 / 20)
        both = tc.complexityBoth(costs, {"star": 200, "chat": 50, "tsar": None}, FREQ, {"star", "chat", "tsar"})
        self.assertEqual((both["words"], both["meanA"], both["meanB"]), (1, 100.0, 200.0))

    def test_collision_resolution(self) -> None:
        view = tc.TheoryView("c", {"star": ["S"], "tsar": ["S"], "chat": ["C"], "rare": ["R"]},
                             claimants={"S": frozenset({"star", "tsar"}), "C": frozenset({"chat", "chats"})})
        view.choose(unitCost)
        words = {"star", "tsar", "chat"}
        # the most frequent claimant keeps the outline (star 10 > tsar 5; chat 5 > chats, which has no frequency)
        self.assertEqual(tc.markedForResolution(view, FREQ, words, "winnerKeeps"), {"tsar"})
        self.assertEqual(tc.markedForResolution(view, FREQ, words, "everyClaimant"), {"star", "tsar", "chat"})
        # the keeper is chosen among all claimants, also those outside the words asked for
        self.assertEqual(tc.markedForResolution(view, FREQ, {"tsar"}, "winnerKeeps"), {"tsar"})
        self.assertEqual(tc.markedForResolution(view, {"star": 1.0, "tsar": 9.0}, {"star"}, "winnerKeeps"), {"star"})
        # equal frequencies: the alphabetically first claimant keeps the outline
        tie = tc.TheoryView("t", {"aa": ["X"], "bb": ["X"]}, claimants={"X": frozenset({"aa", "bb"})})
        tie.choose(unitCost)
        self.assertEqual(tc.markedForResolution(tie, {"aa": 1.0, "bb": 1.0}, {"aa", "bb"}, "winnerKeeps"), {"bb"})
        # a word without a colliding chosen outline is never marked
        self.assertEqual(tc.markedForResolution(view, FREQ, {"rare"}, "everyClaimant"), set())

    def test_resolved_strokes_and_costs(self) -> None:
        view = tc.TheoryView("c", {"star": ["S"], "tsar": ["S"], "chat": ["C"]})
        view.choose(unitCost)
        words = {"star", "tsar", "chat"}
        self.assertAlmostEqual(tc.strokesPerWordResolved(view, FREQ, words, {"tsar"}) or 0, (10 + 5 * 2 + 5) / 20)
        self.assertAlmostEqual(tc.strokesPerWordResolved(view, FREQ, words, set()) or 0, 1.0)
        costs: dict[str, int | None] = {"star": 100, "tsar": None, "chat": 100}
        self.assertEqual(tc.costsResolved(costs, {"tsar", "chat"}, 85), {"star": 100, "tsar": None, "chat": 185})
        res = tc.complexity(tc.costsResolved(costs, {"chat"}, 85), FREQ, words)
        self.assertAlmostEqual(res["meanCost"], (100 * 10 + 185 * 5) / 15)

    def test_outline_costs(self) -> None:
        self.assertEqual(tc.outlineCosts(self.a, unitCost, ["chat", "star"]), {"chat": 200, "star": 100})


class TestOrder(unittest.TestCase):
    def test_count_violations(self) -> None:
        self.assertEqual(tc.countViolations([(1,), (0,)]), 1)               # tsar on Ireland: T=1 then S=0
        self.assertEqual(tc.countViolations([(0,), (1,)]), 0)               # star: S then T
        self.assertEqual(tc.countViolations([(0, 1), (1, 2)]), 0)           # shared key is not a violation
        self.assertEqual(tc.countViolations([(3, 4), (1,), (5,)]), 1)

    def test_ireland_star_and_tsar(self) -> None:
        enc = tc.PluvierEncoder(os.path.join(ROOT, "resources", "pluvierPhonemeKeys.tsv"))
        star = enc.encodeWord("staR")
        tsar = enc.encodeWord("tsaR")
        assert star is not None and tsar is not None
        self.assertEqual(tc.pluvierViolations(star[0]), 0)
        self.assertEqual(tc.pluvierViolations(tsar[0]), 1)
        self.assertEqual(star[1], "STAR")
        self.assertIsNone(enc.encodeWord("xa"))                              # unencodable phoneme

    def test_diphthong_and_schwa(self) -> None:
        enc = tc.PluvierEncoder(os.path.join(ROOT, "resources", "pluvierPhonemeKeys.tsv"))
        froid = enc.encodeWord("fRwa")
        assert froid is not None
        self.assertEqual(froid[1], "TPROEU")
        le = enc.encodeWord("l°")
        assert le is not None
        self.assertEqual(le[1], "HR")

    def test_starboard_equivalent(self) -> None:
        board = Starboard.fromJSONFile(os.path.join(ROOT, "starboard3h.json"))
        assert board is not None
        self.assertEqual(tc.splitSyllable("stRa"), {"onset": ["s", "t", "R"], "nucleus": ["a"], "coda": []})
        groups = tc.starboardGroups(board, "sta")
        assert groups is not None
        self.assertEqual(groups, [(3,), (7,), (12,)])
        self.assertEqual(tc.countViolations(groups), 0)
        reverse = tc.starboardGroups(board, "tsa")
        assert reverse is not None
        self.assertEqual(tc.countViolations(reverse), 1)                    # t (7) before s (3): out of key order
        self.assertIsNone(tc.starboardGroups(board, "xa"))

    def test_order_summary(self) -> None:
        res = tc.orderViolations({"star": 0, "tsar": 2, "chat": None}, FREQ, {"star", "tsar", "chat"})
        self.assertAlmostEqual(res["shareWithViolation"], 5 / 15)
        self.assertAlmostEqual(res["meanViolations"], 10 / 15)
        self.assertEqual(res["unencodableWords"], 1)
        self.assertAlmostEqual(res["unencodableFrequencyShare"], 5 / 20)


if __name__ == "__main__":
    unittest.main()
