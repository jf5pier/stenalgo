"""Differential test: the lean per-key sweep (`sweepKey`, `simulateRuleUnits`) must equal the old
`resolveFallbacks` + `simulate` + `ruleScoreFromResults` path bit for bit, on collision-heavy random records."""
import random

import pytest

from src.affixbinding import enumerateKeypresses, phonemeKeys
from src.affixes import (
    PREFIX, RULE, SUFFIX, Binding, Candidate, Carrier, SimContext, WordRecord, makeSimUnit, mergeUnions,
    poolCarriers, simulate, simulateRuleUnits)
from src.affixrules import (
    Rule, _exceptionRate, prepareKeySweep, resolveFallbacks, ruleScoreFromResults, sweepKey)
from src.keyboard import Starboard


def _records(rng: random.Random, alphabet: list[int], n: int) -> list[WordRecord]:
    strokes = [(a,) for a in alphabet] + [tuple(sorted((a, b))) for a in alphabet[:4] for b in alphabet[4:7]]
    recs: list[WordRecord] = []
    for i in range(n):
        length = rng.choice([1, 2, 2, 3, 3, 4])
        base = tuple(rng.choice(strokes[:6]) if rng.random() < 0.6 else rng.choice(strokes) for _ in range(length))
        if recs and rng.random() < 0.25:                     # a homophone (shared base)
            other = rng.choice(recs)
            base = other.base
            lemme = other.lemme if rng.random() < 0.3 else f"w{i}"   # same lemme / different base -> lostDistinction
        else:
            lemme = f"w{i}"
        if recs and rng.random() < 0.1:                      # same lemme, other base
            lemme = rng.choice(recs).lemme
        ortho = f"o{i}" if rng.random() < 0.9 else rng.choice(recs).ortho if recs else f"o{i}"
        recs.append(WordRecord(
            idx=i + 1, ortho=ortho, lemme=lemme, gramCat="NOM", frequency=float(rng.randint(1, 500)) / 7,
            phonoSylls=tuple("x" * len(base)), orthoSylls=tuple("y" * len(base)),
            base=base, extra=(), isLemmaForm=(ortho == lemme)))
    return recs


def _rule(position: str, recs: list[WordRecord]) -> Rule:
    anchorCs, scopedCs = [], []
    for r in recs:
        n = len(r.base)
        if n < 2:
            continue
        start = 0 if position == PREFIX else n - 1
        anchorCs.append(Carrier(r, start, 1, "s"))
        if n >= 3 and r.idx % 2 == 0:
            scopedCs.append(Carrier(r, 0 if position == PREFIX else n - 2, 2, "s"))
    # a few single-syllable carriers (standaloneTrap)
    for r in recs:
        if len(r.base) == 1 and r.idx % 3 == 0:
            anchorCs.append(Carrier(r, 0, 1, "s"))
    root = Candidate(position, 1, "x", "a", carriers=anchorCs, isAnchor=True)
    child = Candidate(position, 2, "x.x", "b", carriers=scopedCs, isScoped=True)
    return Rule(position, root, [root, child])


@pytest.mark.parametrize("position", [PREFIX, SUFFIX])
@pytest.mark.parametrize("seed", [1, 2])
def test_sweepKey_equals_old_path_for_every_keypress(position, seed):
    sb = Starboard.fromJSONFile("starboard3h.json")
    assert sb is not None
    rng = random.Random(seed)
    keysAll = phonemeKeys(sb)
    recs = _records(rng, list(keysAll[:9]), 260)
    ctx = SimContext(sb, recs)
    rule = _rule(position, recs)
    carriers = poolCarriers(rule.forms)
    assert any(c.span > 1 for c in carriers)
    sw = prepareKeySweep(rule, carriers, ctx)
    keypresses = enumerateKeypresses(sb, ctx)
    # include a key equal to a single-stroke outline (trap)
    trapStroke = next((o[0] for o in ctx.finalOutlines if len(o) == 1), None)
    if trapStroke is not None and trapStroke not in keypresses:
        keypresses = keypresses + [trapStroke]
    reasonsSeen: set[str | None] = set()
    for sample in (50, None):
        cs = carriers if sample is None else carriers[:sample]
        for k in keypresses[::3] if sample else keypresses:
            csK, nf = resolveFallbacks(rule, k, cs, ctx)
            (res,) = simulate([(Binding(position, RULE, k), csK)], ctx, boundaryRisk=False)
            sc = ruleScoreFromResults(res, sw.exclusionCount + nf, len(rule.forms))[0]
            assert sweepKey(sw, k, sample) == (sc, _exceptionRate(res), nf)
            reasonsSeen.update(r.reason for r in res)
    assert {"lostDistinction", "noNeighbour"} <= reasonsSeen or len(reasonsSeen) >= 3


@pytest.mark.parametrize("position", [PREFIX, SUFFIX])
def test_simulateRuleUnits_matches_simulate_gains_and_reasons(position):
    sb = Starboard.fromJSONFile("starboard3h.json")
    assert sb is not None
    rng = random.Random(7)
    recs = _records(rng, list(phonemeKeys(sb)[:8]), 200)
    ctx = SimContext(sb, recs)
    rule = _rule(position, recs)
    carriers = poolCarriers(rule.forms)
    ids: dict = {}
    units = [makeSimUnit(position, c, ctx, ids) for c in carriers]
    neighbours = list(ids)
    for k in enumerateKeypresses(sb, ctx)[::7]:
        X = mergeUnions(neighbours, k, ctx)
        D = tuple(sorted(k))
        gains, reasons = simulateRuleUnits(units, ctx, X, D, D in ctx.singleStrokeOutlines)
        (res,) = simulate([(Binding(position, RULE, k), carriers)], ctx, boundaryRisk=False)
        assert gains == [r.gain for r in res]
        assert reasons == [r.reason for r in res]
