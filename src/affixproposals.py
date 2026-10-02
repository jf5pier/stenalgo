"""Proposals for the affix review (`util.review_affix_rules`): what the algorithm suggests for each undecided
fusion or growth, with how much it helps and how much it hurts. The user decides; nothing here writes a verdict.

Every number comes from the engine itself (`affixes.simulate`, `affixrules.resolveFallbacks`,
`chooseRuleKeypress`, `ruleScoreFromResults`), so a proposal is judged by exactly the score the selection uses.

- **Fusion** of a merged spelling-variant anchor (`a|b|c`): the merged rule (the decided parts' growth forms kept
  on the parts' own spellings, every added spelling anchor-only) against the decided parts alone, each on its own
  best keypress. net = merged score - sum of the parts' scores.
- **Growth** of an anchor: forms that fuse the anchor syllable with the NEIGHBOUR syllable on one stroke. Candidate
  forms come from a fixed grammar on the neighbour's SOUND (onset {exact, C, C{1,2}, C*, [mn]} x nucleus {exact,
  vowel class, oral vowel, any vowel}, plus the exact syllable), per anchor spelling; the best (by net score at the
  rule's keys) is proposed first, then an accepted form is offered its best extension (one more alternative, at
  most `MAX_ATOMS`), then the sibling spellings of an accepted form (`dez` -> `dez|der|dé`). Exact neighbour
  SPELLINGS (the `man|ve` case) are offered only when they beat the best sound candidate. Refused labels are never
  proposed again.
"""
import re
from dataclasses import dataclass, field
from typing import Callable

from src import affixes as A
from src import affixrules as R
from src.affixbinding import PhonemeKeys
from src.affixdecisions import APART, FUSED, SINGLE, AnchorDecision, Decisions, ScopeForm
from src.keyboard import Stroke

CONSONANTS = "ptkbdgfsSvzZmnNlRjw"                 # X-SAMPA consonant phonemes
ORAL_VOWELS = "aeiouy"
MAX_ATOMS = 4            # alternatives in one form
MIN_WORDS = 5            # a candidate must cover at least this many carriers
EXACT_TOP = 40           # candidates (best optimistic bound) that get the exact evaluation
SIBLING_MAX_DISTANCE = 2
MAX_ROWS = 40            # groups (rows) of the per-addition table of a growth proposal, one accept line each

Key = tuple[str, str, str]   # (position, spellings, phono)


# ═══════════════════════════════════════════════════════════════════════════
# Numbers
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Numbers:
    """One evaluated rule configuration."""
    score: float
    benefit: float
    gainWords: int           # carriers that gain at least one stroke
    gainFreq: float
    fallbackWords: int       # scoped-form carriers that gained nothing and kept the anchor alone
    fallbackFreq: float
    exceptionWords: int      # hard exceptions (collisions)
    exceptionFreq: float
    keys: tuple[int, ...] | None
    grownWords: int = 0      # carriers that end on a growth form (span > 1) and gain
    grownFreq: float = 0.0


EMPTY = Numbers(0.0, 0.0, 0, 0.0, 0, 0.0, 0, 0.0, None)


def _numbers(rule: R.Rule, results: list[A.CarrierResult], nFallback: int, keys: Stroke | None) -> Numbers:
    exclusions = R.exclusionCountOf(rule.forms) + nFallback
    score, benefit, nExc, excFreq, _top = R.ruleScoreFromResults(results, exclusions, len(rule.forms))
    gained = [r for r in results if r.gain > 0]
    resultSpan1 = {r.carrier.rec.idx for r in results if r.carrier.span == 1}
    fell = [c for c in A.poolCarriers(rule.forms) if c.span > 1 and c.rec.idx in resultSpan1]
    grown = [r for r in gained if r.carrier.span > 1]
    return Numbers(score, benefit, len(gained), sum(r.carrier.rec.frequency for r in gained), nFallback,
                   sum(c.rec.frequency for c in fell), nExc, excFreq, keys, len(grown),
                   sum(r.carrier.rec.frequency for r in grown))


