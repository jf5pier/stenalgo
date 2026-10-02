"""Tests for src/affixes.py -- hand-built records, no pickles."""
import src.affixes as A
from src.affixes import (
    DEDICATED, MERGED, PREFIX, RULE, SUFFIX, Binding, Candidate, Carrier, LemmaIndex, SimContext, WordRecord,
    buildCandidates, inheritedSpan, markCostForCluster, norm, passesPrefixFilter, passesSuffixFilter,
    poolKnownAffixGroups, simulate)
from src.keyboard import Starboard

_idx = [0]


def rec(ortho, base, lemme=None, freq=10.0, extra=()):
    _idx[0] += 1
    lemme = lemme or ortho
    return WordRecord(
        idx=_idx[0], ortho=ortho, lemme=lemme, gramCat="NOM", frequency=freq,
        phonoSylls=tuple("x" * len(base)), orthoSylls=tuple(ortho[i:i + 1] for i in range(len(base))),
        base=tuple(base), extra=tuple(extra), isLemmaForm=(ortho == lemme))


def _sb():
    sb = Starboard.fromJSONFile("starboard3h.json")
    assert sb is not None
    return sb


def _wordRec(orthoSylls, phonoSylls, strokes, lemme=None, freq=10.0):
    """A record with real syllables AND caller-chosen per-syllable strokes -- collisions are
    decided by the remaining stem stroke, so tests must control it (`syllRec`'s auto-numbered base
    makes every same-length record collide)."""
    _idx[0] += 1
    ortho = "".join(orthoSylls)
    return WordRecord(
        idx=_idx[0], ortho=ortho, lemme=lemme or ortho, gramCat="NOM", frequency=freq,
        phonoSylls=tuple(phonoSylls), orthoSylls=tuple(orthoSylls),
        base=tuple((s,) for s in strokes), extra=(), isLemmaForm=(lemme is None or lemme == ortho))


_STEMS = ["abcd", "bcdf", "cdfg", "dfgh", "fghj", "ghjk", "hjkl", "jklm", "klmn", "lmnp"]


def _tailWords(tailOrtho, tailPhono, stems, strokeBase=100, freq=10.0):
    return [_wordRec((st, tailOrtho), (st, tailPhono), (strokeBase + i, 900), freq=freq)
            for i, st in enumerate(stems)]


