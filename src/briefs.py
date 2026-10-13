"""
The brief generator (S9e): one mechanic for the word briefs, the stem briefs and the expression briefs.

A BRIEF replaces the first K strokes of a word's outline (the STEM: strokes 1..K-1 of the word, plus S_K, a subset of
its K-th stroke that keeps its vowel) by ONE invented stroke B. Every form of the word's lemma family whose outline
starts with the stem (strokes 1..K-1 equal, K-th stroke a superset of S_K, the `*`/`#` marks transparent) is rewritten
B + extra keys of its K-th stroke + its marks, then its tail strokes:
  petit p@a/ti -> B;  petite p@a/tit -> B+t;  petits p@a/ti/-s -> B/-s, p@a/tis -> B+s
  travail tRa/vaj (stem tRa/va) -> B+j;  travaille tRa/v*aj -> B+*j;  travailler tRa/va/RweR -> B/RweR
An EXPRESSION brief replaces its whole outline (the concatenation of its tokens' theory strokes) by one stroke.

The chord B is chosen among all legal chords (with each subset of the marks), best first by
`(boundary risk > 0, no shared phoneme, score)`: the score is the chord cost, minus a bonus for each phoneme of the
word the chord holds (a DISJOINT matching of keys to phoneme occurrences), plus a penalty for each key no phoneme
explains and for each pair of held phonemes the chord reads in the wrong order. A candidate must give legal, free
outlines (not a live outline of another word, not a reserved chord, not an attach-merge chord, not taken by an
earlier brief) and, as a one-stroke chord, a zero boundary risk (no live X/B nor B/Y outline, which the neighbour
word would swallow). The chosen one is the best within 90 % of the best saving.

This module is a pure library: `util/build_briefs.py` loads the inputs, runs it and owns the files. The chosen chords
are PINNED in `briefs.json` (`loadPinnedBriefs`, the only reader): the pipeline only validates them.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from src.affixbinding import enumerateKeypresses
from src.affixes import SimContext
from src.expressionmodel import RESERVED_MARK_KEYS
from src.keyboard import Starboard
from src.theorycompare import Lexicon

Stroke = tuple[int, ...]
Outline = tuple[Stroke, ...]

MARKS = frozenset(RESERVED_MARK_KEYS)
MARK_SETS: tuple[frozenset[int], ...] = (frozenset(), frozenset({10}), frozenset({15}), frozenset({10, 15}))
GOOD_ENOUGH = 0.9
SHARED_BONUS = 80          # per word phoneme the brief chord holds
FOREIGN_PENALTY = 60       # per chord key none of the held phonemes explains
ORDER_PENALTY = 40         # per pair of held phonemes the chord reads in the wrong order
MAX_EVALUATED = 300        # family rewrites tried per stem
BRIEF_SCOPE_FAMILY = "family"
VERB_ENDING_MAX = 3        # a lemma and the verb it prefixes by at most this many letters are one family
LEMMA_MIN_LETTERS = 4


def bare(stroke: Stroke) -> frozenset[int]:
    """The stroke without the `*`/`#` marks."""
    return frozenset(k for k in stroke if k not in MARKS)


# --- pins ------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class PinnedBrief:
    """One row of `briefs.json`: the subject, its stem (empty for an expression) and the chord chosen for it."""
    subject: str
    kind: str                  # "word" | "expression"
    scope: str                 # "family" | "word"
    stem: Outline
    chord: Stroke
    reading: str = ""
    shared: int = 0
    foreign: int = 0
    cost: int = 0

    @property
    def units(self) -> tuple[str, ...]:
        return tuple(self.subject.split())


def loadPinnedBriefs(path: str, parse: Callable[[str], Outline]) -> list[PinnedBrief]:
    """The pinned briefs of `briefs.json`, in file order; `parse` reads an RTFCRE outline. Empty when the file is absent."""
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as handle:
        rows = json.load(handle)["briefs"]
    return [PinnedBrief(row["subject"], row["kind"], row["scope"], parse(row["stem"]) if row["stem"] else (),
                        parse(row["chord"])[0], row.get("reading", ""), row.get("shared", 0), row.get("foreign", 0),
                        row.get("cost", 0))
            for row in rows]


def pinnedRows(pins: Iterable[PinnedBrief], render: Callable[[Outline], str]) -> dict[str, Any]:
    """The JSON document of `briefs.json`."""
    return {"briefs": [{"subject": p.subject, "kind": p.kind, "scope": p.scope,
                        "stem": render(p.stem) if p.stem else "", "chord": render((p.chord,)),
                        "reading": p.reading, "shared": p.shared, "foreign": p.foreign, "cost": p.cost}
                       for p in pins]}


# --- families --------------------------------------------------------------------------------------------------------

class FamilyIndex:
    """The lemma families of a lexicon: the forms of a word's lemmas, and of the lemmas `related` to them."""

    def __init__(self, lexicon: Lexicon) -> None:
        self.formsOfLemma: dict[str, set[str]] = defaultdict(set)
        self.lemmasOf: dict[str, set[str]] = defaultdict(set)
        self.verbLemmas: set[str] = set()
        for (lemme, cgram), forms in lexicon.lemmaForms.items():
            self.formsOfLemma[lemme] |= forms
            if cgram in ("VER", "AUX"):
                self.verbLemmas.add(lemme)
            for form in forms:
                self.lemmasOf[form].add(lemme)

    def related(self, lemmas: set[str]) -> set[str]:
        """The lemmas, and the verb a lemma of 4 letters or more prefixes with an ending of at most 3 letters
        (travail, travailler; accord, accorder), or the reverse."""
        def pair(short: str, long: str) -> bool:
            return (len(short) >= LEMMA_MIN_LETTERS and long in self.verbLemmas and long.startswith(short)
                    and 0 < len(long) - len(short) <= VERB_ENDING_MAX)
        return {lemma for lemma in self.formsOfLemma
                if lemma in lemmas or any(pair(m, lemma) or pair(lemma, m) for m in lemmas)}

    def familyForms(self, word: str) -> set[str]:
        """`word` and every form of its related lemmas."""
        return {word} | {form for lemma in self.related(self.lemmasOf.get(word, set())) for form in self.formsOfLemma[lemma]}