def evaluateAtKeys(rule: R.Rule, keys: Stroke, ctx: A.SimContext) -> tuple[Numbers, list[A.CarrierResult]]:
    carriers, nFallback = R.resolveFallbacks(rule, keys, A.poolCarriers(rule.forms), ctx)
    (res,) = A.simulate([(A.Binding(rule.position, A.RULE, keys), carriers)], ctx, boundaryRisk=False)
    return _numbers(rule, res, nFallback, keys), res


def numbersAtKeys(rule: R.Rule, keys: Stroke, ctx: A.SimContext) -> Numbers:
    """The rule scored on a fixed keypress (cheap: two simulations); a rule with no keys has no numbers."""
    return evaluateAtKeys(rule, keys, ctx)[0]


@dataclass
class Row:
    """The statistics of ONE addition (an added spelling, or one neighbour sound of a growth form)."""
    label: str
    words: int = 0                 # carriers of the rule in this group
    freq: float = 0.0
    gainWords: int = 0             # carriers that gain strokes
    benefit: float = 0.0           # sum of frequency x strokes saved
    fallbacks: int = 0             # growth carriers that gained nothing and kept the anchor alone
    fallbackFreq: float = 0.0
    exceptions: int = 0            # hard exceptions (collisions: the word keeps its long outline)
    exceptionFreq: float = 0.0
    examples: list[str] = field(default_factory=list)       # most frequent gaining words
    excExamples: list[str] = field(default_factory=list)    # most frequent hard exceptions

    @property
    def net(self) -> float:
        """This group's own contribution to the rule score (benefit - exception weight - fallback price)."""
        return self.benefit - R.EXCEPTION_ALPHA * self.exceptionFreq - R.EXCLUSION_COST * self.fallbacks

    def line(self) -> str:
        out = (f"{self.label}: {self.words} words freq {self.freq:.0f} | gain {self.gainWords} (benefit {self.benefit:.0f})"
               f" | exc {self.exceptions} (freq {self.exceptionFreq:.0f}) | fb {self.fallbacks} (freq {self.fallbackFreq:.0f})"
               f" | net {self.net:+.0f}")
        if self.examples:
            out += " | e.g. " + ", ".join(self.examples[:5])
        if self.excExamples:
            out += " | exceptions: " + ", ".join(self.excExamples[:5])
        return out


def rowsOf(rule: R.Rule, results: list[A.CarrierResult], groupOf: Callable[[A.Carrier], str | None]) -> dict[str, Row]:
    """Group the evaluated carriers of `rule` (`groupOf` of the carrier as POOLED, before any fallback; None = ignore)."""
    pooled = {c.rec.idx: c for c in A.poolCarriers(rule.forms)}
    rows: dict[str, Row] = {}
    gained: dict[str, list[tuple[float, str]]] = {}
    excepted: dict[str, list[tuple[float, str]]] = {}
    for r in results:
        orig = pooled.get(r.carrier.rec.idx, r.carrier)
        label = groupOf(orig)
        if label is None:
            continue
        row = rows.setdefault(label, Row(label))
        f, w = r.carrier.rec.frequency, r.carrier.rec.ortho
        row.words += 1
        row.freq += f
        if r.gain > 0:
            row.gainWords += 1
            row.benefit += f * r.gain
            gained.setdefault(label, []).append((f, w))
        elif r.reason in R.WORD_EXCEPTION_REASONS:
            row.exceptions += 1
            row.exceptionFreq += f
            excepted.setdefault(label, []).append((f, w))
        if orig.span > 1 and r.carrier.span == 1:
            row.fallbacks += 1
            row.fallbackFreq += f
    for label, row in rows.items():
        row.examples = [w for _f, w in sorted(gained.get(label, []), reverse=True)[:6]]
        row.excExamples = [w for _f, w in sorted(excepted.get(label, []), reverse=True)[:6]]
    return rows