class TestSingleGenerator:
    """Plan 2026-09-28: k=1 anchors + A8 + variant merges + lattice growth, nothing else."""

    def test_only_k1_anchors_and_an_unattested_stem_still_carries(self):
        words = _tailWords("ment", "m@", _STEMS[:6])
        lemmaOfFirstStem = _wordRec(("abcd", "if"), ("abcd", "if"), (500, 501))   # attests "abcd" only
        pool = buildCandidates(words + [lemmaOfFirstStem], A.loadSeeds()[0], excludeTopWords=False)
        ment = pool[(SUFFIX, 1, "m@", "ment")]
        assert ment.isAnchor and ment.k == 1 and len(ment.carriers) == 6
        # no stem-attestation gate: the five words whose stem is no lemma still carry ...
        assert {c.rec.ortho for c in ment.carriers} == {w.ortho for w in words}
        # ... and the old filter is only a reported statistic: 1 of 6 equal-frequency words
        assert abs(ment.attestedShare - 1 / 6) < 1e-9
        assert all(c.isAnchor for c in pool.values() if c.grownFromKey is None)
        assert not any(c.isGeneralized and c.grownFromKey is None and not c.mergeParts
                       for c in pool.values())     # no A7 node

    def test_no_decision_means_no_growth(self):
        from src.affixdecisions import Decisions
        words = _tailWords("ment", "m@", _STEMS[:6])
        pool = buildCandidates(words, A.loadSeeds()[0], excludeTopWords=False, decisions=Decisions())
        assert pool and all(c.k == 1 and c.isAnchor and not c.hasDecision for c in pool.values())

    def test_a_decided_anchor_gets_exactly_its_decided_forms(self):
        from src.affixdecisions import AnchorDecision, Decisions, ScopeForm
        words = [_wordRec((st, "bi", "ment"), (st, "bi", "m@"), (100 + i, 700, 900)) for i, st in enumerate(_STEMS[:6])]
        dec = Decisions([AnchorDecision(SUFFIX, "ment", "m@", "-", [ScopeForm("any")])])
        pool = buildCandidates(words, A.loadSeeds()[0], excludeTopWords=False, decisions=dec)
        assert pool[(SUFFIX, 1, "m@", "ment")].hasDecision
        grown = [c for c in pool.values() if c.k == 2]
        assert len(grown) == 1 and grown[0].isScoped and grown[0].ortho == "·[any]ment"

    def test_a_variant_merge_unions_carriers_and_keeps_its_parts(self):
        words = _tailWords("ment", "m@", _STEMS[:5]) + _tailWords("mant", "m@", _STEMS[5:], strokeBase=200)
        pool = buildCandidates(words, A.loadSeeds()[0], excludeTopWords=False)
        merged = pool[(SUFFIX, 1, "m@", "mant|ment")]
        assert merged.isAnchor and merged.isGeneralized and merged.variants == ["mant", "ment"]
        assert len(merged.carriers) == 10 and merged.newConflictFreq == 0
        assert len(merged.mergeParts) == 2 and all(k in pool for k in merged.mergeParts)

    def test_a_merge_that_creates_collisions_is_dropped(self):
        ments = _tailWords("ment", "m@", _STEMS[:5])
        # each `mant` word has the SAME remaining stem stroke as a `ment` word (different lemma):
        # fusing the two spellings would make them collide -> stay separate (U3a)
        mants = _tailWords("mant", "m@", _STEMS[5:], strokeBase=100)
        pool = buildCandidates(ments + mants, A.loadSeeds()[0], excludeTopWords=False)
        assert (SUFFIX, 1, "m@", "mant|ment") not in pool
        assert (SUFFIX, 1, "m@", "ment") in pool and (SUFFIX, 1, "m@", "mant") in pool




class TestMorphology:
    def test_prefix_filter(self):
        lem = LemmaIndex(["faire", "refaire", "nation"])
        assert passesPrefixFilter("faire", lem)          # re|faire
        assert not passesPrefixFilter("ation", lem)

    def test_suffix_filter_requires_attested_stem(self):
        lem = LemmaIndex(["nation", "national", "organiser", "organisation"])
        assert passesSuffixFilter("nation", "national", lem)    # nation|al
        assert not passesSuffixFilter("na", "nation", lem)       # too short / unattested
        assert passesSuffixFilter("organi", "organisation", lem)  # organi|sation -> organiser

    def test_norm(self):
        assert norm("Élève") == "eleve"[:-1]


class TestInheritance:
    def test_plural_inherits_full_span(self):
        L = rec("nation", [(1,), (2,), (3,)])
        w = rec("nations", [(1,), (2,), (3,)], lemme="nation")
        assert inheritedSpan(L, 2, w) == (1, 2)

    def test_conjugated_form_partial_span_tail_kept(self):
        L = rec("organiser", [(1,), (2,), (3,), (4,)])
        w = rec("organisons", [(1,), (2,), (3,), (9,), (8,)], lemme="organiser")
        assert inheritedSpan(L, 2, w) == (2, 1)   # only the first suffix stroke is identical

    def test_different_stem_inherits_nothing(self):
        L = rec("nation", [(1,), (2,), (3,)])
        w = rec("xxxs", [(5,), (2,), (3,)], lemme="nation")
        assert inheritedSpan(L, 2, w) is None




def syllRec(ortho, orthoSylls, phonoSylls, lemme=None, freq=5.0):
    """A record with real per-syllable ortho/phono, for tests that slice syllable tails."""
    _idx[0] += 1
    lemme = lemme or ortho
    return WordRecord(
        idx=_idx[0], ortho=ortho, lemme=lemme, gramCat="NOM", frequency=freq,
        phonoSylls=tuple(phonoSylls), orthoSylls=tuple(orthoSylls),
        base=tuple((i,) for i in range(1, len(orthoSylls) + 1)),
        extra=(), isLemmaForm=(ortho == lemme))




