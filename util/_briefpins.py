"""
The pinned briefs (`briefs.json`, written only by `python -m util.build_briefs --rederive`) as the other steps read them: the
expression layer's `BriefRule`s (util/_expressioninput.py), the reserved chords (util/_reservedchords.py) and the exporters.
"""

from __future__ import annotations

import json
from collections import defaultdict
from functools import lru_cache

from src.affixes import SimContext
from src.briefs import (BRIEF_SCOPE_FAMILY, FamilyIndex, Outline, PinnedBrief, Stroke, expandBrief, loadPinnedBriefs,
                        pinnedRows, prefixMatch, wordSubject)
from src.keyboard import Starboard, Strokes, canonicalizeStrokes
from src.theorycompare import Lexicon, loadLexicon
from src.word import Word
from util._stenorender import checkedOutline, renderFinalStrokesToRTFCRE

BRIEFS_JSON = "briefs.json"
BRIEF_SUBJECTS = "resources/briefs.tsv"
LEXIQUE = "resources/Lexique383.tsv"


def loadPins(starboard: Starboard, path: str = BRIEFS_JSON) -> list[PinnedBrief]:
    """The pinned briefs, in file order (empty without the file)."""
    keys = tuple(starboard.keyDisplayNames())
    return loadPinnedBriefs(path, lambda text: checkedOutline(text, keys, starboard))


def writePins(starboard: Starboard, pins: list[PinnedBrief], path: str = BRIEFS_JSON) -> None:
    document = pinnedRows(pins, lambda outline: renderFinalStrokesToRTFCRE(starboard, outline))
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(document, handle, ensure_ascii=False, indent=1)
        handle.write("\n")


def loadSubjects(path: str = BRIEF_SUBJECTS) -> list[tuple[str, str]]:
    """The hand-edited subject list, `(subject, scope)` in file order."""
    with open(path, encoding="utf-8") as handle:
        rows = [line.rstrip("\n").split("\t") for line in handle if line.strip()]
    assert rows[0] == ["subject", "scope"], rows[0]
    return [(subject, scope) for subject, scope in rows[1:]]


@lru_cache(maxsize=1)
def _lexicon() -> Lexicon:
    return loadLexicon(LEXIQUE, "films")


def pinnedChords(starboard: Starboard, theory: dict[Word, list[Strokes]] | None = None) -> list[str]:
    """Every outline the pinned briefs reserve (RTFCRE): each chord, and with a `theory` (before the merge) the one-stroke
    outlines the word briefs give their family forms (legal ones, taken or not: a merge just cannot take them)."""
    pins = loadPins(starboard)
    render = lambda outline: renderFinalStrokesToRTFCRE(starboard, outline)  # noqa: E731
    out = [render((pin.chord,)) for pin in pins]
    if theory is None:
        return out
    outlinesOf: dict[str, list[Outline]] = defaultdict(list)
    for word, alternatives in theory.items():
        for strokes in alternatives:
            outline = canonicalizeStrokes(strokes)
            if outline not in outlinesOf[word.ortho.lower()]:
                outlinesOf[word.ortho.lower()].append(outline)
    lexicon = _lexicon()
    families = FamilyIndex(lexicon)
    ctx = SimContext(starboard, [])
    coda = set(starboard.keyIDinSyllabicPart["coda"])
    marks = (10, 15)

    def legal(stroke: Stroke) -> bool:
        syllabic = tuple(k for k in stroke if k not in marks)
        return bool(syllabic) and ctx.isLegal(syllabic)

    for pin in pins:
        if pin.kind != "word" or pin.subject not in outlinesOf or not pin.stem:
            continue
        subject = wordSubject(pin.subject, pin.scope, outlinesOf, lexicon)
        names = families.familyForms(pin.subject) if pin.scope == BRIEF_SCOPE_FAMILY else {pin.subject}
        forms = {f: outlinesOf[f] for f in names if f in outlinesOf}
        k, stemKeys = len(pin.stem), frozenset(pin.stem[-1])
        if not prefixMatch(subject.target, subject.target, k, coda):
            continue
        for outlines in expandBrief(forms, subject.target, k, stemKeys, pin.chord, coda, legal).values():
            out.extend(render(o) for o in outlines if len(o) == 1)
    return out
