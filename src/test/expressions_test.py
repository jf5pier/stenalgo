"""Phase 1 composition algebra (src/expressions.py): the canonical examples
of PLAN_2026-10-01-abbreviations-algorithm.md — brief substitution, attach
merges, the failure ladder, confluence. Chord constants are verified legal
against starboard3h.json (and (11,22,25) verified illegal: the coda pair
22+25 is not a legal keypress)."""

import itertools

from src.affixes import PREFIX, SUFFIX, SimContext
from src.expressions import (EXCEPTION, MERGED, STANDALONE, AttachRule,
                             BriefRule, Failure, Rules, Token, composeOutline,
                             composeOutlineTraced)
from src.keyboard import Starboard, canonicalizeStrokes

sb = Starboard.fromJSONFile("starboard3h.json")
assert sb is not None


class Ctx(SimContext):
    """Empty theory index; single-stroke outlines and final outlines
    injectable for the ladder and boundary-risk tests."""

    def __init__(self, singles=frozenset(), outlines=frozenset()):
        super().__init__(sb, [])
        self.singleStrokeOutlines = set(singles)
        self.finalOutlines = set(outlines)


# Theory strokes (Phase 0 probes): est=((13,14),) il=((13,23),) y=((13,),)
# a=((12,10),) de=((4,5,11,12),) d'=((4,5),) l'=((6,7),)
EST = ((13, 14),)
IL = ((13, 23),)
Y = ((13,),)
A = ((12, 10),)
DE = ((4, 5, 11, 12),)
LA = ((7, 9, 13),)
BETA_IL_Y_A = ((7, 13),)            # the hypothetical brief stroke
KAPPA_NE = (3,)                     # onset "s"
KAPPA_PAS = (2,)                    # onset "s" (second key)
MOT = ((4, 8, 14), (7, 9, 13))      # a two-stroke host word
KAPPA_DE_LA = (5,)                  # shares no syllabic key with MOT's first stroke

def tok(unit, strokes):
    return Token(unit, strokes)


class TestBriefs:
    def test_il_y_a_is_one_stroke(self):
        rules = Rules(briefs=(BriefRule(("il", "y", "a"), BETA_IL_Y_A),))
        result = composeOutline(rules, (tok("il", IL), tok("y", Y), tok("a", A)), Ctx())
        assert result == canonicalizeStrokes(BETA_IL_Y_A)
        traced = composeOutlineTraced(rules, (tok("il", IL), tok("y", Y), tok("a", A)), Ctx())
        assert traced.saving == 3 - 1  # three longform strokes become one
        assert [s.kind for s in traced.segments] == ["brief"]

    def test_longest_brief_wins(self):
        rules = Rules(briefs=(BriefRule(("y", "a"), ((13,),)),
                              BriefRule(("il", "y", "a"), BETA_IL_Y_A)))
        result = composeOutline(rules, (tok("il", IL), tok("y", Y), tok("a", A)), Ctx())
        assert result == canonicalizeStrokes(BETA_IL_Y_A)

    def test_unmatched_words_keep_their_outlines(self):
        rules = Rules(briefs=(BriefRule(("y", "a"), BETA_IL_Y_A),))
        result = composeOutline(rules, (tok("il", IL), tok("y", Y), tok("a", A)), Ctx())
        assert result == canonicalizeStrokes(IL + BETA_IL_Y_A)