class TestKnownAffixGroups:
    def test_pools_co_con_com(self):
        co = Candidate(PREFIX, 1, "ko", "co",
                        carriers=[Carrier(syllRec("coopérer", ("co", "o", "pe", "re"), ("ko", "o", "pe", "Re")), 0, 1, "opérer")])
        con = Candidate(PREFIX, 1, "k§", "con",
                         carriers=[Carrier(syllRec("confiance", ("con", "fiance"), ("k§", "fj@s")), 0, 1, "fiance")])
        com = Candidate(PREFIX, 1, "k§", "com",
                         carriers=[Carrier(syllRec("comprendre", ("com", "prendre"), ("k§", "pR@dR")), 0, 1, "prendre")])
        unrelated = Candidate(PREFIX, 1, "vi", "vi",
                               carriers=[Carrier(syllRec("vivre", ("vi", "vre"), ("vi", "vR")), 0, 1, "vre")])
        cands = {(PREFIX, 1, "ko", "co"): co, (PREFIX, 1, "k§", "con"): con,
                 (PREFIX, 1, "k§", "com"): com, (PREFIX, 1, "vi", "vi"): unrelated}
        pooled = poolKnownAffixGroups(cands)
        gen = [c for c in pooled.values() if c.isGeneralized]
        assert len(gen) == 1
        assert gen[0].variants == ["co", "com", "con"]
        assert len(gen[0].carriers) == 3
        assert (PREFIX, 1, "vi", "vi") in pooled   # unrelated candidate untouched

    def test_no_group_when_fewer_than_two_members_present(self):
        co = Candidate(PREFIX, 1, "ko", "co",
                        carriers=[Carrier(syllRec("coopérer", ("co", "o", "pe", "re"), ("ko", "o", "pe", "Re")), 0, 1, "opérer")])
        cands = {(PREFIX, 1, "ko", "co"): co}
        pooled = poolKnownAffixGroups(cands)
        assert pooled == cands


class TestMarkCost:
    def test_formula(self):
        assert [markCostForCluster(m) for m in (1, 2, 4, 5, 6)] == [0, 0, 0, 1, 2]














class TestSimulate:
    def test_gain_never_negative_and_infeasible_falls_back(self):
        sb = _sb()
        ctx = SimContext(sb, [])
        ok = Carrier(rec("aabc", [(2,), (3,), (7,)]), 0, 1, "abc")
        overlap = Carrier(rec("aabd", [(2,), (3, 4), (7,)]), 0, 1, "abd")
        (res,) = simulate([(Binding(PREFIX, MERGED, (4,)), [ok, overlap])], ctx)
        assert res[0].gain == 1 and res[0].reason is None
        assert res[1].gain == 0 and res[1].reason == "keyOverlap" and res[1].newBase is None
        assert all(r.gain >= 0 for r in res)

    def test_dedicated_needs_two_strokes(self):
        ctx = SimContext(_sb(), [])
        one = Carrier(rec("q", [(2,), (3,)]), 0, 1, "q")
        two = Carrier(rec("qq", [(2,), (3,), (7,)]), 0, 2, "qq")
        (res,) = simulate([(Binding(PREFIX, DEDICATED, (4,)), [one, two])], ctx)
        assert (res[0].gain, res[0].reason) == (0, "noGain")
        assert res[1].gain == 1

    def test_illegal_union_infeasible(self):
        sb = _sb()
        ctx = SimContext(sb, [])
        # keys 11,12,13,14 all nucleus; adding an illegal onset combination (2,3,4,5,6,7)
        c = Carrier(rec("zz", [(2,), (3,)]), 0, 1, "z")
        (res,) = simulate([(Binding(PREFIX, MERGED, (3, 4, 5, 6, 7, 8, 9)), [c])], ctx)
        assert res[0].gain == 0 and res[0].reason in ("illegalChord", "keyOverlap")