# --- boundary risk ---------------------------------------------------------------------------------------------------

class BoundaryRisk:
    """The live outlines and, per stroke, how many live multi-stroke outlines X/C (X live: the word before C swallows
    it) or C/Y (Y live: C swallows the next word) it takes part in."""

    def __init__(self, live: Iterable[Outline]) -> None:
        self.live: set[Outline] = set(live)
        self.counts: dict[Stroke, int] = defaultdict(int)
        for outline in list(self.live):
            self._count(outline)

    def _count(self, outline: Outline) -> None:
        if len(outline) > 1:
            if outline[:-1] in self.live:
                self.counts[outline[-1]] += 1
            if outline[1:] in self.live:
                self.counts[outline[0]] += 1

    def add(self, outline: Outline) -> None:
        """A new outline becomes live (and counts for the next briefs)."""
        self._count(outline)
        self.live.add(outline)

    def of(self, stroke: Stroke) -> int:
        return self.counts.get(stroke, 0)


# --- stems and expansion ---------------------------------------------------------------------------------------------

def splitStroke(stroke: Stroke, coda: set[int]) -> tuple[frozenset[int], frozenset[int]]:
    """(onset and nucleus keys, coda keys) of a stroke, marks dropped."""
    keys = bare(stroke)
    return frozenset(k for k in keys if k not in coda), frozenset(k for k in keys if k in coda)


def prefixMatch(outline: Outline, target: Outline, k: int, coda: set[int]) -> bool:
    """`outline` starts with the stem of `target` of K strokes: strokes 1..K-1 equal (marks ignored) and the K-th with the
    same onset and nucleus."""
    return len(outline) >= k and all(bare(outline[i]) == bare(target[i]) for i in range(k - 1)) \
        and splitStroke(outline[k - 1], coda)[0] == splitStroke(target[k - 1], coda)[0]


