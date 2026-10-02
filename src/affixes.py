"""
Affix Abbreviation Discovery (Part A) and the shared gain simulation (Part B reuses it).

MEASUREMENT AND PROPOSALS ONLY -- nothing here is wired into the theory. See
docs/history/PLAN_2026-09-26-affix-abbreviations.md for the design decisions this module implements.

A word "carries" an affix when its first (or last) k syllable strokes spell it and its stem
is an attested lemma. Affixes are grouped in families of similar members, competing members
(bio+logie / bio+logique) are split into sub-groups, and `simulate` measures the strokes a
keypress binding saves on the family's carriers.
"""
import bisect
import functools
import unicodedata
from dataclasses import dataclass, field
from typing import NamedTuple

from src.affixdecisions import FUSED, Decisions, loadDecisions
from src.ambiguitychecker import assignStarHashCombos, buildWordToStrokes
from src.keyboard import Starboard, Stroke, Strokes, canonicalizeStrokes
from src.word import Word

MIN_STEM_LETTERS = 3
MIN_CARRIER_LEMMAS = 5
MIN_STEM_ROOTS = 5         # distinct 4-letter stem roots (rai|sonner, rai|son count once)
STEM_ROOT_LETTERS = 4
VARIANT_MAX_NEW_CONFLICT_SHARE = 0.02  # U3a: fusing spelling variants may add at most this share of
                                       # the merged frequency as new different-lemma collisions

PREFIX = "prefix"
SUFFIX = "suffix"
MERGED = "merged"
DEDICATED = "dedicated"
RULE = "rule"    # Phase 2 (DESIGN §4.2): merged when clash-free, else a physical-reason standalone
                 # fallback -- collisions still cost the word its abbreviation, never a shorter one.

VOWEL_CLASSES = ("eE@°29", "oO", "a", "i", "y8", "u", "§", "51")


# ═══════════════════════════════════════════════════════════════════════════
# Records
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class WordRecord:
    idx: int
    ortho: str
    lemme: str
    gramCat: str
    frequency: float
    phonoSylls: tuple[str, ...]
    orthoSylls: tuple[str, ...]
    base: Strokes                # canonical phonetic-theory strokes (one per syllable)
    extra: Strokes               # strokes after the base ones (feature strokes, marks)
    isLemmaForm: bool
    markKeys: tuple[int, ...] = ()  # mark keys merged into the last base stroke


def extractRecords(
    phoneticTheory: dict[Strokes, list[Word]],
    disambiguated: dict[Word, list[Strokes]],
) -> tuple[list[WordRecord], int]:
    """One record per Word; returns (records, skipped count)."""
    wordToStrokes = buildWordToStrokes(phoneticTheory)
    records: list[WordRecord] = []
    skipped = 0
    for word, rawBase in wordToStrokes.items():
        full = disambiguated.get(word)
        base = canonicalizeStrokes(rawBase)
        phono = tuple(word.phonemesToSyllableNames(withSilent=False))
        orthoS = tuple(word.graphemsToSyllables(withSilent=False))
        if (not full or len(orthoS) != len(base) or len(phono) != len(base)
                or "".join(orthoS) != word.ortho or not base):
            skipped += 1
            continue
        fullC = canonicalizeStrokes(full[0])
        if len(fullC) < len(base):
            skipped += 1
            continue
        marks = tuple(sorted(set(fullC[len(base) - 1]) - set(base[-1])))
        records.append(WordRecord(
            idx=len(records), ortho=word.ortho, lemme=word.lemme, gramCat=str(word.gramCat),
            frequency=float(word.frequency), phonoSylls=phono, orthoSylls=orthoS,
            base=base, extra=fullC[len(base):], isLemmaForm=(word.ortho == word.lemme),
            markKeys=marks))
    return records, skipped


def fullStrokesOf(rec: WordRecord) -> Strokes:
    """The record's final outline: base with the first mark merged into its last stroke."""
    return withMarks(rec.base, rec.markKeys) + rec.extra


def withMarks(base: Strokes, markKeys: tuple[int, ...]) -> Strokes:
    if not markKeys:
        return base
    return base[:-1] + (tuple(sorted(set(base[-1]) | set(markKeys))),)


# ═══════════════════════════════════════════════════════════════════════════
# Morphology
# ═══════════════════════════════════════════════════════════════════════════

def norm(s: str) -> str:
    """Lowercase, strip accents, drop one final 'e'."""
    s = "".join(c for c in unicodedata.normalize("NFD", s.lower()) if not unicodedata.combining(c))
    return s[:-1] if s.endswith("e") else s


class LemmaIndex:
    """Normalized lemmas, for stem-attestation lookups."""

    def __init__(self, lemmas: set[str] | list[str]) -> None:
        self.set = {norm(x) for x in lemmas}
        self.sorted = sorted(self.set)
        self.attestedCache: dict[tuple[str, str, str], bool] = {}

    def hasLemma(self, nstem: str) -> bool:
        return nstem in self.set

    def hasOtherLemmaStartingWith(self, nstem: str, ownNorm: str) -> bool:
        """Some normalized lemma other than `ownNorm` equals or starts with `nstem`."""
        i = bisect.bisect_left(self.sorted, nstem)
        while i < len(self.sorted) and self.sorted[i].startswith(nstem):
            if self.sorted[i] != ownNorm:
                return True
            i += 1
        return False


def passesPrefixFilter(stem: str, lemmas: LemmaIndex) -> bool:
    return len(stem) >= MIN_STEM_LETTERS and lemmas.hasLemma(norm(stem))


