"""
Metrics that compare two steno theories over one word universe (Stenalgo on the Starboard against Pluvier on the Ireland
layout). Pure functions and small dataclasses; the only I/O are the three loaders at the top (Lexique383, a Stenalgo or Pluvier
dictionary and its collision record). `util/compare_theories.py` is the command line around it.

Word universe and frequencies: the Lexique383 spellings (lower-cased), the frequency of a spelling is the SUM of its rows'
`freqfilms2` (or `freqlivres`). Every mean is frequency-weighted, `sum(x*f)/sum(f)`.

A theory is seen as `word -> outlines` (an outline is the `/`-joined text of its chords). The word's outline is the CHOSEN one,
the cheapest: fewest strokes, ties broken by the Starboard cost of the chords (unpriceable last), then by text.

Choices where the plan was silent:
- Pluvier's `dicofr.json` is outline -> winning word; `dup.json` is outline -> every word that claimed it. A chosen outline
  collides when more than one word claims it. Words that appear only in the collision record (they lost every outline) are
  not covered; they are counted and reported separately.
- Stenalgo's collisions are measured: the dictionary entries are grouped by the parsed key ids of their outline, so two
  spellings of one chord sequence, or a duplicate JSON key, are found, not assumed away.
- The phoneme order metric works on the Lexique383 `syll` column of the best-frequency row of a spelling (homographs with
  several pronunciations: the most frequent row). A violation is a pair of consecutive phonemes of one syllable whose
  exclusive keys (shared keys are dropped) are not in left-to-right order. Stenalgo's keys come from the layout
  (`getStrokesOfPhoneme(...)[0]`), Pluvier's from the phoneme table `resources/pluvierPhonemeKeys.tsv` (a simple per-syllable
  encoding: diphthongs, then pairs, then single phonemes; the Pluvier `CHUNKS` exceptions are not reproduced). A syllable with
  a phoneme missing from the table is unencodable and the word is excluded from that average; the unencodable share and the
  share of words whose table encoding equals one of their `dicofr.json` outlines are reported.
"""
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

from src.grammar import Phoneme
from src.irelandkeyboard import KEYS as IRELAND_KEYS
from src.irelandkeyboard import parseChord, renderChord
from src.keyboard import Starboard

NUCLEUS = Phoneme.nucleusPhonemes
CostFn = Callable[[str], int | None]


# --- loaders --------------------------------------------------------------------------------------------------------------

@dataclass
class Lexicon:
    freq: dict[str, float]                 # lower-cased spelling -> summed frequency (0.0 allowed)
    syll: dict[str, str]                   # spelling -> `syll` of its most frequent row
    lemmaForms: dict[tuple[str, str], set[str]] = field(default_factory=dict)   # (lemme, cgram) -> spellings
    lemmaFreq: dict[tuple[str, str], float] = field(default_factory=dict)       # (lemme, cgram) -> lemma frequency (max over rows)
    tenseForms: dict[str, set[str]] = field(default_factory=dict)               # tense key -> spellings (VER and AUX rows)
    featureForms: dict[str, set[str]] = field(default_factory=dict)             # FEATURES key -> spellings
    featureFreq: dict[str, dict[str, float]] = field(default_factory=dict)      # TENSES/FEATURES key -> spelling -> summed
                                                                                # frequency of the rows carrying the key
    featureFreqSplit: dict[str, dict[str, float]] = field(default_factory=dict) # the same, each VER/AUX row split equally
                                                                                # over its `infover` readings


TENSES = ("ind:pre", "ind:imp", "ind:pas", "ind:fut", "cnd:pre", "sub:pre", "sub:imp", "imp:pre", "inf", "par:pre", "par:pas")
# The other features the conjugation, gender and number keypress groups discriminate: person and its number from the
# VER/AUX `infover` (third field, `1s`..`3p`), gender and number from the `genre`/`nombre` columns of every category.
FEATURES = ("pers:1", "pers:2", "pers:3", "nbr:s", "nbr:p", "genre:m", "genre:f", "nombre:s", "nombre:p")


