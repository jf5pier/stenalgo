"""
Export the adopted Starboard layout (`starboard3h.json`) as a JSON geometry/finger/
Gemini-PR-keymap description the `steno-trainer` web app can render a virtual
keyboard from, without depending on the solver stack (OR-Tools, pandas, ...) --
same dependency-free spirit as `util/export_plover_system.py`, whose
`GEMINI_PR_LABELS` constant this script reuses directly.

No SVG/pixel geometry exists anywhere in the codebase -- the physical grid shape
below (two mirrored 2x5 banks, two off-home index keys, two 2-key thumb clusters)
is hand-encoded here from `Starboard._printableKeyLayout`'s known ASCII shape
(`src/keyboard.py:283-301`), which is this script's source of truth if the
physical key count/shape ever changes.

Run: python -m util.export_keyboard_layout
Requires `starboard3h.json` (`python dictionary.py` generates it).
"""
import json

from src.keyboard import Starboard
from util.export_plover_system import GEMINI_PR_LABELS

KEYBOARD_JSON = "starboard3h.json"
OUTPUT_PATH = "steno-trainer/public/data/keyboard-layout.json"

LEFT_BANK_KEYS = [[0, 2, 4, 6, 8], [1, 3, 5, 7, 9]]
RIGHT_BANK_KEYS = [[16, 18, 20, 22, 24], [17, 19, 21, 23, 25]]
LEFT_THUMB_KEYS = [11, 12]
RIGHT_THUMB_KEYS = [13, 14]
LEFT_OFF_HOME_KEY = 10
RIGHT_OFF_HOME_KEY = 15


def _handAndGridPosition(keyIndex: int) -> tuple[str, int, int]:
    """
    Returns (hand, row, col) for a key index, per the grid hand-encoded above.

    Column 0 is reserved for the right hand's off-home key (15, "#") so it
    doesn't collide with the right bank's own first column; the right bank
    itself is shifted one column over (col 1-5) to make room. The left bank
    keeps columns 0-4 with its own off-home key (10, "*") at column 5. Thumb
    clusters (11-12, 13-14) sit in row 2 near each hand's *inner* edge (close
    to the center gap between hands, where thumbs actually rest) rather than
    under the outer pinky columns -- matching where `_printableKeyLayout`
    (`src/keyboard.py:283-301`) draws them, not literally under column 0-1.
    """
    if keyIndex == LEFT_OFF_HOME_KEY:
        return "left", 0, 5
    if keyIndex == RIGHT_OFF_HOME_KEY:
        return "right", 0, 0
    if keyIndex in LEFT_THUMB_KEYS:
        return "left", 2, 4 + LEFT_THUMB_KEYS.index(keyIndex)
    if keyIndex in RIGHT_THUMB_KEYS:
        return "right", 2, RIGHT_THUMB_KEYS.index(keyIndex)
    if keyIndex in [k for cols in LEFT_BANK_KEYS for k in cols]:
        row = next(r for r, cols in enumerate(LEFT_BANK_KEYS) if keyIndex in cols)
        return "left", row, LEFT_BANK_KEYS[row].index(keyIndex)
    if keyIndex in [k for cols in RIGHT_BANK_KEYS for k in cols]:
        row = next(r for r, cols in enumerate(RIGHT_BANK_KEYS) if keyIndex in cols)
        return "right", row, RIGHT_BANK_KEYS[row].index(keyIndex) + 1
    raise ValueError(f"Key {keyIndex} not placed in any bank/thumb-cluster/off-home slot")


def main() -> None:
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; run dictionary.py once first to generate it.")

    names = starboard.keyDisplayNames()
    partByKey: dict[int, str] = {}
    for part, keys in starboard.keyIDinSyllabicPart.items():
        for k in keys:
            partByKey[k] = part

    keys = []
    for index in range(starboard.nbKeys):
        hand, row, col = _handAndGridPosition(index)
        keys.append({
            "index": index,
            "name": names[index],
            "hand": hand,
            "finger": starboard._fingerAssignments[index],
            "row": row,
            "col": col,
            "part": partByKey.get(index),
            "reserved": index in starboard._reservedKeys,
            "geminiPrLabel": GEMINI_PR_LABELS[index],
        })

    layout = {
        "keys": keys,
        "grid": {
            "leftBank": {"rows": 2, "cols": 5, "keys": LEFT_BANK_KEYS, "offHomeKey": LEFT_OFF_HOME_KEY},
            "rightBank": {"rows": 2, "cols": 5, "keys": RIGHT_BANK_KEYS, "offHomeKey": RIGHT_OFF_HOME_KEY},
            "leftThumb": LEFT_THUMB_KEYS,
            "rightThumb": RIGHT_THUMB_KEYS,
        },
        "syllabicParts": starboard.keyIDinSyllabicPart,
        "reservedKeys": starboard._reservedKeys,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(layout, f, ensure_ascii=False, indent=1)

    print(f"Wrote {OUTPUT_PATH}: {len(keys)} keys.")


if __name__ == "__main__":
    main()