def passesSuffixFilter(stem: str, ownOrtho: str, lemmas: LemmaIndex) -> bool:
    return len(stem) >= MIN_STEM_LETTERS and lemmas.hasOtherLemmaStartingWith(norm(stem), norm(ownOrtho))


def isAttested(pos: str, c: "Carrier", lemmas: LemmaIndex) -> bool:
    """The OLD stem-attestation carrier gate (passesPrefixFilter/passesSuffixFilter, with the
    inflected-prefix lemma fallback), now evaluated only to report `Candidate.attestedShare`
    (plan U2: lemma no longer gates which words a pattern covers). Memoized per stem."""
    r = c.rec
    own = r.ortho if (r.isLemmaForm or isIterParticiple(r)) else r.lemme
    key = (pos, c.stem, own if pos == SUFFIX else r.lemme + "|" + r.ortho)
    hit = lemmas.attestedCache.get(key)
    if hit is None:
        if pos == SUFFIX:
            hit = passesSuffixFilter(c.stem, own, lemmas)
        else:
            hit = passesPrefixFilter(c.stem, lemmas)
            if not hit and not r.isLemmaForm:
                oa = r.ortho[:len(r.ortho) - len(c.stem)]
                hit = r.lemme.startswith(oa) and passesPrefixFilter(r.lemme[len(oa):], lemmas)
        lemmas.attestedCache[key] = hit
    return hit


def attestedShareOf(pos: str, carriers: list["Carrier"], lemmas: LemmaIndex) -> float:
    total = sum(c.rec.frequency for c in carriers)
    if total <= 0:
        return 0.0
    return sum(c.rec.frequency for c in carriers if isAttested(pos, c, lemmas)) / total


VERB_GRAMCAT = "GramCat.VER"  # WordRecord.gramCat is str(word.gramCat), e.g. "GramCat.VER"


def isIterParticiple(r: WordRecord) -> bool:
    """2026-09-27 (user request): an inflected form of a verb whose infinitive ends "iter" --
    its past participle is spelled "...ité" (+ gender/number), identical in shape to the -ité
    noun suffix, so let it seed/join suffix candidates the same way a lemma form does. Safe to
    admit unconditionally (not just the participle moods): a present-tense form like "habite"
    doesn't end in a suffix-shaped tail either, so only the participle's own syllables actually
    match anything -- this never resurrects the bare "-er ending" fragments dropped above."""
    return r.gramCat == VERB_GRAMCAT and not r.isLemmaForm and r.lemme.endswith("iter")


def inheritedSpan(lemmaRec: WordRecord, k: int, w: WordRecord) -> tuple[int, int] | None:
    """Suffix inheritance (A2c): (start, run length) of `w`'s span, or None.

    The lemma's last k strokes are the suffix; `w` inherits the maximal run of identical strokes
    from the suffix start, provided its stem strokes are the lemma's."""
    nL = len(lemmaRec.base)
    start = nL - k
    if start < 0 or len(w.base) < start or w.base[:start] != lemmaRec.base[:start]:
        return None
    run = 0
    i = start
    while i < len(w.base) and i < nL and w.base[i] == lemmaRec.base[i]:
        run += 1
        i += 1
    return (start, run) if run >= 1 else None


# ═══════════════════════════════════════════════════════════════════════════
# Candidates
# ═══════════════════════════════════════════════════════════════════════════

class Carrier(NamedTuple):
    rec: WordRecord
    start: int      # index of the first affix stroke in rec.base
    span: int       # number of affix strokes this word has (k_w)
    stem: str
    member: int = 0  # family-member index (set when carriers are pooled per family)


@dataclass
class Candidate:
    position: str
    k: int
    phono: str        # syllable names joined by '.'
    ortho: str
    carriers: list[Carrier] = field(default_factory=list)
    isSeed: bool = False
    lemmas: int = 0
    freq: float = 0.0
    examples: list[str] = field(default_factory=list)
    stemFreq: dict[str, float] = field(default_factory=dict)  # norm(stem) -> summed lemma-form carrier freq
    stemRoots: int = 0
    isGeneralized: bool = False        # pooled from spelling variants (A8 group / variant merge) or grown
    variants: list[str] = field(default_factory=list)  # the orthos pooled into this one, if isGeneralized
    grownDepth: int = 0                # A9: syllables absorbed beyond the base candidate that seeded growth
    exceptionCount: int = 0            # A9: carriers dropped (kept unabbreviated) to allow the growth
    exceptionFreq: float = 0.0
    grownFromKey: tuple[str, int, str, str] | None = None  # A9/lattice: the exact parent grown from
    slots: tuple["Slot", ...] = ()     # lattice (§3.1): slots[0] is next to the base, last next to the stem
    aliases: list[tuple[str, int, str, str]] = field(default_factory=list)  # lattice dedupe (§3.4)
    rootKey: tuple[str, int, str, str] | None = None  # lattice (§3.4): the ungrown ancestor
    alsoFrom: list[tuple[str, int, str, str]] = field(default_factory=list)  # further parents whose
                                       # identical duplicate child was folded into this node
    isAnchor: bool = False             # a rule root: k=1 seed, A8 group or variant merge (never grown)
    attestedShare: float = 0.0         # freq share of carriers whose stem passes the OLD lemma filter
                                       # (report only -- no longer a carrier gate, plan U2)
    mergeParts: list[tuple[str, int, str, str]] = field(default_factory=list)  # variant merge: the parts
    newConflictFreq: float = 0.0       # variant merge: collision frequency the fusion added
    isScoped: bool = False             # a form built from a decided scope (affix_decisions.json): its carriers
                                       # that gain nothing fall back to the anchor alone (affixrules)
    hasDecision: bool = False          # an anchor whose growth is decided (forms or none): never grown by the lattice

    @property
    def phonoFlat(self) -> str:
        return self.phono.replace(".", "")

    @property
    def strokeFreq(self) -> float:
        return sum(c.rec.frequency * c.span for c in self.carriers)