class TestComposition:
    def test_il_n_y_a_pas_is_one_stroke(self):
        """The plan's canonical composition: brief + ne prefix + pas suffix
        collapse to a single chord."""
        rules = Rules(briefs=(BriefRule(("il", "y", "a"), BETA_IL_Y_A),),
                      attaches=(AttachRule(("n'",), PREFIX, KAPPA_NE),
                                AttachRule(("pas",), SUFFIX, KAPPA_PAS)))
        tokens = (tok("il", IL), tok("n'", ((6, 8),)), tok("y", Y),
                  tok("a", A), tok("pas", ((7, 8),)))
        result = composeOutline(rules, tokens, Ctx())
        assert result == ((2, 3, 7, 13),)  # beta | kappa_ne | kappa_pas
        traced = composeOutlineTraced(rules, tokens, Ctx())
        assert traced.saving == 5 - 1
        assert all(s.outcome != EXCEPTION for s in traced.segments)

    def test_attach_beats_brief(self):
        """Q1: with (n'), (pas) attaches declared, the brief over the same
        three units never fires; the host word takes both merges."""
        rules = Rules(briefs=(BriefRule(("n'", "est", "pas"), BETA_IL_Y_A),),
                      attaches=(AttachRule(("n'",), PREFIX, KAPPA_NE),
                                AttachRule(("pas",), SUFFIX, KAPPA_PAS)))
        tokens = (tok("n'", ((6, 8),)), tok("est", EST), tok("pas", ((7, 8),)))
        result = composeOutline(rules, tokens, Ctx())
        assert result == ((2, 3, 13, 14),)  # est | kappa_ne | kappa_pas
        traced = composeOutlineTraced(rules, tokens, Ctx())
        assert not any(s.kind == "brief" for s in traced.segments)

    def test_both_sides_attach_on_multistroke_brief(self):
        """Prefix and suffix on a 2-stroke brief land on different strokes."""
        beta = ((13,), (23,))
        rules = Rules(briefs=(BriefRule(("il", "y"), beta),),
                      attaches=(AttachRule(("n'",), PREFIX, KAPPA_NE),
                                AttachRule(("pas",), SUFFIX, KAPPA_PAS)))
        tokens = (tok("n'", ((6, 8),)), tok("il", IL), tok("y", Y), tok("pas", ((7, 8),)))
        result = composeOutline(rules, tokens, Ctx())
        assert result == canonicalizeStrokes(((3, 13), (2, 23)))


class TestAttachMerges:
    def test_de_la_prefix_merges_into_first_stroke(self):
        rules = Rules(attaches=(AttachRule(("de", "la"), PREFIX, KAPPA_DE_LA),))
        tokens = (tok("de", DE), tok("la", LA), tok("mot", MOT))
        result = composeOutline(rules, tokens, Ctx())
        assert result == canonicalizeStrokes(
            ((4, 5, 8, 14), (7, 9, 13)))  # mot first | kappa, mot rest
        traced = composeOutlineTraced(rules, tokens, Ctx())
        assert traced.saving == 2  # de+la strokes vanish
        assert traced.segments[0].outcome == MERGED

    def test_suffix_merges_into_last_stroke(self):
        rules = Rules(attaches=(AttachRule(("pas",), SUFFIX, KAPPA_PAS),))
        tokens = (tok("mot", MOT), tok("pas", ((7, 8),)))
        result = composeOutline(rules, tokens, Ctx())
        assert result == canonicalizeStrokes(
            ((4, 8, 14), (2, 7, 9, 13)))  # mot, mot last | kappa

    def test_longest_attach_wins(self):
        rules = Rules(attaches=(AttachRule(("la",), PREFIX, (3,)),
                               AttachRule(("de", "la"), PREFIX, KAPPA_DE_LA)))
        tokens = (tok("de", DE), tok("la", LA), tok("mot", MOT))
        result = composeOutline(rules, tokens, Ctx())
        assert result == canonicalizeStrokes(((4, 5, 8, 14), (7, 9, 13)))