def numbersBest(rule: R.Rule, pk: PhonemeKeys, ctx: A.SimContext, keypresses: list[Stroke]) -> Numbers:
    """The rule scored on its own best keypress (`chooseRuleKeypress`, ~30 s)."""
    if not rule.exactDone:
        R.chooseRuleKeypress(rule, pk, ctx, keypresses)
    if rule.keys is None:
        return EMPTY
    return _numbers(rule, rule.results, rule.fallbacks, rule.keys)


# ═══════════════════════════════════════════════════════════════════════════
# Proposals
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Proposal:
    kind: str                         # "fusion" | "growth"
    position: str
    spellings: str                    # the anchor the verdict belongs to
    phono: str
    label: str                        # shown to the user, and recorded in `refused` when refused
    helpsWords: int
    helpsFreq: float
    hurtsFallbacks: int
    hurtsFallbackFreq: float
    hurtsExceptions: int
    hurtsExceptionFreq: float
    net: float
    entry: AnchorDecision             # the entry to store when accepted
    flags: list[str] = field(default_factory=list)       # "similar rule: ...", "two decided rules on one key"
    rows: list[Row] = field(default_factory=list)        # per addition (added spelling / neighbour sound)
    notes: list[str] = field(default_factory=list)       # context lines (e.g. the effect on the existing words)
    groups: dict[str, tuple[str, str]] = field(default_factory=dict)   # row label -> (anchor spelling, neighbour sound)
    baseSpellings: list[str] = field(default_factory=list)             # fusion: the spellings of the rules being merged
    evaluateSubset: Callable[[list[str]], "Proposal"] | None = field(default=None, repr=False, compare=False)
    examples: list[str] = field(default_factory=list)
    alternatives: list[tuple[str, float]] = field(default_factory=list)   # next best (label, net)

    @property
    def key(self) -> Key:
        return (self.position, self.spellings, self.phono)

    def line(self) -> str:
        """`helps N words freq F | hurts N fb freq F, N exc | net +N | similar rule: ...`"""
        out = (f"helps {self.helpsWords} words freq {self.helpsFreq:.0f} | hurts {self.hurtsFallbacks} fb "
               f"freq {self.hurtsFallbackFreq:.0f}, {self.hurtsExceptions} exc | net {self.net:+.0f}")
        return out + "".join(f" | {f}" for f in self.flags)


def _entryOf(decisions: Decisions, position: str, spellings: str, phono: str) -> AnchorDecision:
    e = decisions.get(position, spellings, phono)
    if e is not None:
        return e
    return AnchorDecision(position, spellings, phono, FUSED if "|" in spellings else SINGLE, None)


def _otherRuleWithSpelling(decisions: Decisions, position: str, spelling: str, exclude: Key) -> str | None:
    for e in decisions.entries.values():
        if e.position == position and e.key != exclude and e.verdict != APART and e.growth is not None \
                and spelling in e.spellings.split("|"):
            return f"`{e.spellings}` /{e.phono}/"
    return None


# ── fusion ─────────────────────────────────────────────────────────────────

def restrictedGrowth(part: A.Candidate, forms: list[ScopeForm]) -> list[ScopeForm]:
    """The part's growth forms for the merged anchor: kept on the part's own spellings only (the other spellings
    of the merge stay anchor-only)."""
    own = frozenset(part.ortho.split("|"))
    return [ScopeForm(f.label, (f.anchors & own) if f.anchors is not None else own, f.sound, f.spelling)
            for f in forms if f.anchors is None or f.anchors & own]


