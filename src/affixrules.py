"""
Phases 2-4 (docs/history/DESIGN_2026-09-27-affix-rule-selection.md §4-6): turn the Phase-1 lattice pool into a
budgeted, keypress-bound set of rules.

- Phase 2 (§4): turn a pool node into a candidate rule -- a root plus a small set of its lattice
  descendants ("forms") sharing one keypress, grown by a cheap Part-A-only proxy score, with the
  expensive keyboard evaluation (§4.4 step 4) done lazily.
- Phase 3 (§5): `selectRules` -- a lazy-greedy budgeted selection over all roots, crediting each
  word once at its best selected rule.
- Phase 4 (§6): `bindKeypresses` -- assigns each selected rule its keypress, allowing two rules of
  the same position to share one when a joint simulation loses at most `SPLIT_MAX_LOSS` of either.

MEASUREMENT AND PROPOSALS ONLY -- nothing here is wired into the theory.
"""
import heapq
import multiprocessing
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Callable, Iterator

from src.affixbinding import (
    MAX_ALTERNATIVES, SAMPLE_CARRIERS, SPLIT_MAX_LOSS, PhonemeKeys, salientPhonemes, simScore)
from src.affixes import (
    Binding, Candidate, Carrier, CarrierResult, RULE, SimContext, SimUnit, _exceptionShare, PREFIX,
    makeSimUnit, mergeUnions, poolCarriers, simulate, simulateRuleBase, simulateRuleDelta, ruleKeysOverlap)
from src.affixdecisions import Decisions
from src.keyboard import Stroke

RULE_BUDGET = 30
EXCEPTION_ALPHA = 2.0       # the user's decided prices (2026-09-30, "setting D"): exception weight 2,
EXCLUSION_COST = 5.0        # fallback / slot-exclusion price 5,
FORM_COST = 100.0           # form price 100 (stroke-frequency units)
MAX_EXCEPTION_RATE = 0.05   # 2026-09-27 (user decision): a rule's exception rate -- exceptions /
                            # (covered + exceptions) -- must not exceed this, full stop, whatever
                            # its score. Found empirically on "re": the highest-similarity key
                            # (R, the prefix's own onset -- similarity rank 27/1751) had an 18.7%
                            # rate (875 exceptions on common words: reviens, revient, retrouve...),
                            # while a key with ~zero phonetic similarity (rank 926/1751) scored
                            # HIGHER (5917.9 vs 4199.4) and cleared this bar easily -- similarity
                            # was actively hiding the better answer, not just failing to help.
                            # Superseded SIM_TOP_N/SIM_MIN entirely: similarity is no longer any
                            # kind of gate on which keys get simulated (see chooseRuleKeypress),
                            # only a label on the final pick for human review (rule.keySimilarity).
SWAP_CANDIDATES = 20
SWAP_PASSES = 3
RULE_OVERLAP_MAX = 0.5      # 2026-09-28: a rule whose carriers overlap a selected same-position rule
                            # this much (frequency-weighted, as a share of the smaller rule) is
                            # SKIPPED, never merged. With one generator, only anchors are roots and
                            # merged-vs-parts rivalry is settled up front (resolveVariantRivals), so
                            # this is a safety net: expect about zero skips.

# Word exceptions (§4.3): collision fallbacks only. keyOverlap/illegalChord go standalone instead
# (§4.2) and are never counted here.
WORD_EXCEPTION_REASONS = frozenset({"lostDistinction", "markCostTooHigh", "standaloneTrap"})


def candidateKey(c: Candidate) -> tuple[str, int, str, str]:
    return (c.position, c.k, c.phono, c.ortho)


def childrenIndex(
    pool: dict[tuple[str, int, str, str], Candidate],
) -> dict[tuple[str, int, str, str], list[Candidate]]:
    """Direct-child lookup by `grownFromKey`, for walking a root's descendants regardless of the
    root's own depth (§4.4: "every pool node is a potential root")."""
    idx: dict[tuple[str, int, str, str], list[Candidate]] = {}
    for c in pool.values():
        for parent in ([c.grownFromKey] if c.grownFromKey is not None else []) + c.alsoFrom:
            idx.setdefault(parent, []).append(c)
    return idx


def descendantsOf(root: Candidate, childrenIdx: dict[tuple[str, int, str, str], list[Candidate]]) -> list[Candidate]:
    """All descendants of `root` at any depth (its whole grown subtree)."""
    out: list[Candidate] = []
    seen: set[tuple[str, int, str, str]] = {candidateKey(root)}
    stack = list(childrenIdx.get(candidateKey(root), []))
    while stack:
        c = stack.pop()
        if candidateKey(c) in seen:      # a folded duplicate can be reached through two parents
            continue
        seen.add(candidateKey(c))
        out.append(c)
        stack.extend(childrenIdx.get(candidateKey(c), []))
    return out


def exclusionCountOf(forms: list[Candidate]) -> int:
    return sum(len(s.excluded) for f in forms for s in f.slots)


