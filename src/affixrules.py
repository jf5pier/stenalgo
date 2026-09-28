"""
Phases 2-4 (DESIGN_2026-09-27-affix-rule-selection.md §4-6): turn the Phase-1 lattice pool into a
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
from dataclasses import dataclass, field

from src.affixbinding import (
    MAX_ALTERNATIVES, SAMPLE_CARRIERS, SPLIT_MAX_LOSS, PhonemeKeys, salientPhonemes, simScore)
from src.affixes import (
    Binding, Candidate, Carrier, CarrierResult, RULE, SimContext, _exceptionShare, poolCarriers,
    simulate)
from src.keyboard import Stroke

RULE_BUDGET = 30
MAX_RULE_FORMS = 4
EXCEPTION_ALPHA = 1.0
EXCLUSION_COST = 5.0
FORM_COST = 10.0
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
TERRITORY_OVERLAP = 0.5     # 2026-09-28: two same-position rules whose carriers overlap this much
                            # (frequency-weighted, as a share of the smaller rule) are one territory
                            # -- one key. Word-once crediting alone let `·°ment` (-dt) sit next to
                            # `ment` (-tm) on 83% of the same words, and let `·[..]ter` patch `ter`'s
                            # own exceptions on a second key: two outlines per word, two keys per
                            # morpheme. A territory-mate may only join the selected rule as a form.
REBIND_MAX_LOSS = 0.10
REBIND_ITERATIONS = 3

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
        if c.grownFromKey is not None:
            idx.setdefault(c.grownFromKey, []).append(c)
    return idx


def descendantsOf(root: Candidate, childrenIdx: dict[tuple[str, int, str, str], list[Candidate]]) -> list[Candidate]:
    """All descendants of `root` at any depth (its whole grown subtree)."""
    out: list[Candidate] = []
    stack = list(childrenIdx.get(candidateKey(root), []))
    while stack:
        c = stack.pop()
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
    sources: list[Candidate] = field(default_factory=list)  # roots whose subtrees fed the forms
                                                            # (more than one after a territory merge)
    _wordFreq: dict[int, float] | None = field(default=None, repr=False, compare=False)

    def wordFreq(self) -> dict[int, float]:
        """rec.idx -> frequency over the pooled carriers (cached: forms never change in place)."""
        if self._wordFreq is None:
            self._wordFreq = {c.rec.idx: c.rec.frequency for c in poolCarriers(self.forms)}
        return self._wordFreq


def buildCandidateRule(
    root: Candidate, childrenIdx: dict[tuple[str, int, str, str], list[Candidate]],
) -> Rule:
    """§4.4 steps 1-3: greedily add the descendant that most increases the proxy score, up to
    `MAX_RULE_FORMS`. No keyboard evaluation here -- cheap enough to run for every pool node."""
    rule = _greedyForms(root, descendantsOf(root, childrenIdx))
    rule.sources = [root]
    return rule


def buildMergedRule(
    roots: list[Candidate], childrenIdx: dict[tuple[str, int, str, str], list[Candidate]],
) -> Rule:
    """Phase 2 over one territory (2026-09-28): the same greedy form selection as
    `buildCandidateRule`, but drawing forms from several same-territory roots' subtrees at once
    (`ment` + the A7-pooled `·°ment`), so one rule -- one key -- can cover both. Each root is
    tried as forms[0]; the better proxy score wins. The greedy may still leave a root out."""
    nodes: dict[tuple[str, int, str, str], Candidate] = {}
    for r in roots:
        for c in [r] + descendantsOf(r, childrenIdx):
            nodes.setdefault(candidateKey(c), c)
    best: Rule | None = None
    for r in roots:
        rule = _greedyForms(r, [c for k, c in nodes.items() if k != candidateKey(r)])
        if best is None or rule.score > best.score:
            best = rule
    assert best is not None
    best.sources = list(roots)
    return best


def _greedyForms(root: Candidate, remaining: list[Candidate]) -> Rule:
    forms = [root]
    remaining = list(remaining)
    bestScore = proxyScore(root.position, forms)
    while remaining and len(forms) < MAX_RULE_FORMS:
        best: tuple[float, Candidate] | None = None
        for cand in remaining:
            s = proxyScore(root.position, forms + [cand])
            if best is None or s > best[0]:
                best = (s, cand)
        assert best is not None
        s, cand = best
        if s <= bestScore:
            break
        forms.append(cand)
        remaining.remove(cand)
        bestScore = s
    return Rule(root.position, root, forms, score=bestScore)


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
    for k in keypresses:
        (res,) = simulate([(Binding(rule.position, RULE, k), sample)], ctx)
        sc, _benefit, _exc, _excFreq, _top = ruleScoreFromResults(res, exclusionCount, len(rule.forms))
        if sc > 0 and _exceptionRate(res) <= MAX_EXCEPTION_RATE:
            stage1.append((sc, simOf[k], k))
    stage1.sort(key=lambda t: (-t[0], -t[1], t[2]))
    finalKeys = [(k, s) for _sc, s, k in stage1[:MAX_ALTERNATIVES]]
    finals: list[tuple[float, Stroke, float, list[CarrierResult]]] = []
    for k, s in finalKeys:
        (res,) = simulate([(Binding(rule.position, RULE, k), carriers)], ctx)
        sc, _benefit, _exc, _excFreq, _top = ruleScoreFromResults(res, exclusionCount, len(rule.forms))
        if _exceptionRate(res) <= MAX_EXCEPTION_RATE:   # re-confirm against the full carrier set
            finals.append((sc, k, s, res))
    finals.sort(key=lambda t: -t[0])
    if not finals:
        return
    _bestScore, bestKeys, bestSim, bestResults = finals[0]
    sc, benefit, excCount, excFreq, top = ruleScoreFromResults(bestResults, exclusionCount, len(rule.forms))
    rule.keys, rule.score, rule.strokeFreqSaved = bestKeys, sc, benefit
    rule.wordExceptions, rule.exceptionFreq, rule.topExceptions = excCount, excFreq, top
    rule.results = bestResults
    rule.keySimilarity = bestSim
    rule.alternatives = [(fsc, k) for fsc, k, _s, _res in finals]


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
            - EXCLUSION_COST * exclusionCountOf(rule.forms) - FORM_COST * (len(rule.forms) - 1))


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


def territoryMate(rule: Rule, selected: list[Rule], threshold: float = TERRITORY_OVERLAP) -> Rule | None:
    """The selected rule `rule` overlaps most, if at or above `threshold` (see TERRITORY_OVERLAP)."""
    best: tuple[float, Rule] | None = None
    for s in selected:
        if s is rule:
            continue
        ov = territoryOverlap(rule, s)
        if ov >= threshold and (best is None or ov > best[0]):
            best = (ov, s)
    return best[1] if best else None


def _bestSOf(rules: list[Rule]) -> dict[tuple[str, int], float]:
    bestS: dict[tuple[str, int], float] = {}
    for rule in rules:
        gains, _excFreq = _exactCarrierGains(rule)
        for idx2, (_freq, gain) in gains.items():
            k2 = (rule.position, idx2)
            if gain > bestS.get(k2, 0.0):
                bestS[k2] = gain
    return bestS


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
class TerritoryEvent:
    """One territory-mate met by the selection (reported for review)."""
    selectedRoot: str          # the selected rule's root ortho, before any merge
    mateRoot: str              # the candidate that overlapped it
    overlap: float
    outcome: str               # "merged", "rejected" (merge no better), "inLineage" (the greedy
                               # already weighed it), "noKey" (merged rule has no legal key)
    totalBefore: float = 0.0
    totalAfter: float = 0.0


@dataclass
class SelectionResult:
    selected: list[Rule]
    curve: list[float]                    # cumulative total after each acceptance, 1..min(40, N)
    evaluatedExactCount: int               # roots that got the expensive §4.4 step 4 evaluation
    unselectedExact: list[Rule]            # exact-evaluated but not selected, best-score first
    territoryEvents: list[TerritoryEvent] = field(default_factory=list)


def selectRules(
    cands: dict[tuple[str, int, str, str], Candidate], pk: PhonemeKeys, ctx: SimContext,
    keypresses: list[Stroke], budget: int = RULE_BUDGET, curveLength: int = 40,
) -> SelectionResult:
    """§5: lazy greedy over a 3-stage heap (raw upper bound -> proxy marginal -> exact marginal),
    each stage recomputed fresh against the current selection before being trusted, so a root is
    only accepted once its exact marginal has survived a fresh recompute with no other rule
    accepted in between. `chooseRuleKeypress` (the expensive step) runs at most once per root,
    only for roots that reach stage 2.

    One key per territory (2026-09-28, TERRITORY_OVERLAP): before a root is exact-evaluated or
    accepted, it is checked against the selected rules. A territory-mate is never selected on its
    own; instead the selected rule is rebuilt over both roots (`buildMergedRule`) and replaced in
    place -- same budget slot -- if that raises the word-once-credited total. Either way the mate
    leaves the heap for good. A mate already inside the selected rule's lineage is dropped without
    evaluation: `buildCandidateRule`'s greedy already weighed it as a form."""
    idx = childrenIndex(cands)
    ruleCache: dict[tuple[str, int, str, str], Rule] = {}

    def getRule(key: tuple[str, int, str, str]) -> Rule:
        r = ruleCache.get(key)
        if r is None:
            r = ruleCache[key] = buildCandidateRule(cands[key], idx)
        return r

    heap: list[tuple[float, int, tuple[str, int, str, str], int]] = []
    seq = 0
    for key, root in cands.items():
        rule = getRule(key)
        carriers = poolCarriers(rule.forms)
        ub = sum(c.rec.frequency * c.span for c in carriers)
        heap.append((-ub, seq, key, 0))
        seq += 1
    heapq.heapify(heap)

    bestS: dict[tuple[str, int], float] = {}
    selected: list[Rule] = []
    curve: list[float] = []
    total = 0.0
    exactEvaluated: set[tuple[str, int, str, str]] = set()
    droppedExact: list[Rule] = []
    events: list[TerritoryEvent] = []

    def lineageKeys(rule: Rule) -> set[tuple[str, int, str, str]]:
        keys: set[tuple[str, int, str, str]] = set()
        for src in rule.sources:
            keys.add(candidateKey(src))
            keys.update(candidateKey(d) for d in descendantsOf(src, idx))
        return keys

    def handleTerritory(rule: Rule, mate: Rule) -> None:
        """`rule` overlaps the selected `mate`: try the merge, never select `rule` alone."""
        nonlocal bestS, total
        ev = TerritoryEvent(mate.root.ortho, rule.root.ortho, territoryOverlap(rule, mate), "inLineage")
        events.append(ev)
        if candidateKey(rule.root) in lineageKeys(mate):
            return
        merged = buildMergedRule(mate.sources + [rule.root], idx)
        if [candidateKey(f) for f in merged.forms] == [candidateKey(f) for f in mate.forms]:
            ev.outcome = "rejected"
            return
        chooseRuleKeypress(merged, pk, ctx, keypresses)
        if merged.keys is None:
            ev.outcome = "noKey"
            return
        i = next(j for j, x in enumerate(selected) if x is mate)
        trial = selected[:i] + [merged] + selected[i + 1:]
        ev.totalBefore, ev.totalAfter = total, creditedTotal(trial)
        others = selected[:i] + selected[i + 1:]
        if ev.totalAfter <= ev.totalBefore or territoryMate(merged, others) is not None:
            ev.outcome = "rejected"
            return
        ev.outcome = "merged"
        selected[i] = merged
        bestS = _bestSOf(selected)
        total = ev.totalAfter

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
            handleTerritory(rule, mate)
            continue
        if stage == 1:
            gains, excFreq = _proxyCarrierGains(rule)
            marg = _marginal(gains, excFreq, rule, bestS)
            if marg <= 0:
                continue
            if key not in exactEvaluated:
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
    return SelectionResult(selected, curve[:curveLength], len(exactEvaluated), droppedExact, events)


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
                # One key per territory (TERRITORY_OVERLAP): a swap may not bring in a rule
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
                           result.territoryEvents)


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
    carriersA = poolCarriers(a.forms)
    carriersB = poolCarriers(b.forms)
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
