"""
Different-Lemma or Grammatical-Category Disambiguation (S7) refresh as a command:
recompute the disambiguated theory (every word's final strokes -- the Realization
Phase's same-lemma coda-bank marks plus the star/hash reserved-key marks, composed
on the phonetic theory; see Dictionary.buildDisambiguatedTheory) and write its
human view disambiguated_theory.tsv. Nothing reads that TSV -- every exporter
recomputes the disambiguated theory inline (util/_theoryio.py) -- but the
tracked-output verification protocol compares it.

Run: python -m util.build_disambiguated_theory   (from the repo root; it chdirs there)
Requires Dictionary.pickle/PhoneticTheory.pickle (`python -m util.build_phonetic_theory`
first), keypress_groups.json (`python -m util.build_keypress_groups`) and
resolved_press_sets.json (`python -m src.elicitation`).
Outputs: disambiguated_theory.tsv.

Fails (exit 1, after writing the TSV) when two differently-spelled words of different
lemmas or categories share a final stroke -- a collision S7 should have marked apart
(src.ambiguitychecker.findFinalCollisions). The Realization Phase's same-lemma residuals
and the reform-doublet exemption (R2) pairs are reported, not failed on.
"""
import os
import sys

from src.ambiguitychecker import FinalCollisionReport, findFinalCollisions, loadReform1990DoubletPairs
from src.keyboard import Starboard
from src.word import Word
from util._stenorender import renderFinalStrokesToRTFCRE
from util._theoryio import _loadDictionaryAndPhoneticTheory
from util._timing import timedCall

KEYBOARD_JSON_PATH = "starboard3h.json"
KEYPRESS_GROUPS_PATH = "keypress_groups.json"
RESOLVED_PRESS_SETS_PATH = "resolved_press_sets.json"
OUTPUT_PATH = "disambiguated_theory.tsv"
DICTIONARY_PICKLE_PATH = "Dictionary.pickle"
PHONETIC_THEORY_PICKLE_PATH = "PhoneticTheory.pickle"


def reportFinalCollisions(report: FinalCollisionReport, keyboard: Starboard) -> None:
    """Print the final-stroke collision summary; exit 1 on any cross-lemma collision."""
    def describe(words: list[Word]) -> str:
        return ", ".join(sorted(f"{w.ortho} ({w.lemmeGramCat})" for w in words))

    print(f"Final-stroke collisions: {len(report.crossLemma)} cross-lemma,"
          f" {len(report.sameLemmeGramCat)} same-lemma residual (Realization Phase),"
          f" {len(report.reformDoublet)} reform doublet (R2, exempted).")
    for stroke, words in sorted(report.sameLemmeGramCat.items(), key=lambda item: describe(item[1]))[:10]:
        print(f"  same-lemma residual {renderFinalStrokesToRTFCRE(keyboard, stroke)!r}: {describe(words)}")
    if report.crossLemma:
        for stroke, words in sorted(report.crossLemma.items(), key=lambda item: describe(item[1])):
            print(f"  CROSS-LEMMA {renderFinalStrokesToRTFCRE(keyboard, stroke)!r}: {describe(words)}", file=sys.stderr)
        print(f"FAILED: {len(report.crossLemma)} final strokes output a different lemma's spelling"
              " (Different-Lemma or Grammatical-Category Disambiguation (S7) left them unmarked).",
              file=sys.stderr)
        raise SystemExit(1)


def main() -> None:
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if not os.path.exists(DICTIONARY_PICKLE_PATH) or not os.path.exists(PHONETIC_THEORY_PICKLE_PATH):
        raise RuntimeError("Run `python -m util.build_phonetic_theory` first to build "
                           f"{DICTIONARY_PICKLE_PATH} / {PHONETIC_THEORY_PICKLE_PATH}.")
    if not os.path.exists(KEYPRESS_GROUPS_PATH):
        raise RuntimeError(f"Run `python -m util.build_keypress_groups` first to generate {KEYPRESS_GROUPS_PATH}.")
    if not os.path.exists(RESOLVED_PRESS_SETS_PATH):
        raise RuntimeError(f"Run `python -m src.elicitation` first to generate {RESOLVED_PRESS_SETS_PATH}.")

    starboard = Starboard.fromJSONFile(KEYBOARD_JSON_PATH)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON_PATH} not found; it is a committed input -- "
                           "run from the repo root.")

    # _loadDictionaryAndPhoneticTheory (not the public loadPhoneticAndDisambiguatedTheory)
    # because the disambiguated theory must NOT be recomputed here just to be thrown
    # away: writeDisambiguatedTheory needs the Dictionary instance itself, and this
    # way the 58 MB Dictionary.pickle unpickles exactly once.
    with timedCall("phase", "util.build_disambiguated_theory: unpickle Dictionary + PhoneticTheory"):
        dictionary, phoneticTheory = _loadDictionaryAndPhoneticTheory()
    with timedCall("phase", "util.build_disambiguated_theory: buildDisambiguatedTheory"):
        disambiguatedTheory = dictionary.buildDisambiguatedTheory(
            phoneticTheory, starboard, KEYPRESS_GROUPS_PATH, RESOLVED_PRESS_SETS_PATH)
    with timedCall("phase", f"util.build_disambiguated_theory: writeDisambiguatedTheory ({OUTPUT_PATH})"):
        dictionary.writeDisambiguatedTheory(phoneticTheory, disambiguatedTheory, starboard, OUTPUT_PATH)
    print(f"\nWrote {OUTPUT_PATH}: {len(disambiguatedTheory)} words with disambiguated-theory"
          f" (Phase P + */# track) strokes.")
    reportFinalCollisions(findFinalCollisions(disambiguatedTheory, loadReform1990DoubletPairs()), starboard)


if __name__ == "__main__":
    main()