def personKeys(infover: str) -> set[str]:
    """The person and person-number keys of a Lexique `infover` field (`ind:pre:3s` gives `pers:3`, `nbr:s`)."""
    keys: set[str] = set()
    for entry in infover.split(";"):
        fields = entry.strip().split(":")
        if len(fields) == 3 and len(fields[2]) == 2 and fields[2][0] in "123" and fields[2][1] in "sp":
            keys |= {"pers:" + fields[2][0], "nbr:" + fields[2][1]}
    return keys


def tenseKeys(infover: str) -> set[str]:
    """The tense keys of a Lexique `infover` field: the first two `:`-fields of each `;`-separated entry (`inf` alone)."""
    keys: set[str] = set()
    for entry in infover.split(";"):
        entry = entry.strip()
        if entry:
            keys.add("inf" if entry == "inf" else ":".join(entry.split(":")[:2]))
    return keys


def loadLexicon(path: str, freq: str = "films") -> Lexicon:
    column = {"films": "freqfilms2", "livres": "freqlivres"}[freq]
    lemmaColumn = {"films": "freqlemfilms2", "livres": "freqlemlivres"}[freq]
    lemmaForms: dict[tuple[str, str], set[str]] = defaultdict(set)
    lemmaFreq: dict[tuple[str, str], float] = {}
    tenseForms: dict[str, set[str]] = defaultdict(set)
    featureForms: dict[str, set[str]] = defaultdict(set)
    featureFreq: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    featureFreqSplit: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    sums: dict[str, float] = defaultdict(float)
    best: dict[str, tuple[float, str]] = {}
    with open(path, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE):
            word = row["ortho"].lower()
            value = float(row[column] or 0.0)
            sums[word] += value
            if word not in best or value > best[word][0]:
                best[word] = (value, row["syll"])
            lemma = (row.get("lemme", "").lower(), row.get("cgram", ""))
            if lemma[0]:
                lemmaForms[lemma].add(word)
                lemmaFreq[lemma] = max(lemmaFreq.get(lemma, 0.0), float(row.get(lemmaColumn) or 0.0))
            if lemma[1] in ("VER", "AUX"):
                infover = row.get("infover", "")
                for key in tenseKeys(infover):
                    tenseForms[key].add(word)
                    featureFreq[key][word] += value
                for key in personKeys(infover):
                    featureForms[key].add(word)
                    featureFreq[key][word] += value
                readings = [entry.strip() for entry in infover.split(";") if entry.strip()]
                for entry in readings:
                    for key in tenseKeys(entry) | personKeys(entry):
                        featureFreqSplit[key][word] += value / len(readings)
            for inflection in ("genre", "nombre"):
                if row.get(inflection) in ("m", "f", "s", "p"):
                    key = f"{inflection}:{row[inflection]}"
                    featureForms[key].add(word)
                    featureFreq[key][word] += value
                    featureFreqSplit[key][word] += value
    return Lexicon(dict(sums), {w: s for w, (_, s) in best.items()}, dict(lemmaForms), lemmaFreq, dict(tenseForms),
                   dict(featureForms), {key: dict(words) for key, words in featureFreq.items()},
                   {key: dict(words) for key, words in featureFreqSplit.items()})


@dataclass
class TheoryView:
    """A theory as `word -> outlines`, with the words sharing an outline."""
    name: str
    outlines: dict[str, list[str]]
    claimants: dict[str, frozenset[str]] = field(default_factory=dict)      # outline text -> its claimants (> 1 only)
    lostWords: set[str] = field(default_factory=set)                        # claimed outlines only, none of their own
    chosen: dict[str, str] = field(default_factory=dict)
    notes: dict[str, Any] = field(default_factory=dict)

    def choose(self, strokeCost: CostFn) -> None:
        """Pick each word's cheapest outline: fewest strokes, then Starboard cost, then text."""
        def key(text: str) -> tuple[int, int, str]:
            costs = [strokeCost(s) for s in text.split("/")]
            total = 10**9 if any(c is None for c in costs) else sum(c for c in costs if c is not None)
            return (len(costs), total, text)
        self.chosen = {w: min(texts, key=key) for w, texts in self.outlines.items()}


