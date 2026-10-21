"""The layout statistics: what the keyboard layout solve (S4, src/cpsatsolver.py) reads, rebuilt from any list of words.

The solver reads the `Syllable` class-level collections (phoneme, biphoneme and multiphoneme frequencies per syllabic part, the biphoneme order
scores) and the three ambiguity tables of `Dictionary`. `Dictionary.analyseSyllabification` builds the collections from the lexicon; the same
pass, `buildSyllableStatistics`, runs here on the words of a (possibly rewritten) phonetic theory (docs/PHONOLOGY_REWRITE_PLAN.md PRP11), so the
solve can see the typed phonology. `canonicalStatistics` is the comparable form the equivalence checks use (util/check_layout_statistics.py).
"""
import pickle
from collections.abc import Collection, Iterable
from typing import Any

from tqdm import tqdm

from src.grammar import (
    BiphonemeCollection, MultiphonemeCollection, MultiphonemePairScores, PhonemeCollection, PhonemePairScores,
    Syllable, SyllableCollection,
)
from src.keyboard import Keyboard
from src.strokes import Strokes
from src.phonologyrewrite import applyPhonologyRewrite, loadPhonologyRules
from src.word import Word

PARTS = ("onset", "nucleus", "coda")
FORMAT = 1  # bump when the saved envelope layout changes


def resetSyllableStatistics() -> None:
    """Fresh class-level collections: the statistics are global state of `Syllable`, so two builds in one process would otherwise add up."""
    Syllable.allPhonemeCol = PhonemeCollection("all")
    Syllable.phonemeColByPart = {part: PhonemeCollection(part) for part in PARTS}
    Syllable.biphonemeColByPart = {part: BiphonemeCollection(part) for part in PARTS}
    Syllable.multiphonemeColByPart = {part: MultiphonemeCollection(part) for part in PARTS}


def buildSyllableStatistics(words: Iterable[Word], excludedOrthos: Collection[str],
                            syllableCollection: SyllableCollection | None = None) -> SyllableCollection:
    """Fills the `Syllable` class collections and the syllable collection from `words`, most frequent first. A word whose spelling is in
    `excludedOrthos` is still tracked but adds frequency 0 (the frequent words the solve leaves out). Starts from empty class collections;
    `Syllable.optimizeBiphonemeOrder()` is the caller's next step."""
    resetSyllableStatistics()
    collection = syllableCollection if syllableCollection is not None else SyllableCollection()
    for word in tqdm(sorted(words, key=lambda w: w.frequency, reverse=True), unit=" words", ascii=True, ncols=80):
        frequency = word.frequency if word.ortho not in excludedOrthos else 0.0
        syllableNames = word.phonemesToSyllableNames(withSilent=False)
        spellings = word.graphemsToSyllables(withSilent=False)
        for syllableName, spelling in zip(syllableNames, spellings):
            collection.updateSyllable(syllableName, spelling, frequency, word)
    Syllable.sortPhonemesCollections()
    return collection


def wordsOfTheory(theory: dict[Strokes, list[Word]]) -> list[Word]:
    """The distinct words of a phonetic theory (a word can sit under several outlines), in the theory's order."""
    return list(dict.fromkeys(word for words in theory.values() for word in words))


def loadFrequentWords(path: str = "resources/top500_film.txt", count: int = 200) -> list[str]:
    """The first `count` spellings of the frequent-words file (the list `Dictionary.readCorpus` keeps as `frequentWords`)."""
    with open(path) as ffile:
        ffile.readline()  # the total frequency
        return [line.strip().split("\t")[0] for line in ffile.readlines()[:count]]


def layoutInput(theory: dict[Strokes, list[Word]], frequentWords: Collection[str], keyboard: Keyboard,
                rewrite: bool) -> tuple[list[Word], set[str]]:
    """The words and the excluded spellings the layout statistics are built from. Without `rewrite`: the theory's words and the plain frequent
    words. With it: the theory with the phonology overrides applied (resources/phonologyOverrides.tsv), and the frequent words minus the
    overridden spellings (je te se le ce de me ne que), which are typed with their forced phonology and so count."""
    if not rewrite:
        return wordsOfTheory(theory), set(frequentWords)
    rules = loadPhonologyRules()
    return wordsOfTheory(applyPhonologyRewrite(theory, keyboard, rules)), set(frequentWords) - set(rules.phonology)