def proxyScore(pos: str, forms: list[Candidate]) -> float:
    """§4.4 step 2: the Part-A-only proxy score, before a keypress is known -- sum(f x span) over
    the pooled (longest-form-wins, D5) carriers, minus the collision, exclusion and form costs."""
    carriers = poolCarriers(forms)
    if not carriers:
        return -FORM_COST * (len(forms) - 1)
    benefit = sum(c.rec.frequency * c.span for c in carriers)
    denom = sum(c.rec.frequency for c in carriers) or 1.0
    share, excSet = _exceptionShare(pos, carriers, denom)
    exceptionFreq = sum(c.rec.frequency for c in carriers if c.rec.idx in excSet)
    return (benefit - EXCEPTION_ALPHA * exceptionFreq - EXCLUSION_COST * exclusionCountOf(forms)
            - FORM_COST * (len(forms) - 1))


@dataclass
class Rule:
    position: str
    root: Candidate
    forms: list[Candidate]
    keys: tuple[int, ...] | None = None
    score: float = 0.0
    strokeFreqSaved: float = 0.0
    wordExceptions: int = 0
    exceptionFreq: float = 0.0
    topExceptions: list[str] = field(default_factory=list)
    results: list[CarrierResult] = field(default_factory=list)
    alternatives: list[tuple[float, tuple[int, ...]]] = field(default_factory=list)
    keySimilarity: float = 0.0   # the chosen key's phonetic-similarity score (not gated -- see
                                 # SIM_TOP_N -- so a low value here flags a non-mnemonic key)
    exactDone: bool = False      # chooseRuleKeypress already ran (score/keys are exact, not proxy)
    fallbacks: int = 0           # scoped-form carriers that gained nothing under `keys` and kept the anchor alone;
                                 # each costs EXCLUSION_COST like a slot exclusion (the user's "fallback price")
    _wordFreq: dict[int, float] | None = field(default=None, repr=False, compare=False)

    def wordFreq(self) -> dict[int, float]:
        """rec.idx -> frequency over the pooled carriers (cached: forms never change in place)."""
        if self._wordFreq is None:
            self._wordFreq = {c.rec.idx: c.rec.frequency for c in poolCarriers(self.forms)}
        return self._wordFreq


def buildCandidateRule(
    root: Candidate, childrenIdx: dict[tuple[str, int, str, str], list[Candidate]],
) -> Rule:
    """A rule = its anchor plus the decided growth forms (`affix_decisions.json`), in the table's order. No
    growth without a verdict: an undecided anchor is a rule of the anchor alone."""
    forms = [root] + [c for c in descendantsOf(root, childrenIdx) if c.isScoped]
    return Rule(root.position, root, forms, score=proxyScore(root.position, forms))


def ruleExclusions(rule: Rule) -> int:
    """Slot exclusions plus scope fallbacks: the words the learner must know as exceptions to the forms."""
    return exclusionCountOf(rule.forms) + rule.fallbacks


def resolveFallbacks(
    rule: Rule, keys: Stroke, carriers: list[Carrier], ctx: SimContext,
) -> tuple[list[Carrier], int]:
    """A carrier of a scoped form (span > 1) that gains nothing under `keys` reverts to the anchor alone
    (the user's "fallback"; `affixdecisions`). Returns the carriers with those replaced and their count; a
    rule without scoped forms is returned untouched, without simulating."""
    if not any(f.isScoped for f in rule.forms):
        return carriers, 0
    (res,) = simulate([(Binding(rule.position, RULE, keys), carriers)], ctx, boundaryRisk=False)
    failed = {r.carrier.rec.idx for r in res
              if r.carrier.span > 1 and r.gain <= 0 and rule.forms[r.carrier.member].isScoped}
    if not failed:
        return carriers, 0
    anchor = {c.rec.idx: c._replace(member=0) for c in rule.root.carriers}
    return [anchor[c.rec.idx] if c.rec.idx in failed else c for c in carriers], len(failed)


def ruleScoreFromResults(
    results: list[CarrierResult], exclusionCount: int, numForms: int,
) -> tuple[float, float, int, float, list[str]]:
    """§4.3: (score, strokeFreqSaved, wordExceptionCount, exceptionFreq, top10 exception orthos)."""
    benefit = 0.0
    exceptions: list[tuple[float, str]] = []
    for r in results:
        f = r.carrier.rec.frequency
        if r.gain > 0:
            benefit += f * r.gain
        elif r.reason in WORD_EXCEPTION_REASONS:
            exceptions.append((f, r.carrier.rec.ortho))
    exceptionFreq = sum(f for f, _ in exceptions)
    exceptions.sort(key=lambda t: -t[0])
    score = (benefit - EXCEPTION_ALPHA * exceptionFreq - EXCLUSION_COST * exclusionCount
             - FORM_COST * (numForms - 1))
    return score, benefit, len(exceptions), exceptionFreq, [o for _f, o in exceptions[:10]]


