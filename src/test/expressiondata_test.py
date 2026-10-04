import random
import unittest

from src.affixes import SimContext
from src.expressiondata import ChordLegality, bundleToDict, legalityFromStarboard, loadBundle
from src.expressions import AttachRule, BriefRule, Rules
from src.keyboard import Starboard
from src.keyconflicts import KeyConflicts


class TestExpressionData(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.starboard = Starboard.fromJSONFile("starboard3h.json")
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
        doc = bundleToDict(rules, {((1, 2),): ["mot"]}, {"mot": 1}, {(((1, 2),), (("content", ("mot",), False, (), (), ()),)): 2.0},
                           {"mot": 0.5}, KeyConflicts(), self.legality)
        decoder, ranker = loadBundle(doc)
        self.assertEqual(decoder.rules, rules)
        self.assertEqual(ranker.unitProbability, {"mot": 0.5})
        self.assertEqual(list(ranker.attested.values()), [2.0])
        (reading,) = decoder.decode(((1, 2),))
        self.assertEqual(reading[0].units, ("mot",))
