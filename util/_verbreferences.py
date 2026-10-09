"""
Unified reference-pronunciation index for verb forms: the French Wiktionary conjugation pages
(resources/wiktionaryVerbPronunciations.tsv, committed) and GLÀFF 1.2.2 (glaff/glaff-1.2.2.txt, gitignored, see README: GLÀFF /
TODO.md "Install instructions"), both converted to the lexicon's phoneme alphabet (util/_pronunciation.py).

A slot is (lemme, ortho, tag), the tag in the lexicon's infover vocabulary (`ind:pre:3s`, `par:pas:fp` ...). For each slot,
`VerbReferences.get` gives a `RefSet`: the union of the variants of both sources, the variants of each source, whether the two
sources genuinely disagree, and the variants to prefer (docs/SYNTHETIC_LEXICON_STATUS.md 6.2):

  - identical or equivalent (util._pronunciation.equivalenceKey: schwas, mid vowels, doubled glide ignored) = agreement,
    `preferred` is the union;
  - genuine conflict (no variant of one source equivalent to a variant of the other): prefer the current Wiktionary unless
    every one of its variants fails `isPlausibleIpa`, then GLÀFF (its plausible variants); when neither source is plausible,
    the union.

Plausibility (`isPlausibleIpa`, applied to the raw IPA string of a source row): brackets and parentheses balanced; every
symbol of the converted pronunciation in the lexicon's alphabet (so a stray accented letter or a garbled `ouv9j§` fails on
the letters it should not contain); and the length of the converted pronunciation within [len(ortho)/4, len(ortho) + 2]
(a pronunciation is never much longer than the spelling, and a verb form of n letters is not read in fewer than n/4 phonemes).
The bounds were tuned on the committed data (see `python -m util._verbreferences --conflicts OUT.tsv`).

`VerbReferences.forRow` mirrors util/check_against_wiktionary's rule: union over the row's tags. `matchRow` is the checker's
rule exactly: the first source (Wiktionary, then GLÀFF) that has any variant for any tag of the lemma, ortho ignored.

Run: python -m util._verbreferences --conflicts OUT.tsv [--wiktionary PATH] [--glaff PATH]
"""
import argparse
import os
import sys
from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass

from util._pronunciation import equivalenceKey, ipaToLexicon

WIKTIONARY_PATH = "resources/wiktionaryVerbPronunciations.tsv"
GLAFF_PATH = "glaff/glaff-1.2.2.txt"
SOURCES = ("wiktionary", "glaff")

MOOD = {"i": "ind", "s": "sub", "c": "cnd", "m": "imp"}
TENSE = {"p": "pre", "i": "imp", "s": "pas", "f": "fut"}

LEXICON_ALPHABET = frozenset("12589@EGNORSZabdefgijklmnopstuvwxyz§°")
MAX_EXTRA_LENGTH = 2   # a pronunciation has at most len(ortho) + 2 symbols
MIN_LENGTH_RATIO = 4   # and at least len(ortho) / 4

PRESENT_PARTICIPLE_TAG = "par:pre"  # GRACE Vmpp--- in GLÀFF (aimant); Wiktionary's file has no participle rows
INFINITIVE_TAG = "inf"  # the lexicon's infover of an infinitive; GRACE Vmn---- in GLÀFF (Wiktionary's file has no infinitive rows)

Slot = tuple[str, str, str]  # (lemme, ortho, tag)


@dataclass(frozen=True)
class RefSet:
    variants: frozenset[str]
    bySource: Mapping[str, frozenset[str]]
    conflict: bool
    preferred: frozenset[str]


def decodeGrace(tag: str) -> str | None:
    """A GLÀFF verb tag (Vmip3s-, Vmcp1p-, Vmps-sm ...) in the lexicon's infover vocabulary, None when it is not one we compare."""
    if not tag.startswith("Vm") or len(tag) < 7:
        return None
    if tag == "Vmn----":
        return INFINITIVE_TAG
    if tag == "Vmpp---":
        return PRESENT_PARTICIPLE_TAG
    mood, tense, person, number = tag[2], tag[3], tag[4], tag[5]
    if mood in MOOD and tense in TENSE and person in "123" and number in "sp":
        return f"{MOOD[mood]}:{TENSE[tense]}:{person}{number}"
    if mood == "p" and tense == "s" and tag[5] in "sp" and tag[6] in "mf":
        return f"par:pas:{tag[6]}{tag[5]}"
    return None


