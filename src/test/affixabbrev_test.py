"""Tests for src/affixabbrev.py -- hand-built records, no pickles."""
import json

import pytest

import src.affixes as A
from src.affixabbrev import RuleSpec, buildAbbreviations, loadRuleSpecs
from src.affixes import PREFIX, Candidate, Carrier, SimContext, WordRecord
from src.keyboard import Starboard

_idx = [9000]
KEYS = (4,)


def _sb():
    sb = Starboard.fromJSONFile("starboard3h.json")
    assert sb is not None
    return sb


def _rec(ortho, base, freq=10.0, marks=(), extra=()):
    _idx[0] += 1
    return WordRecord(
        idx=_idx[0], ortho=ortho, lemme=ortho, gramCat="NOM", frequency=freq, phonoSylls=tuple("x" * len(base)),
        orthoSylls=tuple(ortho[i:i + 1] for i in range(len(base))), base=tuple(base), extra=tuple(extra),
        isLemmaForm=True, markKeys=tuple(marks))


def _pool(*words, forms=()):
    root = Candidate(PREFIX, 1, "x", "a", carriers=[Carrier(w, 0, 1, "s") for w in words], isAnchor=True,
                     hasDecision=True)
    pool = {(PREFIX, 1, "x", "a"): root}
    for i, (label, carriers) in enumerate(forms):
        form = Candidate(PREFIX, 2, "x.y", label, carriers=carriers, isScoped=True, grownFromKey=(PREFIX, 1, "x", "a"))
        pool[(PREFIX, 2, "x.y", label)] = form
    return pool


def _run(pool, words, taken=()):
    ctx = SimContext(_sb(), words)
    long = {w.idx: A.canonicalizeStrokes(A.fullStrokesOf(w)) for w in words}
    return buildAbbreviations([RuleSpec(1, PREFIX, "a", "x", KEYS)], pool, ctx, set(taken), long)


def test_a_free_outline_gets_an_abbreviation_and_the_long_form_is_kept():
    w = _rec("aabc", [(2,), (3,), (7,)])
    abbr, stats = _run(_pool(w), [w])
    (a,) = abbr
    assert a.outline == ((3, 4), (7,)) and a.longOutline == ((2,), (3,), (7,)) and a.saved == 1 and a.k == 1
    assert stats.carriers == 1 and stats.abbreviated == 1 and stats.noOption == 0


def test_an_outline_of_the_stable_theory_is_never_taken():
    w = _rec("aabc", [(2,), (3,), (7,)])
    abbr, stats = _run(_pool(w), [w], taken=[((3, 4), (7,))])
    assert abbr == [] and stats.noOption == 1


def test_the_words_own_marks_are_kept():
    w = _rec("aabc", [(2,), (3,), (7,)], marks=(10,))
    (a,), _ = _run(_pool(w), [w])
    assert a.outline == ((3, 4), (7, 10))


def test_two_spellings_on_one_outline_the_more_frequent_keeps_it():
    big = _rec("aabc", [(2,), (3,), (7,)], freq=50.0)
    small = _rec("aabd", [(5,), (3,), (7,)], freq=1.0)
    # both abbreviate to ((3, 4), (7,)): the first stroke is replaced by the rule key
    abbr, stats = _run(_pool(big, small), [big, small])
    assert [a.ortho for a in abbr] == ["aabc"] and stats.outranked == 1


def test_a_growth_form_wins_and_falls_back_to_the_anchor_when_it_collides():
    w = _rec("aabcd", [(2,), (3,), (7,), (9,)], freq=100.0)
    grown = Carrier(w, 0, 2, "s")
    ctx = SimContext(_sb(), [w])
    binding = A.Binding(PREFIX, A.RULE, KEYS)
    longForm, _w, _m = A._newBase(binding, grown, ctx)
    assert longForm is not None
    pool = _pool(w, forms=[("a[b]·", [grown])])
    (a,), _ = _run(pool, [w])
    assert a.k == 2 and a.saved == 2 and a.outline == longForm
    (b,), _ = _run(pool, [w], taken=[longForm])
    assert b.k == 1 and b.saved == 1


def test_a_rule_whose_anchor_vanished_is_skipped_with_a_record_not_a_crash():
    w = _rec("aabc", [(2,), (3,), (7,)])
    ctx = SimContext(_sb(), [w])
    long = {w.idx: A.canonicalizeStrokes(A.fullStrokesOf(w))}
    abbr, stats = buildAbbreviations(
        [RuleSpec(1, PREFIX, "zz", "q", KEYS), RuleSpec(2, PREFIX, "a", "x", KEYS)], _pool(w), ctx, set(), long)
    assert stats.skippedRules == [1] and [a.rank for a in abbr] == [2]


def test_load_rule_specs(tmp_path):
    p = tmp_path / "r.json"
    p.write_text(json.dumps([{"rank": 2, "position": "suffix", "ortho": "ment", "phono": "m@", "keys": [16, 20, 25]}]))
    assert loadRuleSpecs(str(p)) == [RuleSpec(2, "suffix", "ment", "m@", (16, 20, 25))]