def proposeFusion(
    merged: A.Candidate, pool: dict[tuple[str, int, str, str], A.Candidate], decisions: Decisions,
    pk: PhonemeKeys, ctx: A.SimContext, keypresses: list[Stroke], selectedKeys: frozenset[Key] = frozenset(),
    progress: Callable[[str], None] = lambda _m: None,
) -> Proposal | None:
    """Merged rule vs the parts that are decided anchors or selected rules (the other spellings are the ones
    the fusion adds). None when no part is a rule (nothing to compare with)."""
    byKey = {(c.position, c.k, c.phono, c.ortho): c for c in pool.values()}
    parts = [byKey[k] for k in merged.mergeParts if k in byKey]
    rules = [p for p in parts if p.hasDecision or (p.position, p.ortho, p.phono) in selectedKeys]
    if not rules:
        return None
    alone: list[Numbers] = []
    aloneRules: list[R.Rule] = []
    growth: list[ScopeForm] = []
    pendingGrowth = True
    for p in rules:
        progress(f"  evaluating `{p.ortho}` alone ...")
        # the part WITH the growth decided so far (also in this session: the pool was built before), so the merge is
        # compared with what the part is worth once grown
        aloneRule = R.Rule(p.position, p, [p] + A.growScopedForms(p, decisions), score=0.0)
        aloneRules.append(aloneRule)
        alone.append(numbersBest(aloneRule, pk, ctx, keypresses))
        partForms = decisions.growthForms(p.position, p.ortho, p.phono)
        if partForms is not None:
            pendingGrowth = False
            growth += restrictedGrowth(p, partForms)
    ruleIdx = {c.rec.idx for p in rules for c in p.carriers}
    own = sorted({s for p in rules for s in p.ortho.split("|")})
    spellingOf = (lambda c: c.rec.orthoSylls[c.start]) if merged.position == A.PREFIX else \
        (lambda c: c.rec.orthoSylls[c.start + c.span - 1])
    aloneSum = sum(a.score for a in alone)
    aloneExisting = Row("(existing words, alone)")
    for ar in aloneRules:
        for row in rowsOf(ar, ar.results, lambda c: "x").values():
            for f in ("words", "freq", "gainWords", "benefit", "fallbacks", "fallbackFreq", "exceptions", "exceptionFreq"):
                setattr(aloneExisting, f, getattr(aloneExisting, f) + getattr(row, f))

    def evaluateMerge(cand: A.Candidate) -> Proposal:
        entry = AnchorDecision(cand.position, cand.ortho, cand.phono, FUSED, None if pendingGrowth else growth)
        forms = A.growScopedForms(cand, decisions.withEntry(entry)) if growth else []
        progress(f"  evaluating the merged rule `{cand.ortho}` ...")
        fusedRule = R.Rule(cand.position, cand, [cand] + forms, score=0.0)
        fused = numbersBest(fusedRule, pk, ctx, keypresses)
        results = fusedRule.results
        keyNote = ""
        # the key search shortlists on a sample of the most frequent words and can miss a better key (found on `a|ha|â`:
        # the parts' own keys scored +1,200 above the shortlist's best): judge the merge at least at the parts' keys
        for a in alone:
            if a.keys is not None and a.keys != fused.keys:
                n2, res2 = evaluateAtKeys(fusedRule, a.keys, ctx)
                if n2.score > fused.score:
                    keyNote = f" (the search chose {fused.keys} = {fused.score:.0f}; the parts' keys {a.keys} are better)"
                    fused, results = n2, res2
        added = sorted((c for c in cand.carriers if c.rec.idx not in ruleIdx), key=lambda c: (-c.rec.frequency, c.rec.idx))
        flags: list[str] = []
        for sp in sorted({x for x in cand.ortho.split("|") if x not in own}):
            other = _otherRuleWithSpelling(decisions, cand.position, sp, (cand.position, cand.ortho, cand.phono))
            if other:
                flags.append(f"similar rule: added spelling `{sp}` is already in rule {other}")
        if len(rules) > 1:
            flags.append(f"two decided rules on one key ({', '.join('`' + p.ortho + '`' for p in rules)})")
        fusedRows = rowsOf(fusedRule, results,
                           lambda c: "(existing words)" if c.rec.idx in ruleIdx else spellingOf(c))
        rows = sorted((r for k, r in fusedRows.items() if k != "(existing words)"), key=lambda r: (-r.freq, r.label))
        before = fusedRows.get("(existing words)", Row("(existing words)"))
        notes = [
            f"existing words: alone {aloneExisting.words} words, benefit {aloneExisting.benefit:.0f}, exc "
            f"{aloneExisting.exceptions} (freq {aloneExisting.exceptionFreq:.0f}), fb {aloneExisting.fallbacks} -> merged "
            f"{before.words} words, benefit {before.benefit:.0f}, exc {before.exceptions} (freq {before.exceptionFreq:.0f}), "
            f"fb {before.fallbacks}; net change {before.net - aloneExisting.net:+.0f}"
            + (f"; their exceptions: {', '.join(before.excExamples[:6])}" if before.excExamples else ""),
            f"score with growth: parts alone {aloneSum:.0f} -> merged {fused.score:.0f}",
            "keys: parts alone " + ", ".join(str(a.keys) for a in alone) + f" -> merged {fused.keys}" + keyNote]
        return Proposal(
            "fusion", cand.position, cand.ortho, cand.phono, f"fuse {cand.ortho}", len(added),
            sum(c.rec.frequency for c in added),
            fused.fallbackWords - sum(a.fallbackWords for a in alone),
            fused.fallbackFreq - sum(a.fallbackFreq for a in alone),
            fused.exceptionWords - sum(a.exceptionWords for a in alone),
            fused.exceptionFreq - sum(a.exceptionFreq for a in alone), fused.score - aloneSum, entry, flags,
            rows=rows, notes=notes, examples=[c.rec.ortho for c in added[:6]])

    full = evaluateMerge(merged)
    full.groups = {row.label: (row.label, "") for row in full.rows}
    full.baseSpellings = own

    def evaluateSubset(accepted: list[str]) -> Proposal:
        """The merge of the rules' own spellings with only the `accepted` added spellings."""
        keep = set(own) | set(accepted)
        if keep == set(merged.ortho.split("|")):
            return full
        sub = A.Candidate(merged.position, 1, merged.phono, "|".join(sorted(keep)), isGeneralized=True,
                          variants=sorted(keep), isAnchor=True, mergeParts=[
                              k for k in merged.mergeParts if k[3] in keep],
                          carriers=[c for c in merged.carriers if spellingOf(c) in keep])
        A._finishStats(sub)
        return evaluateMerge(sub)

    full.evaluateSubset = evaluateSubset
    return full