class TestFailureLadder:
    def test_key_overlap_falls_back_to_standalone(self):
        """kappa sharing a key with the host's first stroke cannot merge; the
        constant stroke replaces the particle at its position (saving
        span-1)."""
        kappa = (13, 3)  # shares nucleus 13 with est
        rules = Rules(attaches=(AttachRule(("de", "la"), PREFIX, kappa),))
        tokens = (tok("de", DE), tok("la", LA), tok("est", EST))
        traced = composeOutlineTraced(rules, tokens, Ctx())
        assert traced.segments[0].outcome == STANDALONE
        assert traced.segments[0].reason == "keyOverlap"
        assert traced.strokes == canonicalizeStrokes(((3, 13), EST[0]))
        assert traced.saving == 1  # two particle strokes become one

    def test_illegal_chord_falls_back_to_standalone(self):
        """The union contains the illegal coda pair (22,25): illegalChord."""
        host = ((11, 22),)
        rules = Rules(attaches=(AttachRule(("de", "la"), PREFIX, (25,)),))
        tokens = (tok("de", DE), tok("la", LA), tok("mot", host))
        traced = composeOutlineTraced(rules, tokens, Ctx())
        assert traced.segments[0].outcome == STANDALONE
        assert traced.segments[0].reason == "illegalChord"
        assert traced.strokes == ((25,), (11, 22))

    def test_no_neighbour_keeps_longform(self):
        """A prefix particle with no following content segment: exception,
        saving 0. The segment carries its token span (Stage B's pool-
        fragment detection reads it)."""
        rules = Rules(attaches=(AttachRule(("de", "la"), PREFIX, KAPPA_DE_LA),))
        tokens = (tok("mot", MOT), tok("de", DE), tok("la", LA))
        traced = composeOutlineTraced(rules, tokens, Ctx())
        assert traced.segments[-1].outcome == EXCEPTION
        assert traced.segments[-1].reason == "noNeighbour"
        assert traced.segments[-1].span == (1, 3)
        assert traced.strokes == canonicalizeStrokes(MOT + DE + LA)
        assert traced.saving == 0
        assert traced.exceptions == 1

    def test_hostless_adjacent_attaches_merge_into_one_stroke(self):
        """qu' + il with no content after them: both are noNeighbour, so they
        compose with each other into one stroke (saving 1) instead of two
        exceptions."""
        rules = Rules(attaches=(AttachRule(("qu'",), PREFIX, KAPPA_NE),
                                AttachRule(("il",), PREFIX, KAPPA_PAS)))
        tokens = (tok("qu'", ((15, 16),)), tok("il", IL))
        traced = composeOutlineTraced(rules, tokens, Ctx())
        assert traced.strokes == canonicalizeStrokes(((2, 3),))
        assert traced.saving == 1
        assert traced.exceptions == 0
        assert traced.segments[0].outcome == STANDALONE
        assert traced.segments[0].reason == "attachCluster"
        assert traced.segments[1].outcome == MERGED

    def test_hostless_attaches_sharing_a_key_do_not_merge(self):
        rules = Rules(attaches=(AttachRule(("qu'",), PREFIX, KAPPA_NE),
                                AttachRule(("il",), PREFIX, KAPPA_NE)))
        tokens = (tok("qu'", ((15, 16),)), tok("il", IL))
        traced = composeOutlineTraced(rules, tokens, Ctx())
        assert traced.exceptions == 2
        assert traced.saving == 0

    def test_hostless_attaches_with_a_host_still_stack_on_it(self):
        rules = Rules(attaches=(AttachRule(("qu'",), PREFIX, KAPPA_NE),
                                AttachRule(("il",), PREFIX, KAPPA_PAS)))
        tokens = (tok("qu'", ((15, 16),)), tok("il", IL), tok("est", EST))
        traced = composeOutlineTraced(rules, tokens, Ctx())
        assert all(seg.reason != "attachCluster" for seg in traced.segments)

    def test_trailing_particle_uses_its_suffix_twin(self):
        """`le` has a prefix and a suffix rule: with a host before it and
        nothing after, the suffix rule fires (it used to be dead code, the
        prefix rule always won and failed noNeighbour)."""
        rules = Rules(attaches=(AttachRule(("de", "la"), PREFIX, KAPPA_DE_LA),
                                AttachRule(("de", "la"), SUFFIX, (14,))))
        tokens = (tok("mot", MOT), tok("de", DE), tok("la", LA))
        traced = composeOutlineTraced(rules, tokens, Ctx())
        assert traced.segments[-1].rule.position == SUFFIX
        assert traced.segments[-1].outcome == MERGED
        assert traced.saving == 2
        # a following token keeps the prefix rule
        followed = composeOutlineTraced(rules, tokens + (tok("est", EST),), Ctx())
        assert followed.segments[1].rule.position == PREFIX

    def test_span_one_never_goes_standalone(self):
        """A one-stroke particle with a failed merge keeps its longform
        (spanOne): a standalone would save nothing."""
        rules = Rules(attaches=(AttachRule(("n'",), PREFIX, (13, 3)),))
        tokens = (tok("n'", ((6, 8),)), tok("est", EST))
        traced = composeOutlineTraced(rules, tokens, Ctx())
        assert traced.segments[0].outcome == EXCEPTION
        assert traced.segments[0].reason == "spanOne"
        assert traced.saving == 0

    def test_standalone_trap_in_single_stroke_outlines(self):
        """A standalone stroke that is an existing single-stroke outline is an
        exception, not a silent homograph."""
        rules = Rules(attaches=(AttachRule(("de", "la"), PREFIX, (13, 3)),))
        tokens = (tok("de", DE), tok("la", LA), tok("est", EST))
        traced = composeOutlineTraced(rules, tokens, Ctx(singles={(3, 13)}))
        assert traced.segments[0].outcome == EXCEPTION
        assert traced.segments[0].reason == "standaloneTrap"
        assert traced.saving == 0