def stemsOf(target: Outline, formOutlines: Iterable[Outline], coda: set[int]) -> set[tuple[int, frozenset[int]]]:
    """The stems (K, S_K) of a word, K >= 2: S_K is the K-th stroke's onset and nucleus plus all of its coda, or the part of
    the coda a family form shares."""
    stems: set[tuple[int, frozenset[int]]] = set()
    forms = list(formOutlines)
    for k in range(2, len(target) + 1):
        head, tail = splitStroke(target[k - 1], coda)
        stems.add((k, head | tail))
        for outline in forms:
            if prefixMatch(outline, target, k, coda):
                stems.add((k, head | (tail & splitStroke(outline[k - 1], coda)[1])))
    return stems


def expandBrief(forms: Mapping[str, list[Outline]], target: Outline, k: int, stemKeys: frozenset[int], brief: Stroke,
                coda: set[int], legal: Callable[[Stroke], bool],
                free: Callable[[str, Outline], bool] | None = None) -> dict[str, list[Outline]]:
    """The outlines the brief gives to each form that matches the stem: `brief` + extra coda keys + all marks of strokes
    1..K, then the tail strokes. Legal ones, and free ones when `free(form, outline)` is given."""
    out: dict[str, list[Outline]] = {}
    for form in sorted(forms):
        for outline in forms[form]:
            if not prefixMatch(outline, target, k, coda) or not stemKeys <= bare(outline[k - 1]):
                continue
            marks = {m for stroke in outline[:k] for m in stroke if m in MARKS}
            first = tuple(sorted(set(brief) | (bare(outline[k - 1]) - stemKeys) | marks))
            if not legal(first):
                continue
            new = (first,) + outline[k:]
            if free is None or free(form, new):
                out.setdefault(form, []).append(new)
    return out


# --- subjects --------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Subject:
    """What a brief is for: a word (its shortest outline) or an expression (its tokens' strokes concatenated)."""
    name: str
    kind: str                  # "word" | "expression"
    scope: str                 # "family" | "word"
    target: Outline
    phonemes: str
    freq: float = 0.0          # expressions only (words: the lexicon)


def wordSubject(word: str, scope: str, outlinesOf: Mapping[str, list[Outline]], lexicon: Lexicon) -> Subject:
    return Subject(word, "word", scope, min(outlinesOf[word], key=lambda o: (len(o), o)),
                   lexicon.syll.get(word, "").replace("-", ""))


def expressionSubject(units: tuple[str, ...], tokenStrokes: Iterable[Outline], lexicon: Lexicon, freq: float) -> Subject:
    target = tuple(stroke for strokes in tokenStrokes for stroke in strokes)
    phonemes = "".join(lexicon.syll.get(u, lexicon.syll.get(u.rstrip("'"), "")).replace("-", "") for u in units)
    return Subject(" ".join(units), "expression", "word", target, phonemes, freq)


@dataclass
class Derived:
    """A brief the generator chose or validated: its chord, stem and the outlines it gives."""
    subject: Subject
    k: int
    stemKeys: frozenset[int]
    chord: Stroke
    news: dict[str, list[Outline]]
    reading: str = ""
    shared: int = 0
    foreign: int = 0
    cost: int = 0
    risk: int = 0
    gain: float = 0.0

    def stem(self) -> Outline:
        """The stem as an outline (empty for an expression)."""
        if self.subject.kind == "expression":
            return ()
        return tuple(tuple(sorted(bare(s))) for s in self.subject.target[:self.k - 1]) + (tuple(sorted(self.stemKeys)),)

    def pin(self) -> PinnedBrief:
        return PinnedBrief(self.subject.name, self.subject.kind, self.subject.scope, self.stem(), self.chord,
                           self.reading, self.shared, self.foreign, self.cost)


# --- the generator ---------------------------------------------------------------------------------------------------

@dataclass
class BriefInputs:
    """The theory the briefs are made against (loaded by `util/build_briefs.py`)."""
    board: Starboard
    ctx: SimContext                              # finalOutlines: the canonical live outlines of the dictionary
    render: Callable[[Outline], str]
    lexicon: Lexicon
    outlinesOf: dict[str, list[Outline]]         # spelling (lower-cased) -> its theory outlines
    owner: dict[str, set[str]]                   # live outline text (dictionary and affix abbreviations) -> spellings
    reserved: Mapping[str, str]                  # reserved chord text -> source (its own `brief` source left out)
    mergeChords: set[Stroke]                     # the one-stroke chords an attach merge can write
    liveOutlines: Iterable[Outline] = ()         # dictionary and affix abbreviation outlines, for the boundary risk
    common: set[str] | None = None               # the words the saving counts (default: every word with an outline)
    strokesNow: dict[str, int] | None = None     # spelling -> strokes of its shortest form today (default: the dictionary's)