def longForm(view: TheoryView, strokeCost: CostFn) -> TheoryView:
    """A copy of `view` whose chosen outline is the LONGEST one of each word (most strokes, then cheapest by cost, then text):
    the full spelling-out, where `choose` takes the briefest. A word with one outline has the same long and short form."""
    def key(text: str) -> tuple[int, int, str]:
        costs = [strokeCost(s) for s in text.split("/")]
        total = 10**9 if any(c is None for c in costs) else sum(c for c in costs if c is not None)
        return (-len(costs), total, text)
    return TheoryView(view.name + "Long", view.outlines, view.claimants, view.lostWords,
                      {w: min(texts, key=key) for w, texts in view.outlines.items()}, dict(view.notes))


def loadStenalgoTheory(path: str, parse: Callable[[str], tuple[tuple[int, ...], ...] | None]) -> TheoryView:
    """The Plover dictionary of Stenalgo (outline -> spelling). `parse` gives the key ids of an outline text."""
    duplicates = 0

    def pairs(items: list[tuple[str, str]]) -> dict[str, str]:
        nonlocal duplicates
        out: dict[str, str] = {}
        for k, v in items:
            if k in out:
                duplicates += 1
            out[k] = v
        return out

    with open(path, encoding="utf-8") as handle:
        entries: dict[str, str] = json.load(handle, object_pairs_hook=pairs)
    return buildStenalgoView(entries, parse, duplicates)


def buildStenalgoView(entries: dict[str, str], parse: Callable[[str], tuple[tuple[int, ...], ...] | None],
                      duplicates: int = 0) -> TheoryView:
    outlines: dict[str, set[str]] = defaultdict(set)
    byKeys: dict[tuple[tuple[int, ...], ...], dict[str, str]] = defaultdict(dict)    # key ids -> {text: word}
    unparsable = 0
    for text, spelling in entries.items():
        word = spelling.lower()
        outlines[word].add(text)
        keys = parse(text)
        if keys is None:
            unparsable += 1
        else:
            byKeys[keys][text] = word
    claimants: dict[str, frozenset[str]] = {}
    for texts in byKeys.values():
        words = frozenset(texts.values())
        if len(texts) > 1 and len(words) > 1:
            for text in texts:
                claimants[text] = words
    return TheoryView("stenalgo", {w: sorted(t) for w, t in outlines.items()}, claimants, set(), {},
                      {"entries": len(entries), "duplicateJsonKeys": duplicates, "unparsableOutlines": unparsable})