def _exceptionRate(results: list[CarrierResult]) -> float:
    """exceptions / (covered + exceptions) -- MAX_EXCEPTION_RATE's unit."""
    covered = sum(1 for r in results if r.gain > 0)
    exceptions = sum(1 for r in results if r.reason in WORD_EXCEPTION_REASONS)
    total = covered + exceptions
    return exceptions / total if total else 0.0


def _neighbourGroups(position: str, carriers: list[Carrier]) -> dict[tuple[Stroke | None, bool], int]:
    """Carriers counted by what `_newBase` looks at for a RULE binding: the neighbouring stroke
    (None when the carrier has no neighbour) and whether the carrier is a single syllable."""
    groups: dict[tuple[Stroke | None, bool], int] = {}
    for c in carriers:
        base = c.rec.base
        ni = c.start + c.span if position == PREFIX else c.start - 1
        key = (base[ni] if 0 <= ni < len(base) else None, c.span == 1)
        groups[key] = groups.get(key, 0) + 1
    return groups


def _exceptionRateFloor(
    groups: dict[tuple[Stroke | None, bool], int], keys: Stroke, ctx: SimContext,
) -> float:
    """Lower bound on `_exceptionRate` of `simulate` for a RULE binding of `keys`, from the pass-1
    classification of `_newBase` alone (evaluated per neighbour group, not per carrier).
    The rate is exceptions / (gaining + exceptions). Every carrier with a valid new base ends as a
    gainer or as a `lostDistinction`/`markCostTooHigh` exception, and `standaloneTrap` is decided
    in pass 1, so the denominator is fixed by pass 1 while the numerator can only grow in pass 2."""
    keySet = set(keys)
    trapKey = tuple(sorted(keys)) in ctx.singleStrokeOutlines
    valid = trapped = 0
    for (neighbour, single), n in groups.items():
        if neighbour is None:
            continue   # noNeighbour: neither a gain candidate nor an exception
        if ruleKeysOverlap(neighbour, keys, ctx.partialOverlap) or not ctx.isLegal(tuple(sorted(set(neighbour) | keySet))):
            if single or trapKey:
                trapped += n   # standaloneTrap
            else:
                valid += n     # falls back to a standalone stroke
        else:
            valid += n
    total = valid + trapped
    return trapped / total if total else 0.0


@dataclass
class KeySweep:
    """The key-independent state of one rule's keypress sweep (built once by `prepareKeySweep`, read-only
    afterwards so a fork pool can share it): the lean units of the full `poolCarriers` order, the anchor-only
    alternative of each scoped carrier (`resolveFallbacks`' replacement) and the neighbour-stroke table."""
    units: list[SimUnit]
    alts: list[SimUnit | None]
    scopedIdx: list[int]         # positions of the carriers of a scoped form with span > 1: they fall back when they gain nothing
    neighbours: list[Stroke]     # neighbour id -> stroke
    exclusionCount: int
    numForms: int
    hasScoped: bool
    ctx: SimContext


def prepareKeySweep(rule: Rule, carriers: list[Carrier], ctx: SimContext) -> KeySweep:
    ids: dict[Stroke, int] = {}
    units = [makeSimUnit(rule.position, c, ctx, ids) for c in carriers]
    hasScoped = any(f.isScoped for f in rule.forms)
    alts: list[SimUnit | None] = [None] * len(carriers)
    scopedIdx: list[int] = []
    if hasScoped:
        anchor = {c.rec.idx: c._replace(member=0) for c in rule.root.carriers}
        for i, c in enumerate(carriers):
            if c.span > 1 and rule.forms[c.member].isScoped:
                scopedIdx.append(i)
                a = anchor.get(c.rec.idx)
                if a is not None:   # a missing anchor raises KeyError only if this carrier fails, as in resolveFallbacks
                    alts[i] = makeSimUnit(rule.position, a, ctx, ids)
    return KeySweep(units, alts, scopedIdx, list(ids), exclusionCountOf(rule.forms), len(rule.forms), hasScoped, ctx)


def fallbackCarriers(sw: KeySweep, carriers: list[Carrier], k: Stroke) -> tuple[list[Carrier], int]:
    """`resolveFallbacks(rule, k, carriers, ctx)` from the lean units, without the full `simulate`."""
    ctx = sw.ctx
    D = tuple(sorted(k))
    gains = simulateRuleBase(sw.units, ctx, mergeUnions(sw.neighbours, k, ctx), D, D in ctx.singleStrokeOutlines)[0]
    out = list(carriers)
    n = 0
    for i in sw.scopedIdx:
        if gains[i] <= 0:
            alt = sw.alts[i]
            if alt is None:
                raise KeyError(carriers[i].rec.idx)
            out[i] = alt.carrier
            n += 1
    return out, n


