"""Phase 2 Stage A (src/expressionrules.py): candidate generation floors,
touched-expression indexing, proxy savings through the Phase 1
segmentation, and the greedy budgeted selection — all keyboard-free (the
proxy stage never composes strokes, so dummy token strokes suffice).
Frequencies are >= 5M so the Q6 floors pass."""

from src.expressionrules import (MAX_BRIEF_FAMILY_VARIANTS, MIN_OCCURRENCES,
                                 ExprRule, PoolExpression, _fallbackPair,
                                 assignBriefStrokes, assignKeypresses,
                                 attachCandidates, auditExpressionRules,
                                 briefCandidates, deriveBriefStroke,
                                 jointFrequency, proxySaving,
                                 selectExpressionRules, touchedExpressions)
from src.expressions import (PREFIX, SUFFIX, AttachRule, BriefRule, Token)


def expr(units, freq, strokesPerUnit=1):
    return PoolExpression(tuple(units), freq,
                          tuple(Token(u, ((9,),) * strokesPerUnit) for u in units))


PARTICLES = frozenset({"de", "la", "le", "les", "ne", "pas", "un", "une", "à", "au"})


class TestBriefCandidates:
    def test_floors(self):
        pool = [
            expr(["il", "y", "a"], MIN_OCCURRENCES),          # eligible: 3 strokes
            expr(["c'est"], MIN_OCCURRENCES),                 # single unit: never
            expr(["un", "mot"], MIN_OCCURRENCES - 1),         # under 5M: no
            expr(["de", "la", "mer"], MIN_OCCURRENCES),       # eligible
        ]
        rules = briefCandidates(pool)
        assert [r.units for r in rules] == [("de", "la", "mer"), ("il", "y", "a")]
        assert all(r.strokesSaved == 2 for r in rules)


class TestAttachCandidates:
    def test_proper_particle_runs_only(self):
        pool = [expr(["de", "la", "maison"], 10_000_000)]
        rules = attachCandidates(pool, PARTICLES)
        got = {(r.units, r.position) for r in rules}
        # proper PREFIX runs only: the suffix runs all end in "maison"
        # (content), so none qualify
        assert got == {(("de",), PREFIX), (("de", "la"), PREFIX)}

    def test_standalone_supersedes_nested_evidence(self):
        pool = [expr(["de", "la", "maison"], 6_000_000),
                expr(["de", "la", "mer"], 4_000_000),
                expr(["de", "la"], 202_000_000)]
        rules = {r.units: r for r in attachCandidates(pool, PARTICLES)
                 if r.position == PREFIX}
        assert rules[("de", "la")].freq == 202_000_000  # standalone: every occurrence
        assert rules[("de",)].freq == 212_000_000       # no standalone: summed evidence

    def test_one_stroke_particles_are_eligible(self):
        """Q6's stroke floor is a BRIEF floor: 'ne'/'pas' (1 stroke) remain
        attach candidates — the plan's 'ne + verbe + pas' route."""
        pool = [expr(["ne", "sait", "pas"], 18_300_000)]
        rules = attachCandidates(pool, frozenset({"ne", "pas"}))
        assert {r.units for r in rules} == {("ne",), ("pas",)}
        assert all(r.strokesSaved == 1 for r in rules)


class TestTouched:
    def test_position_edges(self):
        from src.expressionrules import matchedSpans
        pool = [expr(["maison", "de", "la"], 10_000_000)]
        suffix = next(r for r in attachCandidates(pool, PARTICLES)
                      if r.units == ("de", "la"))
        assert suffix.position == SUFFIX
        assert touchedExpressions(suffix, pool) == {0}
        prefix = ExprRule("attach", ("de", "la"), position=PREFIX)
        assert matchedSpans(prefix, ("maison", "de", "la")) == []  # no host after
        assert matchedSpans(ExprRule("attach", ("de", "la"), position=SUFFIX),
                            ("de", "la", "maison")) == []          # no host before

    def test_brief_subsequence_interleaves_particles(self):
        pool = [expr(["il", "n'", "y", "a", "pas"], 1.0)]
        brief = ExprRule("brief", ("il", "y", "a"))
        assert touchedExpressions(brief, pool) == {0}
        attach = ExprRule("attach", ("ne",), position=PREFIX)
        assert touchedExpressions(attach, pool) == set()  # "ne" not "n'" here


