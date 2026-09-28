"""
Affix Abbreviation Binding (Part B): choose, for each affix family found by `src.affixes`, the
keypress (merged into the neighbouring stroke) or dedicated stroke that stands for it.

MEASUREMENT AND PROPOSALS ONLY -- nothing here is wired into the theory. See
PLAN_2026-09-26-affix-abbreviations.md, sections 2 and 5.
"""
from dataclasses import dataclass, field
from itertools import combinations

from src.affixes import (
    buildFamily, candidateSim, colourSubgroups,
    Candidate, DEDICATED, FAMILY_LINK_SIM, MAX_STEMS_FOR_JACCARD, MERGED, PREFIX, Binding, Carrier,
    CarrierResult, Family, FamilyMetrics, SimContext, familyMetrics, simulate)
from src.keyboard import Starboard, Stroke

SIM_MIN = 0.5
GAIN_KEEP = 0.8
OTHER_BANK_WEIGHT = 0.5
NUCLEUS_VOWEL_WEIGHT = 0.5
UNEXPLAINED_KEY_PENALTY = 0.25
MAX_KEYPRESS_KEYS = 3
SAMPLE_CARRIERS = 2000      # first-pass simulation sample (top frequency); finalists use all
FINALISTS = 12
MAX_ALTERNATIVES = 5
SPLIT_MAX_LOSS = 0.02       # a single keypress is kept unless more than this share of frequency collides
FORBIDDEN_KEYS = frozenset({0, 1, 10, 15})   # reserved keys: never used (Decision 2)