def loadSeeds(path: str = "resources/affixSeeds.tsv") -> tuple[set[tuple[str, str]], dict[str, list[tuple[str, str]]]]:
    """(position, affix) seed pairs, and the seed families' members."""
    pairs: set[tuple[str, str]] = set()
    fams: dict[str, list[tuple[str, str]]] = {}
    with open(path, encoding="utf-8") as f:
        next(f)
        for line in f:
            pos, affix, _chord, fam = line.rstrip("\n").split("\t")
            pairs.add((pos, affix))
            fams.setdefault(fam, [])
            if (pos, affix) not in fams[fam]:
                fams[fam].append((pos, affix))
    return pairs, fams


@dataclass(frozen=True)
class Slot:
    """One absorbed syllable of a lattice node (§3.1): a fixed value, a group sharing a fixed
    nucleus+coda but varying onset, or a full wildcard -- each may exclude a short list of
    attested values that would otherwise cause too many collisions (D3, D6)."""
    kind: str                        # "exact" | "onset" | "any" | "scope" (value: the scope label)
    value: str = ""                  # exact: the syllable phono; onset: the nucleus+coda ("rest")
    excluded: tuple[str, ...] = ()   # onset: excluded onset consonants; any: excluded syllable phonos














# Latin prefix assimilation groups, citation-backed (not auto-discovered by A7 or A3's
# clustering -- see docs/history/PLAN_2026-09-26-affix-abbreviations.md §11 for the etymological research).
# `con-` assimilates to `co-` before a vowel, `col-` before l, `com-` before b/m/p, `cor-`
# before r (Wiktionnaire, fr.wiktionary.org/wiki/con-): one prefix, safe to pool.
#
# Deliberately NOT included despite the same assimilation pattern: in-/im-/il-/ir- (negation) --
# `in-` is ALSO a second, unrelated "into" prefix (intérieur, induire) sharing the same spelling,
# so pooling by spelling alone would merge two different prefixes. di-/dis- and sub-/su- are
# confirmed genuinely-or-mostly distinct prefixes despite looking similar -- never pool these.
KNOWN_PREFIX_ASSIMILATION_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"co", "con", "com", "col", "cor"}),
)


def poolKnownAffixGroups(
    cands: dict[tuple[str, int, str, str], Candidate],
) -> dict[tuple[str, int, str, str], Candidate]:
    """A8: pool the curated `KNOWN_PREFIX_ASSIMILATION_GROUPS` (run alongside A7, before the
    thresholds), for etymological relationships too irregular for A7's structural
    same-tail-different-onset rule (a consonant is inserted or dropped, not substituted)."""
    pooled = dict(cands)
    for group in KNOWN_PREFIX_ASSIMILATION_GROUPS:
        members = [(key, c) for key, c in cands.items()
                   if c.position == PREFIX and c.k == 1 and c.ortho in group and c.carriers]
        if len(members) < 2:
            continue
        keys, cs = zip(*members)
        variants = sorted({c.ortho for c in cs})
        merged = Candidate(PREFIX, 1, "+".join(sorted({c.phono for c in cs})), "+".join(variants),
                            isSeed=any(c.isSeed for c in cs), isGeneralized=True, variants=variants)
        merged.carriers = [carrier for c in cs for carrier in c.carriers]
        for key in keys:
            del pooled[key]
        pooled[(PREFIX, 1, merged.phono, merged.ortho)] = merged
    return pooled


# ═══════════════════════════════════════════════════════════════════════════
# A9: iterative breadth-first affix growth
# ═══════════════════════════════════════════════════════════════════════════

def _growCarrier(pos: str, c: Carrier) -> tuple[Carrier, str, str] | None:
    """Absorb one more syllable into `c`'s affix span, toward the stem. Returns the grown
    carrier plus the absorbed syllable's (phono, ortho), or None if no stem syllable is left."""
    rec = c.rec
    if pos == SUFFIX:
        newStart = c.start - 1
        if newStart < 1:
            return None
        stem = "".join(rec.orthoSylls[:newStart])
        grown = Carrier(rec, newStart, c.span + 1, stem, c.member)
        return grown, rec.phonoSylls[newStart], rec.orthoSylls[newStart]
    newSpan = c.span + 1
    if newSpan >= len(rec.base):
        return None
    stem = "".join(rec.orthoSylls[newSpan:])
    grown = Carrier(rec, 0, newSpan, stem, c.member)
    return grown, rec.phonoSylls[newSpan - 1], rec.orthoSylls[newSpan - 1]


