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
from collections import defaultdict

from src.keyboard import Starboard
from src.word import Word
from util._theoryio import loadFirstTheory

KEYBOARD_JSON = "starboard3h.json"
OUTPUT_PATH = "plover_stenalgo_dictionary.json"


def main() -> None:
    theory = loadFirstTheory()
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
