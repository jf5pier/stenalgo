"""
Dictionary Loading (S3) + Phonetic Theory Building (S5) as one command: load or
build Dictionary.pickle (with its four trailing Syllable-collection pickles), load
the keyboard layout, then load or build the phonetic theory (PhoneticTheory.pickle:
base onset/nucleus/coda strokes only, no homophone marks) and write its human view
phonetic_theory.tsv -- always, pickle hit or miss.

Run: python -m util.build_phonetic_theory [--theory-only]   (from the repo root; it chdirs there)
--theory-only is the light rebuild between the rounds of the Synthetic Lexicon Building (S2) loop: it parses the
lexicons, syllabifies, builds the phonetic theory and writes PhoneticTheory.pickle only (no Dictionary.pickle, no
phonetic_theory.tsv), always from the lexicons. The ambiguity statistics of the layout work are not computed by
either mode (Dictionary.ensureAmbiguityStats, called by util/optimize_keyboard.py).
Requires resources/LexiqueMixte.tsv, resources/LexiqueSynthetic.tsv (python -m
util.build_synthetic_lexicon; python lexique.py before that) and starboard3h.json.
rm -f Dictionary.pickle PhoneticTheory.pickle after ANY lexicon or layout change
(the cache is never checked for staleness).
Outputs: Dictionary.pickle, PhoneticTheory.pickle, phonetic_theory.tsv.
"""
import argparse
import os
import pickle

from dictionary import Dictionary  # module-level ON PURPOSE: pickles written by
# dictionary.py's old buildOnly (removed 2026-09-24) recorded the class as
# __main__.Dictionary, so the name must sit in this module's globals -- which ARE
# __main__'s under `python -m` -- for them to unpickle; new pickles record
# dictionary.Dictionary and unpickle anywhere the repo root is importable.
from src.grammar import Syllable
from src.keyboard import Starboard, Strokes
from src.word import Word
from util._timing import timedCall

DICTIONARY_PICKLE_PATH = "Dictionary.pickle"
PHONETIC_THEORY_PICKLE_PATH = "PhoneticTheory.pickle"
PHONETIC_THEORY_TSV_PATH = "phonetic_theory.tsv"
KEYBOARD_JSON_PATH = "starboard3h.json"


def loadOrBuildDictionary() -> Dictionary:
    """Dictionary.pickle (hit) or the full S3 build (miss): Dictionary() ->
    analyseSyllabification() -> Syllable.optimizeBiphonemeOrder(), the Dictionary and
    its four Syllable-collection pickles dumped back to back. The ambiguity statistics
    (analyseAmbiguities, 16 s) are left out: the theory is the same without them and only
    the keyboard layout work reads them (Dictionary.ensureAmbiguityStats)."""
    if os.path.exists(DICTIONARY_PICKLE_PATH):
        with open(DICTIONARY_PICKLE_PATH, "rb") as pfile:
            dictionary: Dictionary = pickle.load(pfile)
            Syllable.allPhonemeCol = pickle.load(pfile)
            Syllable.phonemeColByPart = pickle.load(pfile)
            Syllable.biphonemeColByPart = pickle.load(pfile)
            Syllable.multiphonemeColByPart = pickle.load(pfile)
        print("Loaded dictionary from pickle file.")
        print(dictionary.syllableCollection)
    else:
        dictionary = Dictionary()

        dictionary.analyseSyllabification()
        Syllable.optimizeBiphonemeOrder()

        with open(DICTIONARY_PICKLE_PATH, "wb") as pfile:
            pickle.dump(dictionary, pfile)
            pickle.dump(Syllable.allPhonemeCol, pfile)
            pickle.dump(Syllable.phonemeColByPart, pfile)
            pickle.dump(Syllable.biphonemeColByPart, pfile)
            pickle.dump(Syllable.multiphonemeColByPart, pfile)
    return dictionary


def loadKeyboard(dictionary: Dictionary) -> Starboard:
    """The committed layout, or a generated fallback keymap when it is missing."""
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON_PATH)
    if starboard is None:
        print("Could not load keyboard from", KEYBOARD_JSON_PATH,
              "generating an initial keymap based on phoneme order")
        starboard = Starboard()
        dictionary.generateBaseKeymap(starboard)
    starboard.printLayout()
    return starboard


def loadOrBuildPhoneticTheory(dictionary: Dictionary, starboard: Starboard) -> dict[Strokes, list[Word]]:
    """PhoneticTheory.pickle (hit) or Dictionary.buildPhoneticTheory (miss)."""
    if os.path.exists(PHONETIC_THEORY_PICKLE_PATH):
        with open(PHONETIC_THEORY_PICKLE_PATH, "rb") as pfile:
            theory: dict[Strokes, list[Word]] = pickle.load(pfile)
            return theory
    phoneticTheory = dictionary.buildPhoneticTheory(starboard)
    with open(PHONETIC_THEORY_PICKLE_PATH, "wb") as pfile:
        pickle.dump(phoneticTheory, pfile)
    return phoneticTheory


def buildTheoryOnly() -> None:
    """The light rebuild: the lexicons -> the phonetic theory -> PhoneticTheory.pickle, nothing else written. Always
    rebuilds (a PhoneticTheory.pickle already there is overwritten)."""
    with timedCall("phase", "util.build_phonetic_theory: light Dictionary build"):
        dictionary = Dictionary()
        dictionary.analyseSyllabification()
        Syllable.optimizeBiphonemeOrder()
    starboard = loadKeyboard(dictionary)
    with timedCall("phase", "util.build_phonetic_theory: light phonetic theory"):
        phoneticTheory = dictionary.buildPhoneticTheory(starboard)
        with open(PHONETIC_THEORY_PICKLE_PATH, "wb") as pfile:
            pickle.dump(phoneticTheory, pfile)
    print(f"\nWrote {PHONETIC_THEORY_PICKLE_PATH} only (--theory-only): {len(phoneticTheory)} phonetic-theory entries.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--theory-only", action="store_true",
                        help="light rebuild: write PhoneticTheory.pickle only (the S2 loop's between-rounds step)")
    args = parser.parse_args(argv)
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if args.theory_only:
        buildTheoryOnly()
        return
    with timedCall("phase", "util.build_phonetic_theory: loadOrBuildDictionary"):
        dictionary = loadOrBuildDictionary()
    with timedCall("phase", "util.build_phonetic_theory: loadKeyboard"):
        starboard = loadKeyboard(dictionary)
    with timedCall("phase", "util.build_phonetic_theory: loadOrBuildPhoneticTheory"):
        phoneticTheory = loadOrBuildPhoneticTheory(dictionary, starboard)
    # Always written, pickle hit or miss (TODO.md B14, fixed 2026-09-24):
    # writePhoneticTheory iterates the dict in insertion order, which a pickle
    # round-trip preserves, so the bytes on a cache hit equal the build-time bytes.
    with timedCall("phase", f"util.build_phonetic_theory: writePhoneticTheory ({PHONETIC_THEORY_TSV_PATH})"):
        dictionary.writePhoneticTheory(phoneticTheory, starboard, PHONETIC_THEORY_TSV_PATH)
    print(f"\nWrote {PHONETIC_THEORY_TSV_PATH}: {len(phoneticTheory)} phonetic-theory entries.")


if __name__ == "__main__":
    main()