def _exceptionShare(pos: str, carriers: list[Carrier], denom: float | None = None) -> tuple[float, set[int]]:
    """The fraction of frequency that would collide -- share an identical remaining stem stroke
    with a different-lemma carrier -- if `carriers`' absorbed syllable(s) are generalized away.
    On each colliding stroke, only the highest-frequency lemma keeps the abbreviation; the rest
    are exceptions (they simply keep their unabbreviated outline, per Decision 1).

    `denom` (default: this call's own carrier frequency) should be the *base candidate's* total
    frequency when comparing candidate merges: measuring share against a merged group's own,
    ever-growing total lets a greedy merge sequence dilute the check to nothing and swallow
    everything (each added straggler barely moves the ratio) -- a fixed denominator caps total
    exceptions as a share of the whole affix, not of whatever subset has been pooled so far."""
    byStroke: dict[Strokes, list[Carrier]] = {}
    for c in carriers:
        stroke = c.rec.base[:c.start] if pos == SUFFIX else c.rec.base[c.span:]
        byStroke.setdefault(stroke, []).append(c)
    excluded: set[int] = set()
    for group in byStroke.values():
        lemmas = {c.rec.lemme for c in group}
        if len(lemmas) < 2:
            continue
        lemmaFreq = {l: sum(c.rec.frequency for c in group if c.rec.lemme == l) for l in lemmas}
        best = max(lemmaFreq, key=lambda l: lemmaFreq[l])
        excluded.update(c.rec.idx for c in group if c.rec.lemme != best)
    totalFreq = denom if denom is not None else (sum(c.rec.frequency for c in carriers) or 1.0)
    exceptionFreq = sum(c.rec.frequency for c in carriers if c.rec.idx in excluded)
    return exceptionFreq / totalFreq, excluded






# ═══════════════════════════════════════════════════════════════════════════
# Lattice growth (docs/history/DESIGN_2026-09-27-affix-rule-selection.md §3): the default path. Replaces the
# single greedy agglomeration above (kept, unchanged, for --legacy) with a lattice where growing
# one syllable emits ALL of an exact leaf per absorbed value, an onset-generalized group per
# shared nucleus+coda, and one full wildcard -- nothing here absorbs anything else (D2, D3).
# Phase 2 (rule construction) and Phase 3/4 (selection, binding) are NOT implemented yet: this
# only builds and returns the pool of pattern nodes.
# ═══════════════════════════════════════════════════════════════════════════



















# filled by the last growAffixesLattice call, for util/affix_scan.py's Part A report


def _candKey(c: Candidate) -> tuple[str, int, str, str]:
    return (c.position, c.k, c.phono, c.ortho)




def growScopedForms(parent: Candidate, decisions: Decisions) -> list[Candidate]:
    """The decided k=2 forms of a scoped anchor, in the table's order. A carrier joins the first form
    that matches it (a word gets one form); the neighbour must be an existing, aligned syllable and
    keep at least one stem syllable (`_growCarrier`)."""
    forms = decisions.growthForms(parent.position, parent.ortho, parent.phono) or []
    taken: set[int] = set()
    out: list[Candidate] = []
    for form in forms:
        kept: list[Carrier] = []
        for c in parent.carriers:
            rec = c.rec
            if c.rec.idx in taken or len(rec.orthoSylls) != len(rec.base):
                continue
            g = _growCarrier(parent.position, c)
            if g is None:
                continue
            gc, nPhono, nOrtho = g
            if form.matches(rec.orthoSylls[c.start], nOrtho, nPhono):
                kept.append(gc)
                taken.add(rec.idx)
        if not kept:
            continue
        label = form.label
        if parent.position == SUFFIX:
            phono, ortho = f"{label}.{parent.phono}", f"·[{label}]{parent.ortho}"
        else:
            phono, ortho = f"{parent.phono}.{label}", f"{parent.ortho}[{label}]·"
        cand = Candidate(
            parent.position, parent.k + 1, phono, ortho, carriers=kept, isGeneralized=True,
            grownDepth=1, grownFromKey=_candKey(parent), rootKey=_candKey(parent),
            slots=(Slot("scope", label),), isScoped=True)
        _finishStats(cand)
        out.append(cand)
    return out




TOP_WORDS_EXCLUDED = 200  # 2026-09-27 (user decision): the N most frequent distinct words earn
                          # their own dedicated stenogram in the real theory regardless of shape
                          # (e.g. "jamais" was propping up 99.7% of the "ja-" prefix rule's score),
                          # so they must not count toward -- or inflate -- any affix rule's carrier
                          # frequency; monosyllabic words get the same treatment (one stroke
                          # already, and disproportionately short hyper-frequent function words
                          # like "pour"/"par"/"car" that also earn their own brief).


def carrierExclusionSet(records: list[WordRecord], n: int = TOP_WORDS_EXCLUDED) -> frozenset[str]:
    byOrtho: dict[str, float] = {}
    for r in records:
        byOrtho[r.ortho] = max(byOrtho.get(r.ortho, 0.0), r.frequency)
    topWords = set(sorted(byOrtho, key=lambda o: -byOrtho[o])[:n])
    monosyllabic = {r.ortho for r in records if len(r.base) == 1}
    return frozenset(topWords | monosyllabic)


BUILD_STATS: dict[str, int] = {"mergesProposed": 0, "mergesDropped": 0}   # last buildCandidates call


def _exceptionFreqOf(pos: str, carriers: list[Carrier]) -> float:
    """Absolute different-lemma collision frequency (`_exceptionShare` with denom 1)."""
    return _exceptionShare(pos, carriers, 1.0)[0]


def unionMerge(parts: list[Candidate]) -> Candidate:
    """The merged anchor `a|b|c` of k=1 candidates with one position and sound: carriers united (a word keeps its
    longest span), parts kept as `mergeParts`. Used by the greedy variant merges and by the merges the user decided."""
    first = parts[0]
    orthos = sorted(p.ortho for p in parts)
    merged = Candidate(first.position, 1, first.phono, "|".join(orthos), isSeed=any(p.isSeed for p in parts),
                       isGeneralized=True, variants=orthos, mergeParts=[_candKey(p) for p in parts])
    byIdx: dict[int, Carrier] = {}
    for p in parts:
        for x in p.carriers:
            old = byIdx.get(x.rec.idx)
            if old is None or x.span > old.span:
                byIdx[x.rec.idx] = x
    merged.carriers = list(byIdx.values())
    return merged


