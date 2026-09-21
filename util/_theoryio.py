"""
Shared `FirstTheory.pickle`/`Dictionary.pickle` loading, factored out of
`util/export_plover_dictionary.py` and `util/build_phase_p_realization.py`,
which both duplicated this exact block.

Requires Dictionary.pickle/FirstTheory.pickle (`python dictionary.py` first).
"""
import os
import pickle
import sys

from src.grammar import Syllable
from src.keyboard import Strokes
from src.word import Word


def loadFirstTheory() -> dict[Strokes, list[Word]]:
    from dictionary import Dictionary
    # Dictionary.pickle was written while `dictionary.py` ran as __main__, so pickle
    # recorded the class under the "__main__" module -- alias it here so unpickling
    # finds it, same trick `src/ambiguitychecker.py`'s own __main__ relies on when run
    # directly (`python -m src.ambiguitychecker` doesn't need this; a plain util script does).
    sys.modules["__main__"].Dictionary = Dictionary  # type: ignore[attr-defined]

    if not os.path.exists("Dictionary.pickle"):
        raise RuntimeError("Run `python dictionary.py` first to generate Dictionary.pickle.")
    with open("Dictionary.pickle", "rb") as pfile:
        pickle.load(pfile)  # the Dictionary itself, unused here
        Syllable.allPhonemeCol = pickle.load(pfile)
        Syllable.phonemeColByPart = pickle.load(pfile)
        Syllable.biphonemeColByPart = pickle.load(pfile)
        Syllable.multiphonemeColByPart = pickle.load(pfile)

    if not os.path.exists("FirstTheory.pickle"):
        raise RuntimeError("Run `python dictionary.py` first to generate FirstTheory.pickle.")
    with open("FirstTheory.pickle", "rb") as pfile:
        return pickle.load(pfile)