def loadAbbreviations(path: str) -> dict[str, set[str]]:
    """`affix_abbreviations.tsv` (S9b) -> spelling (lower-cased) -> its short outlines (all routes)."""
    shorts: dict[str, set[str]] = defaultdict(set)
    with open(path, encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            shorts[row["spelling"].lower()].add(row["short"])
    return dict(shorts)


def withAbbreviations(view: TheoryView, shorts: dict[str, set[str]]) -> TheoryView:
    """A copy of `view` whose words also own their short outlines (`choose` then picks the cheapest of both forms)."""
    outlines = {w: sorted(set(texts) | shorts.get(w, set())) for w, texts in view.outlines.items()}
    return TheoryView(view.name + "Short", outlines, view.claimants, view.lostWords, {}, dict(view.notes))


def loadPluvierTheory(dictPaths: str | list[str], dupPath: str | None = None) -> TheoryView:
    """Pluvier as the layers of `dictPaths` (outline -> word JSON files, LOWEST priority first: a later file takes an outline
    from an earlier one) plus the generator's collision record `dupPath` (outline -> every word that claimed it)."""
    paths = [dictPaths] if isinstance(dictPaths, str) else dictPaths
    layers: list[dict[str, str]] = []
    for path in paths:
        with open(path, encoding="utf-8") as handle:
            layers.append(json.load(handle))
    dup: dict[str, list[str]] = {}
    if dupPath is not None:
        with open(dupPath, encoding="utf-8") as handle:
            dup = json.load(handle)
    return buildLayeredView(layers, dup)


def buildPluvierView(dicofr: dict[str, str], dup: dict[str, list[str]]) -> TheoryView:
    """Pluvier as the single dictionary `dicofr` and its collision record."""
    return buildLayeredView([dicofr], dup)


def buildLayeredView(layers: list[dict[str, str]], dup: dict[str, list[str]]) -> TheoryView:
    """Several outline -> word dictionaries applied in order (later layers win an outline, like Pluvier's `append_tao`, or
    a Plover dictionary list read from the bottom). The word that loses an outline to another word, and every word
    of the collision record `dup`, are CLAIMANTS of that outline together with its final owner; a word that has no outline
    left but is a claimant is lost (not covered)."""
    owner: dict[str, str] = {}
    displaced: dict[str, set[str]] = defaultdict(set)
    for layer in layers:
        for text, word in layer.items():
            previous = owner.get(text)
            if previous is not None and previous != word.lower():
                displaced[text].add(previous)
            owner[text] = word.lower()
    outlines: dict[str, set[str]] = defaultdict(set)
    for text, word in owner.items():
        outlines[word].add(text)
    claimants: dict[str, frozenset[str]] = {}
    claimedWords: set[str] = set()
    for text in sorted(set(dup) | set(displaced)):
        group = {w.lower() for w in dup.get(text, [])} | displaced.get(text, set())
        if text in owner:
            group.add(owner[text])
        claimedWords |= group
        if len(group) > 1:
            claimants[text] = frozenset(group)
    lost = claimedWords - set(outlines)
    return TheoryView("pluvier", {w: sorted(t) for w, t in outlines.items()}, claimants, lost, {},
                      {"entries": sum(len(layer) for layer in layers), "layerEntries": [len(layer) for layer in layers],
                       "collisionOutlines": len(dup), "outlinesTakenByAnotherLayer": sum(len(v) for v in displaced.values())})


# --- helpers --------------------------------------------------------------------------------------------------------------

def share(part: float, whole: float) -> float | None:
    return part / whole if whole else None


def weightedMean(values: dict[str, float], freq: dict[str, float], words: Iterable[str]) -> float | None:
    # exact sums over sorted words: the result must not depend on set iteration order
    kept = sorted(w for w in set(words) if w in values)
    num = math.fsum(values[w] * freq.get(w, 0.0) for w in kept)
    den = math.fsum(freq.get(w, 0.0) for w in kept)
    return num / den if den else None


def mass(freq: dict[str, float], words: Iterable[str]) -> float:
    return math.fsum(freq.get(w, 0.0) for w in sorted(set(words)))


# --- coverage -------------------------------------------------------------------------------------------------------------

def coverage(freq: dict[str, float], a: TheoryView, b: TheoryView) -> dict[str, Any]:
    """Counts and frequency mass of the universe covered by each theory, by both, and by one only."""
    universe = set(freq)
    total = mass(freq, universe)
    setA, setB = set(a.outlines) & universe, set(b.outlines) & universe

    def block(words: set[str]) -> dict[str, Any]:
        return {"spellings": len(words), "withFrequency": sum(1 for w in words if freq[w] > 0),
                "frequencyShare": share(mass(freq, words), total)}

    return {
        "universe": block(universe),
        a.name: block(setA), b.name: block(setB), "both": block(setA & setB),
        a.name + "Only": block(setA - setB), b.name + "Only": block(setB - setA),
        "neither": block(universe - setA - setB),
        "outsideUniverse": {a.name: len(set(a.outlines) - universe), b.name: len(set(b.outlines) - universe)},
        "lostToCollisionsOnly": {b.name: block(b.lostWords & universe - setB)} if b.lostWords else {},
    }


def lemmaCoverage(lexicon: Lexicon, a: TheoryView, b: TheoryView) -> dict[str, Any]:
    """Lemmas (lemme, cgram) with some / all of their forms in each theory, counted and weighted by lemma frequency."""
    lemmas = sorted(lexicon.lemmaForms)
    weight = {lemma: lexicon.lemmaFreq.get(lemma, 0.0) for lemma in lemmas}
    total = math.fsum(weight[lemma] for lemma in lemmas)

    def block(view: TheoryView) -> dict[str, Any]:
        some = [lemma for lemma in lemmas if any(w in view.outlines for w in lexicon.lemmaForms[lemma])]
        full = [lemma for lemma in lemmas if all(w in view.outlines for w in lexicon.lemmaForms[lemma])]
        return {"lemmas": len(lemmas),
                "someFormCovered": {"lemmas": len(some), "frequencyShare": share(math.fsum(weight[x] for x in some), total)},
                "allFormsCovered": {"lemmas": len(full), "frequencyShare": share(math.fsum(weight[x] for x in full), total)}}

    return {"lemmas": len(lemmas), a.name: block(a), b.name: block(b)}


def verbCoverageByTense(lexicon: Lexicon, a: TheoryView, b: TheoryView) -> dict[str, Any]:
    """Per verb tense: the forms listed in it, and the count and frequency share covered by each theory (a form weighs the
    frequency of its VER/AUX rows in that tense, as in `coverageByFeature`)."""
    out: dict[str, Any] = {}
    for tense in TENSES:
        forms = lexicon.tenseForms.get(tense, set())
        weights = lexicon.featureFreq.get(tense, {})
        total = mass(weights, forms)
        row: dict[str, Any] = {"forms": len(forms)}
        for view in (a, b):
            covered = {w for w in forms if w in view.outlines}
            row[view.name] = {"forms": len(covered), "frequencyShare": share(mass(weights, covered), total)}
        out[tense] = row
    return out


def coverageByFeature(lexicon: Lexicon, a: TheoryView, b: TheoryView) -> dict[str, Any]:
    """Per tense (TENSES) and per other feature (FEATURES): the forms carrying it, and for each theory the covered forms and
    the covered forms whose chosen outline is claimed by another word (colliding), each with its share of the feature's
    frequency. A form weighs the frequency of its rows carrying the feature only (the VER row of `y`, not its pronoun row).
    A row with several readings (`mange` ind:pre:1s;ind:pre:3s;sub:pre:1s) weighs its whole frequency in each (the
    `...Share` keys, an upper bound) or an equal part in each (the `...ShareSplit` keys)."""
    out: dict[str, Any] = {}
    for key in TENSES + FEATURES:
        weights = lexicon.featureFreq.get(key, {})
        split = lexicon.featureFreqSplit.get(key, {})
        forms = set(weights)
        total, totalSplit = mass(weights, forms), mass(split, forms)
        row: dict[str, Any] = {"forms": len(forms)}
        for view in (a, b):
            covered = {w for w in forms if w in view.outlines}
            colliding = {w for w in covered if view.chosen.get(w) in view.claimants}
            row[view.name] = {"forms": len(covered), "frequencyShare": share(mass(weights, covered), total),
                              "frequencyShareSplit": share(mass(split, covered), totalSplit),
                              "colliding": len(colliding), "collidingFrequencyShare": share(mass(weights, colliding), total),
                              "collidingFrequencyShareSplit": share(mass(split, colliding), totalSplit)}
        out[key] = row
    return out


# --- collisions -----------------------------------------------------------------------------------------------------------

def collisions(view: TheoryView, freq: dict[str, float], common: set[str]) -> dict[str, Any]:
    """The common words whose chosen outline is claimed by another word."""
    total = mass(freq, common)
    hit = {w for w in common if view.chosen.get(w) in view.claimants}
    groups = {view.claimants[view.chosen[w]] for w in hit}
    closed = {w for w in hit if view.claimants[view.chosen[w]] <= common}
    losers = {x for g in groups for x in g if x in freq} - {w for w in hit}
    return {"wordsColliding": len(hit), "wordsCollidingShare": share(len(hit), len(common)),
            "frequencyShare": share(mass(freq, hit), total), "groups": len(groups),
            "wordsInGroupsFullyCommon": len(closed),
            "otherClaimantsInUniverse": len(losers),
            "otherClaimantsFrequencyShare": share(mass(freq, losers), mass(freq, set(freq)))}


def markedForResolution(view: TheoryView, freq: dict[str, float], words: set[str], rule: str) -> set[str]:
    """The words of `words` that would need one more stroke for their chosen outline to be theirs alone. `rule`
    `winnerKeeps`: in every group sharing a chosen outline the most frequent claimant (ties: first in alphabetical order)
    keeps the outline and the others are marked; `everyClaimant`: every word of such a group is marked (an upper bound)."""
    groups: dict[str, list[str]] = defaultdict(list)
    for w in sorted(words):
        text = view.chosen.get(w)
        if text is not None and text in view.claimants:
            groups[text].append(w)
    marked: set[str] = set()
    for text, group in groups.items():
        if rule == "everyClaimant":
            marked.update(group)
        else:
            keeper = min(view.claimants[text], key=lambda c: (-freq.get(c, 0.0), c))
            marked.update(w for w in group if w != keeper)
    return marked


def strokesPerWordResolved(view: TheoryView, freq: dict[str, float], words: set[str], marked: set[str]) -> float | None:
    """`strokesPerWord` with one more stroke on every marked word."""
    return weightedMean({w: float(len(view.chosen[w].split("/")) + (1 if w in marked else 0))
                         for w in words if w in view.chosen}, freq, words)


def costsResolved(costs: dict[str, int | None], marked: set[str], extraStrokeCost: int) -> dict[str, int | None]:
    """`outlineCosts` with the cost of one more (cheap) stroke on every marked word."""
    return {w: (c + extraStrokeCost if c is not None and w in marked else c) for w, c in costs.items()}


# --- strokes and complexity -----------------------------------------------------------------------------------------------

def strokesPerWord(view: TheoryView, freq: dict[str, float], words: set[str]) -> float | None:
    return weightedMean({w: float(len(view.chosen[w].split("/"))) for w in words if w in view.chosen}, freq, words)


def outlineCosts(view: TheoryView, strokeCost: CostFn, words: Iterable[str]) -> dict[str, int | None]:
    """Word -> summed cost of its chosen outline, None when a chord cannot be priced."""
    result: dict[str, int | None] = {}
    for w in words:
        costs = [strokeCost(s) for s in view.chosen[w].split("/")]
        result[w] = None if any(c is None for c in costs) else sum(c for c in costs if c is not None)
    return result


def complexity(costs: dict[str, int | None], freq: dict[str, float], words: set[str]) -> dict[str, Any]:
    """Weighted mean cost over the priceable words, and the share that is not priceable."""
    priced = {w: float(c) for w, c in costs.items() if c is not None and w in words}
    unpriced = {w for w in words if costs.get(w) is None}
    total = mass(freq, words)
    return {"meanCost": weightedMean(priced, freq, words), "pricedWords": len(priced), "unpricedWords": len(unpriced),
            "unpricedFrequencyShare": share(mass(freq, unpriced), total)}


def complexityBoth(costsA: dict[str, int | None], costsB: dict[str, int | None], freq: dict[str, float],
                   words: set[str]) -> dict[str, Any]:
    """Mean costs restricted to the words priceable in both."""
    both = {w for w in words if costsA.get(w) is not None and costsB.get(w) is not None}
    return {"words": len(both),
            "meanA": weightedMean({w: float(c) for w, c in costsA.items() if c is not None and w in both}, freq, both),
            "meanB": weightedMean({w: float(c) for w, c in costsB.items() if c is not None and w in both}, freq, both)}


# --- phoneme order --------------------------------------------------------------------------------------------------------

def countViolations(groups: list[tuple[int, ...]]) -> int:
    """Consecutive phoneme key groups (positions in chord order) whose exclusive keys are not left to right."""
    count = 0
    for p, q in zip(groups, groups[1:]):
        exclP, exclQ = set(p) - set(q), set(q) - set(p)
        if exclP and exclQ and max(exclP) > min(exclQ):
            count += 1
    return count


def splitSyllable(syllable: str) -> dict[str, list[str]]:
    """Onset / nucleus / coda phonemes of one syllable: consonants before the first vowel, the vowels, the rest."""
    parts: dict[str, list[str]] = {"onset": [], "nucleus": [], "coda": []}
    seen = False
    for ph in syllable:
        if ph in NUCLEUS:
            parts["nucleus"].append(ph)
            seen = True
        else:
            parts["coda" if seen else "onset"].append(ph)
    return parts


def starboardGroups(board: Starboard, syllable: str) -> list[tuple[int, ...]] | None:
    """The key group of every phoneme of a syllable on the Starboard layout, None when a phoneme has no key."""
    groups: list[tuple[int, ...]] = []
    for part, phonemes in splitSyllable(syllable).items():
        for ph in phonemes:
            strokes = board.getStrokesOfPhoneme(ph, part)
            if not strokes:
                return None
            groups.append(tuple(strokes[0]))
    return groups


class PluvierEncoder:
    """Per-syllable phoneme -> Ireland keys, from `resources/pluvierPhonemeKeys.tsv`."""

    def __init__(self, path: str) -> None:
        self.table: dict[str, dict[str, list[str]]] = {"onset": {}, "nucleus": {}, "coda": {}}
        with open(path, encoding="utf-8") as handle:
            lines = [ln.rstrip("\n") for ln in handle if ln.strip() and not ln.startswith("#")]
        for line in lines[1:]:
            part, phonemes, keys, _source = line.split("\t")
            text = keys if part != "coda" or any(c in "AO*EU" for c in keys) else "-" + keys
            parsed = parseChord(text) if text else []
            if parsed is None and part == "coda":      # a mis-ordered source string (`FLP`): put its letters in key order
                parsed = parseChord(("*" if "*" in keys else "-") + "".join(c for c in "FRPBLGTSDZ" if c in keys))
            if parsed is None:
                raise ValueError(f"bad key text {line!r}")
            self.table[part][phonemes] = parsed

    def tokens(self, syllable: str) -> list[list[str]] | None:
        """The Ireland key list of every phoneme token of a syllable, None when a phoneme is not in the table."""
        out: list[list[str]] = []
        pos = 0
        seen = False
        while pos < len(syllable):
            c, two = syllable[pos], syllable[pos:pos + 2]
            if not seen and two in self.table["nucleus"] and len(two) == 2 and (c in "jw" or c in NUCLEUS):
                out.append(self.table["nucleus"][two])
                pos += 2
                seen = True
            elif c in NUCLEUS:
                if c not in self.table["nucleus"]:
                    return None
                out.append(self.table["nucleus"][c])
                seen = True
                pos += 1
            else:
                part = "coda" if seen else "onset"
                if len(two) == 2 and two in self.table[part]:
                    out.append(self.table[part][two])
                    pos += 2
                elif c in self.table[part]:
                    out.append(self.table[part][c])
                    pos += 1
                else:
                    return None
        return out

    def encodeWord(self, syll: str) -> tuple[list[list[list[str]]], str] | None:
        """The tokens of every syllable and the chord text of the word (`/`-joined), None when unencodable."""
        sylls: list[list[list[str]]] = []
        for syllable in syll.split("-"):
            tokens = self.tokens(syllable)
            if tokens is None:
                return None
            sylls.append(tokens)
        text = "/".join(renderChord({k for t in tokens for k in t}) for tokens in sylls)
        return sylls, text


def pluvierViolations(sylls: list[list[list[str]]]) -> int:
    total = 0
    for tokens in sylls:
        total += countViolations([tuple(IRELAND_KEYS.index(k) for k in t) for t in tokens if t])
    return total


def orderViolations(violations: dict[str, int | None], freq: dict[str, float], words: set[str]) -> dict[str, Any]:
    """Weighted share of words with at least one violation, mean violations, and the unencodable share."""
    known = {w: v for w, v in violations.items() if v is not None and w in words}
    unknown = {w for w in words if violations.get(w) is None}
    total = mass(freq, words)
    return {"shareWithViolation": weightedMean({w: float(v > 0) for w, v in known.items()}, freq, words),
            "meanViolations": weightedMean({w: float(v) for w, v in known.items()}, freq, words),
            "encodedWords": len(known), "unencodableWords": len(unknown),
            "unencodableFrequencyShare": share(mass(freq, unknown), total)}