# ── growth ─────────────────────────────────────────────────────────────────

def _atomRegexes(phono: str) -> list[tuple[str, str]]:
    """(label, regex) atoms generalising one neighbour syllable's sound, simplest first."""
    i = 0
    while i < len(phono) and phono[i] in CONSONANTS:
        i += 1
    onset, rest = phono[:i], phono[i:]
    cls = f"[{CONSONANTS}]"
    onsets: list[tuple[str, str]] = [(onset, re.escape(onset))]
    if len(onset) == 1:
        onsets.append(("C", cls))
    if 1 <= len(onset) <= 2:
        onsets.append(("C{1,2}", cls + "{1,2}"))
    onsets.append(("C*", cls + "*"))
    if onset in ("m", "n"):
        onsets.append(("[mn]", "[mn]"))
    nuclei: list[tuple[str, str]] = [(rest, re.escape(rest))]
    vowel = f"[^{CONSONANTS}]"
    if len(rest) == 1:
        for group in A.VOWEL_CLASSES:
            if rest in group and len(group) > 1:
                nuclei.append((f"[{group}]", f"[{re.escape(group)}]"))
        if rest in ORAL_VOWELS:
            nuclei.append((f"[{ORAL_VOWELS}]", f"[{ORAL_VOWELS}]"))
        nuclei.append(("V", vowel))
    elif rest and rest[0] not in CONSONANTS:
        nuclei.append(("V*", vowel + ".*"))
    return [(o[0] + n[0], o[1] + n[1]) for o in onsets for n in nuclei]