def buildVariantMerges(
    cands: dict[tuple[str, int, str, str], Candidate],
) -> dict[tuple[str, int, str, str], Candidate]:
    """U3a, pre-inheritance pass: fuse k=1 spelling variants -- same position and phono, different
    ortho (`ment`/`mant`, `té`/`ter`/`tée`) -- into one `a|b|c` merged node, but only while the
    fusion adds at most VARIANT_MAX_NEW_CONFLICT_SHARE of new different-lemma collisions. Parts
    are sorted by frequency; the largest starts a group and each next part joins if the test
    passes, the rest go to the next round. Parts are never consumed (they stay in `cands`).
    The post-inheritance check in `buildCandidates` is authoritative."""
    byPhono: dict[tuple[str, str], list[Candidate]] = {}
    for c in cands.values():
        if c.k == 1 and c.carriers and not c.isGeneralized:
            byPhono.setdefault((c.position, c.phono), []).append(c)
    merges: dict[tuple[str, int, str, str], Candidate] = {}
    for (pos, phono), parts in byPhono.items():
        if len(parts) < 2:
            continue
        partFreq = {id(p): sum(x.rec.frequency for x in p.carriers) for p in parts}
        partExc = {id(p): _exceptionFreqOf(pos, p.carriers) for p in parts}
        remaining = sorted(parts, key=lambda p: (-partFreq[id(p)], p.ortho))
        while len(remaining) >= 2:
            cur = [remaining[0]]
            carriers = list(remaining[0].carriers)
            freq = partFreq[id(remaining[0])]
            excSum = partExc[id(remaining[0])]
            left: list[Candidate] = []
            for p in remaining[1:]:
                trial = carriers + p.carriers
                trialFreq = freq + partFreq[id(p)]
                newConflict = _exceptionFreqOf(pos, trial) - (excSum + partExc[id(p)])
                if newConflict <= VARIANT_MAX_NEW_CONFLICT_SHARE * trialFreq:
                    cur.append(p)
                    carriers, freq, excSum = trial, trialFreq, excSum + partExc[id(p)]
                else:
                    left.append(p)
            if len(cur) >= 2:
                merged = unionMerge(cur)
                merges[_candKey(merged)] = merged
            remaining = left
    return merges


def buildCandidates(
    records: list[WordRecord],
    seedPairs: set[tuple[str, str]],
    seedsOnly: bool = False,
    excludeTopWords: bool = True,
    decisions: Decisions | None = None,
) -> dict[tuple[str, int, str, str], Candidate]:
    """The pool: the k=1 anchors (seeds, the curated A8 groups, the variant merges) and, for every anchor with a
    decided growth (`affix_decisions.json`), its decided forms. Nothing else is grown: no growth without a
    verdict. Lemma does not gate which words a pattern covers; it stays only for paradigm inheritance and the
    different-lemma collision definition."""
    # Productivity attestation (LemmaIndex lookups) uses every record -- excluding a word from being a
    # CARRIER doesn't mean its lemma shouldn't count when checking whether some OTHER word's stem is
    # independently attested. It only feeds the reported `attestedShare`.
    lemmas = LemmaIndex({r.lemme for r in records})
    if decisions is None:
        decisions = loadDecisions()
    # `excludeTopWords=False` is for small hand-built test fixtures, where "top 200 by frequency"
    # is meaningless (it would swallow every record) -- real callers always want the default.
    excluded = carrierExclusionSet(records) if excludeTopWords else frozenset()
    carrierRecords = [r for r in records if r.ortho not in excluded]
    inflectedByLemme: dict[str, list[WordRecord]] = {}
    for r in carrierRecords:
        if not r.isLemmaForm:
            inflectedByLemme.setdefault(r.lemme, []).append(r)

    cands: dict[tuple[str, int, str, str], Candidate] = {}

    def get(pos: str, k: int, phono: str, ortho: str) -> Candidate:
        key = (pos, k, phono, ortho)
        c = cands.get(key)
        if c is None:
            c = cands[key] = Candidate(pos, k, phono, ortho, isSeed=(pos, ortho) in seedPairs)
        return c

    for r in carrierRecords:
        n = len(r.base)
        if n < 2:
            continue
        # prefixes: every record
        oa = "".join(r.orthoSylls[:1])
        if not seedsOnly or (PREFIX, oa) in seedPairs:
            stem = r.ortho[len(oa):]
            if stem:
                get(PREFIX, 1, r.phonoSylls[0], oa).carriers.append(Carrier(r, 0, 1, stem))
        # suffixes: lemma forms only, inflected forms inherit afterwards (iter-participles
        # are the one exception, see isIterParticiple)
        if r.isLemmaForm or isIterParticiple(r):
            oa = "".join(r.orthoSylls[-1:])
            if not seedsOnly or (SUFFIX, oa) in seedPairs:
                stem = r.ortho[:-len(oa)]
                if stem:
                    get(SUFFIX, 1, r.phonoSylls[-1], oa).carriers.append(Carrier(r, n - 1, 1, stem))

    cands = poolKnownAffixGroups(cands)
    # after A8 (which consumes its members), so no merge part can vanish from the pool.
    merges = buildVariantMerges(cands)
    # merges the user decided that the greedy pass did not make (a chosen subset of the spellings of one sound):
    # built from their parts, and exempt from the conflict test below (the verdict is the user's)
    decidedMerges: set[tuple[str, int, str, str]] = set()
    for e in decisions.entries.values():
        key = (e.position, 1, e.phono, e.spellings)
        if e.verdict != FUSED or key in merges:
            continue
        parts = [cands.get((e.position, 1, e.phono, sp)) for sp in e.spellings.split("|")]
        if all(p is not None and p.carriers for p in parts):
            merges[key] = unionMerge([p for p in parts if p is not None])
            decidedMerges.add(key)
    cands.update(merges)

    def inheritAndStat(c: Candidate) -> None:
        if c.position == SUFFIX:
            inherited: dict[int, Carrier] = {}
            for x in c.carriers:
                for w in inflectedByLemme.get(x.rec.lemme, ()):
                    sp = inheritedSpan(x.rec, c.k, w)
                    if sp is None:
                        continue
                    old = inherited.get(w.idx)
                    if old is None or sp[1] > old.span:
                        inherited[w.idx] = Carrier(w, sp[0], sp[1], x.stem)
            c.carriers.extend(inherited.values())
        _finishStats(c)

    for c in cands.values():
        inheritAndStat(c)
    # U3a, authoritative post-inheritance conflict test: a merge stays only if fusing added at most
    # VARIANT_MAX_NEW_CONFLICT_SHARE x its frequency of new different-lemma collisions.
    dropped: set[tuple[str, int, str, str]] = set()
    for mkey, m in merges.items():
        partExc = sum(_exceptionFreqOf(m.position, cands[pk].carriers) for pk in m.mergeParts)
        m.newConflictFreq = _exceptionFreqOf(m.position, m.carriers) - partExc
        if m.newConflictFreq > VARIANT_MAX_NEW_CONFLICT_SHARE * m.freq and mkey not in decidedMerges:
            dropped.add(mkey)
    # (bare verb-ending candidates are deliberately not filtered -- 2026-09-27 user decision: they
    # compete on their real score in the selection)
    BUILD_STATS.update(mergesProposed=len(merges), mergesDropped=len(dropped))
    pool: dict[tuple[str, int, str, str], Candidate] = {}
    for key, c in cands.items():
        if key in dropped:
            continue
        if c.isSeed or (c.lemmas >= MIN_CARRIER_LEMMAS and c.stemRoots >= MIN_STEM_ROOTS):
            c.isAnchor = True
            c.hasDecision = decisions.growthForms(c.position, c.ortho, c.phono) is not None
            c.attestedShare = attestedShareOf(c.position, c.carriers, lemmas)
            pool[key] = c
    for c in list(pool.values()):
        if c.carriers and c.hasDecision:
            for cand in growScopedForms(c, decisions):
                key = _candKey(cand)
                assert key not in pool, f"decided form key overwritten: {key}"
                pool[key] = cand
    return pool