class TestProxySaving:
    def test_composition_only_composes(self):
        """The brief (il y a) alone does NOT fire on 'il n'y a pas' (n'
        intervenes — no brief rule for it); with the ne/pas attaches
        declared, the residual stream matches and everything composes."""
        e = expr(["il", "n'", "y", "a", "pas"], 1.0)
        brief = (BriefRule(("il", "y", "a"), ((2,),)),)
        ne = (AttachRule(("n'",), PREFIX, (3,)),)
        pas = (AttachRule(("pas",), SUFFIX, (2,)),)
        assert proxySaving(brief, (), e) == 0
        assert proxySaving((), ne + pas, e) == 2
        assert proxySaving(brief, ne + pas, e) == 4  # spans 1+1, brief 3->1

    def test_attach_first_suppresses_brief_on_same_tokens(self):
        """Q1 inside the proxy: with ne+pas attaches declared, a brief over
        (n', est, pas) never fires."""
        e = expr(["n'", "est", "pas"], 1.0)
        attaches = (AttachRule(("n'",), PREFIX, (3,)), AttachRule(("pas",), SUFFIX, (2,)))
        briefs = (BriefRule(("n'", "est", "pas"), ((2,),)),)
        assert proxySaving((), attaches, e) == 2
        assert proxySaving(briefs, attaches, e) == 2  # no extra from the brief


class TestSelection:
    def test_greedy_by_marginal_with_once_credit(self):
        pool = [expr(["de", "la", "maison"], 100_000_000),
                expr(["de", "la", "mer"], 10_000_000),
                expr(["il", "y", "a"], 50_000_000)]
        candidates = briefCandidates(pool) + attachCandidates(pool, PARTICLES)
        result = selectExpressionRules(candidates, pool, budget=3)
        # "de la" attach (110M occurrences x 2 strokes) wins round 1; then the
        # briefs over de-la expressions add nothing (attach-first consumed
        # their tokens) and brief(il y a) takes round 2; round 3 is empty.
        assert [" ".join(r.units) + ":" + r.kind for r in result.selected] == \
            ["de la:attach", "il y a:brief"]
        assert len(result.selected) == 2

    def test_territory_skip_on_span_contest(self):
        """brief(n'est pas) wins round 1; brief(est) (a 2-stroke word, so its
        brief saves one) still has a positive marginal on its other
        expression but contests the same tokens on the shared one — a
        territory skip, not a second selection."""
        two = 2  # strokes per unit, so a single-unit brief saves one stroke
        pool = [expr(["n'", "est", "pas"], 100_000_000, strokesPerUnit=two),
                expr(["est", "si", "bon"], 60_000_000, strokesPerUnit=two)]
        candidates = [ExprRule("brief", ("n'", "est", "pas"), freq=100_000_000,
                               strokesSaved=4),
                      ExprRule("brief", ("est",), freq=160_000_000,
                               strokesSaved=1)]
        result = selectExpressionRules(candidates, pool, budget=5)
        assert [" ".join(r.units) for r in result.selected] == ["n' est pas"]
        assert result.skips and result.skips[0][:2] == ("est", "n' est pas")

    def test_composing_rules_never_skip_each_other(self):
        """ne + pas hold disjoint spans around a host: both selected."""
        pool = [expr(["ne", "sait", "pas"], 100_000_000)]
        candidates = attachCandidates(pool, frozenset({"ne", "pas"}))
        result = selectExpressionRules(candidates, pool, budget=5)
        assert sorted(" ".join(r.units) for r in result.selected) == ["ne", "pas"]
        assert result.skips == []

    def test_budget_respected(self):
        pool = [expr([f"u{i}", f"h{i}"], 10_000_000) for i in range(10)]
        candidates = briefCandidates(pool)
        result = selectExpressionRules(candidates, pool, budget=4)
        assert len(result.selected) == 4
        assert len(result.curve) == 4

    def test_determinism(self):
        pool = [expr(["de", "la", "maison"], 100_000_000),
                expr(["à", "la", "maison"], 90_000_000),
                expr(["il", "y", "a"], 50_000_000)]
        candidates = briefCandidates(pool) + attachCandidates(pool, PARTICLES)
        r1 = selectExpressionRules(list(candidates), pool, budget=5)
        r2 = selectExpressionRules(list(reversed(candidates)), pool, budget=5)
        assert [(r.kind, r.units, r.position) for r in r1.selected] == \
            [(r.kind, r.units, r.position) for r in r2.selected]

    def test_joint_frequency(self):
        pool = [expr(["il", "n'", "y", "a", "pas"], 30_000_000),
                expr(["il", "y", "a"], 10_000_000)]
        brief = ExprRule("brief", ("il", "y", "a"))
        pas = ExprRule("attach", ("pas",), position=SUFFIX)
        assert jointFrequency(brief, pas, pool) == 30_000_000


