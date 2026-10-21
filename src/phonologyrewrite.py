"""Phonology rewrite, iteration 1 (docs/PHONOLOGY_REWRITE_PLAN.md PRP3, PRP4, PRP17, PRB12): the phonology overrides applied in memory
on the phonetic theory after it is loaded, never pickled, behind STENALGO_PHONOLOGY_REWRITE (default off: today's outputs stay byte-identical).

`resources/phonologyOverrides.tsv` has two row kinds: `phonology` (every reading of a spelling is typed with a given single-syllable,
vowel-less phonology: je -> Z), `elided` (a spelling that ranks right after its base in the star/hash order; one that has no lexicon row
is created from its base's frequent readings) and `drop` (a junk reading, spelling + gramcat, removed from the theory).
"""
import csv
import dataclasses
import hashlib
import os
from dataclasses import dataclass
from typing import Any

from src.keyboard import Keyboard, Strokes
from src.word import Word

PHONOLOGY_REWRITE = os.environ.get("STENALGO_PHONOLOGY_REWRITE", "0") == "1"
OVERRIDES_PATH = "resources/phonologyOverrides.tsv"
ONSET = "onset"


@dataclass(frozen=True)
class ElidedRow:
    elided: str
    base: str
    phonology: str       # "" when the lexicon already has rows for the elided spelling


@dataclass(frozen=True)
class PhonologyRules:
    phonology: dict[str, str]          # spelling -> new phonology
    elided: tuple[ElidedRow, ...]
    dropped: frozenset[tuple[str, str]] = frozenset()    # (spelling, GramCat name) readings removed from the theory

    def elidedBases(self) -> dict[str, str]:
        """elided spelling -> its base spelling."""
        return {row.elided: row.base for row in self.elided}

    def markingOverrides(self) -> dict[frozenset[str], str]:
        """The star/hash pair overrides (`src.ambiguitychecker.MARKING_OVERRIDES` format): the elided form carries the mark (PRP4)."""
        return {frozenset({row.base, row.elided}): row.elided for row in self.elided}


def overridesMd5(path: str = OVERRIDES_PATH) -> str | None:
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def loadPhonologyRules(path: str = OVERRIDES_PATH) -> PhonologyRules:
    phonology: dict[str, str] = {}
    elided: list[ElidedRow] = []
    dropped: set[tuple[str, str]] = set()
    with open(path, encoding="utf-8", newline="") as f:
        lines = (line for line in f if line.strip() and not line.startswith("#"))
        for row in csv.DictReader(lines, delimiter="\t"):
            kind, spelling = row["kind"], row["spelling"]
            if kind == "phonology":
                if not row["phonology"]:
                    raise ValueError(f"{path}: phonology row for {spelling!r} without a phonology")
                if spelling in phonology:
                    raise ValueError(f"{path}: duplicate phonology row for {spelling!r}")
                phonology[spelling] = row["phonology"]
            elif kind == "elided":
                if not row["base"]:
                    raise ValueError(f"{path}: elided row for {spelling!r} without a base")
                elided.append(ElidedRow(spelling, row["base"], row["phonology"]))
            elif kind == "drop":
                if not row["gramcat"]:
                    raise ValueError(f"{path}: drop row for {spelling!r} without a gramcat")
                dropped.add((spelling, row["gramcat"]))
            else:
                raise ValueError(f"{path}: unknown row kind {kind!r}")
    return PhonologyRules(phonology, tuple(elided), frozenset(dropped))


def syllableStrokes(keyboard: Keyboard, phonology: str) -> Strokes:
    """The one-stroke outline of a single vowel-less syllable: all its phonemes are onset phonemes."""
    stroke = keyboard.getStrokeOfSyllableByPart({ONSET: list(phonology), "nucleus": [], "coda": []})
    if not stroke:
        raise ValueError(f"phonology {phonology!r} has no chord on the layout")
    return (stroke,)


def retyped(word: Word, ortho: str, phonology: str, frequent: bool) -> Word:
    """A copy of `word` with another phonology (and spelling): one syllable, the phonology's phonemes."""
    changes: dict[str, Any] = {"ortho": ortho, "phonology": phonology, "rawSyllCV": "_".join(phonology)}
    if ortho != word.ortho:
        changes["rawOrthosyllCV"] = "_".join(ortho)
        changes["lemme"] = ortho
        if not frequent:
            changes["frequencyBook"] = 0.0
            changes["frequencyFilm"] = 0.0
    return dataclasses.replace(word, **changes)


def applyPhonologyRewrite(
    theory: dict[Strokes, list[Word]], keyboard: Keyboard, rules: PhonologyRules,
) -> dict[Strokes, list[Word]]:
    """The theory with the overrides applied: a new dict, the input is untouched. Elided spellings become their own lemma. Words of an overridden spelling move to the outline of
    their new phonology; each elided spelling the lexicon lacks is created from the readings of its base that have a frequency."""
    rewritten: dict[Strokes, list[Word]] = {}

    def put(strokes: Strokes, word: Word) -> None:
        rewritten.setdefault(strokes, []).append(word)

    present = {word.ortho for words in theory.values() for word in words}
    elidedOrthos = {row.elided for row in rules.elided}
    created: list[Word] = []
    for strokes, words in theory.items():
        for word in words:
            if (word.ortho, word.gramCat.name) in rules.dropped:
                continue
            newPhonology = rules.phonology.get(word.ortho)
            if newPhonology is None:
                # an elided form is its own lemma (as l', s', t' already are): d' of `de` would otherwise be a same-lemma pair
                # with its base, which S6 handles, not the S7 star/hash ranking that PRP4 relies on
                put(strokes, dataclasses.replace(word, lemme=word.ortho) if word.ortho in elidedOrthos and word.lemme != word.ortho
                    else word)
                continue
            moved = retyped(word, word.ortho, newPhonology, frequent=True)
            put(syllableStrokes(keyboard, newPhonology), moved)
            for row in rules.elided:
                if row.base == word.ortho and row.phonology and row.elided not in present and word.frequency > 0:
                    created.append(retyped(word, row.elided, row.phonology, frequent=False))
    seen: set[tuple[str, str, str]] = set()
    for word in created:
        key = (word.ortho, word.lemme, word.gramCat.name)
        if key not in seen:
            seen.add(key)
            put(syllableStrokes(keyboard, word.phonology), word)
    return rewritten