class TestConfluence:
    def test_rule_declaration_order_never_matters(self):
        briefs = (BriefRule(("il", "y", "a"), BETA_IL_Y_A),
                  BriefRule(("y", "a"), ((13,),)))
        attaches = (AttachRule(("n'",), PREFIX, KAPPA_NE),
                    AttachRule(("pas",), SUFFIX, KAPPA_PAS),
                    AttachRule(("de", "la"), PREFIX, KAPPA_DE_LA))
        tokens = (tok("il", IL), tok("n'", ((6, 8),)), tok("y", Y),
                  tok("a", A), tok("pas", ((7, 8),)))
        results = set()
        for briefPerms in itertools.permutations(briefs):
            for attachPerms in itertools.permutations(attaches):
                rules = Rules(briefs=briefPerms, attaches=attachPerms)
                results.add(composeOutlineTraced(rules, tokens, Ctx()).strokes)
        assert results == {((2, 3, 7, 13),)}

    def test_prefix_before_suffix_on_one_stroke(self):
        """Fixed internal order: prefix merges first, so the suffix overlap
        check sees the prefix's keys — deterministic normal form."""
        host = ((13, 14),)  # est
        prefixKappa = (3,)   # clean against est
        suffixKappa = (3, 2)  # shares key 3 with the post-prefix stroke
        rules = Rules(attaches=(AttachRule(("n'",), PREFIX, prefixKappa),
                                AttachRule(("pas",), SUFFIX, suffixKappa)))
        tokens = (tok("n'", ((6, 8),)), tok("est", host),
                  tok("pas", ((7, 8), (9,))))  # 2 strokes: standalone saves one
        traced = composeOutlineTraced(rules, tokens, Ctx())
        assert traced.segments[0].outcome == MERGED
        assert traced.segments[2].outcome == STANDALONE
        assert traced.segments[2].reason == "keyOverlap"
        assert traced.strokes == ((3, 13, 14), (2, 3))
        assert traced.saving == 2  # n' merged; pas 2 strokes -> 1 standalone


class TestFamiliesAndReports:
    def test_family_variants_differ_only_on_selector_keys(self):
        """Q2: du / de la as one family, a */# selector separating them. The
        selector key is transparent to the merge checks (a live theory stroke
        like (12,10) is 'illegal' per SimContext.isLegal precisely because
        reserved keys sit outside the syllabic banks)."""
        rules = Rules(attaches=(AttachRule(("de", "la"), PREFIX, (5,), family="d-gen"),
                                AttachRule(("du",), PREFIX, (5, 10), family="d-gen")))
        deLa = composeOutline(rules, (tok("de", DE), tok("la", LA), tok("mot", MOT)), Ctx())
        du = composeOutline(rules, (tok("du", ((4, 5, 11, 12),)), tok("mot", MOT)), Ctx())
        assert deLa == canonicalizeStrokes(((4, 5, 8, 14), (7, 9, 13)))
        assert du == canonicalizeStrokes(((4, 5, 8, 10, 14), (7, 9, 13)))
        assert deLa != du

    def test_boundary_risk_flag_on_multistroke_brief(self):
        """A 2-stroke brief splittable into existing outlines is flagged."""
        beta = ((13,), (23,))
        rules = Rules(briefs=(BriefRule(("il", "y"), beta),))
        tokens = (tok("il", IL), tok("y", Y))
        risky = composeOutlineTraced(
            rules, tokens, Ctx(outlines={((13,),), ((23,),)}))
        assert risky.boundaryRisk is True
        safe = composeOutlineTraced(rules, tokens, Ctx(outlines={((13,),)}))
        assert safe.boundaryRisk is False

    def test_single_stroke_brief_never_boundary_risky(self):
        rules = Rules(briefs=(BriefRule(("il", "y", "a"), BETA_IL_Y_A),))
        tokens = (tok("il", IL), tok("y", Y), tok("a", A))
        traced = composeOutlineTraced(
            rules, tokens, Ctx(outlines={BETA_IL_Y_A[0],}))
        assert traced.boundaryRisk is False