def isPlausibleIpa(ipa: str, ortho: str) -> bool:
    """Sanity check of one raw IPA transcription of the form `ortho`: balanced brackets and parentheses, only symbols of the
    lexicon alphabet once converted, a length within [len(ortho) / 4, len(ortho) + 2]. Variants separated by `;` must all pass."""
    pairs = {")": "(", "]": "["}
    for alternative in ipa.split(";"):
        stack: list[str] = []
        for ch in alternative:
            if ch in "([":
                stack.append(ch)
            elif ch in pairs and (not stack or stack.pop() != pairs[ch]):
                return False
        if stack:
            return False
        variants = ipaToLexicon(alternative)
        if not variants:
            return False
        for phon in variants:
            if not set(phon) <= LEXICON_ALPHABET:
                return False
            if len(phon) > len(ortho) + MAX_EXTRA_LENGTH or len(phon) * MIN_LENGTH_RATIO < len(ortho):
                return False
    return True


class _Source:
    """The rows of one source: converted variants per slot, and the variants that came from an implausible transcription."""

    def __init__(self) -> None:
        self.variants: dict[Slot, set[str]] = defaultdict(set)
        self.implausible: dict[Slot, set[str]] = defaultdict(set)
        self.lemmaTag: dict[tuple[str, str], set[str]] = defaultdict(set)

    def add(self, lemme: str, ortho: str, tag: str, ipa: str) -> None:
        phonemes = ipaToLexicon(ipa)
        self.variants[(lemme, ortho, tag)] |= phonemes
        self.lemmaTag[(lemme, tag)] |= phonemes
        if not isPlausibleIpa(ipa, ortho):
            self.implausible[(lemme, ortho, tag)] |= phonemes


def agrees(first: Iterable[str], second: Iterable[str]) -> bool:
    """True when some variant of `first` is identical or equivalent to some variant of `second`."""
    keys = {equivalenceKey(v) for v in first}
    return any(equivalenceKey(v) in keys for v in second)


def _buildRefSet(per: Mapping[str, frozenset[str]], bad: Mapping[str, frozenset[str]]) -> RefSet:
    union = frozenset().union(*per.values())
    wiktionary, glaff = per.get("wiktionary", frozenset()), per.get("glaff", frozenset())
    if not wiktionary or not glaff or agrees(wiktionary, glaff):
        return RefSet(union, per, False, union)
    good = {name: per[name] - bad.get(name, frozenset()) for name in SOURCES}
    preferred = good["wiktionary"] or good["glaff"] or union
    return RefSet(union, per, True, preferred)


class VerbReferences:

    def __init__(self, wiktionary: _Source, glaff: _Source) -> None:
        self.sources = {"wiktionary": wiktionary, "glaff": glaff}
        self._orthoTags: dict[tuple[str, str], set[str]] | None = None

    def get(self, lemme: str, ortho: str, tag: str) -> RefSet | None:
        slot = (lemme, ortho, tag)
        per = {name: frozenset(src.variants[slot]) for name, src in self.sources.items() if slot in src.variants}
        if not per:
            return None
        bad = {name: frozenset(self.sources[name].implausible.get(slot, ())) for name in per}
        return _buildRefSet(per, bad)

    def forRow(self, lemme: str, ortho: str, tags: Iterable[str]) -> RefSet | None:
        """The union of `get` over the tags of a row, as a RefSet (conflict when any tag conflicts, preferred the union of the
        tags' preferred sets)."""
        found = [r for r in (self.get(lemme, ortho, tag) for tag in tags) if r is not None]
        if not found:
            return None
        per: dict[str, frozenset[str]] = {}
        for name in SOURCES:
            merged = frozenset().union(*(r.bySource.get(name, frozenset()) for r in found))
            if merged:
                per[name] = merged
        return RefSet(frozenset().union(*(r.variants for r in found)), per, any(r.conflict for r in found),
                      frozenset().union(*(r.preferred for r in found)))

    def tagsOf(self, lemme: str, ortho: str) -> list[str]:
        """Every tag under which either source lists the spelling `ortho` of `lemme` (sorted)."""
        if self._orthoTags is None:
            index: dict[tuple[str, str], set[str]] = defaultdict(set)
            for source in self.sources.values():
                for l, o, t in source.variants:
                    index[(l, o)].add(t)
            self._orthoTags = index
        return sorted(self._orthoTags.get((lemme, ortho), ()))

    def forOrtho(self, lemme: str, ortho: str) -> RefSet | None:
        """The union of `get` over ANY tag of the spelling: a spelling of one lemma is pronounced the same whatever its
        tag, and Wiktionary lists a homographic form (`criions`: ind:imp:1p and sub:pre:1p) under one tag only.
        Same merge as `forRow`; None when the spelling is unknown to both sources."""
        return self.forRow(lemme, ortho, self.tagsOf(lemme, ortho))

    def matchRow(self, lemme: str, tags: Iterable[str]) -> tuple[str, set[str]] | None:
        """The checker's rule: the first source (Wiktionary, then GLÀFF as a fallback) with any variant for any of the tags
        of the lemma, ortho ignored. (source, the union of its variants)."""
        tagList = list(tags)
        for name in SOURCES:
            found: set[str] = set()
            for tag in tagList:
                found |= self.sources[name].lemmaTag.get((lemme, tag), set())
            if found:
                return name, found
        return None

    def lemmaTagIndex(self, source: str) -> dict[tuple[str, str], set[str]]:
        """One source as (lemme, tag) -> variants, ortho ignored."""
        return self.sources[source].lemmaTag

    def slots(self) -> Iterator[Slot]:
        seen = set(self.sources["wiktionary"].variants)
        yield from seen
        for slot in self.sources["glaff"].variants:
            if slot not in seen:
                yield slot

    def iterConflicts(self) -> Iterator[tuple[str, str, str, RefSet]]:
        """The slots both sources have and genuinely disagree on."""
        wiktionary, glaff = self.sources["wiktionary"].variants, self.sources["glaff"].variants
        for slot in sorted(wiktionary.keys() & glaff.keys()):
            ref = self.get(*slot)
            if ref is not None and ref.conflict:
                yield slot[0], slot[1], slot[2], ref

    def sharedSlotCount(self) -> int:
        return len(self.sources["wiktionary"].variants.keys() & self.sources["glaff"].variants.keys())

    def conflictReason(self, ref: RefSet, ortho: str) -> str:
        """Why `preferred` is what it is, for the review file."""
        wik = ref.bySource.get("wiktionary", frozenset())
        if ref.preferred == ref.variants:
            return "no plausible variant in either source: union"
        return "wiktionary plausible: wiktionary" if ref.preferred <= wik else "wiktionary implausible: glaff"


