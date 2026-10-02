"""
Expression rule selection — Phase 2 Stage A of
PLAN_2026-10-01-abbreviations-algorithm.md: greedy budgeted selection where
briefs and attach rules compete by marginal frequency-weighted saving, in the
`affixrules.selectRules` tradition (fresh marginals against the current
selection, once-credit per expression, territory skips, budget) but over
EXPRESSION occurrences segmented by the Phase 1 algebra
(`src/expressions.planStream`), not word carriers.

Round-2 decisions encoded here: queue floors >= 2 longform strokes AND
>= 5M occurrences (Q6, both tunable below) — read as BRIEF floors: an
expression worth briefing costs >= 2 strokes, while a 1-stroke particle
("ne", "pas") is still a legitimate ATTACH rule (the plan's own
"ne + verbe + pas" route; a merged 1-stroke particle saves a whole
stroke); the 5M occurrence floor applies to both kinds. A separate
expression budget (Q4) — the 30 affix rules are not touched; pricing in
the FORM_COST tradition with a family's variants as its forms (Q2); an
explicit composability pair bonus, weight tunable and OFF (0.0) until
Phase 2 tuning measures it (Q5). Composition-first contests (Q1) come
from the algebra's attach-first segmentation: an attach pair already
covering an expression's tokens suppresses the brief there, before any
territory skip.

Stage status: PROXY only. A candidate's saving is the upper bound — every
attach of its expressions merges cleanly (saves its stroke span), every
brief collapses its segment to one stroke — computed on real segmentations
of the pool (placeholder keypresses/brief strokes drive only the matching).
The exact stage (real keypress/brief-stroke choice, legality, collisions)
is Phase 2 Stage B; `ExprRule.keys`/`beta` stay None until then.
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass, field

from src.affixes import PREFIX, SUFFIX, SimContext
from src.affixrules import MAX_EXCEPTION_RATE
from src.ambiguitychecker import HASH_KEY, STAR_KEY
from src.expressions import (AttachRule, BriefRule, MERGED, RESERVED_MARK_KEYS,
                             Rules, STANDALONE, Token, composeOutlineTraced,
                             planStream)
from src.keyboard import Stroke, Strokes

# Q6 floors — tunable in one place.
MIN_LONGFORM_STROKES = 2      # expressions under 2 strokes never enter the queue
MIN_OCCURRENCES = 5_000_000   # ditto for window-occurrence counts

# Q4: the expression budget is SEPARATE from affixrules.RULE_BUDGET (30).
# User decision 2026-10-01: raised to 30, priority on the most frequent
# words/expressions (the greedy's marginal frequency-weighted saving IS
# that priority).
EXPR_RULE_BUDGET = 30

# Forced briefs (user decision 2026-10-01): tao entries too infrequent to
# win a frequency slot get INVENTED brief strokes from their OWN budget,
# separate from the selection budget; `deriveBriefStroke` is also the
# word-adding mechanic for later additions to the theory.
FORCED_BRIEF_BUDGET = 40

# Pricing in the affix sweep-D tradition (2026-09-30 user decision:
# exception alpha 2, fallback/exclusion price 5, form cost 100), extended
# with the family notion: a family's variants are its forms.
EXCEPTION_ALPHA = 2.0
EXCLUSION_COST = 5.0
FORM_COST = 100.0

# Q5: explicit composability pair bonus — rewards rule pairs whose joint use
# is frequent ("il y a" x ne…pas). Tunable; 0.0 = off until measured.
PAIR_BONUS_WEIGHT = 0.0

# Q2 families: one base keypress, variants separated by */# selector keys —
# at most 4 distinguishable variants per family (selectors: none, *, #, *#).
MAX_FAMILY_VARIANTS = 4

RULE_OVERLAP_MAX = 0.5        # territory-contest threshold (affix tradition)

# Proxy placeholders for the matching-only rules (never composed to strokes).
_PLACEHOLDER_KEYS = (2,)
_PLACEHOLDER_BETA = ((2,),)


@dataclass(frozen=True)
class PoolExpression:
    """One candidate-pool row the selection runs on: a word-unit sequence,
    its window frequency, and its tokens with longform strokes (Phase 0c)."""
    units: tuple[str, ...]
    freq: float
    tokens: tuple[Token, ...]

    @property
    def longformStrokes(self) -> int:
        return sum(len(t.strokes) for t in self.tokens)


@dataclass
class ExprRule:
    """A selection candidate: a brief (whole-expression strokes) or an
    attach particle run. Proxy-scored here; `keys`/`beta` and the exact
    score arrive with Stage B."""
    kind: str                       # "brief" | "attach"
    units: tuple[str, ...]
    position: str = ""              # attach only: PREFIX | SUFFIX
    family: str = ""                # Q2: variants of one learnable unit
    freq: float = 0.0               # window occurrences this rule would fire on
    strokesSaved: int = 0           # per-occurrence strokes saved (proxy: span)
    forms: int = 1                  # family variants (extra ones cost FORM_COST)
    keys: tuple[int, ...] | None = None    # attach kappa (Stage B)
    beta: tuple[tuple[int, ...], ...] | None = None  # brief strokes (Stage B)
    score: float = 0.0              # the accepted marginal total
    exactDone: bool = False         # Stage B ran (score is exact, not proxy)

    def proxyBrief(self) -> BriefRule:
        """The matching-only brief driving `planStream` in the proxy stage
        (placeholder stroke — the plan never composes strokes)."""
        assert self.kind == "brief"
        return BriefRule(self.units, _PLACEHOLDER_BETA, self.family)

    def proxyAttach(self) -> AttachRule:
        """The matching-only attach rule for the proxy stage (placeholder
        kappa)."""
        assert self.kind == "attach"
        return AttachRule(self.units, self.position, _PLACEHOLDER_KEYS, self.family)

    def toBrief(self) -> BriefRule:
        """The Phase 1 brief for real composition (after Stage B's brief
        stroke assignment)."""
        assert self.kind == "brief" and self.beta is not None
        return BriefRule(self.units, tuple(self.beta), self.family)

    def toAttach(self) -> AttachRule:
        """The Phase 1 attach rule for real composition (after Stage B's
        keypress assignment)."""
        assert self.kind == "attach" and self.keys is not None
        return AttachRule(self.units, self.position, self.keys, self.family)


# Stage B (keypress assignment). Q2: families share ONE base keypress on the
# 22 phoneme keys; variants are separated by */# selector keys, assigned in
# descending-frequency order (the strongest variant is the bare base form).
SELECTORS: tuple[tuple[int, ...], ...] = ((), (STAR_KEY,), (HASH_KEY,),
                                          (STAR_KEY, HASH_KEY))
SAMPLE_EXPRESSIONS = 30   # stage-1 sample per family (affix SAMPLE_CARRIERS spirit)
REPAIR_CANDIDATES = 20    # sample survivors fully evaluated; clean ones are repair candidates


def _familyGroups(selected: list[ExprRule]) -> list[list[ExprRule]]:
    """Attach rules grouped one group per budget slot: a family (head +
    absorbed variants) or a standalone rule. Briefs are NOT Stage B's job
    (their strokes come from the brief-derivation stage)."""
    groups: dict[str, list[ExprRule]] = {}
    order: list[str] = []
    for rule in selected:
        if rule.kind != "attach":
            continue
        key = rule.family or f"\0{rule.position}:{' '.join(rule.units)}"
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(rule)
    for key in order:
        groups[key].sort(key=lambda r: (-r.freq, r.units, r.position))
    return [groups[key] for key in order]


def assignKeypresses(selected: list[ExprRule], pool: list[PoolExpression],
                     ctx: SimContext, keypresses: list[Stroke],
                     selectors: tuple[tuple[int, ...], ...] = SELECTORS,
                     repairCandidates: int = REPAIR_CANDIDATES) -> dict:
    """Stage B: give every selected attach rule a real keypress. Per family:
    try every legal base chord; variants take base + selector in
    descending-frequency order; stage 1 on the top-frequency sample with
    the MAX_EXCEPTION_RATE gate (occurrence-weighted: exceptional-expression
    mass over touched mass), stage 2 on all touched expressions for the
    finalists; score = frequency-weighted saving - EXCEPTION_ALPHA x
    exception mass - FORM_COST x extra variants. Each family evaluates in
    ISOLATION (cross-family truth is Stage C's joint repair). Sets
    `keys`/`exactDone` on each rule; returns per-family diagnostics."""
    report: dict[str, dict] = {}
    for group in _familyGroups(selected):
        family = group[0].family or " ".join(group[0].units)
        variants = group[:len(selectors)]
        touched = sorted({i for r in variants
                          for i in touchedExpressions(r, pool)})
        touched.sort(key=lambda i: -pool[i].freq)
        sample = touched[:SAMPLE_EXPRESSIONS]

        def evaluate(base: Stroke, carrierIdx: list[int]) -> tuple[float, float, int]:
            """(score, exceptionRate, shadowCount) for this base over the
            given carriers, the family evaluated ISOLATED (only its own
            variants compose): evaluating alongside earlier-assigned
            families would strand hostless particle n-grams ("et de" with
            de consumed by the de family's rule) and trip the gate on pool
            fragments, and the order would distort which family merges
            where — cross-family truth is Stage C's joint repair.
            Trailing/leading pool FRAGMENTS (a prefix run ending the
            expression, a suffix run starting it — noNeighbour at the
            stream edge) are artifacts of the n-gram slices, not carriers:
            excluded from both masses. A composed outline that is an
            existing live outline (canonical index on `ctx.finalOutlines`)
            is a shadow (Q7: hard no) and is counted."""
            rules: tuple[AttachRule, ...] = tuple(
                AttachRule(r.units, r.position,
                           tuple(sorted(set(base) | set(selector))),
                           r.family)
                for r, selector in zip(variants, selectors))
            variantKeys = {(r.units, r.position) for r in variants}
            savingMass = 0.0
            exceptionMass = 0.0
            carrierMass = 0.0
            shadowCount = 0
            for i in carrierIdx:
                expr = pool[i]
                traced = composeOutlineTraced(Rules(attaches=rules),
                                              expr.tokens, ctx)
                ours = [seg for seg in traced.segments
                        if seg.kind == "attach" and isinstance(seg.rule, AttachRule)
                        and (seg.rule.expression, seg.rule.position) in variantKeys]
                if not ours:
                    continue
                if all(seg.outcome == "exception" and seg.reason == "noNeighbour"
                       and isinstance(rule := seg.rule, AttachRule)
                       and ((rule.position == PREFIX
                             and seg.span[1] == len(expr.tokens))
                            or (rule.position == SUFFIX and seg.span[0] == 0))
                       for seg in ours):
                    continue          # fragment artifact, not a carrier
                carrierMass += expr.freq
                savingMass += expr.freq * traced.saving
                if any(seg.outcome in (MERGED, STANDALONE) for seg in ours) \
                        and traced.strokes in ctx.finalOutlines:
                    shadowCount += 1
                if any(seg.outcome == "exception" for seg in ours):
                    exceptionMass += expr.freq
            score = (savingMass - EXCEPTION_ALPHA * exceptionMass
                     - FORM_COST * (len(variants) - 1))
            return (score, (exceptionMass / carrierMass) if carrierMass else 1.0,
                    shadowCount)

        stage1: list[tuple[float, Stroke]] = []
        for base in keypresses:
            score, rate, _shadows = evaluate(base, sample)
            if rate <= MAX_EXCEPTION_RATE and score > 0:
                stage1.append((score, base))
        stage1.sort(key=lambda t: (-t[0], t[1]))
        # Full evaluation of the sample survivors; a base is a repair
        # candidate only if the gate AND no-shadowing hold on ALL touched
        # expressions (Q7 hard no).
        alternatives: list[tuple[float, Stroke]] = []
        for _score, base in stage1[:repairCandidates]:
            score, rate, shadows = evaluate(base, touched)
            if rate <= MAX_EXCEPTION_RATE and shadows == 0:
                alternatives.append((score, base))
        best = min(alternatives, key=lambda t: (-t[0], t[1])) if alternatives else None
        info: dict[str, object] = {"variants": len(variants), "touched": len(touched)}
        if best is None:
            info["base"] = None
            report[family] = info
            continue
        score, base = best
        for rule, selector in zip(variants, selectors):
            rule.keys = tuple(sorted(set(base) | set(selector)))
            rule.exactDone = True
        variants[0].score = score
        info.update({"base": base, "score": score, "alternatives": alternatives})
        report[family] = info
    return report


def repairKeypresses(selected: list[ExprRule], report: dict,
                     selectors: tuple[tuple[int, ...], ...] = SELECTORS,
                     disjointPairs: frozenset[frozenset[str]] = frozenset(),
                     ) -> dict[str, tuple[int, ...]]:
    """Stage C joint repair: re-assign the families' bases so variants of
    DIFFERENT families never share an effective keypress (base + selector)
    — the cross-family union trap: hosts are productive (Q10), so any two
    rules can meet on one host, and a 1-stroke host collapses prefix and
    suffix into the same chord; equal effective keypresses then write
    different particles identically.

    CP-SAT in the featuregroupingsat tradition: one integer variable per
    family over its Stage B candidate bases (gate- and shadow-clean,
    score-ranked); pairwise add_allowed_assignments forbid base
    combinations whose effective variant sets collide; `disjointPairs`
    (family-name pairs) tightens collision to INTERSECTION for pairs that
    co-occur on one stroke (Q3's ne x pas finding: ne=(2,8,17) and
    pas=(2,9) share key 2, so on a 1-stroke host the second merge
    keyOverlaps and degrades to an exception — disjoint keys let BOTH
    rules merge into the same stroke); the objective maximizes total
    score with a candidate-rank tie-break (deterministic; the Stage B
    winner hints the solver). Returns family -> chosen base; families
    with no candidates keep their Stage B state (None stays None)."""
    from ortools.sat.python import cp_model

    groups = _familyGroups(selected)
    fams: list[tuple[str, list[ExprRule], list[tuple[float, Stroke]]]] = []
    for group in groups:
        name = group[0].family or " ".join(group[0].units)
        info = report.get(name, {})
        bases = [b for b in info.get("alternatives", [])]  # type: ignore[union-attr]
        if bases:
            fams.append((name, group[:len(selectors)], bases))

    model = cp_model.CpModel()
    baseVars = []
    effSets: list[list[tuple[tuple[int, ...], ...]]] = []
    scoreInts: list[list[int]] = []
    for i, (_name, group, bases) in enumerate(fams):
        var = model.new_int_var(0, len(bases) - 1, f"family{i}")
        baseVars.append(var)
        effSets.append([tuple(tuple(sorted(set(base) | set(sel)))
                              for sel in selectors[:len(group)])
                        for _s, base in bases])
        scoreInts.append([int(round(s * 1e-6)) for s, _b in bases])
    # Stage B winners as determinism hints.
    for var, (name, _group, bases) in zip(baseVars, fams):
        stageB = report.get(name, {}).get("base")
        if stageB in [b for _s, b in bases]:
            model.add_hint(var, [b for _s, b in bases].index(stageB))

    for i in range(len(baseVars)):
        for j in range(i + 1, len(baseVars)):
            names = {fams[i][0], fams[j][0]}
            mustDisjoint = frozenset(names) in disjointPairs
            allowed = []
            for a in range(len(effSets[i])):
                for b in range(len(effSets[j])):
                    # syllabic keys only: the composer's overlap check is
                    # reserved-key-transparent (_syllabic), so */# selectors
                    # never block stacking -- only shared phoneme keys do
                    keysA = {k for kappa in effSets[i][a] for k in kappa
                             if k not in RESERVED_MARK_KEYS}
                    keysB = {k for kappa in effSets[j][b] for k in kappa
                             if k not in RESERVED_MARK_KEYS}
                    if mustDisjoint:
                        # no KEY overlap at all: both families can stack
                        # their merges on one stroke
                        if not (keysA & keysB):
                            allowed.append((a, b))
                    elif not any(set(k1) == set(k2) for k1 in effSets[i][a]
                                 for k2 in effSets[j][b]):
                        # equality collision only: some effective keypress
                        # appears in both families' variant sets
                        allowed.append((a, b))
            model.add_allowed_assignments([baseVars[i], baseVars[j]], allowed)

    objective = []
    for k, (var, scores) in enumerate(zip(baseVars, scoreInts)):
        s = model.new_int_var(min(scores), max(scores), f"score{k}")
        model.add_element(var, scores, s)
        objective.append(s)
    ranks = []
    for k, (var, scores) in enumerate(zip(baseVars, scoreInts)):
        r = model.new_int_var(0, len(scores) - 1, f"rank{k}")
        model.add_element(var, list(range(len(scores))), r)
        ranks.append(r)
    model.maximize(sum(objective) * 100 - sum(ranks))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 120.0
    status = solver.Solve(model)
    chosen: dict[str, tuple[int, ...]] = {}
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print(f"  repair solver status: {solver.StatusName(status)} "
              f"({solver.WallTime():.1f}s)", flush=True)
        return chosen
    for var, (name, group, bases) in zip(baseVars, fams):
        base = bases[solver.Value(var)][1]
        for rule, selector in zip(group, selectors):
            rule.keys = tuple(sorted(set(base) | set(selector)))
        chosen[name] = base
    return chosen


def deriveBriefStroke(expr: PoolExpression, ctx: SimContext,
                      takenStrokes: set[Stroke],
                      freeChords: list[Stroke] | tuple[()] = (),
                      ) -> tuple[Stroke, str] | None:
    """The brief-creation mechanic (user decision 2026-10-01): invent ONE
    standalone stroke for a FORCED expression — tao entries too infrequent
    to win a frequency slot, or a word added to the theory later. Q9's
    mnemonic AND free-chord derivations, in preference order:

      1. `union` — every member word's first-stroke keys pressed together;
      2. `skeleton` — first word's first stroke + last word's last stroke;
      3. `vowels` — the expression's nucleus keys, first occurrence order;
      4. `free` — legal chords from `freeChords` (smallest first, then key
         order; deterministic), the free-chord fallback.

    A candidate must be a legal chord, must not be a live single-stroke
    outline (Q7 no-shadowing -- `ctx.finalOutlines` is the canonical live
    index), and must not be taken by another brief.
    Single stroke only (multi-stroke briefs, Q8, would need boundary-risk
    gating — none of the forced entries need it). Returns (stroke,
    derivation label) or None."""
    tokens = expr.tokens

    def acceptable(keys: tuple[int, ...]) -> Stroke | None:
        stroke = tuple(sorted(set(keys)))
        # reserved keys are legality-transparent (the composer's convention)
        syllabic = tuple(k for k in stroke if k not in RESERVED_MARK_KEYS)
        if not stroke or not ctx.isLegal(syllabic):
            return None
        if stroke in ctx.singleStrokeOutlines or (stroke,) in ctx.finalOutlines:
            return None
        if stroke in takenStrokes:
            return None
        return stroke

    candidates: list[tuple[Stroke, str]] = []
    union = tuple(k for t in tokens for k in t.strokes[0])
    if (stroke := acceptable(union)) is not None:
        candidates.append((stroke, "union"))
    skeleton = tuple(set(tokens[0].strokes[0]) | set(tokens[-1].strokes[-1]))
    if (stroke := acceptable(skeleton)) is not None and (not candidates or candidates[0][0] != stroke):
        candidates.append((stroke, "skeleton"))
    nucleus = set(ctx.starboard.keyIDinSyllabicPart["nucleus"])
    vowels = []
    for token in tokens:
        for stroke in token.strokes:
            for key in stroke:
                if key in nucleus and key not in vowels:
                    vowels.append(key)
    if (stroke := acceptable(tuple(vowels))) is not None and all(stroke != s for s, _ in candidates):
        candidates.append((stroke, "vowels"))
    if candidates:
        return candidates[0]
    for chord in sorted(freeChords, key=lambda c: (len(c), c)):
        if (stroke := acceptable(chord)) is not None:
            return stroke, "free"
    return None


@dataclass
class ExprAudit:
    """Stage C audit of the FINAL rule set over the whole pool, all
    families composing together for the first time (the Phase 3 preview)."""
    savingMass: float = 0.0            # frequency-weighted strokes saved
    longformMass: float = 0.0          # the same pool written longform
    exceptions: int = 0                # attach segments that kept longform
    shadows: list[tuple[tuple[str, ...], Strokes]] = field(default_factory=list)
    collisions: dict[Strokes, list[tuple[str, ...]]] = field(default_factory=dict)


def auditExpressionRules(selected: list[ExprRule], pool: list[PoolExpression],
                         ctx: SimContext) -> ExprAudit:
    """Compose every pool expression under the final attach rules (jointly);
    verify Q7 (no composed outline is a live outline) and global injectivity
    (no two different expressions compose alike), and total the savings.
    `ctx.finalOutlines` must be the CANONICAL live-outline index."""
    rules = Rules(attaches=tuple(r.toAttach() for r in selected
                                 if r.kind == "attach" and r.keys is not None))
    audit = ExprAudit()
    byOutline: dict[Strokes, list[tuple[str, ...]]] = {}
    for expr in pool:
        traced = composeOutlineTraced(rules, expr.tokens, ctx)
        if traced.strokes is None:
            continue                      # cannot happen over the resolved pool
        audit.savingMass += expr.freq * traced.saving
        audit.longformMass += expr.freq * expr.longformStrokes
        audit.exceptions += traced.exceptions
        if traced.saving > 0 and traced.strokes in ctx.finalOutlines:
            audit.shadows.append((expr.units, traced.strokes))
        byOutline.setdefault(traced.strokes, []).append(expr.units)
    audit.collisions = {o: us for o, us in byOutline.items() if len(set(us)) > 1}
    return audit


@dataclass
class ExprSelectionResult:
    selected: list[ExprRule] = field(default_factory=list)
    curve: list[float] = field(default_factory=list)   # running credited total
    skips: list[tuple[str, str, float]] = field(default_factory=list)  # territory
    evaluated: int = 0


def briefCandidates(pool: list[PoolExpression]) -> list[ExprRule]:
    """Whole-expression briefs from the pool: multi-unit expressions past
    both floors. Single words are the affix system's domain, never briefed
    here. A brief's proxy per-occurrence saving collapses the whole
    expression to one stroke."""
    out: list[ExprRule] = []
    for expr in pool:
        if len(expr.units) < 2:
            continue
        if expr.longformStrokes < MIN_LONGFORM_STROKES or expr.freq < MIN_OCCURRENCES:
            continue
        out.append(ExprRule("brief", expr.units, freq=expr.freq,
                            strokesSaved=expr.longformStrokes - 1))
    out.sort(key=lambda r: (-r.freq, r.units))
    return out


def attachCandidates(pool: list[PoolExpression], particles: frozenset[str],
                     familyOf=None) -> list[ExprRule]:
    """Attach-rule candidates: PROPER prefix/suffix runs of pool expressions
    (a proper run leaves a non-empty remainder), keyed by (run, position) —
    a run seen at an edge is a candidate for that edge only. A run's
    frequency evidence is the sum over expressions carrying it at that edge;
    a run that is itself a pool entry uses its own (true) occurrence count —
    every occurrence of "de la" is a potential prefix use. Every unit of a
    run must be an elision unit or one of `particles` (function words):
    particle runs, not content words. Proxy per-occurrence saving = the
    run's stroke span (merge assumed clean)."""
    evidence: dict[tuple[tuple[str, ...], str], float] = {}
    for expr in pool:
        for k in range(1, len(expr.units)):
            prefix, suffix = expr.units[:k], expr.units[k:]
            if all(u in particles or "'" in u for u in prefix):
                evidence[(prefix, PREFIX)] = evidence.get((prefix, PREFIX), 0.0) + expr.freq
            if all(u in particles or "'" in u for u in suffix):
                evidence[(suffix, SUFFIX)] = evidence.get((suffix, SUFFIX), 0.0) + expr.freq
    poolByUnits = {e.units: e for e in pool}
    out: list[ExprRule] = []
    for (units, position), freq in evidence.items():
        if len(units) > 6:      # a six-unit particle run is already a brief's job
            continue
        standalone = poolByUnits.get(units)
        # A standalone entry's own count SUPERSEDES the summed evidence: every
        # occurrence of "de la" is a potential use, and the summed contexts
        # are nested inside it (they would double-count). Without a
        # standalone entry the sum undercounts (top-slice contexts only) —
        # an acceptable proxy bound, like the affix proxy's.
        bound = standalone.freq if standalone else freq
        if bound < MIN_OCCURRENCES:
            continue
        span = standalone.longformStrokes if standalone else len(units)
        out.append(ExprRule("attach", units, position=position, freq=bound,
                            strokesSaved=span,
                            family=familyOf(units) if familyOf else ""))
    out.sort(key=lambda r: (-r.freq, r.units, r.position))
    return out


def touchedExpressions(rule: ExprRule, pool: list[PoolExpression]) -> set[int]:
    """Pool indexes whose segmentation `rule` can enter — a pruning index
    only (marginals always come from real segmentations). An attach needs a
    contiguous run with its position's edge validity (a prefix has a
    following token, a suffix a preceding one). A BRIEF matches the residual
    stream after attach consumption, so its units may interleave with
    particle units ("il n'y a paS" touches brief (il, y, a)) — subsequence
    containment is the safe over-approximation."""
    n, want = len(rule.units), rule.units
    touched: set[int] = set()
    for i, expr in enumerate(pool):
        units = expr.units
        if rule.kind == "brief":
            it = iter(units)
            if all(u in it for u in want):
                touched.add(i)
            continue
        if len(units) < n:
            continue
        for start in range(len(units) - n + 1):
            if units[start:start + n] != want:
                continue
            if rule.position == PREFIX and start + n == len(units):
                continue  # a prefix with nothing after it has no host
            if rule.position == SUFFIX and start == 0:
                continue  # a suffix with nothing before it has no host
            touched.add(i)
            break
    return touched


def proxySaving(briefs: tuple[BriefRule, ...], attaches: tuple[AttachRule, ...],
                expr: PoolExpression) -> float:
    """Upper-bound saving on one expression: every attach WITH a merge
    target merges cleanly (its stroke span vanishes); an attach with no
    host (the ladder's noNeighbour — a trailing prefix, a suffix with
    nothing before it) keeps its longform and saves nothing. Every brief
    segment collapses to len(beta) strokes. Real segmentation, placeholder
    chords."""
    plan = planStream(Rules(briefs=briefs, attaches=attaches), list(expr.tokens))
    tokens = list(expr.tokens)
    saving = 0
    for kind, payload, extra in plan.entries:
        if kind == "attach":
            rule, (start, end) = payload, extra
            if rule.position == PREFIX:
                i = bisect_left(plan.residual, end)
                if i >= len(plan.residual):
                    continue          # no host after it — longform stays
            else:
                i = bisect_left(plan.residual, start) - 1
                if i < 0:
                    continue          # no host before it — longform stays
            saving += sum(len(t.strokes) for t in tokens[start:end])
        else:
            segTokens, brief = payload, extra
            if brief is not None:
                saving += (sum(len(t.strokes) for t in segTokens)
                           - len(brief.strokes))
    return saving


def jointFrequency(a: ExprRule, b: ExprRule, pool: list[PoolExpression]) -> float:
    """Q5's joint-use frequency: occurrences where BOTH rules can enter the
    segmentation (composability evidence, e.g. "il y a" x ne…pas on
    "il n'y a pas")."""
    ta, tb = touchedExpressions(a, pool), touchedExpressions(b, pool)
    return sum(pool[i].freq for i in ta & tb)


def matchedSpans(rule: ExprRule, units: tuple[str, ...]) -> list[tuple[int, int]]:
    """Token spans [start, end) `rule` would consume in `units` — the
    pruning view used for territory contests: attaches as contiguous
    edge-valid runs; a brief as the first..last cover of one subsequence
    occurrence (its real span is contextual, after attach consumption)."""
    n, want = len(rule.units), rule.units
    if rule.kind == "brief":
        pos, idxs = 0, []
        for u in want:
            while pos < len(units) and units[pos] != u:
                pos += 1
            if pos == len(units):
                return []
            idxs.append(pos)
            pos += 1
        return [(idxs[0], idxs[-1] + 1)]
    spans: list[tuple[int, int]] = []
    for start in range(len(units) - n + 1):
        if units[start:start + n] != want:
            continue
        if rule.position == PREFIX and start + n == len(units):
            continue
        if rule.position == SUFFIX and start == 0:
            continue
        spans.append((start, start + n))
    return spans


def territoryOverlap(spansA: list[list[tuple[int, int]]],
                     spansB: list[list[tuple[int, int]]],
                     pool: list[PoolExpression]) -> float:
    """Frequency-weighted share (of the smaller rule's touched mass) of
    occurrences where the two rules' consumed token spans INTERSECT — a
    contest for the same tokens. Composing rules score 0 and never skip
    each other: ne + pas hold disjoint spans around a host; a prefix and a
    suffix never share tokens; a brief and an attach that compose
    ("il y a" x pas) are disjoint too."""
    massA = massB = shared = 0.0
    for spans_a, spans_b, expr in zip(spansA, spansB, pool):
        if not spans_a or not spans_b:
            continue
        massA += expr.freq
        massB += expr.freq
        if any(x[0] < y[1] and y[0] < x[1] for x in spans_a for y in spans_b):
            shared += expr.freq
    smaller = min(massA, massB)
    return shared / smaller if smaller > 0 else 0.0


def pruneRedundantVariants(selected: list[ExprRule], pool: list[PoolExpression],
                           savingAt=proxySaving) -> list[ExprRule]:
    """Drop absorbed family variants (forms == 0) whose removal leaves the
    pool's total saving unchanged — their work is done by other selected
    rules composing (greedy absorption is myopic: "et à" absorbed into the
    et family before the et and à attaches were themselves selected). The
    swapPass spirit, applied to variants; heads and standalone rules stay.
    """
    changed = True
    while changed:
        changed = False
        variants = [r for r in selected if r.family and r.forms == 0]
        for v in reversed(variants):
            without = [r for r in selected if r is not v]
            briefsAll = tuple(r.proxyBrief() for r in selected if r.kind == "brief")
            attachesAll = tuple(r.proxyAttach() for r in selected if r.kind == "attach")
            briefsWithout = tuple(r.proxyBrief() for r in without if r.kind == "brief")
            attachesWithout = tuple(r.proxyAttach() for r in without if r.kind == "attach")
            loss = 0.0
            for i in touchedExpressions(v, pool):
                withV = savingAt(briefsAll, attachesAll, pool[i])
                sansV = savingAt(briefsWithout, attachesWithout, pool[i])
                loss += pool[i].freq * (withV - sansV)
            if loss <= 0:
                selected = without
                changed = True
    # keep the head's form count honest after drops
    for head in (r for r in selected if r.forms > 0):
        head.forms = sum(1 for r in selected if r.family == head.family) \
            if head.family else head.forms
    return selected


def selectExpressionRules(
    candidates: list[ExprRule],
    pool: list[PoolExpression],
    budget: int = EXPR_RULE_BUDGET,
    savingAt=proxySaving,
) -> ExprSelectionResult:
    """Greedy budgeted selection in the `selectRules` tradition, evaluated on
    real segmentations of the pool: each round takes the candidate whose
    FRESH marginal (extra frequency-weighted strokes over the pool under the
    current selection, once-credited per expression) is best, skips territory
    mates at RULE_OVERLAP_MAX (the biggest overlap, like `territoryMate`),
    adds the composability pair bonus (Q5, weight 0 = off), and stops at the
    budget or when no positive marginal remains.

    `savingAt(briefs, attaches, expr)` is injectable so tests can run
    without a keyboard; production uses `proxySaving` (Stage A).
    """
    touchedOf = [touchedExpressions(c, pool) for c in candidates]
    spansOf = [[matchedSpans(c, e.units) for e in pool] for c in candidates]
    # Deterministic order regardless of caller input ordering.
    order = sorted(range(len(candidates)),
                   key=lambda i: (-candidates[i].freq, candidates[i].units,
                                  candidates[i].position))
    candOf = [candidates[i] for i in order]
    touchedOf = [touchedOf[i] for i in order]
    spansOf = [spansOf[i] for i in order]
    currentSaving = [0.0] * len(pool)
    briefs: tuple[BriefRule, ...] = ()
    attaches: tuple[AttachRule, ...] = ()

    selected: list[ExprRule] = []
    selectedSpans: list[list[list[tuple[int, int]]]] = []
    result = ExprSelectionResult(evaluated=len(candidates))
    slots = 0        # budget units: a family (head + absorbed variants) is ONE
    closed: set[str] = set()   # families already selected — never re-opened
    while candOf and slots < budget:
        if closed:
            keep = [i for i, c in enumerate(candOf)
                    if not (c.family and c.family in closed)]
            if len(keep) != len(candOf):
                candOf = [candOf[i] for i in keep]
                touchedOf = [touchedOf[i] for i in keep]
                spansOf = [spansOf[i] for i in keep]
        bestIdx: int | None = None
        bestMarg = 0.0
        for i, cand in enumerate(candOf):
            candBriefs = briefs + ((cand.proxyBrief(),) if cand.kind == "brief" else ())
            candAttaches = attaches + ((cand.proxyAttach(),) if cand.kind == "attach" else ())
            marginal = 0.0
            for e in touchedOf[i]:
                extra = savingAt(candBriefs, candAttaches, pool[e]) - currentSaving[e]
                if extra > 0:
                    marginal += pool[e].freq * extra
            marginal -= FORM_COST * (cand.forms - 1)
            if PAIR_BONUS_WEIGHT and selected:
                marginal += PAIR_BONUS_WEIGHT * sum(
                    jointFrequency(cand, s, pool) for s in selected)
            if marginal > bestMarg:
                bestMarg, bestIdx = marginal, i
        if bestIdx is None:
            break
        cand, touched = candOf.pop(bestIdx), touchedOf.pop(bestIdx)
        spans = spansOf.pop(bestIdx)
        mate: tuple[ExprRule, float] | None = None
        for s, sSpans in zip(selected, selectedSpans):
            ov = territoryOverlap(spans, sSpans, pool)
            if ov >= RULE_OVERLAP_MAX and (mate is None or ov > mate[1]):
                mate = (s, ov)
        if mate is not None:
            result.skips.append((" ".join(cand.units), " ".join(mate[0].units), mate[1]))
            continue
        cand.score = bestMarg
        selected.append(cand)
        selectedSpans.append(spans)
        slots += 1
        if cand.kind == "brief":
            briefs = briefs + (cand.proxyBrief(),)
        else:
            attaches = attaches + (cand.proxyAttach(),)
        for e in touched:
            currentSaving[e] = savingAt(briefs, attaches, pool[e])

        # Q2 family bundling: the accepted rule's family is ONE budget slot —
        # greedily absorb siblings whose fresh marginal still clears
        # FORM_COST (variants are forms); drop the rest for good; at most
        # MAX_FAMILY_VARIANTS variants (the */# selector budget).
        if cand.family:
            cand.forms = 1
            closed.add(cand.family)
            sibIdx = 0
            while sibIdx < len(candOf) and cand.forms < MAX_FAMILY_VARIANTS:
                sib = candOf[sibIdx]
                if sib.family != cand.family or sib.kind != cand.kind:
                    sibIdx += 1
                    continue
                sibBriefs = briefs + ((sib.proxyBrief(),) if sib.kind == "brief" else ())
                sibAttaches = attaches + ((sib.proxyAttach(),) if sib.kind == "attach" else ())
                sibMarg = 0.0
                for e in touchedOf[sibIdx]:
                    extra = savingAt(sibBriefs, sibAttaches, pool[e]) - currentSaving[e]
                    if extra > 0:
                        sibMarg += pool[e].freq * extra
                candOf.pop(sibIdx)
                sibTouched = touchedOf.pop(sibIdx)
                spansOf.pop(sibIdx)
                if sibMarg - FORM_COST > 0:
                    sib.score = sibMarg - FORM_COST
                    sib.forms = 0          # the family's form count lives on the head
                    cand.forms += 1
                    selected.append(sib)
                    selectedSpans.append([])
                    if sib.kind == "brief":
                        briefs = briefs + (sib.proxyBrief(),)
                    else:
                        attaches = attaches + (sib.proxyAttach(),)
                    for e in sibTouched:
                        currentSaving[e] = savingAt(briefs, attaches, pool[e])
                # else: dropped permanently — the family is closed to it
        result.curve.append(sum(currentSaving[e] * pool[e].freq
                                for e in range(len(pool))))
    result.selected = pruneRedundantVariants(selected, pool, savingAt)
    return result
