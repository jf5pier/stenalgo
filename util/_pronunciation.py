"""
Pronunciation helpers shared by the checks against external sources (Wiktionary, GLÀFF): conversion of an IPA string into
the lexicon's phoneme alphabet, and the tolerant comparison of two strings in that alphabet. Pure functions, standard library only.

The lexicon writes one ASCII symbol per phoneme (docs/GLOSSARY.md): R E O @ 5 § 1 9 2 8 N G S Z ° and the plain letters.
"""
import re
import unicodedata
from collections.abc import Callable
from itertools import product

IPA_TO_LEXICON = {
    "ʁ": "R", "ʀ": "R", "r": "R", "ɛ": "E", "ɔ": "O", "ə": "°", "ǝ": "°", "ɑ": "a", "œ": "9", "ø": "2", "ʃ": "S", "ʒ": "Z",
    "ɥ": "8", "ɲ": "N", "ŋ": "G", "ɡ": "g",
}
NASALS = {"ɑ̃": "@", "ɛ̃": "5", "ɔ̃": "§", "œ̃": "1", "õ": "§", "ã": "@", "ẽ": "5"}
IGNORED = set(".ˈˌ‿ːʔ'​ ‿ ")
OPTIONAL = re.compile(r"\(([^()]*)\)")
MAX_VARIANTS = 16


def ipaToLexicon(ipa: str) -> set[str]:
    """The lexicon spellings of an IPA transcription. Optional parts in parentheses -- `(ə.)` -- give one variant with
    and one without; an optional `(h)` is always dropped. Variants of the source separated by `;` are all returned."""
    result: set[str] = set()
    for alternative in ipa.split(";"):
        alternative = unicodedata.normalize("NFD", alternative.strip())
        alternative = alternative.replace("̃", "~")
        groups = OPTIONAL.findall(alternative)
        choices = [("", g) if g.strip(".") not in ("h",) else ("",) for g in groups]
        template = OPTIONAL.sub("\0", alternative)
        for picked in list(product(*choices))[:MAX_VARIANTS]:
            pieces = iter(picked)
            text = "".join(next(pieces) if ch == "\0" else ch for ch in template)
            result.add(_convert(text))
    result.discard("")
    return result


def _convert(text: str) -> str:
    out = []
    i = 0
    while i < len(text):
        ch = text[i]
        pair = ch + ("̃" if text[i + 1:i + 2] == "~" else "")
        if text[i + 1:i + 2] == "~":
            symbol = NASALS.get(unicodedata.normalize("NFC", pair))
            if symbol is not None:
                out.append(symbol)
            i += 2
            continue
        symbol = NASALS.get(ch)
        if symbol is not None:
            out.append(symbol)
        elif ch not in IGNORED and ch not in "[]/\\":
            out.append(IPA_TO_LEXICON.get(ch, ch))
        i += 1
    return "".join(out)


MID_VOWELS = str.maketrans({"E": "e", "O": "o", "9": "2"})


def _noSchwa(phon: str) -> str:
    return phon.replace("°", "")


def _midMerged(phon: str) -> str:
    return phon.translate(MID_VOWELS)


def _glideCollapsed(phon: str) -> str:
    return re.sub(r"j+", "j", phon)


# The relaxations in the order they are tried, each a (name, transformations applied to both sides).
RELAXATIONS: list[tuple[str, tuple[Callable[[str], str], ...]]] = [
    ("schwa", (_noSchwa,)),
    ("mid vowel", (_midMerged,)),
    ("glide", (_glideCollapsed,)),
    ("schwa + mid vowel", (_noSchwa, _midMerged)),
    ("schwa + glide", (_noSchwa, _glideCollapsed)),
    ("mid vowel + glide", (_midMerged, _glideCollapsed)),
    ("schwa + mid vowel + glide", (_noSchwa, _midMerged, _glideCollapsed)),
]


def _apply(phon: str, steps: tuple[Callable[[str], str], ...]) -> str:
    for step in steps:
        phon = step(phon)
    return phon


def equivalenceKey(phon: str) -> str:
    """The comparison key of the most tolerant matching: schwas dropped, open and close mid vowels merged, a doubled
    glide (`ij.j` against `i.j`) collapsed."""
    return _apply(phon, RELAXATIONS[-1][1])


def compare(ours: str, references: set[str]) -> tuple[str, str]:
    """('exact' | 'equivalent' | 'differs', detail): `ours` against the reference spellings (already in the lexicon alphabet).
    For 'equivalent' the detail names the relaxation that made them equal (schwa, mid vowel, glide or a combination, the
    mildest first); for 'differs' it shows the first differing symbols against the nearest reference."""
    if ours in references:
        return "exact", ""
    for name, steps in RELAXATIONS:
        key = _apply(ours, steps)
        matching = sorted(ref for ref in references if _apply(ref, steps) == key)
        if matching:
            return "equivalent", name + _midVowelDirection(ours, matching, steps)
    nearest = min(sorted(references), key=lambda r: _editDistance(ours, r)) if references else ""
    return "differs", _firstDifference(ours, nearest)


def _midVowelDirection(ours: str, matching: list[str], steps: tuple[Callable[[str], str], ...]) -> str:
    """For a match that needed the mid-vowel merge, which way the vowels differ: ' (ours e, ref E)' for the first one."""
    if _midMerged not in steps:
        return ""
    others = tuple(step for step in steps if step is not _midMerged)
    mine = _apply(ours, others)
    ref = min(sorted(_apply(r, others) for r in matching), key=lambda r: _editDistance(mine, r))
    for x, y in zip(mine, ref):
        if x != y:
            return f" (ours {x}, ref {y})"
    return ""


def _editDistance(a: str, b: str) -> int:
    previous = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        current = [i]
        for j, y in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (x != y)))
        previous = current
    return previous[-1]


def _firstDifference(a: str, b: str) -> str:
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return f"{a[max(0, i - 2):i + 3]} / {b[max(0, i - 2):i + 3]}"
    return f"length: {a} / {b}"