class TestRuleBinding:
    """§4.2: a RULE binding merges when clash-free, else falls back to a standalone stroke for a
    physical reason only -- never a word exception."""

    def test_key_overlap_falls_back_to_standalone_not_an_exception(self):
        ctx = SimContext(_sb(), [])
        c = Carrier(rec("xxab", [(2,), (3,), (3, 4), (7,)]), 0, 2, "stem")
        (res,) = simulate([(Binding(PREFIX, RULE, (4,)), [c])], ctx)
        assert res[0].reason is None and res[0].gain == 1     # span(2) - 1, standalone saving
        assert res[0].newBase == ((4,), (3, 4), (7,))
        assert not res[0].mergedSaving

    def test_standalone_trap_when_dedicated_stroke_is_an_existing_outline(self):
        existing = rec("q", [(4,)])
        ctx = SimContext(_sb(), [existing])
        c = Carrier(rec("xxab", [(2,), (3,), (3, 4), (7,)]), 0, 2, "stem")
        (res,) = simulate([(Binding(PREFIX, RULE, (4,)), [c])], ctx)
        assert (res[0].gain, res[0].reason, res[0].newBase) == (0, "standaloneTrap", None)

    def test_standalone_trap_when_span_is_one_no_saving(self):
        ctx = SimContext(_sb(), [])
        c = Carrier(rec("xab", [(2,), (3, 4), (7,)]), 0, 1, "stem")
        (res,) = simulate([(Binding(PREFIX, RULE, (4,)), [c])], ctx)
        assert (res[0].gain, res[0].reason, res[0].newBase) == (0, "standaloneTrap", None)

    def test_merges_when_clash_free_like_merged(self):
        ctx = SimContext(_sb(), [])
        c = Carrier(rec("aabc", [(2,), (3,), (7,)]), 0, 1, "abc")
        (res,) = simulate([(Binding(PREFIX, RULE, (4,)), [c])], ctx)
        assert res[0].gain == 1 and res[0].mergedSaving


class TestRulePartialOverlap:
    """SimContext.partialOverlap (the decided mode, default ON): a 2-key rule merges when only some of
    its keys are in the neighbouring stroke."""

    def _run(self, neighbour, keys, flag):
        c = Carrier(rec("xab", [(2,), neighbour, (7,)]), 0, 1, "stem")
        (res,) = simulate([(Binding(PREFIX, RULE, keys), [c])], SimContext(_sb(), [], partialOverlap=flag))
        return res[0]

    def test_partial_overlap_fails_when_off(self):
        r = self._run((3,), (3, 4), False)
        assert (r.gain, r.reason, r.newBase) == (0, "standaloneTrap", None)

    def test_partial_overlap_merges_when_on(self):
        r = self._run((3,), (3, 4), True)
        assert r.gain == 1 and r.mergedSaving and r.newBase == ((2,), (3, 4), (7,))[1:]

    def test_complete_overlap_fails_in_both_modes(self):
        for flag in (False, True):
            r = self._run((3, 4), (3, 4), flag)
            assert (r.gain, r.reason) == (0, "standaloneTrap")

    def test_single_key_rule_unchanged(self):
        for flag in (False, True):
            r = self._run((3, 4), (4,), flag)
            assert (r.gain, r.reason) == (0, "standaloneTrap")


class TestDecidedSubMerge:
    def test_a_decided_merge_the_greedy_pass_did_not_make_is_built_from_its_parts(self):
        from src.affixdecisions import AnchorDecision, Decisions
        words = _tailWords("ment", "m@", _STEMS[:5]) + _tailWords("mant", "m@", _STEMS[5:], strokeBase=100) \
            + [_wordRec((st, "ba", "man"), (st, "ba", "m@"), (300 + i, 701, 901)) for i, st in enumerate(_STEMS[:5])]
        dec = Decisions([AnchorDecision(SUFFIX, "man|ment", "m@", "fused", [])])
        pool = buildCandidates(words, A.loadSeeds()[0], excludeTopWords=False, decisions=dec)
        m = pool[(SUFFIX, 1, "m@", "man|ment")]
        assert m.isAnchor and m.variants == ["man", "ment"] and len(m.carriers) >= 10
