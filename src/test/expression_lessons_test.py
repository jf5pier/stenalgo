"""Unit tests for the expression lesson and sentence exporters (`util/export_expression_lessons.py`,
`util/export_expression_sentences.py`): the pure builders on a hand-made rule set and pool (the real inputs are
multi-MB artifacts), plus a consistency check of the committed trainer files when they exist."""

import json
import os

import pytest

import util.export_expression_lessons as lessonsModule
from src.affixes import PREFIX, SUFFIX, SimContext
from src.expressionrules import PoolExpression
from src.expressions import AttachRule, BriefRule, Rules, Token, composeOutlineTraced
from src.keyboard import Starboard
from util._stenorender import renderFinalStrokesToRTFCRE
from util.export_expression_lessons import (MAX_ALTERNATES, buildExpressionLessons, composeAll, partialOutlines,
                                            rankRules, ruleRanks)
from util.export_expression_sentences import wordStrokeCounts
from util.export_lessons import RECORD_FIELDS

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
IPA_MAPPED = set("E@°§5O9821RZSNG")

EST, IL = (13, 14), (13, 23)
CAFE = ((2, 12), (3, 14))             # a two-stroke word
DE_LONG, DEL_LONG, PAS_LONG = (4, 5, 11, 12), (4, 5), (9,)
CHORD = (17, 24)                      # one chord for the pair de / d'


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


def phrase(units: tuple[str, ...], freq: float, *tokens: Token) -> PoolExpression:
    return PoolExpression(units, freq, tokens)


RULES = Rules(
    attaches=(AttachRule(("de",), PREFIX, CHORD, "de", "base"), AttachRule(("d'",), PREFIX, CHORD, "de", "elided"),
              AttachRule(("pas",), SUFFIX, (9,), "pas")),
    briefs=(BriefRule(("il", "est"), ((8, 13, 14, 23),)),))

POOL = [
    phrase(("de", "cafe"), 90.0, tok("de", DE_LONG), tok("cafe", *CAFE)),
    phrase(("d'", "est"), 80.0, tok("d'", DEL_LONG), tok("est", EST)),
    phrase(("de", "cafe", "pas"), 70.0, tok("de", DE_LONG), tok("cafe", *CAFE), tok("pas", PAS_LONG)),
    phrase(("cafe", "pas"), 60.0, tok("cafe", *CAFE), tok("pas", PAS_LONG)),
    phrase(("il", "est"), 50.0, tok("il", IL), tok("est", EST)),
    phrase(("rien",), 40.0, tok("rien", (3,))),            # nothing shortens it: not in any lesson
]


@pytest.fixture
def document(ctx: SimContext, starboard: Starboard) -> dict:
    return buildExpressionLessons(RULES, POOL, ctx, starboard, {("de", "cafe"): "d°.ka.fe"})


def _lesson(document: dict, index: int) -> dict:
    return document["lessons"][index]


class TestRanking:
    def test_families_by_weighted_saving_and_rules_by_family(self, ctx):
        composed = composeAll(RULES, POOL, ctx)
        families, attaches, briefs = rankRules(RULES, composed)
        assert families == ["de", "pas"]                                    # de: 90+80+70, pas: 70+60
        assert [r.expression for r in attaches] == [("de",), ("d'",), ("pas",)]   # base form before the elided one
        assert [r.expression for r in briefs] == [("il", "est")]
        assert ruleRanks(RULES, POOL, ctx) == {attaches[0]: 1, attaches[1]: 2, attaches[2]: 3, briefs[0]: 4}

    def test_phrase_without_abbreviation_is_not_composed(self, ctx):
        assert ("rien",) not in {c.expr.units for c in composeAll(RULES, POOL, ctx)}