def sweepKey(sw: KeySweep, k: Stroke, limit: int | None) -> tuple[float, float, int]:
    """(score, exception rate, fallback count) of `rule` under key `k` on the first `limit` carriers (all when
    None): bit-identical to `resolveFallbacks` + `simulate` + `ruleScoreFromResults` / `_exceptionRate`."""
    ctx = sw.ctx
    units = sw.units if limit is None else sw.units[:limit]
    X = mergeUnions(sw.neighbours, k, ctx)
    D = tuple(sorted(k))
    trap = D in ctx.singleStrokeOutlines
    base = simulateRuleBase(units, ctx, X, D, trap)
    gains, reasons = base[0], base[1]
    nFallback = 0
    if sw.hasScoped:
        repl: dict[int, SimUnit] = {}
        for i in sw.scopedIdx:
            if i < len(units) and gains[i] <= 0:
                alt = sw.alts[i]
                if alt is None:
                    raise KeyError(units[i].carrier.rec.idx)
                repl[i] = alt
        if repl:
            nFallback = len(repl)
            gains, reasons, units = simulateRuleDelta(units, base, repl, ctx, X, D, trap)
    benefit = 0.0
    exceptions: list[float] = []
    covered = 0
    for u, gain, reason in zip(units, gains, reasons):
        if gain > 0:
            benefit += u.freq * gain
            covered += 1
        elif reason in WORD_EXCEPTION_REASONS:
            exceptions.append(u.freq)
    exceptionFreq = sum(exceptions)
    score = (benefit - EXCEPTION_ALPHA * exceptionFreq - EXCLUSION_COST * (sw.exclusionCount + nFallback)
             - FORM_COST * (sw.numForms - 1))
    total = covered + len(exceptions)
    return score, (len(exceptions) / total if total else 0.0), nFallback


SWEEP_WORKERS = 1       # worker processes of the keypress sweep (1: serial); `util.build_affix_rules --workers`
SWEEP_MIN_KEYS = 4      # fewer keys than this are swept in-process (a fork would cost more than it saves)
_SWEEP: KeySweep | None = None   # the sweep the forked workers read (set before the fork, never mutated)
_GROUPS: dict[tuple[Stroke | None, bool], int] = {}   # the stage-1 sample's neighbour groups, likewise


def _sweepTask(task: tuple[Stroke, int | None]) -> tuple[float, float, int]:
    assert _SWEEP is not None
    return sweepKey(_SWEEP, task[0], task[1])


def _floorTask(k: Stroke) -> float:
    assert _SWEEP is not None
    return _exceptionRateFloor(_GROUPS, k, _SWEEP.ctx)


@dataclass
class KeyMaps:
    """In-key-order maps over keypresses for one rule: `floor(keys)` is `_exceptionRateFloor` on the stage-1
    sample's groups, `sweep(keys, limit)` is `sweepKey(sw, k, limit)`."""
    floor: Callable[[list[Stroke]], list[float]]
    sweep: Callable[[list[Stroke], int | None], list[tuple[float, float, int]]]


