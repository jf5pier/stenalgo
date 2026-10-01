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

from src.affixes import PREFIX, SUFFIX
from src.expressions import AttachRule, BriefRule, Rules, Token, planStream

# Q6 floors — tunable in one place.
MIN_LONGFORM_STROKES = 2      # expressions under 2 strokes never enter the queue
MIN_OCCURRENCES = 5_000_000   # ditto for window-occurrence counts

# Q4: the expression budget is SEPARATE from affixrules.RULE_BUDGET (30).
# Mid-range placeholder of the user's ~10-20; the number is theirs to fix.
EXPR_RULE_BUDGET = 15

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

    def toRule(self) -> BriefRule | AttachRule:
        """The Phase 1 rule object for real composition (Stage B fields)."""
        if self.kind == "brief":
            assert self.beta is not None, "Stage B must assign the brief stroke first"
            return BriefRule(self.units, tuple(self.beta), self.family)
        assert self.keys is not None, "Stage B must assign the keypress first"
        return AttachRule(self.units, self.position, self.keys, self.family)


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