class TestDocument:
    def test_dense_ids_track_and_order(self, document):
        lessons = document["lessons"]
        assert [x["id"] for x in lessons] == [f"expressions-{i:02d}" for i in range(1, len(lessons) + 1)]
        assert {x["track"] for x in lessons} == {"expressions"} == {x["kind"] for x in lessons}
        titles = [x["title"] for x in lessons]
        assert titles[0] == "Leçon un : « de » · « d' »"             # the elision pair shares one lesson
        assert titles[1] == "Leçon deux : « pas »"

    def test_family_lesson_keys_and_one_piece_phrases(self, document):
        de = _lesson(document, 0)
        assert de["newKeys"] == [17, 24] and de["newChords"] == [[17, 24]]
        assert [w["ortho"] for w in de["words"][:2]] == ["de cafe", "d'est"]   # (-frequency); elided unit glued
        assert de["words"][0]["phonology"] == "d°.ka.fe"

    def test_rules_list_is_the_legend(self, document):
        rules = document["rules"]
        assert [(r["rank"], r["kind"]) for r in rules] == [(1, "attach"), (2, "attach"), (3, "attach"), (4, "brief")]
        assert rules[0]["label"] == "« de » ou « d' » : se joint au mot suivant"
        assert rules[2]["label"] == "« pas » : se joint au mot précédent"
        assert rules[3]["steno"] and rules[3]["units"] == ["il", "est"]

    def test_word_records_follow_the_practice_words_shape(self, document):
        for lesson in document["lessons"]:
            for word in lesson["words"]:
                assert tuple(word)[:len(RECORD_FIELDS)] == RECORD_FIELDS
                assert set(word) == set(RECORD_FIELDS) | {"alternates", "ruleRanks"}
                assert all(set(a) == {"steno", "strokes"} for a in word["alternates"])
                assert word["steno"] not in [a["steno"] for a in word["alternates"]]

    def test_longform_always_accepted_and_alternates_unique(self, document, starboard):
        words = {w["ortho"]: w for lesson in document["lessons"] for w in lesson["words"]}
        cafe = words["de cafe"]
        longform = renderFinalStrokesToRTFCRE(starboard, (DE_LONG, *CAFE))
        assert longform in [a["steno"] for a in cafe["alternates"]]
        for word in words.values():
            stenos = [a["steno"] for a in word["alternates"]]
            assert len(stenos) == len(set(stenos)) <= MAX_ALTERNATES

    def test_composed_lesson_holds_multi_piece_phrases(self, document):
        composed = [x for x in document["lessons"] if x["sectionTitle"] == lessonsModule.SECTION_COMPOSED]
        assert [w["ortho"] for x in composed for w in x["words"]] == ["de cafe pas"]
        assert composed[0]["title"] == "Leçon trois : les phrases composées, partie un"
        assert composed[0]["words"][0]["ruleRanks"] == [1, 3]
        assert composed[0]["newKeys"] == []

    def test_partial_compositions_are_accepted(self, ctx, starboard):
        item = next(c for c in composeAll(RULES, POOL, ctx) if c.expr.units == ("de", "cafe", "pas"))
        partials = partialOutlines(RULES, item, ctx)
        assert len(partials) == 2 and item.comp.strokes not in partials and item.longform not in partials
        only = lambda rule: composeOutlineTraced(Rules(attaches=(rule,)), item.expr.tokens, ctx).strokes  # noqa: E731
        assert set(partials) == {only(RULES.attaches[0]), only(RULES.attaches[2])}

    def test_brief_lessons_by_frequency_with_the_brief_stroke_as_hint(self, ctx, starboard, monkeypatch):
        monkeypatch.setattr(lessonsModule, "BRIEFS_PER_LESSON", 1)
        monkeypatch.setattr(lessonsModule, "BRIEF_LESSONS", 4)
        document = buildExpressionLessons(RULES, POOL, ctx, starboard)
        briefs = [x for x in document["lessons"] if x["sectionTitle"] == lessonsModule.SECTION_BRIEFS]
        assert [w["ortho"] for x in briefs for w in x["words"]] == ["il est"]
        word = briefs[0]["words"][0]
        assert word["strokes"] == [[8, 13, 14, 23]] and word["ruleRanks"] == [4]

    def test_regeneration_is_identical(self, ctx, starboard):
        first = buildExpressionLessons(RULES, POOL, ctx, starboard)
        second = buildExpressionLessons(RULES, list(reversed(POOL)), ctx, starboard)
        assert json.dumps(first, ensure_ascii=False) == json.dumps(second, ensure_ascii=False)

    def test_prose_has_no_ipa_mapped_character(self, document):
        strings: list[str] = []
        for lesson in document["lessons"]:
            strings += [lesson["title"], lesson["sectionTitle"], *(r["text"].split(" : ", 1)[0] for r in lesson["rules"][:1])]
            strings += [word["label"] for word in lesson["words"]]
        strings += [r["label"] for r in document["rules"]]
        for text in strings:
            assert not set(text) & IPA_MAPPED, text
            assert not any(ch.isdigit() for ch in text), text


class TestSentenceSegmentation:
    def test_merged_particle_owns_no_stroke_and_the_counts_add_up(self, ctx):
        tokens = (tok("d'", DEL_LONG), tok("est", EST), tok("cafe", *CAFE))
        comp = composeOutlineTraced(RULES, tokens, ctx)
        assert wordStrokeCounts(comp, tokens) == [0, 1, 2]

    def test_brief_puts_its_strokes_on_the_first_token(self, ctx):
        tokens = (tok("il", IL), tok("est", EST), tok("cafe", *CAFE))
        comp = composeOutlineTraced(RULES, tokens, ctx)
        assert wordStrokeCounts(comp, tokens) == [1, 0, 2]

    def test_exception_keeps_the_longform_strokes(self, ctx):
        tokens = (tok("de", DE_LONG), tok("est", EST))          # `de` before a vowel word cannot join (elision rule)
        comp = composeOutlineTraced(RULES, tokens, ctx)
        assert wordStrokeCounts(comp, tokens) == [1, 1]


@pytest.mark.skipif(not os.path.exists(os.path.join(ROOT, "steno-trainer/public/data/expression-lessons.json")),
                    reason="expression trainer data not generated")
class TestCommittedFiles:
    def _load(self, name: str):
        with open(os.path.join(ROOT, "steno-trainer/public/data", name), encoding="utf-8") as f:
            return json.load(f)

    def test_rule_ranks_resolve_in_the_rules_list(self):
        lessons = self._load("expression-lessons.json")
        ranks = {r["rank"] for r in lessons["rules"]}
        assert ranks == set(range(1, len(ranks) + 1))
        for lesson in lessons["lessons"]:
            for word in lesson["words"]:
                assert word["ruleRanks"] and set(word["ruleRanks"]) <= ranks

    def test_sentences_are_consistent_with_their_words(self):
        path = os.path.join(ROOT, "steno-trainer/public/data/expression-sentences.json")
        if not os.path.exists(path):
            pytest.skip("expression sentences not generated")
        ranks = {r["rank"] for r in self._load("expression-lessons.json")["rules"]}
        for sentence in self._load("expression-sentences.json"):
            assert len(sentence["strokes"]) == sum(w["strokeCount"] for w in sentence["words"])
            assert sentence["alternates"] and set(sentence["ruleRanks"]) <= ranks
            assert len(sentence["alternates"][0]["strokes"]) > len(sentence["strokes"])
