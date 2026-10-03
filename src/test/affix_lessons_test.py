"""Unit tests for the affix lesson exporter `util/export_affix_lessons.py`: the pure builder on hand-made
abbreviations (the real inputs are multi-MB artifacts the unit tests must not depend on)."""

import json
import os
import re

import pytest

from ..affixabbrev import Abbreviation, RuleSpec
from ..keyboard import Starboard
from util.export_affix_lessons import WORDS_PER_LESSON, buildAffixLessons, isVerb, ruleLabel
from util.export_lessons import RECORD_FIELDS


@pytest.fixture
def starboard() -> Starboard:
    path = os.path.join(os.path.dirname(__file__), "..", "..", "starboard3h.json")   # the committed layout
    board = Starboard.fromJSONFile(path)
    assert board is not None
    return board


RULES = [
    RuleSpec(1, "prefix", "re|reh", "R°", (9, 18)),
    RuleSpec(2, "suffix", "ment", "m@", (16, 20, 25)),
    RuleSpec(3, "prefix", "x", "ks", (3,)),          # one key, no carrier below
]


def _abbr(ortho: str, rank: int, freq: float, route: int = 0, gramCat: str = "NOM", saved: int = 1,
          idx: int = 0) -> Abbreviation:
    return Abbreviation(ortho, ((9, 12), (13,)), ((3,), (12,), (13,)), saved, rank, "re", 1, freq, route, idx, gramCat)


def _abbreviations() -> list[Abbreviation]:
    out = [_abbr(f"re{i:02d}", 1, 100 - i, idx=i) for i in range(30)]
    out += [_abbr("rapidement", 2, 5.0, idx=100), _abbr("lentement", 2, 7.0, idx=101, saved=2)]
    out += [_abbr("refait", 1, 1000.0, route=1, gramCat="VER", idx=102), _abbr("reine", 1, 900.0, route=1, idx=103)]
    return out


def _build(starboard):
    return buildAffixLessons(RULES, _abbreviations(), starboard, {})


def test_one_lesson_per_rule_with_carriers_then_verbs(starboard):
    doc = _build(starboard)
    assert [r["rank"] for r in doc["rules"]] == [1, 2, 3]
    assert [l["id"] for l in doc["lessons"]] == ["affixes-01", "affixes-02", "affixes-03"]   # rule 3 skipped, ids dense
    assert [l["index"] for l in doc["lessons"]] == [1, 2, 3]
    assert all(l["track"] == "affixes" == l["kind"] for l in doc["lessons"])


def test_words_top_frequency_route_zero_only(starboard):
    first = _build(starboard)["lessons"][0]
    words = first["words"]
    assert len(words) == WORDS_PER_LESSON
    freqs = [w["frequency"] for w in words]
    assert freqs == sorted(freqs, reverse=True)
    assert "refait" not in [w["ortho"] for w in words]       # route 1 is for the last lesson only


def test_verb_lesson_is_ver_only_and_route_ge_one(starboard):
    last = _build(starboard)["lessons"][-1]
    assert [w["ortho"] for w in last["words"]] == ["refait"]
    assert last["newKeys"] == [] and last["newChords"] == []


def test_word_record_shape_and_alternates(starboard):
    word = _build(starboard)["lessons"][1]["words"][0]
    assert list(word)[:len(RECORD_FIELDS)] == list(RECORD_FIELDS) and "alternates" in word
    assert word["strokes"] == [[9, 12], [13]]
    assert word["alternates"] == [[[3], [12], [13]]]
    assert all(stroke == sorted(stroke) for stroke in word["strokes"] + word["alternates"][0])
    assert word["before"] == word["after"] == ""


def test_new_chords_rule(starboard):
    lessons = _build(starboard)["lessons"]
    assert lessons[0]["newChords"] == [[9, 18]] and lessons[0]["newKeys"] == [9, 18]
    assert lessons[1]["newChords"] == [[16, 20, 25]]


def test_prose_has_no_mapped_digits(starboard):
    for lesson in _build(starboard)["lessons"]:
        prose = [lesson["title"], lesson["sectionTitle"]] + [w["label"] for w in lesson["words"]]
        assert not any(re.search("[12589]", p) for p in prose), prose
    assert all(not re.search("[12589]", r["label"]) for r in _build(starboard)["rules"])


def test_deterministic(starboard):
    a = json.dumps(_build(starboard), ensure_ascii=False)
    assert a == json.dumps(buildAffixLessons(RULES, list(reversed(_abbreviations())), starboard, {}), ensure_ascii=False)


def test_rule_label_and_helpers():
    assert ruleLabel(RULES[0]) == "préfixe « re- » (aussi reh-)"
    assert ruleLabel(RULES[1]) == "suffixe « -ment »"
    assert isVerb("VER") and not isVerb("NOM")


def test_empty_rules_gives_no_lesson(starboard):
    assert buildAffixLessons([], [], starboard, {}) == {"rules": [], "lessons": []}
