"""Tests for src/affixes.py -- hand-built records, no pickles."""
import src.affixes as A
from src.affixes import (
    DEDICATED, MERGED, PREFIX, RULE, SUFFIX, Binding, Candidate, Carrier, LemmaIndex, Slot,
    SimContext, WordRecord, _dedupeByCarrierSet, _growLatticeLevel, _onsetRest, _reduceExceptions,
    buildCandidates, buildFamily, colourSubgroups, inheritedSpan, markCostForCluster, norm,
    passesPrefixFilter, passesSuffixFilter, poolKnownAffixGroups, poolTailVariants, simulate,
    slotLabel, slotMatchesSyllable)
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


class TestCompetition:
    def _cand(self, ortho, stems):
        return Candidate(SUFFIX, 2, "x", ortho, stemFreq={s: 10.0 for s in stems}, carriers=[])

    def test_logie_logique_logiste_three_subgroups(self):
        members = [self._cand("logie", ["bio", "socio"]), self._cand("logique", ["bio", "socio"]),
                   self._cand("logiste", ["bio", "socio"])]
        assert len(colourSubgroups(3, {(0, 1): 20.0, (0, 2): 20.0, (1, 2): 20.0})) == 3

    def test_ation_ition_one_subgroup(self):
        assert len(colourSubgroups(2, {})) == 1

    def test_buildFamily_competition_from_shared_stems(self):
        r = rec("x", [(1,), (2,)])
        a = self._cand("ation", ["cr", "pr"])
        b = self._cand("ition", ["dem", "ed"])
        a.carriers = [Carrier(r, 1, 1, "cr")]
        b.carriers = [Carrier(rec("y", [(1,), (2,)]), 1, 1, "dem")]
        fam = buildFamily("S001", [a, b])
        assert len(fam.stemSubgroups) == 1


def syllRec(ortho, orthoSylls, phonoSylls, lemme=None, freq=5.0):
    """A record with real per-syllable ortho/phono, for tests that slice syllable tails."""
    _idx[0] += 1
    lemme = lemme or ortho
    return WordRecord(
        idx=_idx[0], ortho=ortho, lemme=lemme, gramCat="NOM", frequency=freq,
        phonoSylls=tuple(phonoSylls), orthoSylls=tuple(orthoSylls),
        base=tuple((i,) for i in range(1, len(orthoSylls) + 1)),
        extra=(), isLemmaForm=(ortho == lemme))