def _editDistance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


@dataclass
class _Cand:
    label: str
    forms: list[ScopeForm]          # the whole growth list this candidate would store
    covered: frozenset[int]         # carriers (rec.idx) the new/extended form takes
    bound: float                    # optimistic gain: one extra stroke per covered word
    isSpelling: bool = False


def _growthRule(root: A.Candidate, forms: list[ScopeForm], decisions: Decisions) -> R.Rule:
    entry = AnchorDecision(root.position, root.ortho, root.phono, FUSED if "|" in root.ortho else SINGLE, forms)
    grown = A.growScopedForms(root, decisions.withEntry(entry)) if forms else []
    return R.Rule(root.position, root, [root] + grown, score=0.0)


def proposeGrowth(
    root: A.Candidate, decisions: Decisions, keys: Stroke, ctx: A.SimContext, refused: frozenset[str] = frozenset(),
    maxExact: int = EXACT_TOP,
) -> Proposal | None:
    """The best growth change of `root`'s rule at its keys: a new form, an extension of an existing form by one
    alternative, or a sibling spelling added to an existing form. None when nothing has a positive net."""
    entry = _entryOf(decisions, root.position, root.ortho, root.phono)
    current: list[ScopeForm] = list(entry.growth or [])
    refused = refused | frozenset(entry.refused)
    refusedGroups = {r for r in refused if " + /" in r}          # "spelling + /sound/" groups the user refused
    base = numbersAtKeys(_growthRule(root, current, decisions), keys, ctx)

    info: dict[int, tuple[str, str, str]] = {}        # rec.idx -> (anchor spelling, neighbour spelling, neighbour sound)
    for c in root.carriers:
        rec = c.rec
        if len(rec.orthoSylls) != len(rec.base):
            continue
        g = A._growCarrier(root.position, c)
        if g is None:
            continue
        _gc, nPhono, nOrtho = g
        info[rec.idx] = (rec.orthoSylls[c.start], nOrtho, nPhono)
    taken = {c.rec.idx for f in _growthRule(root, current, decisions).forms[1:] for c in f.carriers}
    taken |= {i for i, (sp, _o, ph) in info.items() if f"{sp} + /{ph}/" in refusedGroups}
    freq = {c.rec.idx: c.rec.frequency for c in root.carriers}
    merged = "|" in root.ortho
    cands: list[_Cand] = []

    def covered(spelling: str | None, pattern: re.Pattern[str], on: str) -> frozenset[int]:
        out = set()
        for idx, (sp, nOrtho, nPhono) in info.items():
            if idx in taken or (spelling is not None and sp != spelling):
                continue
            if pattern.fullmatch(nPhono if on == "sound" else nOrtho):
                out.add(idx)
        return frozenset(out)

    bySpelling: dict[str, dict[str, int]] = {}
    for idx, (sp, _o, nPhono) in info.items():
        if idx not in taken:
            bySpelling.setdefault(sp, {})[nPhono] = bySpelling.get(sp, {}).get(nPhono, 0) + 1

    seen: dict[tuple[str, frozenset[int]], _Cand] = {}
    for sp in sorted(bySpelling):
        atoms: dict[str, str] = {}                     # regex -> label (simplest label wins)
        for phono in bySpelling[sp]:
            for label, rx in _atomRegexes(phono):
                if rx not in atoms or len(label) < len(atoms[rx]):
                    atoms[rx] = label
        for rx, label in atoms.items():
            cov = covered(sp, re.compile(rx), "sound")
            if len(cov) < MIN_WORDS:
                continue
            anchors = frozenset({sp}) if merged else None
            full = f"{sp}:{label}" if merged else label
            key = (sp, cov)
            if key in seen and len(seen[key].label) <= len(full):
                continue
            seen[key] = _Cand(full, current + [ScopeForm(full, anchors, re.compile(rx))], cov,
                              sum(freq[i] for i in cov) - R.FORM_COST)
        # exact neighbour spellings (shown only when they beat the best sound candidate)
        nOrthos = {n for _i, (s, n, _p) in info.items() if s == sp}
        for nOrtho in sorted(nOrthos):
            cov = frozenset(i for i, (s, n, _p) in info.items() if s == sp and n == nOrtho and i not in taken)
            if len(cov) >= MIN_WORDS:
                full = f"{sp}:{nOrtho}" if merged else nOrtho
                cands.append(_Cand(full, current + [ScopeForm(full, frozenset({sp}) if merged else None, None,
                                                              re.compile(re.escape(nOrtho)))],
                                   cov, sum(freq[i] for i in cov) - R.FORM_COST, isSpelling=True))
    cands += list(seen.values())

    # extensions of an existing form: one more alternative atom, or a sibling spelling
    for fi, form in enumerate(current):
        if form.sound is not None and form.sound.pattern.count("|") + 1 < MAX_ATOMS:
            sps = sorted(form.anchors) if form.anchors is not None else sorted(bySpelling)
            for sp in sps:
                for rx, label in {rx: label for phono in bySpelling.get(sp, {}) for label, rx in _atomRegexes(phono)}.items():
                    cov = covered(sp, re.compile(rx), "sound")
                    if len(cov) < MIN_WORDS:
                        continue
                    ext = ScopeForm(f"{form.label}|{label}", form.anchors, re.compile(f"(?:{form.sound.pattern})|{rx}"),
                                    form.spelling)
                    cands.append(_Cand(ext.label, current[:fi] + [ext] + current[fi + 1:], cov,
                                       sum(freq[i] for i in cov)))
        if form.anchors is not None:
            for sp in sorted(bySpelling):
                if sp in form.anchors or not any(
                        sp[:1] == a[:1] and _editDistance(sp, a) <= SIBLING_MAX_DISTANCE for a in form.anchors):
                    continue
                sibling = ScopeForm(f"{form.label}+{sp}", form.anchors | {sp}, form.sound, form.spelling)
                cov = frozenset(i for i, (s, n, p) in info.items() if s == sp and i not in taken
                                and (form.sound is None or form.sound.fullmatch(p))
                                and (form.spelling is None or form.spelling.fullmatch(n)))
                if len(cov) >= 1:
                    cands.append(_Cand(sibling.label, current[:fi] + [sibling] + current[fi + 1:], cov,
                                       sum(freq[i] for i in cov)))
    cands = [c for c in cands if c.label not in refused]
    sound = sorted((c for c in cands if not c.isSpelling), key=lambda c: (-c.bound, len(c.label), c.label))[:maxExact]
    spell = sorted((c for c in cands if c.isSpelling), key=lambda c: (-c.bound, len(c.label), c.label))[:maxExact // 4]
    scored: list[tuple[float, _Cand, Numbers]] = []
    for cand in sound + spell:
        n = numbersAtKeys(_growthRule(root, cand.forms, decisions), keys, ctx)
        scored.append((n.score - base.score, cand, n))
    bestSound = max((s for s in scored if not s[1].isSpelling), key=lambda t: t[0], default=None)
    ranked = sorted((s for s in scored if s[0] > 0 and (not s[1].isSpelling or bestSound is None or s[0] > bestSound[0])),
                    key=lambda t: (-t[0], len(t[1].label), t[1].label))
    if not ranked:
        return None
    net, best, n = ranked[0]
    flags: list[str] = []
    patterns = {f.sound.pattern for f in best.forms if f.sound is not None}
    for e in decisions.entries.values():
        if e.key == (root.position, root.ortho, root.phono) or e.growth is None:
            continue
        for f in e.growth:
            if f.sound is not None and f.sound.pattern in patterns:
                flags.append(f"similar rule: pattern `{f.label}` already used by `{e.spellings}`")
                break
    for sp in sorted({a for f in best.forms if f.anchors is not None for a in f.anchors} - set(root.ortho.split("|"))):
        other = _otherRuleWithSpelling(decisions, root.position, sp, (root.position, root.ortho, root.phono))
        if other:
            flags.append(f"similar rule: added spelling `{sp}` is already in rule {other}")
    helped = [c for c in root.carriers if c.rec.idx in best.covered]
    helped.sort(key=lambda c: (-c.rec.frequency, c.rec.idx))
    newEntry = AnchorDecision(root.position, root.ortho, root.phono, entry.verdict, best.forms, list(entry.refused),
                              entry.note, entry.date, dict(entry.numbers))
    # per addition: the newly covered words grouped by (anchor spelling, neighbour sound)
    rule = _growthRule(root, best.forms, decisions)
    _n, results = evaluateAtKeys(rule, keys, ctx)

    def group(c: A.Carrier) -> str | None:
        if c.rec.idx not in best.covered or c.span < 2:
            return None
        r = c.rec
        a, nb = (c.start, c.start + c.span - 1) if root.position == A.PREFIX else (c.start + c.span - 1, c.start)
        return f"{r.orthoSylls[a]} + /{r.phonoSylls[nb]}/"

    allRows = sorted(rowsOf(rule, results, group).values(), key=lambda r: (-r.freq, r.label))
    shown = allRows[:MAX_ROWS]
    notes = [f"base (current forms) at keys {keys}: score {base.score:.0f}; proposed: score {n.score:.0f}; "
             f"{len(allRows)} (anchor spelling, neighbour sound) groups newly covered"
             + (f", the {MAX_ROWS} largest shown" if len(allRows) > MAX_ROWS else "")]
    groups = {}
    for row in shown:
        sp, _plus, ph = row.label.partition(" + /")
        groups[row.label] = (sp, ph[:-1])
    return Proposal(
        "growth", root.position, root.ortho, root.phono, best.label, n.grownWords - base.grownWords,
        n.grownFreq - base.grownFreq, n.fallbackWords - base.fallbackWords, n.fallbackFreq - base.fallbackFreq,
        n.exceptionWords - base.exceptionWords, n.exceptionFreq - base.exceptionFreq, net, newEntry, flags,
        rows=shown, notes=notes, examples=[c.rec.ortho for c in helped[:6]],
        alternatives=[(s[1].label, s[0]) for s in ranked[1:4]], groups=groups)


def formsForGroups(root: A.Candidate, accepted: list[tuple[str, str]]) -> list[ScopeForm]:
    """Growth forms for the accepted (anchor spelling, neighbour sound) groups: one form per distinct set of sounds
    (spellings that take the same sounds share a form, which saves form prices); a single spelling needs no anchor."""
    bySpelling: dict[str, list[str]] = {}
    for sp, ph in accepted:
        bySpelling.setdefault(sp, [])
        if ph not in bySpelling[sp]:
            bySpelling[sp].append(ph)
    if "|" not in root.ortho:
        sounds = sorted({ph for _sp, ph in accepted})
        return [ScopeForm("|".join(sounds), None, re.compile("|".join(re.escape(p) for p in sounds)))] if sounds else []
    bySounds: dict[tuple[str, ...], list[str]] = {}
    for sp, phs in sorted(bySpelling.items()):
        bySounds.setdefault(tuple(sorted(phs)), []).append(sp)
    return [ScopeForm(f"{'|'.join(sps)}:{'|'.join(phs)}", frozenset(sps), re.compile("|".join(re.escape(p) for p in phs)))
            for phs, sps in bySounds.items()]