def _finishStats(c: Candidate) -> None:
    c.lemmas = len({x.rec.lemme for x in c.carriers})
    c.freq = sum(x.rec.frequency for x in c.carriers)
    top = sorted(c.carriers, key=lambda x: -x.rec.frequency)
    c.examples = list(dict.fromkeys(x.rec.ortho for x in top))[:6]
    # Competition is between different lemmas (bio+logie / bio+logique), so only lemma-form
    # carriers count: the inflections of one verb (chanter/chanté/chantant) are no competition.
    sf: dict[str, float] = {}
    for x in c.carriers:
        if x.rec.isLemmaForm:
            s = norm(x.stem)
            sf[s] = sf.get(s, 0.0) + x.rec.frequency
    c.stemFreq = sf
    c.stemRoots = len({norm(x.stem)[:STEM_ROOT_LETTERS] for x in c.carriers})


# ═══════════════════════════════════════════════════════════════════════════
# Families
# ═══════════════════════════════════════════════════════════════════════════















def poolCarriers(members: list[Candidate]) -> list[Carrier]:
    best: dict[int, Carrier] = {}
    for mi, m in enumerate(members):
        for c in m.carriers:
            old = best.get(c.rec.idx)
            if old is None or c.span > old.span:
                best[c.rec.idx] = c._replace(member=mi)
    return sorted(best.values(), key=lambda c: (-c.rec.frequency, c.rec.idx))










# ═══════════════════════════════════════════════════════════════════════════
# Gain simulation
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Binding:
    position: str
    kind: str                # MERGED or DEDICATED
    keys: tuple[int, ...]    # the merged keypress K, or the dedicated stroke D


@dataclass
class CarrierResult:
    carrier: Carrier
    gain: int = 0
    reason: str | None = None     # fallback reason when gain == 0
    newBase: Strokes | None = None
    markCost: int = 0
    boundaryRisk: bool = False
    partners: list[int] = field(default_factory=list)   # other members whose carriers share the new outline
    mergedSaving: bool = False    # True: saved = span (merged); False: saved = span - 1 (dedicated/standalone)


@functools.lru_cache(maxsize=None)
def markCostForCluster(m: int) -> int:
    """Extra strokes a reading pays when ranked last in a cluster of m spellings; the first
    mark merges into the last stroke for free."""
    if m <= 1:
        return 0
    return max(0, len(assignStarHashCombos(m)[m - 1]) - 1)


