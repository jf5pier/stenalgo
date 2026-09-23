"""
Shared `FirstTheory.pickle`/`Dictionary.pickle` loading, factored out of
`util/export_plover_dictionary.py` and `util/build_realization_report.py`,
which both duplicated this exact block.

Requires Dictionary.pickle/FirstTheory.pickle (`python dictionary.py` first).
"""
import os
import pickle
import sys

from src.grammar import Syllable
from src.keyboard import Keyboard, Strokes
from src.word import Word


def _loadDictionaryAndFirstTheory():  # type: ignore[no-untyped-def]
    from dictionary import Dictionary
    # Dictionary.pickle was written while `dictionary.py` ran as __main__, so pickle
    # recorded the class under the "__main__" module -- alias it here so unpickling
    # finds it, same trick `src/ambiguitychecker.py`'s own __main__ relies on when run
    # directly (`python -m src.ambiguitychecker` doesn't need this; a plain util script does).
    sys.modules["__main__"].Dictionary = Dictionary  # type: ignore[attr-defined]

    if not os.path.exists("Dictionary.pickle"):
        raise RuntimeError("Run `python dictionary.py` first to generate Dictionary.pickle.")
    with open("Dictionary.pickle", "rb") as pfile:
        dictionary = pickle.load(pfile)
        Syllable.allPhonemeCol = pickle.load(pfile)
        Syllable.phonemeColByPart = pickle.load(pfile)
        Syllable.biphonemeColByPart = pickle.load(pfile)
        Syllable.multiphonemeColByPart = pickle.load(pfile)

    if not os.path.exists("FirstTheory.pickle"):
        raise RuntimeError("Run `python dictionary.py` first to generate FirstTheory.pickle.")
    with open("FirstTheory.pickle", "rb") as pfile:
        theory: dict[Strokes, list[Word]] = pickle.load(pfile)

    return dictionary, theory


def loadFirstTheory() -> dict[Strokes, list[Word]]:
    """Theory 1: base (onset/nucleus/coda) strokes only, no homophone marks."""
    _dictionary, theory = _loadDictionaryAndFirstTheory()
    return theory


def loadFinalTheory(
    keyboard: Keyboard,
    keypressGroupsPath: str = "keypress_groups.json",
    resolvedPressSetsPath: str = "resolved_press_sets.json",
) -> dict[Word, list[Strokes]]:
    """
    Theory 2: every word's final resolved Strokes -- a LIST, since a self-homograph
    spelling (e.g. "calmez") has more than one independently-valid stroke; index 0 is
    always the primary one. Theory 1 composed with Phase P's same-lemma coda-bank marks
    and the `*`/`#` lemma-homophone track (see `Dictionary.buildFinalTheory`,
    `ROADMAP.md`'s "Status update"). This is what actually disambiguates homophones like
    "a"/"as"/"à" -- `loadFirstTheory` alone does not.

    Requires `keypressGroupsPath` (`python -m util.build_keypress_groups`) and
    `resolvedPressSetsPath` (`python -m src.elicitation`) to already exist.
    """
    _theory, finalTheory = loadFirstAndFinalTheory(keyboard, keypressGroupsPath, resolvedPressSetsPath)
    return finalTheory


def loadFirstAndFinalTheory(
    keyboard: Keyboard,
    keypressGroupsPath: str = "keypress_groups.json",
    resolvedPressSetsPath: str = "resolved_press_sets.json",
) -> tuple[dict[Strokes, list[Word]], dict[Word, list[Strokes]]]:
    """`loadFirstTheory` and `loadFinalTheory` together, unpickling only once -- for a
    caller that needs theory 1 alongside theory 2 (e.g. to map `resolved_press_sets.json`
    entries back onto real `Word`s, which is keyed by theory-1 strokes)."""
    if not os.path.exists(keypressGroupsPath):
        raise RuntimeError(f"Run `python -m util.build_keypress_groups` first to generate {keypressGroupsPath}.")
    if not os.path.exists(resolvedPressSetsPath):
        raise RuntimeError(f"Run `python -m src.elicitation` first to generate {resolvedPressSetsPath}.")

    dictionary, theory = _loadDictionaryAndFirstTheory()
    return theory, dictionary.buildFinalTheory(theory, keyboard, keypressGroupsPath, resolvedPressSetsPath)
