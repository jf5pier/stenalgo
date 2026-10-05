import random
import unittest

from src.affixes import SimContext
from src.expressiondata import (ChordLegality, bundleToDict, legalityFromStarboard, loadBundle,
                                wordIndexFingerprint)
from src.expressions import AttachRule, BriefRule, Rules
from src.keyboard import Starboard, Strokes
from src.keyconflicts import KeyConflicts


class TestExpressionData(unittest.TestCase):
    starboard: Starboard
    ctx: SimContext
    legality: ChordLegality

    @classmethod
    def setUpClass(cls) -> None:
        loaded = Starboard.fromJSONFile("starboard3h.json")
        assert loaded is not None
        cls.starboard = loaded
        cls.ctx = SimContext(cls.starboard, [])
        cls.legality = legalityFromStarboard(cls.starboard)

    def test_legality_matches_simcontext(self) -> None:
        rng = random.Random(7)
        for _ in range(4000):
            keys = tuple(sorted(rng.sample(range(26), rng.randint(1, 7))))
            self.assertEqual(self.legality(keys), self.ctx.isLegal(keys), keys)

    def test_legality_survives_json(self) -> None:
        again = ChordLegality.fromDict(self.legality.toDict())
        rng = random.Random(8)
        for _ in range(500):
            keys = tuple(sorted(rng.sample(range(26), rng.randint(1, 6))))
            self.assertEqual(again(keys), self.legality(keys))

    def test_bundle_round_trip(self) -> None:
        rules = Rules(attaches=(AttachRule(("de",), "prefix", (3, 4)),),
                      briefs=(BriefRule(("a", "b"), ((5,),)),))
        mot: dict[Strokes, list[str]] = {((1, 2),): ["mot"]}
        doc = bundleToDict(rules, mot, {"mot": 1}, {(((1, 2),), (("content", ("mot",), False, (), (), ()),)): 2.0},
                           {"mot": 0.5}, KeyConflicts(), self.legality)
        decoder, ranker = loadBundle(doc)
        self.assertEqual(decoder.rules, rules)
        self.assertEqual(ranker.unitProbability, {"mot": 0.5})
        self.assertEqual(list(ranker.attested.values()), [2.0])
        (reading,) = decoder.decode(((1, 2),))
        self.assertEqual(reading[0].units, ("mot",))

    def test_word_index_from_a_file_is_fingerprinted(self) -> None:
        rules = Rules(attaches=(AttachRule(("de",), "prefix", (3, 4)),))
        words: dict[Strokes, list[str]] = {((1, 2),): ["mot"], ((5,),): ["a", "b"]}
        doc = bundleToDict(rules, words, {}, {}, {}, KeyConflicts(), self.legality, wordsFile="stock.json")
        self.assertNotIn("words", doc)
        self.assertEqual(doc["wordIndex"]["count"], 2)
        decoder, _ranker = loadBundle(doc, words)
        self.assertEqual(decoder.decode(((1, 2),))[0][0].units, ("mot",))
        with self.assertRaises(ValueError):                       # the index was not passed
            loadBundle(doc)
        with self.assertRaises(ValueError):                       # another theory's index
            other: dict[Strokes, list[str]] = {((1, 2),): ["mot"], ((5,),): ["a", "c"]}
            loadBundle(doc, other)

    def test_fingerprint_ignores_order_and_duplicates(self) -> None:
        a: dict[Strokes, list[str]] = {((1,),): ["x", "y"], ((2,),): ["z"]}
        b: dict[Strokes, list[str]] = {((2,),): ["z", "z"], ((1,),): ["y", "x"]}
        self.assertEqual(wordIndexFingerprint(a), wordIndexFingerprint(b))
        c: dict[Strokes, list[str]] = {((1,),): ["x"], ((2,),): ["z"]}
        self.assertNotEqual(wordIndexFingerprint(a), wordIndexFingerprint(c))

    def test_unit_strokes_keep_only_attach_particles(self) -> None:
        rules = Rules(attaches=(AttachRule(("il", "n'"), "prefix", (3, 4)),))
        mot: dict[Strokes, list[str]] = {((1,),): ["mot"]}
        doc = bundleToDict(rules, mot, {"il": 1, "n'": 1, "mot": 1, "autre": 2}, {}, {},
                           KeyConflicts(), self.legality)
        self.assertEqual(doc["unitStrokes"], {"il": 1, "n'": 1})
