"""
Shared `PhoneticTheory.pickle`/`Dictionary.pickle` loading, factored out of
`util/export_plover_dictionary.py` and `util/build_realization_report.py`,
which both duplicated this exact block.

Requires Dictionary.pickle/PhoneticTheory.pickle (`python -m
util.build_phonetic_theory` first).
"""
import hashlib
import os
import pickle
import sys
from typing import TYPE_CHECKING

from src.ambiguitychecker import buildWordToStrokes, buildWordsByOrthoLemme
from src.grammar import Syllable
from src.keyboard import Keyboard, Strokes
from src.word import Word

if TYPE_CHECKING:
    from dictionary import Dictionary


def loadDictionary() -> "Dictionary":
    """Dictionary.pickle plus its four trailing Syllable-collection pickles, WITHOUT
    PhoneticTheory.pickle -- for callers needing only the Dictionary and its layout
    statistics (Keyboard Layout Optimization (S4), util/optimize_keyboard.py)."""
    from dictionary import Dictionary
    # Pickles written by dictionary.py's old buildOnly (removed 2026-09-24) recorded
    # the class under the "__main__" module -- alias it here so unpickling finds it
    # (the same trick `src/ambiguitychecker.py`'s own __main__ relies on when run
    # directly). Pickles written by `python -m util.build_phonetic_theory` record
    # dictionary.Dictionary and need no alias; both generations load through this.
    sys.modules["__main__"].Dictionary = Dictionary  # type: ignore[attr-defined]

    if not os.path.exists("Dictionary.pickle"):
        raise RuntimeError("Run `python -m util.build_phonetic_theory` first to generate Dictionary.pickle.")
    with open("Dictionary.pickle", "rb") as pfile:
        dictionary: Dictionary = pickle.load(pfile)
        Syllable.allPhonemeCol = pickle.load(pfile)
        Syllable.phonemeColByPart = pickle.load(pfile)
        Syllable.biphonemeColByPart = pickle.load(pfile)
        Syllable.multiphonemeColByPart = pickle.load(pfile)
    return dictionary


def _loadDictionaryAndPhoneticTheory() -> "tuple[Dictionary, dict[Strokes, list[Word]]]":
    dictionary = loadDictionary()

    if not os.path.exists("PhoneticTheory.pickle"):
        raise RuntimeError("Run `python -m util.build_phonetic_theory` first to generate PhoneticTheory.pickle.")
    with open("PhoneticTheory.pickle", "rb") as pfile:
        phoneticTheory: dict[Strokes, list[Word]] = pickle.load(pfile)

    return dictionary, phoneticTheory


# The disambiguated-theory cache. Unlike Dictionary.pickle/PhoneticTheory.pickle
# (never checked for staleness; `rm -f` them after any lexicon or layout change),
# this pickle is FINGERPRINTED: it reloads only when every input below is
# byte-identical to when it was written -- necessary because
# `elicitation_answers.json` is hand-edited between runs and its effect flows
# through `resolved_press_sets.json` without any pickle being deleted.
# `util/build_disambiguated_theory.py` (the S7 step) is the only writer;
# loaders recompute silently on a miss. Synthetic Lexicon Building (S2) deletes
# it (util/build_synthetic_lexicon.py PICKLE_CACHE_PATHS) whenever it appends
# rows, alongside the two unchecked pickles.
DISAMBIGUATED_THEORY_PICKLE_PATH = "DisambiguatedTheory.pickle"
DISAMBIGUATED_THEORY_FINGERPRINT_INPUTS = (
    "resources/LexiqueMixte.tsv",
    "resources/LexiqueSynthetic.tsv",
    "starboard3h.json",
    "keypress_groups.json",
    "resolved_press_sets.json",
    "resources/reference/lapwing-numbers.json",     # the reserved number chords (Pluvier's are generated from the code)
)
# Format 2 also carries wordToStrokes/wordsByOrthoLemme -- the exact dicts
# buildWordToStrokes/buildWordsByOrthoLemme produce from the phonetic theory --
# so every consumer stops rebuilding them per subprocess (perf round 2). A
# format-1 envelope (or any older shape) is simply a miss.
_ENVELOPE_FORMAT = 2  # bump when the envelope layout below changes