@contextmanager
def keySweepMap(sw: KeySweep, sampleGroups: dict[tuple[Stroke | None, bool], int]) -> Iterator[KeyMaps]:
    """The maps over a fork pool when `SWEEP_WORKERS > 1` (the workers inherit `sw` copy-on-write; both functions
    are pure up to the `ctx.isLegal` memo, so the results are bit-identical to the serial ones whatever the
    scheduling)."""
    global _SWEEP, _GROUPS
    _SWEEP, _GROUPS = sw, sampleGroups
    pool = multiprocessing.get_context("fork").Pool(SWEEP_WORKERS) if SWEEP_WORKERS > 1 else None

    def chunk(n: int) -> int:
        return max(1, n // (SWEEP_WORKERS * 8))

    def floor(keys: list[Stroke]) -> list[float]:
        if pool is None or len(keys) < SWEEP_MIN_KEYS:
            return [_exceptionRateFloor(sampleGroups, k, sw.ctx) for k in keys]
        return list(pool.imap(_floorTask, keys, chunksize=chunk(len(keys))))

    def sweep(keys: list[Stroke], limit: int | None) -> list[tuple[float, float, int]]:
        if pool is None or len(keys) < SWEEP_MIN_KEYS:
            return [sweepKey(sw, k, limit) for k in keys]
        return list(pool.imap(_sweepTask, [(k, limit) for k in keys], chunksize=chunk(len(keys))))
    try:
        yield KeyMaps(floor, sweep)
    finally:
        _SWEEP, _GROUPS = None, {}
        if pool is not None:
            pool.close()    # not terminate(): that waits seconds on the workers' queue lock
            pool.join()


def chooseRuleKeypress(rule: Rule, pk: PhonemeKeys, ctx: SimContext, keypresses: list[Stroke]) -> None:
    """§4.4 step 4, lazy and expensive (Part B simulation): pick the best keypress for `rule`'s
    forms and fill in its exact score, keeping the top `MAX_ALTERNATIVES` for the report. Call
    this only for roots a caller has chosen to evaluate exactly (e.g. the top of a selection
    heap) -- never for the whole pool (§4.4, §9 "Part B runtime" pitfall).

    Tests EVERY legal keypress, not just the most phonetically-similar ones (2026-09-27, user
    decision): found empirically on `re` that the highest-similarity key (rank 27/1751 -- "R",
    the prefix's own onset) had an 18.7% exception rate on common words (reviens, revient,
    retrouve...), while a key with ~zero similarity (rank 926/1751) scored 41% HIGHER and had a
    fraction of the exceptions -- similarity was hiding the better answer, not just failing to
    help. `MAX_EXCEPTION_RATE` is a hard requirement now, independent of score: a rule that fails
    on more than 5% of its own words is rejected regardless of how good its raw score looks.
    `similarity` is computed only to label the final pick for human review (`rule.keySimilarity`),
    never to decide which keys get tried."""
    carriers = poolCarriers(rule.forms)
    exclusionCount = exclusionCountOf(rule.forms)
    rule.exactDone = True
    rule.fallbacks = 0
    if not carriers:
        return
    # Per form, not uniformly: a SLOT-bearing (lattice-grown) form's `phono` is a human-readable
    # slot LABEL (e.g. "[C-{mi}]i.te"), and its brackets/pipes/braces would get counted as bogus
    # "phonemes" by salientPhonemes (which just iterates set(phono)), diluting every real
    # phoneme's weight. But a form with NO slots (an exact leaf, or an A7-pooled onset-varying
    # group like `·er`) has a clean `.phono` that IS the right salience content, and carrier phono
    # is the wrong one: for `·er` the point is the onset varies (t/d/v/l/s/g/r/ch/...) and should
    # NOT drive key choice, only the shared rest (schwa "e") should.
    def _carrierPhono(c: Carrier) -> str:
        form = rule.forms[c.member]
        if form.slots:
            return ".".join(c.rec.phonoSylls[c.start:c.start + c.span])
        return form.phono

    weights = salientPhonemes([(_carrierPhono(c), c.rec.frequency) for c in carriers], pk)
    simOf = {k: simScore(frozenset(k), weights, pk, rule.position) for k in keypresses}
    sample = carriers[:SAMPLE_CARRIERS]
    stage1: list[tuple[float, float, Stroke]] = []
    sampleGroups = _neighbourGroups(rule.position, sample)
    sw = prepareKeySweep(rule, carriers, ctx)
    finals: list[tuple[float, Stroke, float, int]] = []
    with keySweepMap(sw, sampleGroups) as maps:
        # (the floor is exact: pass 1 alone proves the exception rate exceeds the cap for the dropped keys)
        survivors = [k for k, fl in zip(keypresses, maps.floor(keypresses)) if fl <= MAX_EXCEPTION_RATE]
        for k, (sc, rate, _nf) in zip(survivors, maps.sweep(survivors, SAMPLE_CARRIERS)):
            if sc > 0 and rate <= MAX_EXCEPTION_RATE:
                stage1.append((sc, simOf[k], k))
        stage1.sort(key=lambda t: (-t[0], -t[1], t[2]))
        finalKeys = [(k, s) for _sc, s, k in stage1[:MAX_ALTERNATIVES]]
        for (k, s), (sc, rate, nFallback) in zip(finalKeys, maps.sweep([k for k, _s in finalKeys], None)):
            if rate <= MAX_EXCEPTION_RATE:   # re-confirm against the full carrier set
                finals.append((sc, k, s, nFallback))
    finals.sort(key=lambda t: -t[0])
    if not finals:
        return
    _bestScore, bestKeys, bestSim, bestFallbacks = finals[0]
    carriersK, nFallback = fallbackCarriers(sw, carriers, bestKeys)
    (bestResults,) = simulate([(Binding(rule.position, RULE, bestKeys), carriersK)], ctx)
    sc, benefit, excCount, excFreq, top = ruleScoreFromResults(
        bestResults, exclusionCount + bestFallbacks, len(rule.forms))
    if sc != _bestScore or nFallback != bestFallbacks:
        raise AssertionError(f"sweepKey diverged from simulate for {rule.root.ortho} {bestKeys}: "
                             f"{_bestScore} != {sc} or {bestFallbacks} != {nFallback}")
    rule.fallbacks = bestFallbacks
    rule.keys, rule.score, rule.strokeFreqSaved = bestKeys, sc, benefit
    rule.wordExceptions, rule.exceptionFreq, rule.topExceptions = excCount, excFreq, top
    rule.results = bestResults
    rule.keySimilarity = bestSim
    rule.alternatives = [(fsc, k) for fsc, k, _s, _nf in finals]


# ═══════════════════════════════════════════════════════════════════════════
# Phase 3 (§5): budgeted selection
# ═══════════════════════════════════════════════════════════════════════════

def _proxyCarrierGains(rule: Rule) -> tuple[dict[int, tuple[float, int]], float]:
    """Proxy-stage per-word gain (§5 step 1's bound: no collisions, every carrier merged) --
    gain_r(w) = span for a carrier not flagged by the cheap `_exceptionShare` heuristic."""
    carriers = poolCarriers(rule.forms)
    denom = sum(c.rec.frequency for c in carriers) or 1.0
    _share, excSet = _exceptionShare(rule.position, carriers, denom)
    gains = {c.rec.idx: (c.rec.frequency, c.span) for c in carriers if c.rec.idx not in excSet}
    exceptionFreq = sum(c.rec.frequency for c in carriers if c.rec.idx in excSet)
    return gains, exceptionFreq


def _exactCarrierGains(rule: Rule) -> tuple[dict[int, tuple[float, int]], float]:
    """Exact-stage per-word gain, from `rule.results` (already computed by `chooseRuleKeypress`,
    cached -- no re-simulation)."""
    gains: dict[int, tuple[float, int]] = {}
    exceptionFreq = 0.0
    for r in rule.results:
        if r.gain > 0:
            gains[r.carrier.rec.idx] = (r.carrier.rec.frequency, r.gain)
        elif r.reason in WORD_EXCEPTION_REASONS:
            exceptionFreq += r.carrier.rec.frequency
    return gains, exceptionFreq


def _marginal(
    gains: dict[int, tuple[float, int]], exceptionFreq: float, rule: Rule,
    bestS: dict[tuple[str, int], float],
) -> float:
    """§5: `Σ_w f_w × max(0, gain_r(w) − best_S(w))` minus the rule's own costs."""
    benefit = 0.0
    for idx, (freq, gain) in gains.items():
        extra = gain - bestS.get((rule.position, idx), 0.0)
        if extra > 0:
            benefit += freq * extra
    return (benefit - EXCEPTION_ALPHA * exceptionFreq
            - EXCLUSION_COST * ruleExclusions(rule) - FORM_COST * (len(rule.forms) - 1))


def territoryOverlap(a: Rule, b: Rule) -> float:
    """Frequency-weighted share of the smaller rule's carrier words that the other rule also
    carries (same position only -- a prefix and a suffix rule never compete for a word)."""
    if a.position != b.position:
        return 0.0
    fa, fb = a.wordFreq(), b.wordFreq()
    if len(fb) < len(fa):
        fa, fb = fb, fa
    small = min(sum(fa.values()), sum(fb.values()))
    if small <= 0:
        return 0.0
    return sum(f for idx, f in fa.items() if idx in fb) / small


def territoryMate(rule: Rule, selected: list[Rule], threshold: float = RULE_OVERLAP_MAX) -> Rule | None:
    """The selected rule `rule` overlaps most, if at or above `threshold` (see RULE_OVERLAP_MAX)."""
    best: tuple[float, Rule] | None = None
    for s in selected:
        if s is rule:
            continue
        ov = territoryOverlap(rule, s)
        if ov >= threshold and (best is None or ov > best[0]):
            best = (ov, s)
    return best[1] if best else None


def creditedTotal(rules: list[Rule]) -> float:
    """§5's objective: the word-once-credited total, rules applied in the given order."""
    bestS: dict[tuple[str, int], float] = {}
    total = 0.0
    for rule in rules:
        gains, excFreq = _exactCarrierGains(rule)
        total += _marginal(gains, excFreq, rule, bestS)
        for idx2, (_freq, gain) in gains.items():
            k2 = (rule.position, idx2)
            if gain > bestS.get(k2, 0.0):
                bestS[k2] = gain
    return total


@dataclass
class OverlapSkip:
    """A rule popped by the selection but skipped for overlapping a selected one (reported)."""
    skippedRoot: str
    selectedRoot: str
    overlap: float


@dataclass
class RivalDecision:
    """One `resolveVariantRivals` verdict on a merged spelling-variant anchor (reported)."""
    position: str
    merged: str
    phono: str
    parts: list[str]
    newConflictFreq: float
    outcome: str = ""      # "fused" (parts dropped) or "apart" (merge dropped)
    pending: bool = False  # no verdict in affix_decisions.json: "apart" by default


@dataclass
class SelectionResult:
    selected: list[Rule]
    curve: list[float]                    # cumulative total after each acceptance, 1..min(40, N)
    evaluatedExactCount: int               # roots that got the expensive §4.4 step 4 evaluation
    unselectedExact: list[Rule]            # exact-evaluated but not selected, best-score first
    overlapSkips: list[OverlapSkip] = field(default_factory=list)


def anchorKeys(cands: dict[tuple[str, int, str, str], Candidate]) -> list[tuple[str, int, str, str]]:
    return [k for k, c in cands.items() if c.isAnchor]


def _upperBound(rule: Rule) -> float:
    return sum(c.rec.frequency * c.span for c in poolCarriers(rule.forms))


def resolveVariantRivals(
    cands: dict[tuple[str, int, str, str], Candidate], decisions: Decisions,
) -> tuple[list[tuple[str, int, str, str]], list[RivalDecision]]:
    """A merged spelling-variant anchor M (`ment|mant`) and its parts are rivals, never a family: the
    user's verdict on M (`affix_decisions.json`) settles it before selection. "fused": M replaces ALL its
    parts; "apart": the parts stay and M is dropped. A merge with no verdict is undecided: it behaves as
    "apart" and is reported `pending`. Returns the remaining anchors and one decision per merge."""
    anchors = anchorKeys(cands)
    dropped: set[tuple[str, int, str, str]] = set()
    outcomes: list[RivalDecision] = []
    for mkey in anchors:
        m = cands[mkey]
        parts = [cands[k] for k in m.mergeParts if k in cands]
        if not parts:
            continue
        verdict = decisions.fusionVerdict(m.position, m.ortho, m.phono)
        dec = RivalDecision(m.position, m.ortho, m.phono, [p.ortho for p in parts], m.newConflictFreq, outcome=verdict,
                            pending=not decisions.isDecidedMerge(m.position, m.ortho, m.phono))
        outcomes.append(dec)
        if verdict == "fused":
            dropped.update(candidateKey(p) for p in parts)
        else:
            dropped.add(mkey)
    return [k for k in anchors if k not in dropped], outcomes


def selectRules(
    cands: dict[tuple[str, int, str, str], Candidate], pk: PhonemeKeys, ctx: SimContext,
    keypresses: list[Stroke], budget: int = RULE_BUDGET, curveLength: int = 40,
    anchors: list[tuple[str, int, str, str]] | None = None,
    ruleCache: dict[tuple[str, int, str, str], Rule] | None = None,
    evaluate: Callable[[Rule], None] | None = None,
) -> SelectionResult:
    """§5: lazy greedy over a 3-stage heap (raw upper bound -> proxy marginal -> exact marginal),
    each stage recomputed fresh against the current selection before being trusted, so a root is
    only accepted once its exact marginal has survived a fresh recompute with no other rule
    accepted in between. `chooseRuleKeypress` (the expensive step) runs at most once per root,
    only for roots that reach stage 2.

    Roots are `anchors` (default: every `isAnchor` pool node; pass `resolveVariantRivals`' answer
    to settle merged-vs-parts first) -- a grown node is only ever a form of its anchor's rule (D4).
    A root overlapping a selected rule by `RULE_OVERLAP_MAX` is skipped, never merged.
    `evaluate(rule)` replaces `chooseRuleKeypress` as the exact evaluation (a caller with cached evaluations restores
    them there, at the very point a fresh evaluation would run, so the selection order is the same as without a cache)."""
    idx = childrenIndex(cands)
    ruleCache = ruleCache if ruleCache is not None else {}
    roots = anchors if anchors is not None else anchorKeys(cands)

    def getRule(key: tuple[str, int, str, str]) -> Rule:
        r = ruleCache.get(key)
        if r is None:
            r = ruleCache[key] = buildCandidateRule(cands[key], idx)
        return r

    heap: list[tuple[float, int, tuple[str, int, str, str], int]] = []
    for seq, key in enumerate(roots):
        heap.append((-_upperBound(getRule(key)), seq, key, 0))
    heapq.heapify(heap)

    bestS: dict[tuple[str, int], float] = {}
    selected: list[Rule] = []
    curve: list[float] = []
    total = 0.0
    exactEvaluated: set[tuple[str, int, str, str]] = {k for k in roots if getRule(k).exactDone}
    droppedExact: list[Rule] = []
    skips: list[OverlapSkip] = []

    while heap and len(selected) < budget:
        _negval, s, key, stage = heapq.heappop(heap)
        rule = getRule(key)
        if stage == 0:
            gains, excFreq = _proxyCarrierGains(rule)
            marg = _marginal(gains, excFreq, rule, bestS)
            if marg > 0:
                heapq.heappush(heap, (-marg, s, key, 1))
            continue
        mate = territoryMate(rule, selected)
        if mate is not None:
            skips.append(OverlapSkip(rule.root.ortho, mate.root.ortho, territoryOverlap(rule, mate)))
            continue
        if stage == 1:
            gains, excFreq = _proxyCarrierGains(rule)
            marg = _marginal(gains, excFreq, rule, bestS)
            if marg <= 0:
                continue
            if key not in exactEvaluated:
                if evaluate is not None:
                    evaluate(rule)
                else:
                    chooseRuleKeypress(rule, pk, ctx, keypresses)
                exactEvaluated.add(key)
            if rule.keys is None:
                continue  # no legal/positive keypress at all -- dead end, drop for good
            egains, eexcFreq = _exactCarrierGains(rule)
            emarg = _marginal(egains, eexcFreq, rule, bestS)
            if emarg > 0:
                heapq.heappush(heap, (-emarg, s, key, 2))
            else:
                droppedExact.append(rule)
            continue
        # stage 2: exact marginal, recomputed fresh -- accept if it survives.
        egains, eexcFreq = _exactCarrierGains(rule)
        emarg = _marginal(egains, eexcFreq, rule, bestS)
        if emarg <= 0:
            droppedExact.append(rule)
            continue
        selected.append(rule)
        for idx2, (_freq, gain) in egains.items():
            k2 = (rule.position, idx2)
            if gain > bestS.get(k2, 0.0):
                bestS[k2] = gain
        total += emarg
        curve.append(total)

    droppedExact.sort(key=lambda r: -(r.score or 0.0))
    return SelectionResult(selected, curve[:curveLength], len(exactEvaluated), droppedExact, skips)


def swapPass(
    result: SelectionResult, passes: int = SWAP_PASSES, swapCandidates: int = SWAP_CANDIDATES,
) -> SelectionResult:
    """§5 step 4: try replacing each selected rule with each of the `swapCandidates` best
    unselected exact-evaluated rules; keep any swap that raises the total word-once-credited sum.
    Recomputes the whole objective from scratch each time (cheap: only uses cached `rule.results`,
    no new simulation)."""
    selected = list(result.selected)
    pool = result.unselectedExact[:swapCandidates]

    def totalOf(rules: list[Rule]) -> float:
        """Word-once-credited total (§5's objective), rules applied best-score-first."""
        return creditedTotal(sorted(rules, key=lambda r: -(r.score or 0.0)))

    changed = True
    rounds = 0
    while changed and rounds < passes:
        changed = False
        rounds += 1
        for i, incumbent in enumerate(selected):
            base = totalOf(selected)
            bestSwap = None
            for cand in pool:
                if cand in selected:
                    continue
                # Overlap safety net (RULE_OVERLAP_MAX): a swap may not bring in a rule
                # that overlaps one staying selected.
                if territoryMate(cand, selected[:i] + selected[i + 1:]) is not None:
                    continue
                trial = selected[:i] + [cand] + selected[i + 1:]
                t = totalOf(trial)
                if t > base and (bestSwap is None or t > bestSwap[1]):
                    bestSwap = (cand, t)
            if bestSwap is not None:
                pool.append(incumbent)
                pool.remove(bestSwap[0])
                selected[i] = bestSwap[0]
                changed = True
    return SelectionResult(selected, result.curve, result.evaluatedExactCount, result.unselectedExact,
                           result.overlapSkips)


# ═══════════════════════════════════════════════════════════════════════════
# Phase 4 (§6): keypress binding with sharing
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class BoundRule:
    rule: Rule
    keys: Stroke
    sharedWith: list[str] = field(default_factory=list)   # other bound rules' root orthos
    reboundScore: float = 0.0


def _jointLoss(a: Rule, b: Rule, keys: Stroke, ctx: SimContext) -> float:
    """Share of either rule's own gain lost by simulating both together under the same `keys`
    (§6, `_mutualConflict`'s joint-simulation idea, but measured as a share instead of a
    boolean)."""
    carriersA = resolveFallbacks(a, keys, poolCarriers(a.forms), ctx)[0]
    carriersB = resolveFallbacks(b, keys, poolCarriers(b.forms), ctx)[0]
    bindingA = Binding(a.position, RULE, keys)
    bindingB = Binding(b.position, RULE, keys)
    soloA, soloB = simulate([(bindingA, carriersA)], ctx)[0], simulate([(bindingB, carriersB)], ctx)[0]
    jointA, jointB = simulate([(bindingA, carriersA), (bindingB, carriersB)], ctx)
    lossA = sum(r0.carrier.rec.frequency * max(0, r0.gain - r1.gain) for r0, r1 in zip(soloA, jointA))
    lossB = sum(r0.carrier.rec.frequency * max(0, r0.gain - r1.gain) for r0, r1 in zip(soloB, jointB))
    gainA = sum(r.carrier.rec.frequency * r.gain for r in soloA if r.gain > 0) or 1.0
    gainB = sum(r.carrier.rec.frequency * r.gain for r in soloB if r.gain > 0) or 1.0
    return max(lossA / gainA, lossB / gainB)


def bindKeypresses(
    selected: list[Rule], ctx: SimContext, maxLoss: float = SPLIT_MAX_LOSS,
) -> list[BoundRule]:
    """§6: assign each selected rule its best keypress, descending by score; two rules of the
    same position may share a key if a joint simulation loses no more than `maxLoss` of either."""
    bound: list[BoundRule] = []
    byPosition: dict[str, list[BoundRule]] = {}
    for rule in sorted(selected, key=lambda r: -(r.score or 0.0)):
        alternatives = [rule.keys] + [k for _s, k in rule.alternatives if k != rule.keys]
        placed = False
        for keys in alternatives:
            if keys is None:
                continue
            samePos = byPosition.get(rule.position, [])
            holder = next((b for b in samePos if b.keys == keys), None)
            if holder is None:
                br = BoundRule(rule, keys)
                bound.append(br)
                byPosition.setdefault(rule.position, []).append(br)
                placed = True
                break
            loss = _jointLoss(rule, holder.rule, keys, ctx)
            if loss <= maxLoss:
                br = BoundRule(rule, keys, sharedWith=[holder.rule.root.ortho])
                holder.sharedWith.append(rule.root.ortho)
                bound.append(br)
                byPosition.setdefault(rule.position, []).append(br)
                placed = True
                break
        if not placed and rule.keys is not None:
            br = BoundRule(rule, rule.keys)
            bound.append(br)
            byPosition.setdefault(rule.position, []).append(br)
    return bound