def constantsHeader() -> dict[str, float | int]:
    import src.affixes as a
    return {
        "MAX_AFFIX_SYLL": a.MAX_AFFIX_SYLL, "MIN_STEM_LETTERS": a.MIN_STEM_LETTERS,
        "MIN_CARRIER_LEMMAS": a.MIN_CARRIER_LEMMAS, "MIN_STEM_ROOTS": a.MIN_STEM_ROOTS, "MEMBER_MIN_SHARE": a.MEMBER_MIN_SHARE, "MIN_CANDIDATE_FREQ": a.MIN_CANDIDATE_FREQ,
        "FAMILY_LINK_SIM": a.FAMILY_LINK_SIM, "MAX_FAMILY_MEMBERS": a.MAX_FAMILY_MEMBERS,
        "MIN_FAMILY_STROKEFREQ": a.MIN_FAMILY_STROKEFREQ, "MAX_FAMILY_CANDIDATES": a.MAX_FAMILY_CANDIDATES,
        "SIM_MIN": SIM_MIN, "GAIN_KEEP": GAIN_KEEP, "OTHER_BANK_WEIGHT": OTHER_BANK_WEIGHT,
        "NUCLEUS_VOWEL_WEIGHT": NUCLEUS_VOWEL_WEIGHT, "UNEXPLAINED_KEY_PENALTY": UNEXPLAINED_KEY_PENALTY,
        "MAX_KEYPRESS_KEYS": MAX_KEYPRESS_KEYS, "SPLIT_MAX_LOSS": SPLIT_MAX_LOSS, "NESTED_SIM": a.NESTED_SIM, "MERGE_SIM_MIN": MERGE_SIM_MIN, "MERGE_KEEP": MERGE_KEEP, "MERGE_MAX_MEMBERS": MERGE_MAX_MEMBERS, "MERGE_SIM_DROP": MERGE_SIM_DROP, "MERGE_MEMBER_SIM_FLOOR": MERGE_MEMBER_SIM_FLOOR, "SAMPLE_CARRIERS": SAMPLE_CARRIERS,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Similarity (B1)
# ═══════════════════════════════════════════════════════════════════════════

class PhonemeKeys:
    """Each phoneme's key sets, per bank, read from the layout."""

    def __init__(self, starboard: Starboard) -> None:
        partOf = {k: part for part, keys in starboard.keyIDinSyllabicPart.items() for k in keys}
        self.encodings: dict[str, list[tuple[str, frozenset[int]]]] = {}
        for keyset, phonemes in starboard.phonemesAssignedToStroke.items():
            bank = partOf[keyset[0]]
            for p in phonemes:
                self.encodings.setdefault(p, []).append((bank, frozenset(keyset)))
        self.vowels = {p for p, enc in self.encodings.items() if any(b == "nucleus" for b, _ in enc)}


def naturalBank(position: str) -> str:
    return "onset" if position == PREFIX else "coda"


def salientPhonemes(memberPhonos: list[tuple[str, float]], pk: PhonemeKeys) -> dict[str, float]:
    """Phoneme -> weight: frequency share of the members containing it, vowels x0.5."""
    total = sum(f for _, f in memberPhonos) or 1.0
    share: dict[str, float] = {}
    for phono, f in memberPhonos:
        for p in set(phono.replace(".", "")):
            share[p] = share.get(p, 0.0) + f / total
    return {p: s * (0.5 if p in pk.vowels else 1.0) for p, s in share.items()}


def simScore(keys: frozenset[int], weights: dict[str, float], pk: PhonemeKeys, position: str) -> float:
    total = sum(weights.values())
    if total <= 0:
        return 0.0
    natural = naturalBank(position)
    got = 0.0
    covered: set[int] = set()
    for p, w in weights.items():
        best, bestKeys = 0.0, None
        for bank, ks in pk.encodings.get(p, ()):
            if ks <= keys:
                if bank == natural:
                    bw = 1.0
                elif bank == "nucleus" and p in pk.vowels:
                    bw = NUCLEUS_VOWEL_WEIGHT
                else:
                    bw = OTHER_BANK_WEIGHT
                if bw > best:
                    best, bestKeys = bw, ks
        if bestKeys is not None:
            got += w * best
            covered |= bestKeys
    return (got - UNEXPLAINED_KEY_PENALTY * len(keys - covered)) / total


def phonemeKeys(starboard: Starboard) -> list[int]:
    return sorted(k for ks in starboard.keyIDinSyllabicPart.values() for k in ks if k not in FORBIDDEN_KEYS)


def enumerateKeypresses(starboard: Starboard, ctx: SimContext) -> list[Stroke]:
    keys = phonemeKeys(starboard)
    out: list[Stroke] = []
    for n in range(1, MAX_KEYPRESS_KEYS + 1):
        for combo in combinations(keys, n):
            if ctx.isLegal(combo):
                out.append(combo)
    return out


# ═══════════════════════════════════════════════════════════════════════════
# Options
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SubgroupChoice:
    members: list[int]
    binding: Binding
    sim: float
    comfort: float = 0.0


@dataclass
class Option:
    subgroups: list[SubgroupChoice]
    metrics: FamilyMetrics
    sim: float
    comfort: float
    results: list[list[CarrierResult]] = field(default_factory=list, repr=False)

    def signature(self) -> tuple[tuple[str, tuple[int, ...]], ...]:
        return tuple((s.binding.position, s.binding.keys) for s in self.subgroups)


def comfortCost(results: list[list[CarrierResult]], bindings: list[Binding], ctx: SimContext) -> float:
    """Frequency-weighted mean per-bank stroke cost of the strokes the binding lands on."""
    tot = w = 0.0
    for res, b in zip(results, bindings):
        for r in res:
            if r.gain <= 0 or r.newBase is None:
                continue
            c = r.carrier
            if b.kind == MERGED:
                idx = 0 if b.position == PREFIX else c.start - 1
            else:
                idx = c.start
            cost = ctx.bankCost(r.newBase[idx])
            if cost is not None:
                tot += cost * c.rec.frequency
                w += c.rec.frequency
    return tot / w if w else 0.0


def familySalience(fam: Family, pk: PhonemeKeys) -> dict[str, float]:
    return salientPhonemes([(m.phono, m.strokeFreq) for m in fam.members], pk)


def evaluate(
    groups: list[tuple[list[int], Binding, float, list[Carrier]]], ctx: SimContext,
) -> Option:
    results = simulate([(b, cs) for _m, b, _s, cs in groups], ctx)
    metrics = familyMetrics(results)
    comfort = comfortCost(results, [b for _m, b, _s, _c in groups], ctx)
    tot = sum(sum(c.rec.frequency for c in cs) for _m, _b, _s, cs in groups) or 1.0
    sim = sum(s * sum(c.rec.frequency for c in cs) for _m, _b, s, cs in groups) / tot
    subs = [SubgroupChoice(m, b, s, comfort) for m, b, s, _c in groups]
    return Option(subs, metrics, sim, comfort, results)


def rankOptions(options: list[Option]) -> list[Option]:
    """B2 selection: options within GAIN_KEEP of the best gain first (highest sim, then lowest
    comfort cost), then the rest by gain."""
    good = [o for o in options if o.metrics.strokeFreqSaved > 0]
    if not good:
        return []
    best = max(o.metrics.strokeFreqSaved for o in good)
    band = [o for o in good if o.metrics.strokeFreqSaved >= GAIN_KEEP * best]
    rest = [o for o in good if o.metrics.strokeFreqSaved < GAIN_KEEP * best]
    band.sort(key=lambda o: (-o.sim, o.comfort, o.signature()))
    rest.sort(key=lambda o: (-o.metrics.strokeFreqSaved, o.signature()))
    return (band + rest)[:MAX_ALTERNATIVES]


def mergedOptions(
    fam: Family, pk: PhonemeKeys, ctx: SimContext, keypresses: list[Stroke],
) -> tuple[list[Option], list[tuple[float, Stroke]]]:
    """B2: merged keypresses for the whole family (as one group). Also returns the
    similarity-ranked keypresses (used by B4)."""
    weights = familySalience(fam, pk)
    scored = sorted(((simScore(frozenset(k), weights, pk, fam.position), k) for k in keypresses),
                    key=lambda t: (-t[0], t[1]))
    passing = [(s, k) for s, k in scored if s >= SIM_MIN]
    sample = fam.carriers[:SAMPLE_CARRIERS]
    stage1: list[tuple[float, float, Stroke]] = []
    for s, k in passing:
        res = simulate([(Binding(fam.position, MERGED, k), sample)], ctx)
        saved = familyMetrics(res).strokeFreqSaved
        if saved > 0:
            stage1.append((saved, s, k))
    stage1.sort(key=lambda t: (-t[0], -t[1], t[2]))
    finalists: dict[Stroke, float] = {}
    if stage1:
        best = stage1[0][0]
        # keep the near-best by gain (the selection band) plus the top by gain
        for saved, s, k in stage1:
            if saved >= GAIN_KEEP * best * 0.9 and len(finalists) < FINALISTS * 3:
                finalists[k] = s
        for saved, s, k in stage1[:FINALISTS]:
            finalists[k] = s
    options: list[Option] = []
    for k, s in finalists.items():
        options.append(evaluate([([m for m in range(len(fam.members))], Binding(fam.position, MERGED, k), s, fam.carriers)], ctx))
    return options, scored


def conflictShare(opt: Option) -> float:
    """Share of the carriers' frequency whose shortening is lost to collisions with other words."""
    tot = bad = 0.0
    for res in opt.results:
        for r in res:
            f = r.carrier.rec.frequency
            tot += f
            if r.reason in ("lostDistinction", "markCostTooHigh"):
                bad += f
    return bad / tot if tot else 0.0


def collisionSubgroups(fam: Family, opt: Option) -> list[list[int]]:
    """Sub-groups from the collisions a single keypress actually causes between members."""
    mass: dict[tuple[int, int], float] = {}
    for res in opt.results:
        for r in res:
            for j in set(r.partners):
                i = r.carrier.member
                key = (min(i, j), max(i, j))
                mass[key] = mass.get(key, 0.0) + r.carrier.rec.frequency
    return colourSubgroups(len(fam.members), mass)


def discriminatorWeights(fam: Family, group: list[int], subgroups: list[list[int]], pk: PhonemeKeys) -> dict[str, float]:
    """Weights of the phonemes that distinguish `group`'s members from the other sub-groups."""
    def share(idxs: list[int]) -> dict[str, float]:
        tot = sum(fam.members[i].strokeFreq for i in idxs) or 1.0
        out: dict[str, float] = {}
        for i in idxs:
            for p in set(fam.members[i].phonoFlat):
                out[p] = out.get(p, 0.0) + fam.members[i].strokeFreq / tot
        return out
    mine = share(group)
    others = [share(g) for g in subgroups if g is not group]
    w: dict[str, float] = {}
    for p, s in mine.items():
        d = s - max((o.get(p, 0.0) for o in others), default=0.0)
        if d > 0:
            w[p] = d * (0.5 if p in pk.vowels else 1.0)
    return w


def subgroupOption(
    fam: Family, core: Stroke, pk: PhonemeKeys, ctx: SimContext, allKeys: list[int],
    subgroups: list[list[int]],
) -> Option | None:
    """B3: core keypress + one distinct discriminator key per sub-group."""
    used: set[int] = set(core)
    order = sorted(subgroups, key=lambda g: -sum(fam.members[i].strokeFreq for i in g))
    weights = familySalience(fam, pk)
    groups: list[tuple[list[int], Binding, float, list[Carrier]]] = []
    for g in order:
        dw = discriminatorWeights(fam, g, subgroups, pk)
        best: tuple[float, float, int] | None = None
        for d in allKeys:
            if d in used or not ctx.isLegal(tuple(sorted(set(core) | {d}))):
                continue
            cost = ctx.bankCost((d,)) or 0
            nat = 1.0 if d in _bankKeys(ctx, naturalBank(fam.position)) else 0.0
            cand = (simScore(frozenset({d}), dw, pk, fam.position) if dw else 0.0, nat - cost / 1000.0, d)
            if best is None or cand[:2] > best[:2] or (cand[:2] == best[:2] and d < best[2]):
                best = cand
        if best is None:
            return None
        d = best[2]
        used.add(d)
        keys = tuple(sorted(set(core) | {d}))
        carriers = [c for c in fam.carriers if c.member in g]
        # the discriminator key is unexplained by design: score the shared core only
        groups.append((g, Binding(fam.position, MERGED, keys), simScore(frozenset(core), weights, pk, fam.position), carriers))
    return evaluate(groups, ctx)


def _bankKeys(ctx: SimContext, bank: str) -> set[int]:
    return {k for k, p in ctx._partOf.items() if p == bank}


def dedicatedOptions(
    fam: Family, pk: PhonemeKeys, ctx: SimContext, scored: list[tuple[float, Stroke]],
) -> list[Option]:
    """B4: a whole replacement stroke, for families with a k>=2 member and no merged option."""
    counts: dict[Stroke, float] = {}
    for c in fam.carriers[:400]:
        if c.span < 2:
            continue
        for st in c.rec.base[c.start:c.start + c.span]:
            counts[st] = counts.get(st, 0.0) + c.rec.frequency
    top = [s for s, _ in sorted(counts.items(), key=lambda t: (-t[1], t[0]))[:8]]
    cands: set[Stroke] = set(top)
    for a, b in combinations(top, 2):
        u = tuple(sorted(set(a) | set(b)))
        if ctx.isLegal(u):
            cands.add(u)
    cands.update(k for _s, k in scored[:5])
    weights = familySalience(fam, pk)
    options: list[Option] = []
    for d in sorted(cands):
        if d in ctx.singleStrokeOutlines or not ctx.isLegal(d) or set(d) & FORBIDDEN_KEYS:
            continue
        s = simScore(frozenset(d), weights, pk, fam.position)
        opt = evaluate([(list(range(len(fam.members))), Binding(fam.position, DEDICATED, d), s, fam.carriers)], ctx)
        options.append(opt)
    return options


def familyOptions(
    fam: Family, pk: PhonemeKeys, ctx: SimContext, keypresses: list[Stroke], allKeys: list[int],
) -> list[Option]:
    """Ranked options (best first, at most MAX_ALTERNATIVES) for one family."""
    merged, scored = mergedOptions(fam, pk, ctx, keypresses)
    ranked = rankOptions(merged)
    if ranked:
        # One keypress for the whole family, unless it makes distinct words collide.
        single = [o for o in ranked if conflictShare(o) <= SPLIT_MAX_LOSS]
        if single:
            return single
        subgroups = collisionSubgroups(fam, ranked[0])
        if len(subgroups) > 1:
            split = []
            for o in ranked:
                so = subgroupOption(fam, o.subgroups[0].binding.keys, pk, ctx, allKeys, subgroups)
                if so is not None and so.metrics.strokeFreqSaved > 0:
                    split.append(so)
            if split:
                return rankOptions(split)
        return ranked
    if any(m.k >= 2 for m in fam.members):
        return rankOptions(dedicatedOptions(fam, pk, ctx, scored))
    return []


# ═══════════════════════════════════════════════════════════════════════════
# Global assignment (B5)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Assigned:
    fam: Family
    option: Option
    alternativeIndex: int


def _groupsOf(fam: Family, opt: Option) -> list[tuple[Binding, list[Carrier]]]:
    return [(s.binding, [c for c in fam.carriers if c.member in s.members]) for s in opt.subgroups]


def assignGreedy(
    families: list[Family], options: dict[str, list[Option]], ctx: SimContext,
) -> tuple[list[Assigned], list[Family]]:
    """Process families by descending best gain; each takes its best non-conflicting option."""
    order = sorted((f for f in families if options.get(f.familyId)),
                   key=lambda f: -options[f.familyId][0].metrics.strokeFreqSaved)
    taken: set[tuple[str, tuple[int, ...]]] = set()
    assigned: list[Assigned] = []
    outlineOwner: dict[tuple, set[int]] = {}   # new outline -> indices into `assigned`
    unbound: list[Family] = [f for f in families if not options.get(f.familyId)]
    for fam in order:
        chosen: Assigned | None = None
        for ai, opt in enumerate(options[fam.familyId][:MAX_ALTERNATIVES]):
            if any(sig in taken for sig in opt.signature()):
                continue
            if _mutualConflict(fam, opt, assigned, outlineOwner, ctx):
                continue
            chosen = Assigned(fam, opt, ai)
            break
        if chosen is None:
            unbound.append(fam)
            continue
        idx = len(assigned)
        assigned.append(chosen)
        taken.update(chosen.option.signature())
        for res in chosen.option.results:
            for r in res:
                if r.newBase is not None:
                    outlineOwner.setdefault(r.newBase, set()).add(idx)
    return assigned, unbound


def _mutualConflict(
    fam: Family, opt: Option, assigned: list[Assigned], outlineOwner: dict[tuple, set[int]], ctx: SimContext,
) -> bool:
    owners: set[int] = set()
    for res in opt.results:
        for r in res:
            if r.newBase is not None and r.newBase in outlineOwner:
                owners |= outlineOwner[r.newBase]
    if not owners:
        return False
    groups = _groupsOf(fam, opt)
    solo = [[r.gain for r in res] for res in opt.results]
    for oi in sorted(owners):
        groups += _groupsOf(assigned[oi].fam, assigned[oi].option)
        solo += [[r.gain for r in res] for res in assigned[oi].option.results]
    combined = simulate(groups, ctx)
    for before, after in zip(solo, combined):
        for b, a in zip(before, after):
            if b > 0 and a.gain <= 0:
                return True
    return False


# ═══════════════════════════════════════════════════════════════════════════
# Unifying similar families under one keypress
# ═══════════════════════════════════════════════════════════════════════════

MERGE_SIM_MIN = 0.85       # cosine of the two families' salient-phoneme weights (tightened
                           # 2026-09-27, 0.75 -> 0.85: the loose bound let unrelated short
                           # suffixes chain together near-losslessly -- e.g. -ilite absorbed
                           # -icite, -aliste, lette, tuel, tel, quette, nnette one merge at a time,
                           # each individually >= 0.9 MERGE_KEEP, because this pass measures
                           # binding efficiency, not whether the result is a learnable single rule)
MERGE_MAX_MEMBERS = 8      # a unified family stays small enough to be one recognisable affix
                           # (tightened 16 -> 8, matching affixes.GROWTH_MAX_SLOT_VALUES's same
                           # "a wildcard/union this wide is its own unlearnable rule" principle)
MERGE_SIM_DROP = 0.9       # the union's similarity must stay this share of the weaker part's
MERGE_KEEP = 0.9           # the union must keep this share of the two families' separate gain
MERGE_PARTNERS = 3         # partners tried per family per round
MERGE_MEMBER_SIM_FLOOR = FAMILY_LINK_SIM   # same bar A3 used to cluster members together
GROWTH_MERGE_KEEP = 0.98   # phase 0 (growthMerges): a base candidate and the A9-grown candidate it
                           # produced are a KNOWN relationship, not one inferred from phoneme
                           # salience, so this runs first and is held to a much stricter bar than
                           # the general MERGE_KEEP -- merge only when it is very nearly free


def _stemSets(members: list[Candidate]) -> list[frozenset[str]]:
    return [frozenset(sorted(m.stemFreq, key=lambda s: -m.stemFreq[s])[:MAX_STEMS_FOR_JACCARD])
            for m in members]


def orphanMembers(fa: Family, fb: Family, floor: float = MERGE_MEMBER_SIM_FLOOR) -> list[str]:
    """Members of either family with no `floor`-similar (A3's `candidateSim`) partner in the
    OTHER family -- riding along on the aggregate salient-phoneme cosine (`MERGE_SIM_MIN`) rather
    than because they're actually the same affix (the `-cier`/`-ion` false-merge failure,
    RESUME_2026-09-26-affix-scan-state.md "Open problems"; scratch/oqlf-crosscheck-report.md).

    Diagnostic only, NOT a merge gate: tried as a hard per-member floor, it also rejected clearly
    good merges (`-tion` k=1 candidates score < 0.6 against every `-isation`-style k=2 candidate
    on length-normalized Levenshtein alone, even though `isation` literally ends in `tion`) --
    see scratch/oqlf-crosscheck-report.md for the validation. Reported in `affix-merges.tsv` for
    the user's manual review instead."""
    stemsA, stemsB = _stemSets(fa.members), _stemSets(fb.members)
    orphansA = [ma.ortho for i, ma in enumerate(fa.members)
                if not any(candidateSim(ma, mb, stemsA[i], stemsB[j]) >= floor for j, mb in enumerate(fb.members))]
    orphansB = [mb.ortho for j, mb in enumerate(fb.members)
                if not any(candidateSim(ma, mb, stemsA[i], stemsB[j]) >= floor for i, ma in enumerate(fa.members))]
    return orphansA + orphansB


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    dot = sum(w * b.get(p, 0.0) for p, w in a.items())
    na = sum(w * w for w in a.values()) ** 0.5
    nb = sum(w * w for w in b.values()) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


@dataclass
class Merge:
    a: str
    b: str
    result: str
    separateGain: float
    unionGain: float
    cosine: float
    orphans: list[str] = field(default_factory=list)   # diagnostic only, see `orphanMembers`


def growthMerges(
    fams: list[Family], options: dict[str, list[Option]], pk: PhonemeKeys, ctx: SimContext,
    keypresses: list[Stroke], allKeys: list[int],
) -> tuple[list[Family], dict[str, list[Option]], list[Merge], list[Merge]]:
    """Phase 0, run before `unifyFamilies` (2026-09-27 decision): merge a family holding an A9-grown
    candidate with the family holding the exact base candidate it grew from. This is a KNOWN
    structural relationship (`Candidate.grownFromKey`), not one inferred from phoneme-salience
    cosine -- so it gets first claim on merging, before the general pass's cosine-nearest-neighbour
    search can consume either family into an unrelated chain (which is how `-ilite` ended up merged
    with `-iciste`/`lette`/`tuel`/... before ever being compared to its own grown `-Xlite`
    extension). Held to `GROWTH_MERGE_KEEP`, much stricter than `MERGE_KEEP`, since a merge here
    should be nearly free, not just efficient."""
    fams = list(fams)
    options = dict(options)
    accepted: list[Merge] = []
    rejected: list[Merge] = []
    byKey: dict[tuple[str, int, str, str], Family] = {}
    for fam in fams:
        for m in fam.members:
            byKey[(m.position, m.k, m.phono, m.ortho)] = fam

    changed = True
    reportedRejections: set[tuple[str, str]] = set()
    while changed:
        changed = False
        pairKeys: set[tuple[str, str]] = set()
        for fam in fams:
            for m in fam.members:
                if m.grownFromKey is None:
                    continue
                parentFam = byKey.get(m.grownFromKey)
                if parentFam is None or parentFam is fam:
                    continue
                pairKeys.add(tuple(sorted((fam.familyId, parentFam.familyId))))  # type: ignore[arg-type]
        byId = {f.familyId: f for f in fams}
        used: set[str] = set()
        for aId, bId in sorted(pairKeys):
            if aId in used or bId in used:
                continue
            fa, fb = byId[aId], byId[bId]
            if not options.get(aId) or not options.get(bId):
                continue
            if (aId, bId) in reportedRejections:
                continue
            if len(fa.members) + len(fb.members) > MERGE_MAX_MEMBERS:
                continue
            # A true growth pair's carriers are NOT independent: the child's carriers are always
            # a subset of the parent's (it grew from them), so naively summing each side's own
            # strokeFreqSaved double-counts the overlap -- crediting the same word once at its
            # shallow (parent) saving and again at its deep (child) saving, though a word can only
            # ever be typed one way. The fair baseline takes, per carrier, whichever side's own
            # saving is better, summed once (found and fixed 2026-09-27: this bug made a
            # near-lossless merge, S026+S064, look like an 82.5%-retention loss and get rejected).
            gaByIdx = {cr.carrier.rec.idx: cr.gain * cr.carrier.rec.frequency
                       for grp in options[aId][0].results for cr in grp}
            gbByIdx = {cr.carrier.rec.idx: cr.gain * cr.carrier.rec.frequency
                       for grp in options[bId][0].results for cr in grp}
            fairBaseline = sum(max(gaByIdx.get(i, 0.0), gbByIdx.get(i, 0.0))
                                for i in gaByIdx.keys() | gbByIdx.keys())
            union = buildFamily(f"{aId}+{bId}", fa.members + fb.members)
            uopts = familyOptions(union, pk, ctx, keypresses, allKeys)
            gu = uopts[0].metrics.strokeFreqSaved if uopts else 0.0
            merge = Merge(aId, bId, union.familyId, fairBaseline, gu, 1.0, orphanMembers(fa, fb))
            if uopts and len(uopts[0].subgroups) == 1 and gu >= GROWTH_MERGE_KEEP * fairBaseline:
                accepted.append(merge)
                used |= {aId, bId}
                fams = [f for f in fams if f.familyId not in used] + [union]
                options.pop(aId, None)
                options.pop(bId, None)
                options[union.familyId] = uopts
                for mm in union.members:
                    byKey[(mm.position, mm.k, mm.phono, mm.ortho)] = union
                changed = True
            else:
                rejected.append(merge)
                reportedRejections.add((aId, bId))
    return fams, options, accepted, rejected


def unifyFamilies(
    fams: list[Family], options: dict[str, list[Option]], pk: PhonemeKeys, ctx: SimContext,
    keypresses: list[Stroke], allKeys: list[int],
) -> tuple[list[Family], dict[str, list[Option]], list[Merge], list[Merge]]:
    """Merge families of one position when a single keypress for their union keeps
    MERGE_KEEP of their separate gains. Returns (families, options, accepted, rejected)."""
    fams = list(fams)
    options = dict(options)
    accepted: list[Merge] = []
    rejected: list[Merge] = []
    tried: set[tuple[str, str]] = set()
    orig = {f.familyId: options[f.familyId][0].metrics.strokeFreqSaved for f in fams if options.get(f.familyId)}
    while True:
        sal = {f.familyId: familySalience(f, pk) for f in fams}
        pairs: list[tuple[float, Family, Family]] = []
        for i, fa in enumerate(fams):
            near = sorted(((_cosine(sal[fa.familyId], sal[fb.familyId]), fb) for fb in fams
                           if fb is not fa and fb.position == fa.position
                           and options.get(fa.familyId) and options.get(fb.familyId)),
                          key=lambda t: (-t[0], t[1].familyId))
            for c, fb in near[:MERGE_PARTNERS]:
                key = tuple(sorted((fa.familyId, fb.familyId)))
                if c >= MERGE_SIM_MIN and key not in tried and fa.familyId < fb.familyId:
                    pairs.append((c, fa, fb))
                    tried.add(key)  # type: ignore[arg-type]
        if not pairs:
            break
        pairs.sort(key=lambda t: (-t[0], t[1].familyId))
        merged = False
        used: set[str] = set()
        for c, fa, fb in pairs:
            if fa.familyId in used or fb.familyId in used:
                continue
            if len(fa.members) + len(fb.members) > MERGE_MAX_MEMBERS:
                continue
            # gains are measured against the ORIGINAL families so chained merges cannot erode
            ga, gb = orig[fa.familyId], orig[fb.familyId]
            simFloor = MERGE_SIM_DROP * min(options[fa.familyId][0].sim, options[fb.familyId][0].sim)
            union = buildFamily(f"{fa.familyId}+{fb.familyId}", fa.members + fb.members)
            uopts = familyOptions(union, pk, ctx, keypresses, allKeys)
            gu = uopts[0].metrics.strokeFreqSaved if uopts else 0.0
            m = Merge(fa.familyId, fb.familyId, union.familyId, ga + gb, gu, c, orphanMembers(fa, fb))
            if (uopts and len(uopts[0].subgroups) == 1 and gu >= MERGE_KEEP * (ga + gb)
                    and uopts[0].sim >= max(SIM_MIN, simFloor)):
                accepted.append(m)
                used |= {fa.familyId, fb.familyId}
                fams = [f for f in fams if f.familyId not in used] + [union]
                options[union.familyId] = uopts
                orig[union.familyId] = ga + gb
                merged = True
            else:
                rejected.append(m)
        if not merged:
            break
    fams.sort(key=lambda f: -f.upperBound)
    return fams, options, accepted, rejected
