"""
Export a frequency-ordered word -> chord list for the `steno-trainer` web app to
drill from, keyed by orthography (not by steno string, the way
`util/export_plover_dictionary.py` is) -- the trainer only ever needs "what chord
for this word," never the reverse, so it dedupes on `ortho` instead of `steno`
when a word appears under more than one entry, keeping the highest-frequency one.

Uses `util._theoryio.loadFinalTheory` (theory 2: base strokes + Phase P's
same-lemma marks + the `*`/`#` lemma-homophone track), not the raw unmarked
theory 1 -- this is what actually disambiguates homophones like "a"/"as"/"à"
(same base phonology, different final chords once Phase P/the */# track are
applied). A word whose final chord still collides with another word's (the same
lemma+gramCat, or an intentionally-exempted pair -- 1990-reform doublets, or one
word >10x rarer than the other) is expected, not a bug in this exporter; the
most frequent variant is kept.

Emits both a display steno string and the raw key-index strokes, so the browser
never needs a steno-notation parser -- it just compares sets of key indices
against a decoded Gemini PR packet.

Run: python -m util.export_practice_words [--limit N]
Requires FirstTheory.pickle/Dictionary.pickle (`python dictionary.py` first),
phase_g_keypress_assignment.json (`python -m util.build_phase_g_assignment`) and
resolved_press_sets.json (`python -m src.elicitation`).
"""
import argparse
import json

from src.keyboard import Starboard
from src.word import Word
from util._stenorender import renderFinalStrokesToRTFCRE
from util._theoryio import loadFinalTheory

KEYBOARD_JSON = "starboard3h.json"
OUTPUT_PATH = "steno-trainer/public/data/practice-words.json"
DEFAULT_LIMIT = 10000


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                         help="Keep only the N most frequent words (default %(default)s).")
    args = parser.parse_args()

    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; run dictionary.py once first to generate it.")

    finalTheory = loadFinalTheory(starboard)

    byOrtho: dict[str, tuple[str, list[list[int]], Word]] = {}
    orthoCollisions = 0
    for word, strokes in finalTheory.items():
        steno = renderFinalStrokesToRTFCRE(starboard, strokes)
        keyIndexStrokes = [sorted(set(stroke)) for stroke in strokes]

        existing = byOrtho.get(word.ortho)
        if existing is not None:
            orthoCollisions += 1
            if word.frequency <= existing[2].frequency:
                continue
        byOrtho[word.ortho] = (steno, keyIndexStrokes, word)

    records = [
        {"ortho": ortho, "steno": steno, "strokes": strokes, "frequency": round(w.frequency, 3)}
        for ortho, (steno, strokes, w) in byOrtho.items()
    ]
    records.sort(key=lambda r: -r["frequency"])
    records = records[:args.limit]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=1)

    print(f"Wrote {OUTPUT_PATH}: {len(records)} words"
          f" ({orthoCollisions} same-ortho collisions -- expected for homograph/exempted"
          f" pairs, not a bug in this exporter; kept the most frequent variant of each).")


if __name__ == "__main__":
    main()