class TestFamilies:
    """Q2: related particle variants are ONE learnable rule (one budget
    slot, one base keypress, */# selector variants)."""

    @staticmethod
    def lemmas(units):
        return {"de": "de", "d'": "de", "la": "la"}.get(units[0], "")

    def test_family_is_one_slot_with_variant_absorption(self):
        pool = [expr(["de", "la", "maison"], 100_000_000),
                expr(["de", "chat"], 60_000_000)]
        candidates = (briefCandidates(pool)
                      + attachCandidates(pool, PARTICLES, familyOf=self.lemmas))
        result = selectExpressionRules(candidates, pool, budget=3)
        # (de la) prefix wins round 1; (de,) — same family — is absorbed as a
        # variant (its marginal on "de chat" clears FORM_COST); everything
        # else is suppressed; one slot, two rules.
        assert [( " ".join(r.units), r.position) for r in result.selected] == \
            [("de la", PREFIX), ("de", PREFIX)]
        assert result.selected[0].forms == 2
        assert result.selected[1].forms == 0   # the family's count lives on the head

    def test_family_cap_closes_the_family(self):
        """Five same-family variants: the head plus three absorbed (the
        selector budget), the fifth dropped for good — never a new head."""
        pool = [expr([u, "chat"], 10_000_000)
                for u in ("l'", "la", "le", "leur", "les")]
        candidates = attachCandidates(pool, frozenset({"l'", "la", "le", "leur", "les"}),
                                      familyOf=lambda units: "le")
        result = selectExpressionRules(candidates, pool, budget=5)
        assert len(result.selected) == 4          # MAX_FAMILY_VARIANTS
        assert all(r.family == "le" for r in result.selected)
        assert result.selected[0].forms == 4


class TestAssignKeypresses:
    """Stage B: families share one base keypress; variants take */#
    selectors in descending-frequency order; the 5% exception gate rejects
    bases whose merges fail on the sample."""

    @staticmethod
    def ctx():
        from src.affixes import SimContext
        from src.keyboard import Starboard
        sb = Starboard.fromJSONFile("starboard3h.json")
        assert sb is not None
        return SimContext(sb, [])

    def test_family_shares_base_with_selectors(self):
        ctx = self.ctx()
        mot = (Token("de", ((4, 5, 11, 12),)), Token("la", ((7, 9, 13),)),
               Token("maison", ((4, 8, 14), (7, 9, 13))))
        pool = [PoolExpression(("de", "la", "maison"), 100_000_000, mot)]
        head = ExprRule("attach", ("de", "la"), position=PREFIX, family="de",
                        freq=100_000_000, strokesSaved=2)
        head.forms = 2
        variant = ExprRule("attach", ("de",), position=PREFIX, family="de",
                           freq=60_000_000, strokesSaved=1)
        variant.forms = 0
        report = assignKeypresses([head, variant], pool, ctx, [(3,), (2,)])
        assert report["de"]["base"] in [(2,), (3,)]
        base = report["de"]["base"]
        assert head.keys == base                          # strongest: bare base
        assert variant.keys == tuple(sorted(set(base) | {10}))   # * selector
        assert head.keys != variant.keys
        assert head.exactDone and variant.exactDone

    def test_gate_rejects_overlapping_base(self):
        """The only candidate base shares a key with the host's first
        stroke: a 1-stroke particle's failed merge is a spanOne EXCEPTION
        (a standalone would save nothing), the gate trips, no base."""
        ctx = self.ctx()
        tokens = (Token("de", ((4, 5, 11, 12),)),
                  Token("maison", ((4, 8, 14), (7, 9, 13))))
        pool = [PoolExpression(("de", "maison"), 100_000_000, tokens)]
        rule = ExprRule("attach", ("de",), position=PREFIX,
                        freq=100_000_000, strokesSaved=1)
        report = assignKeypresses([rule], pool, ctx, [(4,)])  # 4 is in maison
        assert report["de"]["base"] is None
        assert rule.keys is None and not rule.exactDone


