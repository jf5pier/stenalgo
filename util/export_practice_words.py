"""
Export a frequency-ordered word -> chord list for the `steno-trainer` web app to
drill from: `dictionary.py`'s theory, keyed by orthography (not by steno string,
the way `util/export_plover_dictionary.py` is) -- the trainer only ever needs
"what chord for this word," never the reverse, so it dedupes on `ortho` instead
of `steno` when a word appears under more than one entry, keeping the
highest-frequency one. Cross-word steno collisions (the same ~47k Phase-P-pending
case `export_plover_dictionary.py`'s docstring documents) are harmless here for
the same reason.

Emits both the RTFCRE display string (`Starboard.strokesToRTFCRE`) and the raw
key-index strokes, so the browser never needs a steno-notation parser -- it just
compares sets of key indices against a decoded Gemini PR packet.

Run: python -m util.export_practice_words [--limit N]
Requires FirstTheory.pickle/Dictionary.pickle (`python dictionary.py` first).
"""
import argparse
import json

from src.keyboard import Starboard
from src.word import Word
from util._theoryio import loadFirstTheory

KEYBOARD_JSON = "starboard3h.json"
OUTPUT_PATH = "steno-trainer/public/data/practice-words.json"
DEFAULT_LIMIT = 10000


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                         help="Keep only the N most frequent words (default %(default)s).")
    args = parser.parse_args()

    theory = loadFirstTheory()
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; run dictionary.py once first to generate it.")

    byOrtho: dict[str, tuple[str, list[list[int]], Word]] = {}
    orthoCollisions = 0
    for strokes, words in theory.items():
        steno = starboard.strokesToRTFCRE(strokes)
        keyIndexStrokes = [sorted(set(stroke)) for stroke in strokes]
        for w in words:
            existing = byOrtho.get(w.ortho)
            if existing is not None:
                orthoCollisions += 1
                if w.frequency <= existing[2].frequency:
                    continue
            byOrtho[w.ortho] = (steno, keyIndexStrokes, w)

    records = [
        {"ortho": ortho, "steno": steno, "strokes": strokes, "frequency": round(w.frequency, 3)}
        for ortho, (steno, strokes, w) in byOrtho.items()
    ]
    records.sort(key=lambda r: -r["frequency"])
    records = records[:args.limit]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=1)

    print(f"Wrote {OUTPUT_PATH}: {len(records)} words"
          f" ({orthoCollisions} same-ortho collisions -- expected, the pending"
          f" homophone-marking work's job, not this exporter's; kept the most frequent"
          f" variant of each).")


if __name__ == "__main__":
    main()