def _md5(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def disambiguatedTheoryFingerprint(
    inputs: tuple[str, ...] = DISAMBIGUATED_THEORY_FINGERPRINT_INPUTS,
) -> dict[str, str | None]:
    """Per-input md5s of the disambiguated theory's five inputs (None for a
    missing file, so a deleted input never validates a cache)."""
    return {path: _md5(path) for path in inputs}


def writeDisambiguatedTheoryPickle(
    disambiguatedTheory: dict[Word, list[Strokes]],
    wordToStrokes: dict[Word, Strokes],
    wordsByOrthoLemme: dict[tuple[str, str], list[Word]],
    path: str = DISAMBIGUATED_THEORY_PICKLE_PATH,
    inputs: tuple[str, ...] = DISAMBIGUATED_THEORY_FINGERPRINT_INPUTS,
) -> None:
    """Envelope `(format, fingerprint, theory, wordToStrokes, wordsByOrthoLemme)`;
    only the S7 step calls this. The two indexes must be the dicts
    `buildWordToStrokes`/`buildWordsByOrthoLemme` return for the SAME phonetic
    theory (same objects as S7's build used), so cache-hit consumers get exactly
    what they would have rebuilt."""
    with open(path, "wb") as pfile:
        pickle.dump((_ENVELOPE_FORMAT, disambiguatedTheoryFingerprint(inputs),
                     disambiguatedTheory, wordToStrokes, wordsByOrthoLemme),
                    pfile, protocol=pickle.HIGHEST_PROTOCOL)


def loadCachedDisambiguatedTheory(
    path: str = DISAMBIGUATED_THEORY_PICKLE_PATH,
    inputs: tuple[str, ...] = DISAMBIGUATED_THEORY_FINGERPRINT_INPUTS,
) -> tuple[dict[Word, list[Strokes]], dict[Word, Strokes], dict[tuple[str, str], list[Word]]] | None:
    """The cached `(disambiguated theory, wordToStrokes, wordsByOrthoLemme)`, or
    None on a miss (absent/corrupt pickle, envelope-format change -- including
    round-1 format-1 envelopes -- or any fingerprint-input mismatch) -- the
    caller then recomputes via `Dictionary.buildDisambiguatedTheory`."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as pfile:
            (formatVersion, fingerprint, disambiguatedTheory,
             wordToStrokes, wordsByOrthoLemme) = pickle.load(pfile)
    except Exception:
        return None  # a corrupt (e.g. truncated) cache is a miss, never an error
    if formatVersion != _ENVELOPE_FORMAT or fingerprint != disambiguatedTheoryFingerprint(inputs):
        return None
    return disambiguatedTheory, wordToStrokes, wordsByOrthoLemme


def _loadPhoneticTheoryOnly() -> dict[Strokes, list[Word]]:
    """PhoneticTheory.pickle alone -- no Dictionary.pickle (59 MB), no Syllable
    class-state pickles. Safe for consumers that only walk the theory dict and
    its Words (every S8 exporter, the realization report): none of them touches
    the Dictionary object or Syllable's class-level collections."""
    if not os.path.exists("PhoneticTheory.pickle"):
        raise RuntimeError("Run `python -m util.build_phonetic_theory` first to generate PhoneticTheory.pickle.")
    with open("PhoneticTheory.pickle", "rb") as pfile:
        phoneticTheory: dict[Strokes, list[Word]] = pickle.load(pfile)
    return phoneticTheory


def loadPhoneticTheory() -> dict[Strokes, list[Word]]:
    """The phonetic theory: base (onset/nucleus/coda) strokes only, no homophone
    marks. Loads PhoneticTheory.pickle without Dictionary.pickle (see
    `_loadPhoneticTheoryOnly`)."""
    return _loadPhoneticTheoryOnly()


def loadDisambiguatedTheory(
    keyboard: Keyboard,
    keypressGroupsPath: str = "keypress_groups.json",
    resolvedPressSetsPath: str = "resolved_press_sets.json",
) -> dict[Word, list[Strokes]]:
    """
    The disambiguated theory: every word's final resolved Strokes -- a LIST, since a
    self-homograph spelling (e.g. "calmez") has more than one independently-valid
    stroke; index 0 is always the primary one. The phonetic theory composed with the
    same-lemma coda-bank marks of Discriminating-Feature Stroke Realization
    (Realization Phase) and the star/hash marks of Different-Lemma or
    Grammatical-Category Disambiguation (S7) (see
    `Dictionary.buildDisambiguatedTheory`, `ROADMAP.md`'s "Status update"). This is
    what actually disambiguates homophones like "a"/"as"/"à" --
    `loadPhoneticTheory` alone does not.

    On a cache hit NO large pickle is unpickled at all (the cached theory carries
    everything this returns); a miss loads Dictionary.pickle + PhoneticTheory.pickle
    and recomputes.

    Requires `keypressGroupsPath` (`python -m util.build_keypress_groups`) and
    `resolvedPressSetsPath` (`python -m src.elicitation`) to already exist.
    """
    if not os.path.exists(keypressGroupsPath):
        raise RuntimeError(f"Run `python -m util.build_keypress_groups` first to generate {keypressGroupsPath}.")
    if not os.path.exists(resolvedPressSetsPath):
        raise RuntimeError(f"Run `python -m src.elicitation` first to generate {resolvedPressSetsPath}.")

    cached = loadCachedDisambiguatedTheory(
        inputs=("resources/LexiqueMixte.tsv", "resources/LexiqueSynthetic.tsv",
                "starboard3h.json", keypressGroupsPath, resolvedPressSetsPath))
    if cached is not None:
        return cached[0]
    dictionary, phoneticTheory = _loadDictionaryAndPhoneticTheory()
    return dictionary.buildDisambiguatedTheory(
        phoneticTheory, keyboard, keypressGroupsPath, resolvedPressSetsPath)


def loadPhoneticAndDisambiguatedTheory(
    keyboard: Keyboard,
    keypressGroupsPath: str = "keypress_groups.json",
    resolvedPressSetsPath: str = "resolved_press_sets.json",
) -> tuple[dict[Strokes, list[Word]], dict[Word, list[Strokes]],
           dict[Word, Strokes], dict[tuple[str, str], list[Word]]]:
    """The phonetic theory, the disambiguated theory, and the two word indexes
    (`wordToStrokes`, `wordsByOrthoLemme`) the disambiguated-theory pickle
    envelope carries -- for a caller that maps `resolved_press_sets.json`
    entries back onto real `Word`s (keyed by phonetic-theory strokes) or renders
    base strokes per word.

    On a cache hit only PhoneticTheory.pickle is unpickled (Dictionary.pickle
    and its Syllable class-state are unused on that path -- see
    `_loadPhoneticTheoryOnly`); a miss loads both, recomputes the theory, and
    rebuilds the two indexes alongside it."""
    if not os.path.exists(keypressGroupsPath):
        raise RuntimeError(f"Run `python -m util.build_keypress_groups` first to generate {keypressGroupsPath}.")
    if not os.path.exists(resolvedPressSetsPath):
        raise RuntimeError(f"Run `python -m src.elicitation` first to generate {resolvedPressSetsPath}.")

    # The layout input is pinned to starboard3h.json: every caller builds
    # `keyboard` from it (no exporter loads a different layout).
    cached = loadCachedDisambiguatedTheory(
        inputs=("resources/LexiqueMixte.tsv", "resources/LexiqueSynthetic.tsv",
                "starboard3h.json", keypressGroupsPath, resolvedPressSetsPath))
    if cached is not None:
        disambiguatedTheory, wordToStrokes, wordsByOrthoLemme = cached
        return _loadPhoneticTheoryOnly(), disambiguatedTheory, wordToStrokes, wordsByOrthoLemme

    dictionary, phoneticTheory = _loadDictionaryAndPhoneticTheory()
    wordToStrokes = buildWordToStrokes(phoneticTheory)
    wordsByOrthoLemme = buildWordsByOrthoLemme(phoneticTheory)
    disambiguatedTheory = dictionary.buildDisambiguatedTheory(
        phoneticTheory, keyboard, keypressGroupsPath, resolvedPressSetsPath,
        wordToStrokes=wordToStrokes, wordsByOrthoLemme=wordsByOrthoLemme)
    return phoneticTheory, disambiguatedTheory, wordToStrokes, wordsByOrthoLemme