class TestGeneralizedAffixPooling:
    def test_onset_rest_split(self):
        assert _onsetRest("bi") == ("b", "i")
        assert _onsetRest("i") == ("", "i")
        assert _onsetRest("str") == ("str", "")   # no nucleus vowel: not poolable

    def test_pools_same_tail_different_onset(self):
        rb = syllRec("fabilité", ("fa", "bi", "li", "té"), ("fa", "bi", "li", "te"))
        rt = syllRec("fatilité", ("fa", "ti", "li", "té"), ("fa", "ti", "li", "te"))
        a = Candidate(SUFFIX, 3, "bi.li.te", "bilité", carriers=[Carrier(rb, 1, 3, "fa")])
        b = Candidate(SUFFIX, 3, "ti.li.te", "tilité", carriers=[Carrier(rt, 1, 3, "fa")])
        pooled = poolTailVariants({(SUFFIX, 3, "bi.li.te", "bilité"): a, (SUFFIX, 3, "ti.li.te", "tilité"): b},
                                   keepOriginals=True)
        # 2026-09-27 (DESIGN §3.5): the originals survive alongside the pooled candidate.
        assert len(pooled) == 3
        assert pooled[(SUFFIX, 3, "bi.li.te", "bilité")] is a
        assert pooled[(SUFFIX, 3, "ti.li.te", "tilité")] is b
        merged = next(c for c in pooled.values() if c.isGeneralized)
        assert merged.variants == ["bilité", "tilité"]
        assert merged.ortho == "·ilité" and merged.phono == "i.li.te"
        assert len(merged.carriers) == 2

    def test_default_still_consumes_originals_for_legacy(self):
        rb = syllRec("fabilité", ("fa", "bi", "li", "té"), ("fa", "bi", "li", "te"))
        rt = syllRec("fatilité", ("fa", "ti", "li", "té"), ("fa", "ti", "li", "te"))
        a = Candidate(SUFFIX, 3, "bi.li.te", "bilité", carriers=[Carrier(rb, 1, 3, "fa")])
        b = Candidate(SUFFIX, 3, "ti.li.te", "tilité", carriers=[Carrier(rt, 1, 3, "fa")])
        pooled = poolTailVariants({(SUFFIX, 3, "bi.li.te", "bilité"): a, (SUFFIX, 3, "ti.li.te", "tilité"): b})
        assert len(pooled) == 1

    def test_singleton_tail_group_untouched(self):
        r = syllRec("fabilité", ("fa", "bi", "li", "té"), ("fa", "bi", "li", "te"))
        a = Candidate(SUFFIX, 3, "bi.li.te", "bilité", carriers=[Carrier(r, 1, 3, "fa")])
        pooled = poolTailVariants({(SUFFIX, 3, "bi.li.te", "bilité"): a})
        assert pooled == {(SUFFIX, 3, "bi.li.te", "bilité"): a}
        assert not a.isGeneralized

    def test_prefix_pools_from_the_syllable_nearest_the_stem(self):
        # prefix span is at the START of the word, so the variable onset is the LAST affix
        # syllable (closest to the stem) and the invariant tail is the leading syllables.
        rb = syllRec("rebonjour", ("re", "bon", "jour"), ("R@", "bon", "ZuR"))
        rt = syllRec("retonjour", ("re", "ton", "jour"), ("R@", "ton", "ZuR"))
        a = Candidate(PREFIX, 2, "R@.bon", "rebon", carriers=[Carrier(rb, 0, 2, "jour")])
        b = Candidate(PREFIX, 2, "R@.ton", "reton", carriers=[Carrier(rt, 0, 2, "jour")])
        pooled = poolTailVariants({(PREFIX, 2, "R@.bon", "rebon"): a, (PREFIX, 2, "R@.ton", "reton"): b},
                                   keepOriginals=True)
        # 2026-09-27 (DESIGN §3.5): the originals survive alongside the pooled candidate.
        assert len(pooled) == 3
        merged = next(c for c in pooled.values() if c.isGeneralized)
        assert merged.ortho == "reon·" and merged.phono == "R@.on"

    def test_buildCandidates_pools_variants_below_the_threshold_alone(self):
        # Three onset variants of the same k=3 suffix, 2 lemmas each: none alone clears
        # MIN_STEM_ROOTS (5), but pooled they do (6 lemmas, 6 distinct stem roots).
        records = []
        stems = ["respo", "possi", "ferti", "hosti", "steri", "puera"]
        onsets = ["bi", "bi", "ti", "ti", "ri", "ri"]
        for stem, onset in zip(stems, onsets):
            lemma = f"{stem}able"
            records.append(syllRec(lemma, (stem, "able"), (stem, "able"), lemme=lemma))
            word = f"{stem}{onset}lité"
            records.append(syllRec(word, (stem, onset, "li", "té"), (stem, onset, "li", "te")))
        seedPairs, _ = A.loadSeeds()
        # excludeTopWords=False: this tiny fixture has far fewer than TOP_WORDS_EXCLUDED distinct
        # words, so the "top 200 by frequency" carrier exclusion would swallow every record --
        # meaningless here, real callers always want the default.
        kept = buildCandidates(records, seedPairs, excludeTopWords=False)
        gen = [c for c in kept.values() if c.isGeneralized]
        assert len(gen) == 1
        assert gen[0].variants == ["bilité", "rilité", "tilité"]
        assert gen[0].lemmas == 6


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


class TestSlots:
    def test_exact(self):
        s = Slot("exact", "li")
        assert slotMatchesSyllable(s, "li")
        assert not slotMatchesSyllable(s, "ti")

    def test_onset_including_empty(self):
        s = Slot("onset", "i")
        assert slotMatchesSyllable(s, "bi")
        assert slotMatchesSyllable(s, "i")     # empty onset
        assert not slotMatchesSyllable(s, "ba")

    def test_onset_exclusion(self):
        s = Slot("onset", "i", excluded=("m",))
        assert not slotMatchesSyllable(s, "mi")
        assert slotMatchesSyllable(s, "bi")

    def test_any_with_exclusion(self):
        s = Slot("any", excluded=("li",))
        assert slotMatchesSyllable(s, "ti")
        assert not slotMatchesSyllable(s, "li")

    def test_labels_fold_in_exclusions(self):
        assert slotLabel(Slot("exact", "li")) == "li"
        assert slotLabel(Slot("onset", "i")) == "[C]i"
        assert slotLabel(Slot("onset", "i", ("m",))) == "[C-{m}]i"
        assert slotLabel(Slot("any", excluded=("x", "y"))) == "*-{x,y}"


def _distinctStemRec(stemStroke, midPhono, midOrtho):
    """A 4-syllable record (stem, mid, li, té) with a *unique* stem stroke -- `syllRec`'s
    auto-numbered base (always (1,2,3,4) for any 4-syllable record) would make every same-length
    record collide regardless of content, which is wrong for tests that check exception handling."""
    _idx[0] += 1
    ortho = f"stem{stemStroke}{midOrtho}lité"
    return WordRecord(
        idx=_idx[0], ortho=ortho, lemme=ortho, gramCat="NOM", frequency=10.0,
        phonoSylls=("s", midPhono, "li", "te"), orthoSylls=("s", midOrtho, "li", "té"),
        base=((stemStroke,), (900 + stemStroke,), (990,), (991,)), extra=(), isLemmaForm=True)


