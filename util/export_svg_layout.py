"""
Export the adopted Starboard layout (`starboard3h.json`) as a stand-alone SVG picture: one
top-level `<g id="key-NN">` per key (NN the zero-padded key index, `<title>` the key's name),
placed on the same grid as the trainer's virtual keyboard (`util.export_keyboard_layout`),
labelled with the phonemes the key writes alone and tinted by finger, on a light board so it
reads on a light or a dark page. The trainer's Introduction page shows it; it is also the
picture the SVG Layout Display plugin TODO (TODO.md) builds on (that plugin's lit variants and
`convert_stroke` script are not generated here yet).

Run: python -m util.export_svg_layout [OUTPUT]
Requires `starboard3h.json` (a committed input).
"""
import sys
from xml.sax.saxutils import escape

from src.keyboard import Starboard
from util.export_keyboard_layout import KEYBOARD_JSON, _handAndGridPosition

OUTPUT_PATH = "steno-trainer/public/stenalgo_layout.svg"

KEY = 54  # key size
PITCH = 60  # key spacing
MARGIN = 12
HAND_GAP = 56  # between the left hand's 6 columns and the right hand's 6
BOARD_RIGHT_X = MARGIN + 6 * PITCH + HAND_GAP

# pinky, ring, middle, index, thumb: the same tint for both hands
FINGER_FILL = {"p": "#f6c8c8", "r": "#f7dfb5", "m": "#d6ecb8", "i": "#bfe3ee", "t": "#d9cdf0"}
MARK_FILL = "#f1e3a0"  # the `*` and `#` marks
RESERVED_FILL = "#e4e4e4"


def _keyRect(index: int, hand: str, row: int, col: int, tall: bool) -> tuple[int, int, int, int]:
    x = (MARGIN if hand == "left" else BOARD_RIGHT_X) + col * PITCH
    y = MARGIN + row * PITCH
    return x, y, KEY, (KEY + PITCH if tall else KEY)


def buildSvg(starboard: Starboard) -> str:
    names = starboard.keyDisplayNames()
    width = BOARD_RIGHT_X + 6 * PITCH - (PITCH - KEY) + MARGIN
    height = MARGIN * 2 + 2 * PITCH + KEY
    groups = []
    for index in range(starboard.nbKeys):
        hand, row, col = _handAndGridPosition(index)
        phonemes = "".join(starboard.phonemesAssignedToStroke.get((index,), []))
        isMark = names[index] in ("*", "#")
        reserved = index in starboard._reservedKeys
        label = phonemes or names[index]
        x, y, w, h = _keyRect(index, hand, row, col, isMark)
        if isMark:
            fill = MARK_FILL
        elif reserved:
            fill = RESERVED_FILL
        else:
            fill = FINGER_FILL[starboard._fingerAssignments[index][1]]
        opacity = ' opacity="0.55"' if reserved and not isMark else ""
        size = 20 if len(label) <= 2 else 15
        groups.append(
            f'<g id="key-{index:02d}"{opacity}>'
            f"<title>{escape(names[index])}</title>"
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="#777" stroke-width="1.5"/>'
            f'<text x="{x + w // 2}" y="{y + h // 2 + size // 3}" text-anchor="middle" '
            f'font-family="monospace" font-size="{size}" fill="#222">{escape(label)}</text>'
            "</g>"
        )
    board = (
        '<g id="board">'
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="14" fill="#f3f3ef"/>'
        "</g>"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">\n'
        + board + "\n" + "\n".join(groups) + "\n</svg>\n"
    )


def main() -> None:
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; run dictionary.py once first to generate it.")
    output = sys.argv[1] if len(sys.argv) > 1 else OUTPUT_PATH
    with open(output, "w", encoding="utf-8") as f:
        f.write(buildSvg(starboard))
    print(f"Wrote {output}: {starboard.nbKeys} keys.")


if __name__ == "__main__":
    main()