class TestDeriveBriefStroke:
    """The brief-creation mechanic: forced tao entries / later word additions
    get ONE invented stroke — mnemonic derivations first, free chords last,
    never shadowing a live outline or another brief."""

    @staticmethod
    def ctx(singles=frozenset(), outlines=frozenset()):
        from src.affixes import SimContext
        from src.keyboard import Starboard
        sb = Starboard.fromJSONFile("starboard3h.json")
        assert sb is not None
        c = SimContext(sb, [])
        c.singleStrokeOutlines = set(singles)
        c.finalOutlines = set(outlines)
        return c

    @staticmethod
    def expr(units, strokes):
        return PoolExpression(tuple(units), 1.0,
                              tuple(Token(u, s) for u, s in zip(units, strokes)))

    def test_union_derivation_first(self):
        e = self.expr(("mot", "cle"), (((2, 13),), ((14, 23),)))
        got = deriveBriefStroke(e, self.ctx(), set())
        assert got is not None and got[1] == "union"
        assert got[0] == (2, 13, 14, 23)

    def test_taken_stroke_falls_through(self):
        e = self.expr(("mot", "cle"), (((2, 13),), ((14, 23),)))
        got = deriveBriefStroke(e, self.ctx(), {(2, 13, 14, 23)})
        assert got is not None and got[0] != (2, 13, 14, 23)  # next derivation

    def test_shadowing_outline_skipped(self):
        e = self.expr(("mot", "cle"), (((2, 13),), ((14, 23),)))
        got = deriveBriefStroke(e, self.ctx(outlines={((2, 13, 14, 23),)}),
                                set())
        assert got is None or got[0] != (2, 13, 14, 23)

    def test_free_chord_fallback(self):
        # both tokens carry (13,): every mnemonic derivation yields the live
        # single-stroke outline (13,) -- the free-chord ladder must fire
        e = self.expr(("a", "b"), (((13,),), ((13,),)))
        got = deriveBriefStroke(e, self.ctx(singles={(13,)}), set(),
                                freeChords=[(2,), (3,), (2, 13)])
        assert got is not None and got[1] == "free" and got[0] == (2,)

    def test_none_when_nothing_legal(self):
        e = self.expr(("a", "b"), (((13,),), ((13,),)))
        assert deriveBriefStroke(e, self.ctx(singles={(13,)}), set(),
                                 freeChords=[]) is None


class TestBriefFamilies:
    """2026-10-02: briefs carry a family, compete with the family's attaches
    in one greedy, and their variant cap is the learnability bound (8), not
    the */# selector count (4)."""

    def test_brief_candidates_carry_the_family(self):
        pool = [expr(["que", "je"], MIN_OCCURRENCES), expr(["il", "y"], MIN_OCCURRENCES)]
        rules = briefCandidates(
            pool, familyOf=lambda units: "que+pron" if units[0] == "que" else "")
        assert {r.units: r.family for r in rules} == {("que", "je"): "que+pron",
                                                     ("il", "y"): ""}
        assert all(r.family == "" for r in briefCandidates(pool))

    def test_brief_family_cap_is_eight(self):
        heads = [f"p{i}" for i in range(10)]
        pool = [expr(["que", h], 10_000_000) for h in heads]
        candidates = briefCandidates(pool, familyOf=lambda units: "que+pron")
        result = selectExpressionRules(candidates, pool, budget=10)
        assert MAX_BRIEF_FAMILY_VARIANTS == 8
        assert len(result.selected) == MAX_BRIEF_FAMILY_VARIANTS
        assert result.selected[0].forms == MAX_BRIEF_FAMILY_VARIANTS
        assert all(r.kind == "brief" for r in result.selected)