class TestLatticeGrowth:
    def _base(self):
        # 4 onset-variant carriers, each with its own distinct stem: b/t/r share rest "i" (an
        # onset group), "ka" doesn't. Nothing collides, so every child should emit cleanly.
        recs = [_distinctStemRec(1, "bi", "bi"), _distinctStemRec(2, "ti", "ti"),
                _distinctStemRec(3, "ri", "ri"), _distinctStemRec(4, "ka", "ka")]
        carriers = [Carrier(r, 2, 2, "stem") for r in recs]
        return Candidate(SUFFIX, 2, "li.te", "lité", carriers=carriers)

    def test_emits_exact_onset_and_any_without_consuming(self):
        children = _growLatticeLevel(SUFFIX, self._base())
        kinds = {c.cand.slots[-1].kind for c in children}
        assert kinds == {"exact", "onset", "any"}
        exactPhonos = {c.cand.slots[-1].value for c in children if c.cand.slots[-1].kind == "exact"}
        assert exactPhonos == {"bi", "ti", "ri", "ka"}
        onset = next(c.cand for c in children if c.cand.slots[-1].kind == "onset")
        assert onset.slots[-1].value == "i" and onset.slots[-1].excluded == ()
        assert len(onset.carriers) == 3     # bi/ti/ri pooled, not consumed by the exact leaves
        anyChild = next(c.cand for c in children if c.cand.slots[-1].kind == "any")
        assert len(anyChild.carriers) == 4  # bi/ti/ri/ka, all together

    def test_expand_without_emit_via_subtree_bound(self):
        # A single, low-lemma-count carrier with a long stem still left: freq alone clears
        # GROWTH_MIN_MARGINAL through the subtree bound, but lemmas=1 fails the emit gate.
        orthoSylls = ("a", "b", "c", "d", "e", "mid", "li", "té")
        phonoSylls = ("a", "b", "c", "d", "e", "mi", "li", "te")
        r = syllRec("xxx", orthoSylls, phonoSylls, freq=40.0)
        base = Candidate(SUFFIX, 2, "li.te", "lité", carriers=[Carrier(r, 6, 2, "abcde")])
        children = _growLatticeLevel(SUFFIX, base)
        assert len(children) == 1
        assert children[0].emit is False
        assert children[0].expand is True


class TestReduceExceptions:
    def _carrier(self, onsetPhono, lemma, freq, stroke0):
        r = WordRecord(idx=_idx[0], ortho=lemma, lemme=lemma, gramCat="NOM", frequency=freq,
                        phonoSylls=("s", onsetPhono, "li", "te"), orthoSylls=("s", onsetPhono, "li", "té"),
                        base=((stroke0,), (10,), (900,), (901,)), extra=(), isLemmaForm=True)
        _idx[0] += 1
        return Carrier(r, 1, 2, "s")

    def test_one_colliding_value_gets_excluded(self):
        b = self._carrier("bi", "polb", 20.0, 100)
        m = self._carrier("mi", "polm", 5.0, 100)   # same remaining stem stroke as b -- collides
        t = self._carrier("ti", "fact", 10.0, 200)
        r = self._carrier("ri", "ferr", 10.0, 300)
        groups = {"b": [b], "m": [m], "t": [t], "r": [r]}
        result = _reduceExceptions(SUFFIX, groups, denom=45.0)
        assert result is not None
        remaining, excluded, excSet = result
        assert excluded == ("m",)
        assert set(remaining) == {"b", "t", "r"}

    def test_drops_past_max_slot_exclusions(self):
        b = self._carrier("bi", "polb", 20.0, 100)
        m = self._carrier("mi", "polm", 5.0, 100)     # collides with b
        t = self._carrier("ti", "fact", 10.0, 200)
        m2 = self._carrier("m2i", "factm", 5.0, 200)  # collides with t
        r = self._carrier("ri", "ferr", 10.0, 300)
        m3 = self._carrier("m3i", "ferrm", 5.0, 300)  # collides with r -- 3rd exclusion needed
        groups = {"b": [b], "m": [m], "t": [t], "m2": [m2], "r": [r], "m3": [m3]}
        assert _reduceExceptions(SUFFIX, groups, denom=55.0) is None


class TestLatticeDedupe:
    def test_dedupe_keeps_simpler_pattern_and_records_alias(self):
        r = syllRec("xbilité", ("x", "bi", "li", "té"), ("x", "bi", "li", "te"))
        carrier = Carrier(r, 1, 3, "x")
        exact = Candidate(SUFFIX, 3, "bi.li.te", "bilité", carriers=[carrier], slots=(Slot("exact", "bi"),))
        onset = Candidate(SUFFIX, 3, "[C]i.li.te", "[C]ilité", carriers=[carrier], slots=(Slot("onset", "i"),))
        deduped = _dedupeByCarrierSet([onset, exact])
        assert len(deduped) == 1
        kept = deduped[0]
        assert kept is exact
        assert (SUFFIX, 3, "[C]i.li.te", "[C]ilité") in kept.aliases


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
