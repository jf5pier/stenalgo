"""
Shared `PhoneticTheory.pickle`/`Dictionary.pickle` loading, factored out of
`util/export_plover_dictionary.py` and `util/build_realization_report.py`,
which both duplicated this exact block.

Requires Dictionary.pickle/PhoneticTheory.pickle (`python -m
util.build_phonetic_theory` first).
"""
import os
import pickle
import sys

from src.grammar import Syllable
from src.keyboard import Keyboard, Strokes
from src.word import Word


def loadDictionary():  # type: ignore[no-untyped-def]
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
        dictionary = pickle.load(pfile)
        Syllable.allPhonemeCol = pickle.load(pfile)
        Syllable.phonemeColByPart = pickle.load(pfile)
        Syllable.biphonemeColByPart = pickle.load(pfile)
        Syllable.multiphonemeColByPart = pickle.load(pfile)
    return dictionary


def _loadDictionaryAndPhoneticTheory():  # type: ignore[no-untyped-def]
    dictionary = loadDictionary()

    if not os.path.exists("PhoneticTheory.pickle"):
        raise RuntimeError("Run `python -m util.build_phonetic_theory` first to generate PhoneticTheory.pickle.")
    with open("PhoneticTheory.pickle", "rb") as pfile:
        phoneticTheory: dict[Strokes, list[Word]] = pickle.load(pfile)

    return dictionary, phoneticTheory


def loadPhoneticTheory() -> dict[Strokes, list[Word]]:
    """The phonetic theory: base (onset/nucleus/coda) strokes only, no homophone marks."""
    _dictionary, phoneticTheory = _loadDictionaryAndPhoneticTheory()
    return phoneticTheory


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

    Requires `keypressGroupsPath` (`python -m util.build_keypress_groups`) and
    `resolvedPressSetsPath` (`python -m src.elicitation`) to already exist.
    """
    _phoneticTheory, disambiguatedTheory = loadPhoneticAndDisambiguatedTheory(
        keyboard, keypressGroupsPath, resolvedPressSetsPath)
    return disambiguatedTheory


def loadPhoneticAndDisambiguatedTheory(
    keyboard: Keyboard,
    keypressGroupsPath: str = "keypress_groups.json",
    resolvedPressSetsPath: str = "resolved_press_sets.json",
) -> tuple[dict[Strokes, list[Word]], dict[Word, list[Strokes]]]:
    """`loadPhoneticTheory` and `loadDisambiguatedTheory` together, unpickling only
    once -- for a caller that needs the phonetic theory alongside the disambiguated
    theory (e.g. to map `resolved_press_sets.json` entries back onto real `Word`s,
    which is keyed by phonetic-theory strokes)."""
    if not os.path.exists(keypressGroupsPath):
        raise RuntimeError(f"Run `python -m util.build_keypress_groups` first to generate {keypressGroupsPath}.")
    if not os.path.exists(resolvedPressSetsPath):
        raise RuntimeError(f"Run `python -m src.elicitation` first to generate {resolvedPressSetsPath}.")

    dictionary, phoneticTheory = _loadDictionaryAndPhoneticTheory()
    return phoneticTheory, dictionary.buildDisambiguatedTheory(
        phoneticTheory, keyboard, keypressGroupsPath, resolvedPressSetsPath)
