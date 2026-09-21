"""
Export a real Plover JSON dictionary (steno string -> French word) from
`dictionary.py`'s theory, using `Starboard.strokesToRTFCRE` (Stenalgo's own key
names, matching `plover_stenalgo`'s system plugin) instead of the phoneme-letter
rendering `writeTheory`/`theory.tsv` uses.

This is base strokes only (theory 1, `FirstTheory.pickle`): Phase P's star/hash
marks aren't wired into a persisted `dict[Word, Strokes]` output yet (see
CLAUDE.md/ROADMAP.md), so words that only the roadmap's still-pending
homophone-marking work would distinguish collide onto the same steno string
here -- expected, not a regression. The most frequent word of each colliding
group is kept; the rest are reported, same as `writeTheory`'s existing
ambiguity reporting.

Run: python -m util.export_plover_dictionary
Requires FirstTheory.pickle/Dictionary.pickle (`python dictionary.py` first).
"""
import json
import os
import pickle
import sys
from collections import defaultdict

from src.grammar import Syllable
from src.keyboard import Starboard, Strokes
from src.word import Word

KEYBOARD_JSON = "starboard3h.json"
OUTPUT_PATH = "plover_stenalgo_dictionary.json"


def _loadTheory() -> dict[Strokes, list[Word]]:
    from dictionary import Dictionary
    # Same __main__-aliasing trick util/build_phase_p_realization.py uses: Dictionary
    # was pickled while dictionary.py ran as __main__.
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


def main() -> None:
    theory = _loadTheory()
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; run dictionary.py once first to generate it.")

    stenoToWords: dict[str, list[Word]] = defaultdict(list)
    for strokes, words in theory.items():
        steno = starboard.strokesToRTFCRE(strokes)
        stenoToWords[steno].extend(words)

    stenoDict: dict[str, str] = {}
    collisions: list[tuple[str, list[str]]] = []
    for steno, words in stenoToWords.items():
        chosen = max(words, key=lambda w: w.frequency)
        stenoDict[steno] = chosen.ortho
        if len(words) > 1:
            collisions.append((steno, sorted({w.ortho for w in words})))

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(stenoDict, f, ensure_ascii=False, indent=1, sort_keys=True)

    print(f"Wrote {OUTPUT_PATH}: {len(stenoDict)} strokes"
          f" ({len(collisions)} same-steno collisions -- expected, the pending"
          f" homophone-marking work's job, not this exporter's).")
    for steno, orthos in sorted(collisions, key=lambda c: -len(c[1]))[:10]:
        print(f"  {steno!r}: {orthos} -> kept {stenoDict[steno]!r}")


if __name__ == "__main__":
    main()