class TestFailuresAndValidation:
    def test_empty_stream_fails(self):
        result = composeOutline(Rules(), (), Ctx())
        assert isinstance(result, Failure) and result.reason == "emptyStream"

    def test_token_without_strokes_fails(self):
        result = composeOutline(Rules(), (tok("x", ()),), Ctx())
        assert isinstance(result, Failure) and result.reason == "tokenWithoutStrokes"

    def test_rule_validation(self):
        for bad in (lambda: AttachRule((), PREFIX, (3,)),
                    lambda: AttachRule(("de",), "middle", (3,)),
                    lambda: AttachRule(("de",), PREFIX, ())):
            try:
                bad()
                raise AssertionError("expected ValueError")
            except ValueError:
                pass
        for bad in (lambda: BriefRule((), ((3,),)),
                    lambda: BriefRule(("il",), ())):
            try:
                bad()
                raise AssertionError("expected ValueError")
            except ValueError:
                pass

    def test_saving_is_longform_minus_outline(self):
        rules = Rules(briefs=(BriefRule(("y", "a"), BETA_IL_Y_A),),
                      attaches=(AttachRule(("pas",), SUFFIX, KAPPA_PAS),))
        tokens = (tok("il", IL), tok("y", Y), tok("a", A), tok("pas", ((7, 8),)))
        traced = composeOutlineTraced(rules, tokens, Ctx())
        assert traced.saving == sum(len(t.strokes) for t in tokens) - len(traced.strokes)
        assert traced.saving == 2  # brief: 3->1; pas merged into the brief


class TestAttachKeysOverlap:
    """The expression layer owns its overlap policy: refuse when more than
    `maxShared` syllabic keys are shared (0 = strict, the decoder contract)."""

    def test_strict_default_refuses_any_shared_key(self):
        from src.expressions import EXPR_MAX_SHARED_KEYS, attachKeysOverlap
        assert EXPR_MAX_SHARED_KEYS == 0
        assert not attachKeysOverlap((2, 13), (18, 20, 21))
        assert attachKeysOverlap((2, 13, 18), (18, 20, 21))

    def test_one_shared_key_allowed_at_limit_one(self):
        from src.expressions import attachKeysOverlap
        assert not attachKeysOverlap((2, 13, 18), (18, 20, 21), maxShared=1)
        assert attachKeysOverlap((2, 13, 18, 20), (18, 20, 21), maxShared=1)

    def test_full_overlap_refused_at_every_limit_below_its_size(self):
        from src.expressions import attachKeysOverlap
        assert attachKeysOverlap((18, 20, 21, 5), (18, 20, 21), maxShared=2)
        assert not attachKeysOverlap((18, 20, 21, 5), (18, 20, 21), maxShared=3)

    def test_module_constant_drives_the_composition(self, monkeypatch):
        """Raising the limit lets a one-key-overlap merge through composeOutline."""
        import src.expressions as E
        from src.affixes import SimContext
        from src.keyboard import Starboard
        sb = Starboard.fromJSONFile("starboard3h.json")
        assert sb is not None
        ctx = SimContext(sb, [])
        # host 'est' stroke shares key 18 with the attach keypress (18, 20, 21)
        toks = (Token("de", ((9,),)), Token("mot", ((2, 13, 18),)))
        rules = E.Rules(attaches=(E.AttachRule(("de",), E.PREFIX, (18, 20, 21)),))
        strict = E.composeOutlineTraced(rules, toks, ctx)
        assert strict.segments[0].outcome != E.MERGED
        monkeypatch.setattr(E, "EXPR_MAX_SHARED_KEYS", 1)
        loose = E.composeOutlineTraced(rules, toks, ctx)
        assert loose.segments[0].outcome in (E.MERGED, E.STANDALONE)