def loadVerbReferences(wiktionaryPath: str = WIKTIONARY_PATH, glaffPath: str = GLAFF_PATH,
                       requireGlaff: bool = False) -> VerbReferences:
    wiktionary, glaff = _Source(), _Source()
    with open(wiktionaryPath, encoding="utf-8", newline="") as f:
        header = f.readline().rstrip("\n")
        assert header == "lemme\tortho\ttags\tipa", f"unexpected header in {wiktionaryPath}"
        for line in f:
            lemme, ortho, tags, ipa = line.rstrip("\n").split("\t")
            for tag in tags.split(";"):
                wiktionary.add(lemme, ortho, tag, ipa)
    if glaffPath and not os.path.exists(glaffPath):
        message = f"GLÀFF file {glaffPath} not found (see README.md, GLÀFF install paragraph)"
        if requireGlaff:
            raise FileNotFoundError(message)
        print(f"warning: {message}; continuing with Wiktionary only", file=sys.stderr)
    elif glaffPath:
        with open(glaffPath, encoding="utf-8") as f:
            for line in f:
                fields = line.rstrip("\n").split("|")
                if len(fields) < 5 or not fields[1].startswith("Vm") or not fields[3]:
                    continue
                graceTag = decodeGrace(fields[1])
                if graceTag is not None:
                    glaff.add(fields[2], fields[0], graceTag, fields[3])
    return VerbReferences(wiktionary, glaff)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--conflicts", required=True, metavar="OUT.tsv")
    parser.add_argument("--wiktionary", default=WIKTIONARY_PATH)
    parser.add_argument("--glaff", default=GLAFF_PATH)
    args = parser.parse_args()
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    references = loadVerbReferences(args.wiktionary, args.glaff, requireGlaff=True)
    count = 0
    with open(args.conflicts, "w", encoding="utf-8", newline="") as out:
        out.write("lemme\tortho\ttag\twiktionary\tglaff\tpreferred\treason\n")
        for lemme, ortho, tag, ref in references.iterConflicts():
            count += 1
            out.write("\t".join([lemme, ortho, tag, "|".join(sorted(ref.bySource["wiktionary"])),
                                 "|".join(sorted(ref.bySource["glaff"])), "|".join(sorted(ref.preferred)),
                                 references.conflictReason(ref, ortho)]) + "\n")
    print(f"{count} genuine conflicts on {references.sharedSlotCount()} shared slots, written to {args.conflicts}")


if __name__ == "__main__":
    main()