def ambiguityTables(collection: SyllableCollection) -> dict[str, Any]:
    """The three ambiguity tables of `Dictionary.analyseAmbiguities`, keyed by name, each by syllabic part."""
    syllabic = collection.analysePhonemSyllabicAmbiguity()
    lexical = collection.analysePhonemeLexicalAmbiguity()
    part: tuple[MultiphonemePairScores, MultiphonemePairScores, MultiphonemePairScores] = \
        collection.analyseMultiphonemeLexicalAmbiguity_serial()
    return {
        "syllabicAmbiguity": dict(zip(PARTS, syllabic)),
        "lexicalAmbiguity": dict(zip(PARTS, lexical)),
        "syllabicPartAmbiguity": dict(zip(PARTS, part)),
    }


def _phonemes(collection: PhonemeCollection) -> dict[str, Any]:
    return {p.name: [p.frequency, p.posFrequency, p.invPosFrequency] for p in collection.phonemes}


def canonicalStatistics(collection: SyllableCollection | None = None,
                        tables: dict[str, Any] | None = None) -> dict[str, Any]:
    """The statistics in a plain, comparable form (dicts keyed by repr strings, floats untouched). The lists keep their order under the
    `*Order` keys, so a comparison can tell a different content from a different tie order."""
    out: dict[str, Any] = {"all": _phonemes(Syllable.allPhonemeCol),
                           "allOrder": [p.name for p in Syllable.allPhonemeCol.phonemes]}
    for part in PARTS:
        biphonemes = Syllable.biphonemeColByPart[part]
        out[part] = {
            "phonemes": _phonemes(Syllable.phonemeColByPart[part]),
            "phonemesOrder": [p.name for p in Syllable.phonemeColByPart[part].phonemes],
            "biphonemes": {repr(b.pair): b.frequency for b in biphonemes.biphonemes},
            "biphonemesOrder": [repr(b.pair) for b in biphonemes.biphonemes],
            "bestPermutation": [biphonemes.bestPermutation, biphonemes.bestPermutationScore, biphonemes.bestPermutationNegativeScore],
            "pairwiseOrder": {repr(k): v for k, v in biphonemes.pairwiseBiphonemeOrder.items()},
            "pairwiseScore": {repr(k): v for k, v in biphonemes.pairwiseBiphonemeOrderScore.items()},
            "multiphonemes": {repr(m.phonemes): m.frequency for m in Syllable.multiphonemeColByPart[part].multiphonemes},
        }
    if collection is not None:
        out["syllables"] = {s.name: [s.frequency, sorted(s.spellings.items())] for s in collection.syllables}
    if tables is not None:
        out["tables"] = {name: {part: {repr(k): v for k, v in byPart[part].items()} for part in PARTS}
                         for name, byPart in tables.items()}
    return out


def saveLayoutStatistics(path: str, tables: dict[str, Any], meta: dict[str, Any]) -> None:
    """One self-contained file for the solve (a remote machine needs nothing else): the class collections, the ambiguity tables, and `meta`
    (what it was built from: source, md5s of the inputs)."""
    with open(path, "wb") as pfile:
        pickle.dump({
            "format": FORMAT, "meta": meta, "tables": tables,
            "allPhonemeCol": Syllable.allPhonemeCol, "phonemeColByPart": Syllable.phonemeColByPart,
            "biphonemeColByPart": Syllable.biphonemeColByPart, "multiphonemeColByPart": Syllable.multiphonemeColByPart,
        }, pfile)


def loadLayoutStatistics(path: str) -> dict[str, Any]:
    """Reads a file written by `saveLayoutStatistics`, installs its collections on `Syllable` and returns the envelope (`tables`, `meta`)."""
    with open(path, "rb") as pfile:
        envelope: dict[str, Any] = pickle.load(pfile)
    if envelope.get("format") != FORMAT:
        raise RuntimeError(f"{path}: layout statistics format {envelope.get('format')}, expected {FORMAT}; rebuild it.")
    Syllable.allPhonemeCol = envelope["allPhonemeCol"]
    Syllable.phonemeColByPart = envelope["phonemeColByPart"]
    Syllable.biphonemeColByPart = envelope["biphonemeColByPart"]
    Syllable.multiphonemeColByPart = envelope["multiphonemeColByPart"]
    return envelope


__all__ = [
    "PARTS", "PhonemePairScores", "ambiguityTables", "buildSyllableStatistics", "canonicalStatistics", "loadLayoutStatistics",
    "resetSyllableStatistics", "saveLayoutStatistics", "wordsOfTheory",
]