class TestFallbackPair:
    def test_nested_spans_are_a_fallback(self):
        assert _fallbackPair([[(0, 2)]], [[(0, 1)]])
        assert _fallbackPair([[(1, 2)]], [[(0, 3)]])
        assert _fallbackPair([[(0, 2)]], [[(0, 2)]])          # equal counts as nested

    def test_partial_intersection_contests_territory(self):
        assert not _fallbackPair([[(0, 2)]], [[(1, 3)]])

    def test_one_partial_expression_is_enough(self):
        assert not _fallbackPair([[(0, 2)], [(0, 3)]], [[(0, 1)], [(2, 4)]])

    def test_disjoint_and_empty_are_no_contest(self):
        assert _fallbackPair([[(0, 1)]], [[(2, 3)]])
        assert _fallbackPair([[]], [[(0, 1)]])

    def test_nested_brief_and_attach_both_get_selected(self):
        """The brief owns "le chat"; the attach (le) still serves "le chien".
        Where both match, the attach-first stream makes the brief the
        fallback, so the nested pair is no territory contest."""
        pool = [expr(["le", "chat"], 70_000_000, strokesPerUnit=2),
                expr(["le", "chien"], 20_000_000, strokesPerUnit=2)]
        candidates = ([b for b in briefCandidates(pool) if b.units == ("le", "chat")]
                      + attachCandidates(pool, frozenset({"le"})))
        result = selectExpressionRules(candidates, pool, budget=5)
        assert [(r.kind, r.units) for r in result.selected] == \
            [("brief", ("le", "chat")), ("attach", ("le",))]
        assert result.skips == []

    def test_brief_inside_brief_still_contests(self):
        pool = [expr(["que", "le", "chat"], 50_000_000, strokesPerUnit=2),
                expr(["le", "chat", "noir"], 40_000_000, strokesPerUnit=2)]
        candidates = [ExprRule("brief", ("que", "le", "chat"), freq=50_000_000,
                               strokesSaved=5),
                      ExprRule("brief", ("le", "chat"), freq=90_000_000,
                               strokesSaved=3)]
        result = selectExpressionRules(candidates, pool, budget=5)
        assert [" ".join(r.units) for r in result.selected] == ["le chat"]
        assert result.skips[0][:2] == ("que le chat", "le chat")


class TestAssignBriefStrokes:
    ctx = staticmethod(TestDeriveBriefStroke.ctx)

    @staticmethod
    def pool():
        return [PoolExpression(("mot", "cle"), 9.0,
                               (Token("mot", ((2, 13),)), Token("cle", ((14, 23),)))),
                PoolExpression(("mot", "rue"), 8.0,
                               (Token("mot", ((2, 13),)), Token("rue", ((14, 24),))))]

    def test_distinct_strokes_and_beta_set(self):
        rules = [ExprRule("brief", ("mot", "cle"), freq=9.0),
                 ExprRule("brief", ("mot", "rue"), freq=8.0)]
        report = assignBriefStrokes(rules, self.pool(), self.ctx(),
                                    freeChords=[(2,), (3,), (4,)])
        assert all(v is not None for v in report.values())
        strokes = [r.beta[0] for r in rules]
        assert len(set(strokes)) == 2
        assert all(r.exactDone for r in rules)
        assert report[("mot", "cle")][0] == (2, 13, 14, 23)    # most frequent first

    def test_failure_keeps_beta_none(self):
        rules = [ExprRule("brief", ("a", "b"), freq=1.0)]
        pool = [PoolExpression(("a", "b"), 1.0,
                               (Token("a", ((13,),)), Token("b", ((13,),))))]
        report = assignBriefStrokes(rules, pool, self.ctx(singles={(13,)}),
                                    freeChords=[])
        assert report == {("a", "b"): None}
        assert rules[0].beta is None

    def test_unknown_expression_fails_and_attaches_are_ignored(self):
        rules = [ExprRule("brief", ("nowhere", "here"), freq=1.0),
                 ExprRule("attach", ("de",), position=PREFIX)]
        report = assignBriefStrokes(rules, self.pool(), self.ctx())
        assert report == {("nowhere", "here"): None}

    def test_taken_strokes_are_respected(self):
        rules = [ExprRule("brief", ("mot", "cle"), freq=9.0)]
        report = assignBriefStrokes(rules, self.pool(), self.ctx(),
                                    freeChords=[(2,)],
                                    takenStrokes={(2, 13, 14, 23)})
        assert report[("mot", "cle")] != ((2, 13, 14, 23), "union")
        assert rules[0].beta is None or rules[0].beta[0] != (2, 13, 14, 23)


class TestAuditWithBriefs:
    def test_selected_briefs_compose_in_the_audit(self):
        pool = TestAssignBriefStrokes.pool()
        rule = ExprRule("brief", ("mot", "cle"), freq=9.0)
        rule.beta = ((2, 13, 14, 23),)
        audit = auditExpressionRules([rule], pool, TestDeriveBriefStroke.ctx())
        assert audit.savingMass == 9.0 * 1      # 2 strokes -> 1, only the first expr
        assert audit.shadows == [] and audit.collisions == {}

    def test_brief_without_beta_is_ignored(self):
        pool = TestAssignBriefStrokes.pool()
        audit = auditExpressionRules([ExprRule("brief", ("mot", "cle"), freq=9.0)],
                                     pool, TestDeriveBriefStroke.ctx())
        assert audit.savingMass == 0