class SimContext:
    """Everything `simulate` needs: layout, the collision index over existing outlines."""

    def __init__(self, starboard: Starboard, records: list[WordRecord], partialOverlap: bool = True) -> None:
        self.starboard = starboard
        self.partialOverlap = partialOverlap   # decided mode: a RULE binding fails to merge only when ALL its
                                               # keys are already in the neighbouring stroke (False: ANY shared key)
        self.baseIndex: dict[Strokes, list[WordRecord]] = {}
        self.finalOutlines: set[Strokes] = set()
        for r in records:
            self.baseIndex.setdefault(r.base, []).append(r)
            self.finalOutlines.add(fullStrokesOf(r))
        self.singleStrokeOutlines = {o[0] for o in self.finalOutlines if len(o) == 1}
        self._partOf: dict[int, str] = {
            key: part for part, keys in starboard.keyIDinSyllabicPart.items() for key in keys}
        self._legal: dict[Stroke, bool] = {}

    def isLegal(self, keys: Stroke) -> bool:
        """Every bank's share of the chord is a legal keypress (getStrokeCost per bank)."""
        v = self._legal.get(keys)
        if v is None:
            v = self._legal[keys] = self.bankCost(keys) is not None
        return v

    def bankCost(self, keys: Stroke) -> int | None:
        total = 0
        for part in ("onset", "nucleus", "coda"):
            sub = tuple(sorted(k for k in set(keys) if self._partOf.get(k) == part))
            if not sub:
                continue
            c = self.starboard.getStrokeCost(sub, part)
            if c is None:
                return None
            total += c
        if any(k not in self._partOf for k in keys):
            return None
        return total


def ruleKeysOverlap(neighbour: Stroke, keys: Stroke, partialOverlap: bool = True) -> bool:
    """A RULE binding of `keys` cannot merge into `neighbour`: every key shared (`partialOverlap`, the decided
    mode), or any key shared. `affixrules._exceptionRateFloor` must use this too."""
    shared = set(neighbour) & set(keys)
    if partialOverlap:
        return len(shared) == len(set(keys))
    return bool(shared)


def _newBase(binding: Binding, c: Carrier, ctx: SimContext) -> tuple[Strokes | None, str | None, bool]:
    """Returns (newBase, fallback reason, mergedSaving) -- `mergedSaving` tells `simulate` whether
    this carrier's saving is `span` (merged) or `span - 1` (dedicated, or a RULE binding's
    physical-reason standalone fallback, §4.2)."""
    base = c.rec.base
    lo, hi = c.start, c.start + c.span
    if binding.kind == DEDICATED:
        if c.span < 2:
            return None, "noGain", False
        return base[:lo] + (tuple(sorted(binding.keys)),) + base[hi:], None, False
    ni = hi if binding.position == PREFIX else lo - 1
    mergeReason: str | None
    if ni < 0 or ni >= len(base):
        mergeReason = "noNeighbour"
    else:
        neighbour = base[ni]
        if (ruleKeysOverlap(neighbour, binding.keys, ctx.partialOverlap) if binding.kind == RULE
                else set(neighbour) & set(binding.keys)):
            mergeReason = "keyOverlap"
        else:
            union = tuple(sorted(set(neighbour) | set(binding.keys)))
            if not ctx.isLegal(union):
                mergeReason = "illegalChord"
            else:
                newBase = (base[:lo] + base[hi:ni] + (union,) + base[ni + 1:] if binding.position == PREFIX
                           else base[:ni] + (union,) + base[hi:])
                return newBase, None, True
    if binding.kind != RULE or mergeReason not in ("keyOverlap", "illegalChord"):
        return None, mergeReason, False
    # RULE (§4.2): a physical-reason merge failure falls back to a standalone stroke -- never a
    # word exception, since the writer can feel the chord is impossible.
    D = tuple(sorted(binding.keys))
    if c.span == 1 or D in ctx.singleStrokeOutlines:
        return None, "standaloneTrap", False
    return base[:lo] + (D,) + base[hi:], None, False


def hasBoundaryRisk(full: Strokes, outlines: set[Strokes]) -> bool:
    """`full` can be split into >= 2 consecutive existing outlines."""
    n = len(full)
    reach = [False] * (n + 1)
    reach[0] = True
    for j in range(1, n + 1):
        for i in range(j):
            if reach[i] and not (i == 0 and j == n) and full[i:j] in outlines:
                reach[j] = True
                break
    return reach[n]


def simulate(groups: list[tuple[Binding, list[Carrier]]], ctx: SimContext,
             boundaryRisk: bool = True) -> list[list[CarrierResult]]:
    """Gain of each carrier under its group's binding, all groups considered together so that
    cross-group collisions cost marks. A carrier with no positive gain falls back to its full
    outline (never longer). `boundaryRisk=False` skips the (report-only) `hasBoundaryRisk` flag,
    which never feeds gain, reason or score."""
    results = [[CarrierResult(c) for c in carriers] for _b, carriers in groups]
    pending: dict[Strokes, dict[str, list[CarrierResult]]] = {}
    for (binding, _), res in zip(groups, results):
        for r in res:
            nb, why, mergedSaving = _newBase(binding, r.carrier, ctx)
            if nb is None:
                r.reason = why
                continue
            r.newBase = nb
            r.mergedSaving = mergedSaving
            pending.setdefault(nb, {}).setdefault(r.carrier.rec.ortho, []).append(r)
    for (binding, _), res in zip(groups, results):
        for r in res:
            if r.newBase is None:
                continue
            w = r.carrier.rec
            spellings = {w.ortho}
            lost = False
            for other in ctx.baseIndex.get(r.newBase, ()):
                if other.ortho == w.ortho:
                    continue
                if other.lemme == w.lemme:
                    if other.base != w.base:
                        lost = True
                    continue
                spellings.add(other.ortho)
            for ortho, rs in pending.get(r.newBase, {}).items():
                if ortho == w.ortho:
                    continue
                o = rs[0].carrier.rec
                if o.base != w.base:
                    r.partners.extend(x.carrier.member for x in rs if x.carrier.member != r.carrier.member)
                if o.lemme == w.lemme:
                    if o.base != w.base:
                        lost = True
                    continue
                spellings.add(ortho)
            if lost:
                r.reason, r.newBase = "lostDistinction", None
                continue
            # only the marks beyond those the word's own (old) homophone cluster already pays
            oldSpellings = {o.ortho for o in ctx.baseIndex.get(w.base, ())} | {w.ortho}
            r.markCost = max(0, markCostForCluster(len(spellings)) - markCostForCluster(len(oldSpellings)))
            saved = r.carrier.span if r.mergedSaving else r.carrier.span - 1
            r.gain = saved - r.markCost
            if r.gain <= 0:
                r.gain, r.reason, r.newBase = 0, "markCostTooHigh", None
                continue
            if boundaryRisk:
                full = withMarks(r.newBase, w.markKeys) + w.extra
                r.boundaryRisk = hasBoundaryRisk(full, ctx.finalOutlines)
    return results