class BriefGenerator:
    """Derives or validates briefs one after the other; each accepted brief takes its outlines for the next ones."""

    def __init__(self, inputs: BriefInputs) -> None:
        self.inputs = inputs
        self.board = inputs.board
        self.render = inputs.render
        self.lexicon = inputs.lexicon
        self.outlinesOf = inputs.outlinesOf
        self.coda = set(self.board.keyIDinSyllabicPart["coda"])
        self.families = FamilyIndex(inputs.lexicon)
        self.risk = BoundaryRisk(set(inputs.ctx.finalOutlines) | set(inputs.liveOutlines))
        self.takenNew: dict[str, str] = {}               # new outline text -> its subject
        self.coveredBy: dict[str, str] = {}              # form -> the word whose family brief gave it an outline
        self.strokesNow: dict[str, int] = dict(inputs.strokesNow) if inputs.strokesNow is not None else {
            w: min(len(o) for o in outs) for w, outs in inputs.outlinesOf.items()}
        self.freq: dict[str, float] = dict(inputs.lexicon.freq)
        self.common: set[str] = set(inputs.common) if inputs.common is not None else {
            w for w in inputs.lexicon.freq if w in inputs.outlinesOf}
        self.ctx = inputs.ctx
        freeChords = sorted(enumerateKeypresses(self.board, self.ctx), key=lambda c: (len(c), c))
        self.allChords: list[Stroke] = [tuple(sorted(c + tuple(m))) for c in freeChords for m in MARK_SETS]
        self.phonemeStrokes: dict[str, list[frozenset[int]]] = defaultdict(list)
        for strokeKeys, phonemes in self.board.phonemesAssignedToStroke.items():
            for phoneme in phonemes:
                self.phonemeStrokes[phoneme].append(frozenset(strokeKeys))

    # --- legality and freedom

    def legal(self, stroke: Stroke) -> bool:
        syllabic = tuple(k for k in stroke if k not in MARKS)
        return bool(syllabic) and self.ctx.isLegal(syllabic)

    def free(self, outline: Outline, subject: str) -> bool:
        """The outline is no other word's live outline, no earlier brief's, and (one stroke) no reserved or merge chord."""
        text = self.render(outline)
        if text in self.takenNew and self.takenNew[text] != subject:
            return False
        if self.inputs.owner.get(text, {subject}) - {subject}:
            return False
        if len(outline) == 1 and (text in self.inputs.reserved or outline[0] in self.inputs.mergeChords):
            return False
        return True

    def chordFree(self, chord: Stroke) -> bool:
        """The bare chord may be a brief: not taken, reserved, an attach-merge chord, nor a live one-stroke outline."""
        text = self.render((chord,))
        return text not in self.takenNew and text not in self.inputs.reserved and chord not in self.inputs.mergeChords \
            and (chord,) not in self.ctx.finalOutlines

    # --- the forms of a subject

    def formOutlines(self, subject: Subject) -> dict[str, list[Outline]]:
        if subject.kind == "expression":
            return {}
        words = self.families.familyForms(subject.name) if subject.scope == "family" else {subject.name}
        return {f: self.outlinesOf[f] for f in words
                if f in self.outlinesOf and (f == subject.name or f not in self.coveredBy)}

    def rewrite(self, subject: Subject, forms: Mapping[str, list[Outline]], k: int, stemKeys: frozenset[int],
                chord: Stroke) -> dict[str, list[Outline]]:
        """The outlines the chord gives the subject's forms; two forms on one outline: the more frequent keeps it."""
        if subject.kind == "expression":
            return {subject.name: [(chord,)]} if self.free((chord,), subject.name) else {}
        out = expandBrief(forms, subject.target, k, stemKeys, chord, self.coda, self.legal,
                          lambda form, outline: self.free(outline, form))
        seen: dict[Outline, str] = {}
        for form in sorted(out, key=lambda f: -self.freq.get(f, 0.0)):
            out[form] = [o for o in out[form] if seen.setdefault(o, form) == form]
        return {form: outs for form, outs in out.items() if outs}

    def saving(self, news: Mapping[str, list[Outline]]) -> float:
        return sum(self.freq.get(f, 0.0) * max(0, self.strokesNow.get(f, 99) - min(len(o) for o in outs))
                   for f, outs in news.items() if f in self.common)

    def riskOf(self, chord: Stroke, news: Mapping[str, list[Outline]]) -> int:
        return self.risk.of(chord) + sum(self.risk.of(o[0]) for outs in news.values() for o in outs
                                         if len(o) == 1 and o[0] != chord)

    # --- scoring

    def phonemeMatch(self, chord: Stroke, phonemes: str) -> tuple[int, int, int, str]:
        """(phonemes held, keys explained, -order inversions, the phonemes held): the chord's syllabic keys matched to the
        word's phoneme occurrences as DISJOINT phoneme strokes (one key never reads as two phonemes). A pair of held
        phonemes is inverted when the chord's steno order (its lowest key) reads them against the word's order."""
        syllabic = frozenset(chord) - MARKS
        options = [[st for st in self.phonemeStrokes.get(ph, ()) if st <= syllabic] for ph in phonemes]
        best: tuple[int, int, int, str] = (0, 0, 0, "")

        def search(i: int, used: frozenset[int], matched: tuple[tuple[int, str], ...]) -> None:
            nonlocal best
            if i == len(options):
                inversions = sum(1 for a in range(len(matched)) for b in range(a + 1, len(matched))
                                 if matched[a][0] > matched[b][0])
                best = max(best, (len(matched), len(used), -inversions, "".join(p for _k, p in matched)))
                return
            for st in options[i]:
                if not st & used:
                    search(i + 1, used | st, matched + ((min(st), phonemes[i]),))
            search(i + 1, used, matched)

        search(0, frozenset(), ())
        return best

    def chordScore(self, chord: Stroke, phonemes: str) -> tuple[float, int, int, int, str]:
        """(score, shared, foreign, cost, reading); low is good: cost - bonus per phoneme held + penalty per foreign key
        + penalty per inversion."""
        shared, explained, negInversions, reading = self.phonemeMatch(chord, phonemes)
        foreign = len(frozenset(chord) - MARKS) - explained
        cost = self.board.getChordCost(chord) or 999
        return (cost - SHARED_BONUS * shared + FOREIGN_PENALTY * foreign - ORDER_PENALTY * negInversions,
                shared, foreign, cost, reading)

    # --- derivation

    def derive(self, subject: Subject) -> Derived | None:
        """Search the best brief for `subject` and accept it; None when it is covered by an earlier family brief or nothing fits."""
        if self.coveredBy.get(subject.name, subject.name) != subject.name:
            return None
        forms = self.formOutlines(subject)
        target = subject.target
        if subject.kind == "expression":
            stems: set[tuple[int, frozenset[int]]] = {(len(target), frozenset())}
            self.strokesNow[subject.name] = len(target)
            self.freq[subject.name] = subject.freq
            self.common.add(subject.name)
        else:
            stems = stemsOf(target, (o for outs in forms.values() for o in outs), self.coda)
        scores: dict[Stroke, tuple[float, int, int, int, str]] = {}

        def score(chord: Stroke) -> tuple[float, int, int, int, str]:
            if chord not in scores:
                scores[chord] = self.chordScore(chord, subject.phonemes)
            return scores[chord]

        ranked = sorted((c for c in self.allChords if self.chordFree(c)),
                        key=lambda c: (self.risk.of(c) > 0, score(c)[1] == 0, score(c)[0], c))

        def potential(k: int, stemKeys: frozenset[int]) -> float:
            """The saving if every form matching the stem got its outline (no chord constraint)."""
            if subject.kind == "expression":
                return subject.freq * max(0, len(target) - 1)
            total = 0.0
            for form, outs in forms.items():
                if form not in self.common:
                    continue
                lengths = [len(o) - k + 1 for o in outs if prefixMatch(o, target, k, self.coda)
                           and stemKeys <= bare(o[k - 1])]
                if lengths:
                    total += self.freq.get(form, 0.0) * max(0, self.strokesNow.get(form, 99) - min(lengths))
            return total

        found: list[tuple[float, int, int, frozenset[int], Stroke, dict[str, list[Outline]]]] = []
        for k, stemKeys in sorted(stems, key=lambda s: (-s[0], -len(s[1]))):
            goal = GOOD_ENOUGH * potential(k, stemKeys)
            evaluated = 0
            for chord in ranked:
                news = self.rewrite(subject, forms, k, stemKeys, chord)
                if subject.name not in news:
                    continue
                found.append((self.saving(news), self.riskOf(chord, news), k, stemKeys, chord, news))
                evaluated += 1
                if (found[-1][1] == 0 and found[-1][0] >= goal) or evaluated >= MAX_EVALUATED:
                    break
        if not found:
            return None
        pool = [c for c in found if c[1] == 0] or found
        top = max(c[0] for c in pool)
        good = [c for c in pool if c[0] >= GOOD_ENOUGH * top]
        gain, risk, k, stemKeys, chord, news = min(good, key=lambda c: (score(c[4])[1] == 0, score(c[4])[0], -c[2], c[4]))
        _s, shared, foreign, cost, reading = score(chord)
        derived = Derived(subject, k, stemKeys, chord, news, reading, shared, foreign, cost, risk, gain)
        self.accept(derived)
        return derived

    def check(self, pin: PinnedBrief, subject: Subject) -> tuple[Derived | None, str]:
        """Validate a pin against the current theory: (the brief accepted, \"\") or (None, why it is invalid)."""
        if self.coveredBy.get(subject.name, subject.name) != subject.name:
            return None, f"covered by the family brief of {self.coveredBy[subject.name]}"
        chord = pin.chord
        if not self.legal(chord):
            return None, "the chord is no longer legal"
        if not self.chordFree(chord):
            return None, f"the chord {self.render((chord,))} is taken"
        forms = self.formOutlines(subject)
        if subject.kind == "expression":
            self.strokesNow[subject.name] = len(subject.target)
            self.freq[subject.name] = subject.freq
            self.common.add(subject.name)
            k, stemKeys = len(subject.target), frozenset[int]()
        else:
            if not pin.stem:
                return None, "the pin has no stem"
            k, stemKeys = len(pin.stem), bare(pin.stem[-1])
        news = self.rewrite(subject, forms, k, stemKeys, chord)
        if subject.name not in news:
            return None, "the chord gives the subject no free outline"
        risk = self.riskOf(chord, news)
        if risk:
            return None, f"boundary risk {risk}"
        _s, shared, foreign, cost, reading = self.chordScore(chord, subject.phonemes)
        derived = Derived(subject, k, stemKeys, chord, news, reading, shared, foreign, cost, 0, self.saving(news))
        self.accept(derived)
        return derived, ""

    def pairs(self, derived: Derived) -> list[tuple[str, Outline, Outline]]:
        """(form, its outline today, the outline the brief gives it) for every outline the brief gives."""
        out: list[tuple[str, Outline, Outline]] = []
        for form, news in derived.news.items():
            for old in self.outlinesOf[form]:
                expanded = expandBrief({form: [old]}, derived.subject.target, derived.k, derived.stemKeys, derived.chord,
                                       self.coda, self.legal)
                out.extend((form, old, new) for new in expanded.get(form, []) if new in news)
        return out

    def accept(self, derived: Derived) -> None:
        """The brief takes its chord and outlines: later briefs see them as taken, live, and part of the boundary risk."""
        self.takenNew[self.render((derived.chord,))] = derived.subject.name      # a stem brief's bare chord too
        for form, outs in derived.news.items():
            for outline in outs:
                self.takenNew[self.render(outline)] = form
                self.risk.add(outline)
            self.coveredBy.setdefault(form, derived.subject.name)
            self.strokesNow[form] = min(self.strokesNow.get(form, 99), min(len(o) for o in outs))
