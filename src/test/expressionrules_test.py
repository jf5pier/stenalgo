"""Phase 2 Stage A (src/expressionrules.py): candidate generation floors,
touched-expression indexing, proxy savings through the Phase 1
segmentation, and the greedy budgeted selection — all keyboard-free (the
proxy stage never composes strokes, so dummy token strokes suffice).
Frequencies are >= 5M so the Q6 floors pass."""

from src.expressionrules import (MIN_OCCURRENCES, ExprRule, PoolExpression,
                                 attachCandidates, briefCandidates,
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
