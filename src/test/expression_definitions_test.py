"""Unit tests for the Definitions page's expression entries (`util/export_expression_definitions.py`): the pure
builder on a hand-made rule set and pool (the real inputs are multi-MB artifacts)."""

import os

import pytest

from src.affixes import PREFIX, SimContext
from src.expressionrules import PoolExpression
from src.expressions import AttachRule, Rules, Token
from src.keyboard import Starboard
from util.export_expression_definitions import buildExpressionDefinitions

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
CHORD = (17, 24)
LA_CHORD = (3, 12)
DE_LONG, LA_LONG, CAFE_LONG = (4, 5, 11, 12), (6, 7, 12), (2, 12)


@pytest.fixture
def starboard() -> Starboard:
    board = Starboard.fromJSONFile(os.path.join(ROOT, "starboard3h.json"))
    assert board is not None
    return board


@pytest.fixture
def ctx(starboard: Starboard) -> SimContext:
    context = SimContext(starboard, [])
    context.finalOutlines = set()
    context.singleStrokeOutlines = set()
    return context


def tok(unit: str, *strokes: tuple[int, ...]) -> Token:
    return Token(unit, tuple(strokes))


RULES = Rules(attaches=(AttachRule(("de",), PREFIX, CHORD, "de", "base"),
                        AttachRule(("la",), PREFIX, LA_CHORD, "la")))
POOL = [
    PoolExpression(("de", "cafe"), 90.0, (tok("de", DE_LONG), tok("cafe", CAFE_LONG))),
    PoolExpression(("de", "la"), 80.0, (tok("de", DE_LONG), tok("la", LA_LONG))),
    PoolExpression(("rien",), 10.0, (tok("rien", (3,)),)),
]


@pytest.fixture
def document(ctx: SimContext, starboard: Starboard) -> dict:
    return buildExpressionDefinitions(RULES, POOL, ctx, starboard, {("de", "cafe"): "d°.ka.fe"}, {"de": "d°"})


class TestAttaches:
    def test_one_entry_per_rule_with_its_keypress(self, document, starboard):
        de = next(a for a in document["attaches"] if a["text"] == "de")
        assert de["keys"] == [17, 24] and de["position"] == PREFIX and de["phonology"] == "d°"
        assert de["keyNames"] == [starboard.keyDisplayName(17), starboard.keyDisplayName(24)]
        assert de["steno"]                                          # the keypress alone, parsed back by the trainer

    def test_examples_are_the_phrases_the_rule_shortens(self, document):
        de = next(a for a in document["attaches"] if a["text"] == "de")
        assert [e["text"] for e in de["examples"]] == ["de cafe", "de la"]     # most frequent first, rien excluded
        assert de["examples"][0]["phonology"] == "d°.ka.fe"
        assert de["examples"][0]["steno"] != de["examples"][0]["longform"]


class TestPhrases:
    def test_composed_phrases_listed_with_both_outlines(self, document):
        texts = [p["text"] for p in document["phrases"]]
        assert texts == ["de cafe", "de la"] and "rien" not in texts
        assert all(p["steno"] and p["longform"] and p["label"] for p in document["phrases"])
