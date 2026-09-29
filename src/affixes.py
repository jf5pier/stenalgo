"""
Affix Abbreviation Discovery (Part A) and the shared gain simulation (Part B reuses it).

MEASUREMENT AND PROPOSALS ONLY -- nothing here is wired into the theory. See
PLAN_2026-09-26-affix-abbreviations.md for the design decisions this module implements.

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

import numpy as np

from src.ambiguitychecker import assignStarHashCombos, buildWordToStrokes
from src.keyboard import Starboard, Stroke, Strokes, canonicalizeStrokes
from src.word import Word

MAX_AFFIX_SYLL = 3
MIN_STEM_LETTERS = 3
MIN_CARRIER_LEMMAS = 5
MIN_CANDIDATE_FREQ = 20.0  # summed Word.frequency of morphological carriers
MEMBER_MIN_SHARE = 0.05    # a member needs this share of the family's top member's lemma count
MIN_STEM_ROOTS = 5         # distinct 4-letter stem roots (rai|sonner, rai|son count once)
STEM_ROOT_LETTERS = 4
FAMILY_LINK_SIM = 0.6
MAX_FAMILY_MEMBERS = 12
MIN_FAMILY_STROKEFREQ = 30.0
MAX_FAMILY_CANDIDATES = 1500  # per position, by freq x k; keeps the O(n^2) similarity tractable
MAX_STEMS_FOR_JACCARD = 300
NESTED_SIM = 0.8              # one affix spelled and sounded inside another (-ité / -bilité)
NESTED_MAX_EXTRA_LETTERS = 3
LEGACY_GROWTH_MAX_DEPTH = 3   # --legacy only: A9 extra syllables absorbed beyond a base candidate's own k
LEGACY_GROWTH_MAX_EXCEPTION_SHARE = 0.02  # --legacy only; mirrors affixbinding.SPLIT_MAX_LOSS
GROWTH_MAX_SLOT_VALUES = 8    # --legacy only: a wildcard this wide is its own unlearnable rule
# --legacy only (DESIGN_2026-09-27-affix-rule-selection.md D1: only 20-30 rules ship in the new
# path, so the 300-family sanity ceiling these existed to enforce no longer applies there).
GROWTH_MIN_CARRIER_LEMMAS = 7 * MIN_CARRIER_LEMMAS
GROWTH_MIN_STEM_ROOTS = 7 * MIN_STEM_ROOTS
GROWTH_MIN_CANDIDATE_FREQ = 7 * MIN_CANDIDATE_FREQ

# New lattice-growth path (DESIGN_2026-09-27-affix-rule-selection.md §3, §8), relaxed by
# PLAN_2026-09-28-affix-single-generator-rewrite.md U5: pure pruning thresholds are low, measured
# bounds; learnability lives in the rule score (affixrules.py), not in generation-time gates.
GROWTH_MAX_DEPTH = 4          # extra syllables absorbed beyond a k=1 anchor (k up to 5)
GROWTH_MAX_EXCEPTION_SHARE = 0.05  # aligned with affixrules.MAX_EXCEPTION_RATE; collisions this lets
                                   # through become word exceptions and are scored
MAX_SLOT_EXCLUSIONS = 3
GROWTH_MIN_EXPAND = 5.0       # a child is expanded again iff its subtree bound (sum f x syllables
                              # still absorbable) reaches this -- measured, see the plan §3 step 2
VARIANT_MAX_NEW_CONFLICT_SHARE = 0.02  # U3a: fusing spelling variants may add at most this share of
                                       # the merged frequency as new different-lemma collisions
MAX_POOL = 200000   # raised one order of magnitude from the design's 20000 default (2026-09-27):
                    # on the real lexicon the pool saturates at ~2,199 candidates by 200000 and is
                    # byte-identical at 2,000,000 and 20,000,000 (PYTHONHASHSEED=0 controlled
                    # comparison) -- the natural growth bound is GROWTH_MAX_DEPTH/the marginal and
                    # lemma/stemRoot thresholds, not this cap, so raising it further changes nothing.

PREFIX = "prefix"
SUFFIX = "suffix"
MERGED = "merged"
DEDICATED = "dedicated"
RULE = "rule"    # Phase 2 (DESIGN §4.2): merged when clash-free, else a physical-reason standalone
                 # fallback -- collisions still cost the word its abbreviation, never a shorter one.

VOWEL_CLASSES = ("eE@°29", "oO", "a", "i", "y8", "u", "§", "51")
PHONEME_CLASS = {p: i for i, cls in enumerate(VOWEL_CLASSES) for p in cls}


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
VERB_FRAGMENT_GRAMCAT_SHARE = 0.9  # 2026-09-27 (user request): a SUFFIX candidate this dominated
                                    # by verb carriers, with no meaningful noun/adj attestation, is
                                    # just the shared tail of many unrelated regular verb
                                    # infinitives (ter/der/ver/ler/ner/ser/ger...), not a real
                                    # derivational suffix -- drop it, seeds excepted.


def isVerbEndingFragment(c: Candidate) -> bool:
    if c.position != SUFFIX or c.isSeed or not c.carriers:
        return False
    freq = sum(x.rec.frequency for x in c.carriers) or 1.0
    verbFreq = sum(x.rec.frequency for x in c.carriers if x.rec.gramCat == VERB_GRAMCAT)
    return verbFreq / freq >= VERB_FRAGMENT_GRAMCAT_SHARE


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


def _onsetRest(syll: str) -> tuple[str, str]:
    """(onset consonants, nucleus+coda) of one syllable string -- the onset is every character
    before the first nucleus-vowel phoneme."""
    i = 0
    while i < len(syll) and syll[i] not in PHONEME_CLASS:
        i += 1
    return syll[:i], syll[i:]


@dataclass(frozen=True)
class Slot:
    """One absorbed syllable of a lattice node (§3.1): a fixed value, a group sharing a fixed
    nucleus+coda but varying onset, or a full wildcard -- each may exclude a short list of
    attested values that would otherwise cause too many collisions (D3, D6)."""
    kind: str                        # "exact" | "onset" | "any"
    value: str = ""                  # exact: the syllable phono; onset: the nucleus+coda ("rest")
    excluded: tuple[str, ...] = ()   # onset: excluded onset consonants; any: excluded syllable phonos


def slotMatchesSyllable(slot: Slot, phono: str) -> bool:
    if slot.kind == "exact":
        return phono == slot.value
    if slot.kind == "onset":
        onset, rest = _onsetRest(phono)
        return rest == slot.value and onset not in slot.excluded
    if slot.kind == "any":
        return phono not in slot.excluded
    raise ValueError(f"unknown slot kind {slot.kind!r}")


def slotLabel(slot: Slot) -> str:
    """A phono-space label, unique per distinct pattern (§9 pitfall): exclusions are folded in."""
    excl = "-{" + ",".join(slot.excluded) + "}" if slot.excluded else ""
    if slot.kind == "exact":
        return slot.value
    if slot.kind == "onset":
        return f"[C{excl}]{slot.value}"
    return f"*{excl}"


def poolTailVariants(
    cands: dict[tuple[str, int, str, str], Candidate],
    keepOriginals: bool = False,
) -> dict[tuple[str, int, str, str], Candidate]:
    """Generalized-affix pooling (A7), run before the Part-A thresholds.

    Candidates of the same position and k (>= 2) whose syllable nearest the stem differs only in
    its onset consonant -- same nucleus+coda, same tail of k-1 syllables beyond it (`bi`/`ti`/
    `ci`/.../`li.te`) -- are the same suffix/prefix spelled after different stem-final consonants,
    not different affixes. Pooling them before MIN_CARRIER_LEMMAS/MIN_STEM_ROOTS/
    MIN_CANDIDATE_FREQ apply lets rare spelling variants (`tilité`, `cilité`, ...) clear the
    thresholds together instead of each alone (see the consonant+ilité investigation,
    scratch/cilite-investigation-report.md).

    `keepOriginals` (default off, on for the non-legacy path -- DESIGN §3.5) keeps the pooled-away
    originals alongside the merged candidate instead of deleting them: each still faces the
    ordinary thresholds on its own, so an exact single-onset candidate like `li.te` can survive
    and be grown further by the lattice, instead of only ever existing pre-absorbed into the
    pooled wildcard. Off by default to keep `--legacy` byte-identical to before this change.

    k == 1 candidates are included (2026-09-27, user request: "ter"/"der"/"ver"/... are the same
    onset-varying shape A7 already pools, just with no tail syllable). At k == 1 the grouping key
    is phono-only (no tail beyond the single varying syllable to disambiguate with), which is
    unsafe on its own: a silent trailing letter can make two DIFFERENT spellings share one phono
    (`té` and `ter` both have phono `te`, the infinitive's final `r` being silent) while meaning
    completely different things (a noun/participle ending vs. a verb-infinitive ending). See
    `_splitByOrthoTail`.

    k == 1 is scoped to verb-ending fragments only (`isVerbEndingFragment`), not every k == 1
    candidate: a first pass with no such gate also pooled every other k == 1 family in the
    lexicon (`-able`, `-iste`, `-age`, ...) -- a much bigger, unevaluated change nobody asked for.
    Real k == 1 suffixes/prefixes stay exactly as unpooled as before this change."""
    groups: dict[tuple[str, int, str, str], list[tuple[tuple[str, int, str, str], Candidate]]] = {}
    for key, c in cands.items():
        if c.k < 1 or not c.carriers or (c.k == 1 and not isVerbEndingFragment(c)):
            continue
        syls = c.phono.split(".")
        varSyll, tailSyls = (syls[0], syls[1:]) if c.position == SUFFIX else (syls[-1], syls[:-1])
        _onset, rest = _onsetRest(varSyll)
        if not rest:
            continue
        groups.setdefault((c.position, c.k, ".".join(tailSyls), rest), []).append((key, c))

    pooled = dict(cands)
    for (pos, k, tailPhono, rest), bucket in groups.items():
        for members in (_splitByOrthoTail(bucket) if k == 1 else [bucket]):
            if len(members) < 2:
                continue
            _keys, cs = zip(*members)
            variants = sorted({c.ortho for c in cs})
            if k == 1:
                # No tail syllable to anchor the label on -- use the spelling every member of
                # this (already ortho-split) group actually shares instead of the bare phono
                # `rest`, so a silent letter (the verb infinitive's "-er") shows up in the label.
                tailOrtho = ""
                orthoRest = _commonSuffix([c.ortho for c in cs])
            else:
                sample = max(cs, key=lambda c: c.freq).carriers[0].rec
                tailOrtho = "".join(sample.orthoSylls[-(k - 1):] if pos == SUFFIX else sample.orthoSylls[:k - 1])
                orthoRest = rest
            # `rest` (the nucleus+coda shared by every onset variant) makes both the phono and the
            # ortho label unique per group -- two groups can share the same tail with a different
            # rest (-ilité vs -alité), and a phono lacking `rest` would collide them under one key.
            ortho = ("·" + orthoRest + tailOrtho) if pos == SUFFIX else (tailOrtho + orthoRest + "·")
            phono = (f"{rest}.{tailPhono}" if tailPhono else rest) if pos == SUFFIX \
                else (f"{tailPhono}.{rest}" if tailPhono else rest)
            merged = Candidate(pos, k, phono, ortho, isSeed=any(c.isSeed for c in cs),
                                isGeneralized=True, variants=variants)
            merged.carriers = [carrier for c in cs for carrier in c.carriers]
            if not keepOriginals:
                for key in _keys:
                    del pooled[key]
            pooled[(pos, k, phono, ortho)] = merged
    return pooled


def _commonSuffixLen(a: str, b: str) -> int:
    n = 0
    for ca, cb in zip(reversed(a), reversed(b)):
        if ca != cb:
            break
        n += 1
    return n


def _commonSuffix(orthos: list[str]) -> str:
    s = orthos[0]
    for other in orthos[1:]:
        n = _commonSuffixLen(s, other)
        s = s[len(s) - n:]
    return s


def _splitByOrthoTail(
    members: list[tuple[tuple[str, int, str, str], Candidate]], minShared: int = 1,
) -> list[list[tuple[tuple[str, int, str, str], Candidate]]]:
    """A k == 1 phono-rest bucket's safety net (see `poolTailVariants`): split it into
    ortho-compatible sub-clusters -- union-find on "shares at least `minShared` trailing letters"
    -- so a spelling-distinct member (`té`) never gets pooled with same-sounding-but-differently-
    -spelled ones (`ter`/`der`/`ver`/...) just because a silent letter makes their phono match."""
    n = len(members)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    orthos = [c.ortho for _key, c in members]
    for i in range(n):
        for j in range(i + 1, n):
            if _commonSuffixLen(orthos[i], orthos[j]) >= minShared:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj

    byRoot: dict[int, list[tuple[tuple[str, int, str, str], Candidate]]] = {}
    for i, m in enumerate(members):
        byRoot.setdefault(find(i), []).append(m)
    return list(byRoot.values())


# Latin prefix assimilation groups, citation-backed (not auto-discovered by A7 or A3's
# clustering -- see PLAN_2026-09-26-affix-abbreviations.md §11 for the etymological research).
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


def _growOneLevel(pos: str, base: Candidate) -> list[Candidate]:
    """One breadth-first growth level from `base`: absorb the next syllable, then generalize
    (A9) by greedily merging sibling per-value groups while the resulting exception share stays
    under `LEGACY_GROWTH_MAX_EXCEPTION_SHARE`."""
    grown: dict[int, Carrier] = {}     # rec.idx -> grown carrier
    absorbedPhono: dict[int, str] = {}
    absorbedOrtho: dict[int, str] = {}
    for c in base.carriers:
        grownTriple = _growCarrier(pos, c)
        if grownTriple is None:
            continue
        gc, phono, ortho = grownTriple
        grown[gc.rec.idx] = gc
        absorbedPhono[gc.rec.idx] = phono
        absorbedOrtho[gc.rec.idx] = ortho
    if len(grown) < GROWTH_MIN_CARRIER_LEMMAS:
        return []

    leaves: dict[str, list[int]] = {}
    for idx, phono in absorbedPhono.items():
        leaves.setdefault(phono, []).append(idx)
    # Fixed denominator (Decision, 2026-09-27): a merge's exception cost is judged against the
    # whole base candidate's frequency, not the merged subset's -- otherwise a big group dilutes
    # the ratio to nothing and a greedy sequence swallows everything.
    baseFreq = sum(c.rec.frequency for c in grown.values()) or 1.0

    # Incremental agglomeration: recompute a pair's score only when one of its two groups just
    # changed, instead of the whole O(g^2) matrix every iteration (that made this O(g^3) and
    # dominated Part A's runtime on large families like -ment).
    ids = list(leaves)
    groupOf: dict[str, list[Carrier]] = {gid: [grown[idx] for idx in leaves[gid]] for gid in ids}
    membersOf: dict[str, list[str]] = {gid: [gid] for gid in ids}
    pairScore: dict[tuple[str, str], float] = {}
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            share, _ = _exceptionShare(pos, groupOf[a] + groupOf[b], baseFreq)
            pairScore[(a, b)] = share

    while len(ids) > 1:
        candidates = [(k, v) for k, v in pairScore.items()
                      if len(membersOf[k[0]]) + len(membersOf[k[1]]) <= GROWTH_MAX_SLOT_VALUES]
        best = min(candidates, key=lambda kv: kv[1]) if candidates else None
        if best is None or best[1] > LEGACY_GROWTH_MAX_EXCEPTION_SHARE:
            break
        (a, b), _ = best
        groupOf[a] = groupOf[a] + groupOf[b]
        membersOf[a] = membersOf[a] + membersOf[b]
        del groupOf[b]
        del membersOf[b]
        ids.remove(b)
        for k, v in list(pairScore.items()):
            if a in k or b in k:
                del pairScore[k]
        for other in ids:
            if other == a:
                continue
            key = (a, other) if a < other else (other, a)
            share, _ = _exceptionShare(pos, groupOf[a] + groupOf[other], baseFreq)
            pairScore[key] = share

    results: list[Candidate] = []
    for gid in ids:
        groupKeys = membersOf[gid]
        carriers = groupOf[gid]
        share, excluded = _exceptionShare(pos, carriers)
        kept = [c for c in carriers if c.rec.idx not in excluded]
        if not kept:
            continue
        phonoVals = sorted(set(groupKeys))
        orthoVals = sorted({absorbedOrtho[idx] for key in groupKeys for idx in leaves[key]})
        sample = max(kept, key=lambda c: c.rec.frequency).rec
        tailOrtho = "".join(sample.orthoSylls[-base.k:] if pos == SUFFIX else sample.orthoSylls[:base.k])
        slot = phonoVals[0] if len(phonoVals) == 1 else "[" + "|".join(phonoVals) + "]"
        orthoSlot = orthoVals[0] if len(orthoVals) == 1 else "[" + "|".join(orthoVals) + "]"
        if pos == SUFFIX:
            phono, ortho = f"{slot}.{base.phono}", f"·{orthoSlot}{tailOrtho}"
        else:
            phono, ortho = f"{base.phono}.{slot}", f"{tailOrtho}{orthoSlot}·"
        cand = Candidate(pos, base.k + 1, phono, ortho, carriers=kept, isGeneralized=True,
                          variants=orthoVals, grownDepth=base.grownDepth + 1,
                          exceptionCount=len(excluded), exceptionFreq=sum(
                              c.rec.frequency for c in carriers if c.rec.idx in excluded),
                          grownFromKey=(base.position, base.k, base.phono, base.ortho))
        _finishStats(cand)
        if (cand.lemmas >= GROWTH_MIN_CARRIER_LEMMAS and cand.stemRoots >= GROWTH_MIN_STEM_ROOTS
                and cand.freq >= GROWTH_MIN_CANDIDATE_FREQ):
            results.append(cand)
    return results


def growAffixes(cands: dict[tuple[str, int, str, str], Candidate]) -> dict[tuple[str, int, str, str], Candidate]:
    """A9: breadth-first, try growing every kept candidate one more syllable at a time (up to
    `LEGACY_GROWTH_MAX_DEPTH`), generalizing over whatever is found there. All depth-d results across
    every base are computed and thresholded before any depth-(d+1) growth is attempted -- a
    candidate that fails its threshold is a dead end, since deeper growth only ever loses
    carriers (see PLAN §13)."""
    grown = dict(cands)
    frontier = [c for c in cands.values() if c.carriers]
    for _ in range(LEGACY_GROWTH_MAX_DEPTH):
        nextFrontier: list[Candidate] = []
        for base in frontier:
            for cand in _growOneLevel(base.position, base):
                key = (cand.position, cand.k, cand.phono, cand.ortho)
                if key in grown:
                    continue
                grown[key] = cand
                nextFrontier.append(cand)
        if not nextFrontier:
            break
        frontier = nextFrontier
    return grown


# ═══════════════════════════════════════════════════════════════════════════
# Lattice growth (DESIGN_2026-09-27-affix-rule-selection.md §3): the default path. Replaces the
# single greedy agglomeration above (kept, unchanged, for --legacy) with a lattice where growing
# one syllable emits ALL of an exact leaf per absorbed value, an onset-generalized group per
# shared nucleus+coda, and one full wildcard -- nothing here absorbs anything else (D2, D3).
# Phase 2 (rule construction) and Phase 3/4 (selection, binding) are NOT implemented yet: this
# only builds and returns the pool of pattern nodes.
# ═══════════════════════════════════════════════════════════════════════════

class GrowthChild(NamedTuple):
    cand: Candidate
    emit: bool     # clears the ordinary thresholds on its own (§3.3)
    expand: bool    # its subtree bound justifies growing it again, emitted or not (§3.3)


def _stemSyllablesLeft(pos: str, c: Carrier) -> int:
    """Syllables before the affix span (suffix) or after it (prefix) -- what `_growCarrier`
    still has left to absorb toward the stem, before it must keep at least one."""
    return c.start if pos == SUFFIX else len(c.rec.base) - c.span


def _reduceExceptions(
    pos: str, valueGroups: dict[str, list[Carrier]], denom: float,
) -> tuple[dict[str, list[Carrier]], tuple[str, ...], set[int]] | None:
    """Greedily drop the attested value contributing most to collisions (§3.2) until the
    remaining group's exception share clears `GROWTH_MAX_EXCEPTION_SHARE`, or give up (None)
    once more than `MAX_SLOT_EXCLUSIONS` values would need to go."""
    remaining = dict(valueGroups)
    excluded: list[str] = []
    while True:
        carriers = [c for cs in remaining.values() for c in cs]
        if not carriers:
            return None
        share, excSet = _exceptionShare(pos, carriers, denom)
        if share <= GROWTH_MAX_EXCEPTION_SHARE:
            return remaining, tuple(sorted(excluded)), excSet
        contribution = {v: sum(c.rec.frequency for c in cs if c.rec.idx in excSet)
                        for v, cs in remaining.items()}
        worst = max(contribution, key=lambda v: contribution[v])
        if contribution[worst] <= 0 or len(remaining) <= 1:
            return None
        del remaining[worst]
        excluded.append(worst)
        if len(excluded) > MAX_SLOT_EXCLUSIONS:
            return None


def _buildGrownCandidate(
    pos: str, parent: Candidate, slot: Slot, kept: list[Carrier],
    exceptionFreq: float, exceptionCount: int, absorbedOrtho: dict[int, str],
) -> Candidate:
    orthoVals = sorted({absorbedOrtho[c.rec.idx] for c in kept})
    label = slotLabel(slot)
    orthoLabel = orthoVals[0] if slot.kind == "exact" else "[" + "|".join(orthoVals) + "]" + (
        "-{" + ",".join(slot.excluded) + "}" if slot.excluded else "")
    sample = max(kept, key=lambda c: c.rec.frequency).rec
    tailOrtho = "".join(sample.orthoSylls[-parent.k:] if pos == SUFFIX else sample.orthoSylls[:parent.k])
    if pos == SUFFIX:
        phono, ortho = f"{label}.{parent.phono}", f"·{orthoLabel}{tailOrtho}"
    else:
        phono, ortho = f"{parent.phono}.{label}", f"{tailOrtho}{orthoLabel}·"
    cand = Candidate(
        pos, parent.k + 1, phono, ortho, carriers=kept, isGeneralized=True, variants=orthoVals,
        grownDepth=parent.grownDepth + 1, exceptionCount=exceptionCount, exceptionFreq=exceptionFreq,
        grownFromKey=(parent.position, parent.k, parent.phono, parent.ortho),
        rootKey=parent.rootKey or (parent.position, parent.k, parent.phono, parent.ortho),
        slots=parent.slots + (slot,))
    _finishStats(cand)
    return cand


def _growLatticeLevel(pos: str, parent: Candidate, lemmas: LemmaIndex | None = None) -> list[GrowthChild]:
    """One lattice growth level from `parent`: absorb the next syllable, then emit the exact
    leaf, onset group and any-group children (§3.2) -- none consumes another."""
    grown: dict[int, Carrier] = {}
    absorbedPhono: dict[int, str] = {}
    absorbedOrtho: dict[int, str] = {}
    for c in parent.carriers:
        g = _growCarrier(pos, c)
        if g is None:
            continue
        gc, phono, ortho = g
        grown[gc.rec.idx] = gc
        absorbedPhono[gc.rec.idx] = phono
        absorbedOrtho[gc.rec.idx] = ortho
    if not grown:
        return []
    denom = sum(c.rec.frequency for c in grown.values())
    if denom <= 0:
        return []

    byPhono: dict[str, list[Carrier]] = {}
    for idx, gc in grown.items():
        byPhono.setdefault(absorbedPhono[idx], []).append(gc)

    children: list[GrowthChild] = []

    def finalize(slot: Slot, groupCarriers: list[Carrier], excSet: set[int]) -> GrowthChild | None:
        kept = [c for c in groupCarriers if c.rec.idx not in excSet]
        if not kept:
            return None
        exceptionFreq = sum(c.rec.frequency for c in groupCarriers if c.rec.idx in excSet)
        cand = _buildGrownCandidate(pos, parent, slot, kept, exceptionFreq, len(excSet), absorbedOrtho)
        emit = cand.lemmas >= MIN_CARRIER_LEMMAS and cand.stemRoots >= MIN_STEM_ROOTS
        if emit and lemmas is not None:
            cand.attestedShare = attestedShareOf(pos, kept, lemmas)
        ub = sum(c.rec.frequency * min(GROWTH_MAX_DEPTH - cand.grownDepth, _stemSyllablesLeft(pos, c) - 1)
                 for c in kept)
        return GrowthChild(cand, emit, ub >= GROWTH_MIN_EXPAND)

    # 1. exact leaves: one per distinct absorbed syllable phono.
    for phono, carriers in byPhono.items():
        share, excSet = _exceptionShare(pos, carriers, denom)
        if share > GROWTH_MAX_EXCEPTION_SHARE:
            continue
        child = finalize(Slot("exact", phono), carriers, excSet)
        if child is not None:
            children.append(child)

    # 2. onset groups: same nucleus+coda ("rest"), at least 2 distinct onsets.
    byRest: dict[str, dict[str, list[Carrier]]] = {}
    for phono, carriers in byPhono.items():
        onset, rest = _onsetRest(phono)
        byRest.setdefault(rest, {})[onset] = carriers
    for rest, onsetGroups in byRest.items():
        if len(onsetGroups) < 2:
            continue
        reduced = _reduceExceptions(pos, onsetGroups, denom)
        if reduced is None:
            continue
        remaining, excludedOnsets, excSet = reduced
        carriers = [c for cs in remaining.values() for c in cs]
        child = finalize(Slot("onset", rest, excludedOnsets), carriers, excSet)
        if child is not None:
            children.append(child)

    # 3. any group: every absorbed syllable value at this level, together.
    if len(byPhono) >= 2:
        reduced = _reduceExceptions(pos, byPhono, denom)
        if reduced is not None:
            remaining, excludedVals, excSet = reduced
            carriers = [c for cs in remaining.values() for c in cs]
            child = finalize(Slot("any", "", excludedVals), carriers, excSet)
            if child is not None:
                children.append(child)

    return children


def _patternComplexity(c: Candidate) -> tuple[int, tuple[int, ...], int]:
    """Sort key for dedupe (§3.4): fewer slots, then exact before onset before any, then fewer
    total exclusions -- lower is simpler."""
    order = {"exact": 0, "onset": 1, "any": 2}
    return (len(c.slots), tuple(order[s.kind] for s in c.slots), sum(len(s.excluded) for s in c.slots))


def _carrierSetKey(pos: str, carriers: list[Carrier]) -> tuple[str, frozenset[tuple[int, int, int]]]:
    return (pos, frozenset((c.rec.idx, c.start, c.span) for c in carriers))


def _dedupeByCarrierSet(cands: list[Candidate]) -> list[Candidate]:
    """§3.4: nodes with identical carriers+spans keep the simplest pattern; the rest are recorded
    as aliases on the survivor."""
    byKey: dict[tuple[str, frozenset[tuple[int, int, int]]], Candidate] = {}
    for cand in cands:
        key = _carrierSetKey(cand.position, cand.carriers)
        existing = byKey.get(key)
        if existing is None:
            byKey[key] = cand
        elif _patternComplexity(cand) < _patternComplexity(existing):
            cand.aliases = existing.aliases + [(existing.position, existing.k, existing.phono, existing.ortho)]
            _foldParents(cand, existing)
            byKey[key] = cand
        else:
            existing.aliases.append((cand.position, cand.k, cand.phono, cand.ortho))
            _foldParents(existing, cand)
    return list(byKey.values())


def _foldParents(survivor: Candidate, dropped: Candidate) -> None:
    """The dropped duplicate's parents (grownFromKey + alsoFrom) become parents of the survivor,
    so every anchor whose subtree held one of the two still reaches the surviving node."""
    for parent in ([dropped.grownFromKey] if dropped.grownFromKey else []) + dropped.alsoFrom:
        if parent != survivor.grownFromKey and parent not in survivor.alsoFrom:
            survivor.alsoFrom.append(parent)


LATTICE_STATS: dict[str, int] = {"renames": 0, "duplicates": 0, "generated": 0}
# filled by the last growAffixesLattice call, for util/affix_scan.py's Part A report


def _candKey(c: Candidate) -> tuple[str, int, str, str]:
    return (c.position, c.k, c.phono, c.ortho)


def growAffixesLattice(
    cands: dict[tuple[str, int, str, str], Candidate], lemmas: LemmaIndex | None = None,
) -> dict[tuple[str, int, str, str], Candidate]:
    """Phase 1 (DESIGN_2026-09-27-affix-rule-selection.md §3): generate the pattern lattice.
    Nothing here commits to a rule -- Phase 2/3 do that. Guards `MAX_POOL` instead of the old
    5..300 family sanity check, which no longer applies (§3.6): on hitting it, stops (keeping
    whatever was generated so far) rather than inventing a new threshold (§9 pitfall). Returns
    the pool: the anchors plus the deduped grown nodes.

    No silent key overwrites (plan §2.1.6): two grown nodes that share a (position, k, phono,
    ortho) key are told apart by carrier set -- identical sets are one node (the second parent
    is folded in as `alsoFrom`), different sets get the later one renamed `<ortho>⟨parent⟩`
    before it is expanded or stored, so its own children point at the renamed key."""
    allChildren: list[Candidate] = []
    seenExpand: set[tuple[str, frozenset[tuple[int, int, int]]]] = set()
    keyOwner: dict[tuple[str, int, str, str], tuple[tuple[str, frozenset[tuple[int, int, int]]], Candidate]] = {}
    frontier = [c for c in cands.values() if c.carriers]
    for key, c in cands.items():
        keyOwner[key] = (_carrierSetKey(c.position, c.carriers), c)
    for c in frontier:
        seenExpand.add(_carrierSetKey(c.position, c.carriers))
    total = renames = duplicates = 0
    stoppedEarly = False
    for _depth in range(GROWTH_MAX_DEPTH):
        if stoppedEarly:
            break
        nextFrontier: list[Candidate] = []
        for base in frontier:
            if stoppedEarly:
                break
            for child in _growLatticeLevel(base.position, base, lemmas):
                total += 1
                if total > MAX_POOL:
                    stoppedEarly = True
                    break
                cand = child.cand
                csk = _carrierSetKey(cand.position, cand.carriers)
                if child.emit:
                    key = _candKey(cand)
                    owner = keyOwner.get(key)
                    if owner is not None and owner[0] == csk:
                        duplicates += 1
                        _foldParents(owner[1], cand)
                        continue
                    if key in keyOwner:
                        renames += 1
                        ortho0 = cand.ortho
                        cand.ortho = f"{ortho0}⟨{base.ortho}⟩"
                        n = 1
                        while _candKey(cand) in keyOwner:
                            n += 1
                            cand.ortho = f"{ortho0}⟨{base.ortho}⟩#{n}"
                    keyOwner[_candKey(cand)] = (csk, cand)
                    allChildren.append(cand)
                if child.expand and csk not in seenExpand:
                    seenExpand.add(csk)
                    nextFrontier.append(cand)
        if not nextFrontier:
            break
        frontier = nextFrontier

    if stoppedEarly:
        print(f"WARNING: affix lattice pool exceeded MAX_POOL={MAX_POOL}; stopped early "
              f"({total} pattern nodes generated). Don't invent a new threshold -- report it.")
    LATTICE_STATS.update(renames=renames, duplicates=duplicates, generated=total)
    deduped = _dedupeByCarrierSet(allChildren)
    aliasTo = {alias: _candKey(surv) for surv in deduped for alias in surv.aliases}
    pool = dict(cands)
    for cand in deduped:
        key = _candKey(cand)
        assert key not in pool, f"lattice pool key overwritten: {key}"
        if cand.grownFromKey in aliasTo:
            cand.grownFromKey = aliasTo[cand.grownFromKey]
        cand.alsoFrom = list(dict.fromkeys(
            k for k in (aliasTo.get(k0, k0) for k0 in cand.alsoFrom) if k != cand.grownFromKey))
        pool[key] = cand
    return pool


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
                orthos = sorted(p.ortho for p in cur)
                merged = Candidate(pos, 1, phono, "|".join(orthos), isSeed=any(p.isSeed for p in cur),
                                    isGeneralized=True, variants=orthos,
                                    mergeParts=[_candKey(p) for p in cur])
                byIdx: dict[int, Carrier] = {}
                for x in carriers:
                    old = byIdx.get(x.rec.idx)
                    if old is None or x.span > old.span:
                        byIdx[x.rec.idx] = x
                merged.carriers = list(byIdx.values())
                merges[_candKey(merged)] = merged
            remaining = left
    return merges


def buildCandidates(
    records: list[WordRecord],
    seedPairs: set[tuple[str, str]],
    seedsOnly: bool = False,
    legacy: bool = False,
    excludeTopWords: bool = True,
) -> dict[tuple[str, int, str, str], Candidate]:
    """Phase 1's anchors, then the lattice. Non-legacy (plan 2026-09-28): ONE generator -- k=1
    seeds (one per position/phono/ortho), the curated A8 groups and the U3 variant merges are the
    anchors; everything longer is grown. Lemma no longer gates which words a pattern covers (U2);
    it stays only for paradigm inheritance and the different-lemma collision definition. `legacy`
    keeps the old raw k<=3 enumeration + A7 pooling + stem-attestation gate unchanged."""
    # Productivity attestation (passesPrefixFilter/passesSuffixFilter's lemma lookups) still uses
    # every record -- excluding a word from being a CARRIER doesn't mean its lemma shouldn't count
    # when checking whether some OTHER word's stem is independently attested. Non-legacy: it only
    # feeds the reported `attestedShare`.
    lemmas = LemmaIndex({r.lemme for r in records})
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
        for k in range(1, (min(MAX_AFFIX_SYLL, n - 1) if legacy else min(1, n - 1)) + 1):
            # prefixes: every record
            oa = "".join(r.orthoSylls[:k])
            if not seedsOnly or (PREFIX, oa) in seedPairs:
                stem = r.ortho[len(oa):]
                if not legacy:
                    if stem:
                        get(PREFIX, k, ".".join(r.phonoSylls[:k]), oa).carriers.append(Carrier(r, 0, k, stem))
                else:
                    if not passesPrefixFilter(stem, lemmas) and not r.isLemmaForm and r.lemme.startswith(oa):
                        stem = r.lemme[len(oa):]
                    if passesPrefixFilter(stem, lemmas):
                        get(PREFIX, k, ".".join(r.phonoSylls[:k]), oa).carriers.append(Carrier(r, 0, k, stem))
            # suffixes: lemma forms only, inflected forms inherit afterwards (iter-participles
            # are the one exception, see isIterParticiple)
            if r.isLemmaForm or isIterParticiple(r):
                oa = "".join(r.orthoSylls[-k:])
                if not seedsOnly or (SUFFIX, oa) in seedPairs:
                    stem = r.ortho[:-len(oa)]
                    if stem and (not legacy or passesSuffixFilter(stem, r.ortho, lemmas)):
                        get(SUFFIX, k, ".".join(r.phonoSylls[-k:]), oa).carriers.append(Carrier(r, n - k, k, stem))

    if legacy:
        cands = poolTailVariants(cands, keepOriginals=False)
    cands = poolKnownAffixGroups(cands)
    merges: dict[tuple[str, int, str, str], Candidate] = {}
    if not legacy:
        # after A8 (which consumes its members), so no merge part can vanish from the pool.
        merges = buildVariantMerges(cands)
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

    kept: dict[tuple[str, int, str, str], Candidate] = {}
    if legacy:
        for key, c in cands.items():
            if c.position == SUFFIX and len({x.rec.lemme for x in c.carriers}) < MIN_CARRIER_LEMMAS \
                    and not c.isSeed:
                continue
            inheritAndStat(c)
            if c.isSeed or (c.lemmas >= MIN_CARRIER_LEMMAS and c.stemRoots >= MIN_STEM_ROOTS
                            and c.freq >= MIN_CANDIDATE_FREQ):
                kept[key] = c
        return growAffixes(kept)

    for c in cands.values():
        inheritAndStat(c)
    # U3a, authoritative post-inheritance conflict test: a merge stays only if fusing added at most
    # VARIANT_MAX_NEW_CONFLICT_SHARE x its frequency of new different-lemma collisions.
    dropped: set[tuple[str, int, str, str]] = set()
    for mkey, m in merges.items():
        partExc = sum(_exceptionFreqOf(m.position, cands[pk].carriers) for pk in m.mergeParts)
        m.newConflictFreq = _exceptionFreqOf(m.position, m.carriers) - partExc
        if m.newConflictFreq > VARIANT_MAX_NEW_CONFLICT_SHARE * m.freq:
            dropped.add(mkey)
    # (the isVerbEndingFragment filter is deliberately not applied any more -- 2026-09-27 user
    # decision: bare verb-ending candidates compete on their real score in Phase 3)
    BUILD_STATS.update(mergesProposed=len(merges), mergesDropped=len(dropped))
    for key, c in cands.items():
        if key in dropped:
            continue
        if c.isSeed or (c.lemmas >= MIN_CARRIER_LEMMAS and c.stemRoots >= MIN_STEM_ROOTS):
            c.isAnchor = True
            c.attestedShare = attestedShareOf(c.position, c.carriers, lemmas)
            kept[key] = c
    return growAffixesLattice(kept, lemmas)


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

def levenshtein(a: str, b: str, vowelSubCost: float = 1.0) -> float:
    """Edit distance; substituting two phonemes of one vowel class costs `vowelSubCost`."""
    if a == b:
        return 0.0
    prev = [float(j) for j in range(len(b) + 1)]
    for i, ca in enumerate(a, 1):
        cur = [float(i)]
        for j, cb in enumerate(b, 1):
            if ca == cb:
                sub = 0.0
            elif vowelSubCost != 1.0 and ca in PHONEME_CLASS and PHONEME_CLASS.get(cb) == PHONEME_CLASS[ca]:
                sub = vowelSubCost
            else:
                sub = 1.0
            cur.append(min(prev[j] + 1.0, cur[j - 1] + 1.0, prev[j - 1] + sub))
        prev = cur
    return prev[-1]


def stringSim(a: str, b: str, vowelSubCost: float = 1.0) -> float:
    m = max(len(a), len(b))
    return 1.0 if m == 0 else 1.0 - levenshtein(a, b, vowelSubCost) / m


def _nested(short: Candidate, long: Candidate) -> bool:
    """`short` is the trailing (suffix) or leading (prefix) part of `long`, in spelling and in
    sound: -ité inside -ilité/-bilité, -tion inside -ation."""
    if short.position != long.position or len(short.ortho) < 3 or short is long:
        return False
    if not 0 < len(long.ortho) - len(short.ortho) <= NESTED_MAX_EXTRA_LETTERS:
        return False
    if short.position == SUFFIX:
        return long.ortho.endswith(short.ortho) and long.phonoFlat.endswith(short.phonoFlat)
    return long.ortho.startswith(short.ortho) and long.phonoFlat.startswith(short.phonoFlat)


def candidateSim(a: Candidate, b: Candidate, stemsA: frozenset[str], stemsB: frozenset[str]) -> float:
    s = max(stringSim(a.ortho, b.ortho), stringSim(a.phonoFlat, b.phonoFlat, 0.5))
    if _nested(a, b) or _nested(b, a):
        s = max(s, NESTED_SIM)
    union = len(stemsA | stemsB)
    if union:
        s += 0.1 * len(stemsA & stemsB) / union
    return min(1.0, s)


def clusterCandidates(cands: list[Candidate]) -> list[list[int]]:
    """Average-linkage agglomerative clustering over `cands` (already in descending frequency
    order, which makes the result deterministic). Returns clusters as index lists."""
    n = len(cands)
    if n == 0:
        return []
    stems = [frozenset(sorted(c.stemFreq, key=lambda s: -c.stemFreq[s])[:MAX_STEMS_FOR_JACCARD]) for c in cands]
    sim = np.full((n, n), -1.0)
    for i in range(n):
        for j in range(i + 1, n):
            sim[i, j] = sim[j, i] = candidateSim(cands[i], cands[j], stems[i], stems[j])
    return _averageLinkage(sim, FAMILY_LINK_SIM, MAX_FAMILY_MEMBERS)


def _averageLinkage(sim: np.ndarray, threshold: float, maxMembers: int) -> list[list[int]]:
    n = sim.shape[0]
    members: list[list[int] | None] = [[i] for i in range(n)]
    sums = np.where(sim < 0, 0.0, sim)   # summed pair similarities between clusters
    sizes = np.ones(n)
    alive = np.ones(n, dtype=bool)
    blocked = np.zeros((n, n), dtype=bool)  # merge would exceed maxMembers (sizes only grow)
    np.fill_diagonal(blocked, True)
    while True:
        avg = sums / np.outer(sizes, sizes)
        avg[blocked | ~alive[:, None] | ~alive[None, :]] = -1.0
        flat = int(np.argmax(avg))
        i, j = divmod(flat, n)
        if avg[i, j] < threshold:
            break
        mi, mj = members[i], members[j]
        assert mi is not None and mj is not None
        if len(mi) + len(mj) > maxMembers:
            blocked[i, j] = blocked[j, i] = True
            continue
        sums[i, :] += sums[j, :]
        sums[:, i] += sums[:, j]
        sums[i, i] = 0.0
        sizes[i] += sizes[j]
        members[i] = mi + mj
        members[j] = None
        alive[j] = False
    return [m for m in members if m is not None]


@dataclass
class Family:
    familyId: str
    position: str
    members: list[Candidate]
    carriers: list[Carrier]          # pooled, deduplicated by record, largest span wins
    stemSubgroups: list[list[int]] = field(default_factory=list)   # diagnostic: stem-competition colouring (A4)
    competingPairs: list[tuple[int, int, float, list[str]]] = field(default_factory=list)
    upperBound: float = 0.0
    seedOverlap: list[str] = field(default_factory=list)

    @property
    def freq(self) -> float:
        return sum(c.rec.frequency for c in self.carriers)


def poolCarriers(members: list[Candidate]) -> list[Carrier]:
    best: dict[int, Carrier] = {}
    for mi, m in enumerate(members):
        for c in m.carriers:
            old = best.get(c.rec.idx)
            if old is None or c.span > old.span:
                best[c.rec.idx] = c._replace(member=mi)
    return sorted(best.values(), key=lambda c: (-c.rec.frequency, c.rec.idx))


def competitionMass(a: Candidate, b: Candidate) -> tuple[float, list[str]]:
    """Sum over shared normalized stems of the smaller carrier-frequency, plus the top stems."""
    shared = set(a.stemFreq) & set(b.stemFreq)
    per = sorted(((min(a.stemFreq[s], b.stemFreq[s]), s) for s in shared), reverse=True)
    return sum(m for m, _ in per), [s for _, s in per[:5]]


def colourSubgroups(nMembers: int, mass: dict[tuple[int, int], float]) -> list[list[int]]:
    """Greedy colouring of the competition graph, largest mass first."""
    edges = sorted(((m, i, j) for (i, j), m in mass.items() if m > 0), reverse=True)
    incident = [0.0] * nMembers
    adj: list[set[int]] = [set() for _ in range(nMembers)]
    for m, i, j in edges:
        incident[i] = max(incident[i], m)
        incident[j] = max(incident[j], m)
        adj[i].add(j)
        adj[j].add(i)
    order = sorted(range(nMembers), key=lambda i: (-incident[i], i))
    colour: dict[int, int] = {}
    for i in order:
        used = {colour[j] for j in adj[i] if j in colour}
        c = 0
        while c in used:
            c += 1
        colour[i] = c
    groups: dict[int, list[int]] = {}
    for i in range(nMembers):
        groups.setdefault(colour[i], []).append(i)
    return [groups[c] for c in sorted(groups)]


def buildFamily(familyId: str, members: list[Candidate]) -> Family:
    members = sorted(members, key=lambda c: -c.strokeFreq)
    fam = Family(familyId, members[0].position, members, poolCarriers(members))
    mass: dict[tuple[int, int], float] = {}
    for i in range(len(members)):
        for j in range(i + 1, len(members)):
            m, stems = competitionMass(members[i], members[j])
            if m > 0:
                mass[(i, j)] = m
                fam.competingPairs.append((i, j, m, stems))
    fam.competingPairs.sort(key=lambda t: -t[2])
    fam.stemSubgroups = colourSubgroups(len(members), mass)
    fam.upperBound = sum(c.rec.frequency * c.span for c in fam.carriers)
    return fam


def discoverFamilies(
    cands: dict[tuple[str, int, str, str], Candidate],
    seedFamilies: dict[str, list[tuple[str, str]]],
) -> list[Family]:
    families: list[Family] = []
    for pos in (PREFIX, SUFFIX):
        pool = sorted((c for c in cands.values() if c.position == pos),
                      key=lambda c: (-c.strokeFreq, c.ortho, c.phono))
        pool = pool[:MAX_FAMILY_CANDIDATES]
        for cluster in clusterCandidates(pool):
            top = max(pool[i].lemmas for i in cluster)
            kept = [pool[i] for i in cluster if pool[i].isSeed or pool[i].lemmas >= MEMBER_MIN_SHARE * top]
            fam = buildFamily("", kept)
            if fam.upperBound >= MIN_FAMILY_STROKEFREQ:
                fam.position = pos
                fam.seedOverlap = sorted(
                    name for name, aff in seedFamilies.items()
                    if any(p == pos and a in {m.ortho for m in fam.members} for p, a in aff))
                families.append(fam)
    families.sort(key=lambda f: -f.upperBound)
    counters = {PREFIX: 0, SUFFIX: 0}
    for f in families:
        counters[f.position] += 1
        f.familyId = f"{'P' if f.position == PREFIX else 'S'}{counters[f.position]:03d}"
    return families


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

    def __init__(self, starboard: Starboard, records: list[WordRecord]) -> None:
        self.starboard = starboard
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
        if set(neighbour) & set(binding.keys):
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


@dataclass
class FamilyMetrics:
    strokeFreqSaved: float = 0.0
    freqBenefiting: float = 0.0
    benefitShare: float = 0.0        # by frequency
    benefitShareCount: float = 0.0
    fallbacks: dict[str, int] = field(default_factory=dict)
    boundaryRisks: int = 0


def familyMetrics(results: list[list[CarrierResult]]) -> FamilyMetrics:
    m = FamilyMetrics()
    total = totalF = 0.0
    benefit = 0
    for res in results:
        for r in res:
            f = r.carrier.rec.frequency
            total += 1
            totalF += f
            if r.gain > 0:
                m.strokeFreqSaved += f * r.gain
                m.freqBenefiting += f
                benefit += 1
                m.boundaryRisks += r.boundaryRisk
            else:
                m.fallbacks[r.reason or "unknown"] = m.fallbacks.get(r.reason or "unknown", 0) + 1
    m.benefitShare = m.freqBenefiting / totalF if totalF else 0.0
    m.benefitShareCount = benefit / total if total else 0.0
    return m