# ═══════════════════════════════════════════════════════════════════════════
# Lean single-RULE-group simulation (the per-key sweep of `affixrules.chooseRuleKeypress`)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(slots=True)
class SimUnit:
    """The key-independent data of one carrier under a RULE binding at `position`. `simulateRuleUnits`
    MUST mirror `simulate`/`_newBase` for one RULE group (the differential test pins them together):
    only the per-key part (the new outline tuple, the collision buckets) is rebuilt for each key."""
    carrier: Carrier
    ortho: str
    lemme: str
    base: Strokes
    freq: float
    span: int
    single: bool
    g: int                  # neighbour id (-1: no neighbour)
    pre: Strokes            # merged outline = pre + (union,) + post
    post: Strokes
    preS: Strokes           # standalone outline = preS + (D,) + postS
    postS: Strokes
    mcOld: int              # mark cost of the carrier's own old homophone cluster


def makeSimUnit(position: str, c: Carrier, ctx: SimContext, neighbourIds: dict[Stroke, int]) -> SimUnit:
    w = c.rec
    base = w.base
    lo, hi = c.start, c.start + c.span
    ni = hi if position == PREFIX else lo - 1
    g = -1
    pre: Strokes = ()
    post: Strokes = ()
    if 0 <= ni < len(base):
        nbStroke = base[ni]
        g = neighbourIds.setdefault(nbStroke, len(neighbourIds))
        if position == PREFIX:
            pre, post = base[:lo], base[ni + 1:]
        else:
            pre, post = base[:ni], base[hi:]
    mcOld = markCostForCluster(len({o.ortho for o in ctx.baseIndex.get(base, ())} | {w.ortho}))
    return SimUnit(c, w.ortho, w.lemme, base, w.frequency, c.span, c.span == 1, g,
                   pre, post, base[:lo], base[hi:], mcOld)


def mergeUnions(neighbours: list[Stroke], k: Stroke, ctx: SimContext) -> list[Stroke | None]:
    """Per neighbour stroke, the merged chord of `k` into it, or None when `_newBase` would find a
    keyOverlap or an illegalChord."""
    out: list[Stroke | None] = []
    for n in neighbours:
        if ruleKeysOverlap(n, k, ctx.partialOverlap):
            out.append(None)
            continue
        union = tuple(sorted(set(n) | set(k)))
        out.append(union if ctx.isLegal(union) else None)
    return out


def simulateRuleUnits(units: list[SimUnit], ctx: SimContext, X: list[Stroke | None], D: Stroke,
                      trap: bool) -> tuple[list[int], list[str | None]]:
    """Gain and fallback reason of each unit under one RULE binding: `simulate`'s semantics for a
    single group, minus partners / newBase / markCost / boundaryRisk."""
    n = len(units)
    nbs: list[Strokes | None] = [None] * n
    saved = [0] * n
    reasons: list[str | None] = [None] * n
    buckets: list[dict[str, list[SimUnit]] | None] = [None] * n
    pending: dict[Strokes, dict[str, list[SimUnit]]] = {}
    for i, u in enumerate(units):
        if u.g < 0:
            reasons[i] = "noNeighbour"
            continue
        x = X[u.g]
        if x is not None:
            nb = u.pre + (x,) + u.post
            s = u.span
        elif u.single or trap:
            reasons[i] = "standaloneTrap"
            continue
        else:
            nb = u.preS + (D,) + u.postS
            s = u.span - 1
        bucket = pending.get(nb)
        if bucket is None:
            bucket = pending[nb] = {}
        bucket.setdefault(u.ortho, []).append(u)
        nbs[i] = nb
        saved[i] = s
        buckets[i] = bucket
    gains = [0] * n
    baseIndex = ctx.baseIndex
    for i, u in enumerate(units):
        b = nbs[i]
        if b is None:
            continue
        pe = buckets[i]
        assert pe is not None
        existing = baseIndex.get(b)
        if existing is None and len(pe) == 1:
            gains[i] = saved[i]
            continue
        spellings = {u.ortho}
        lost = False
        for o in existing or ():
            if o.ortho == u.ortho:
                continue
            if o.lemme == u.lemme:
                if o.base != u.base:
                    lost = True
                continue
            spellings.add(o.ortho)
        for ortho, rs in pe.items():
            if ortho == u.ortho:
                continue
            first = rs[0]
            if first.lemme == u.lemme:
                if first.base != u.base:
                    lost = True
                continue
            spellings.add(ortho)
        if lost:
            reasons[i] = "lostDistinction"
            continue
        gain = saved[i] - max(0, markCostForCluster(len(spellings)) - u.mcOld)
        if gain <= 0:
            reasons[i] = "markCostTooHigh"
            continue
        gains[i] = gain
    return gains, reasons
