"""
Shared safe RTFCRE rendering for the disambiguated theory (base strokes + the same-lemma marks of
Discriminating-Feature Stroke Realization (Realization Phase) + the star/hash marks of
Different-Lemma or Grammatical-Category Disambiguation (S7)), used by
`util/export_plover_dictionary.py` and the steno-trainer exporters.

`Starboard.strokesToRTFCRE` only handles base (onset/nucleus/coda) strokes: a
stroke containing STAR_KEY/HASH_KEY (10/15) carries no syllabic part, which
crashes its per-key bucketing (see that method's own docstring, and
`Dictionary.writeDisambiguatedTheory`'s, for why). Two shapes of stroke carry them:

- a bare mark stroke (only reserved keys: an escalated `*`/`#` code's further
  symbols), rendered as a plain concatenation of key display names;
- the word's last phoneme stroke with the mark's first symbol pressed along with
  it (`src.ambiguitychecker.composeReservedKeyStrokes`), rendered by Plover's own
  `plover_stroke` rule: keys in the system's `KEYS` order (ascending index), with a
  "-" before the first key right of the vowels only when the stroke has no
  implicit-hyphen key (a nucleus key or `*`) -- e.g. "*iel", "swa#", "pvR-#".
  `#` sits right of the vowels, `*` among them (see `util/export_plover_system.py`).
"""
from src.ambiguitychecker import HASH_KEY, STAR_KEY
from src.keyboard import Starboard, Strokes

RESERVED_MARK_KEYS = (STAR_KEY, HASH_KEY)


def _renderMarkedStroke(starboard: Starboard, keys: list[int]) -> str:
    implicitHyphenKeys = set(starboard.keyIDinSyllabicPart["nucleus"]) | {STAR_KEY}
    firstRightKey = max(implicitHyphenKeys) + 1
    needsHyphen = not any(k in implicitHyphenKeys for k in keys)
    rendered = ""
    for key in keys:
        if needsHyphen and key >= firstRightKey:
            rendered += "-"
            needsHyphen = False
        rendered += starboard.keyDisplayName(key).strip("-")
    return rendered


def renderFinalStrokesToRTFCRE(starboard: Starboard, strokes: Strokes) -> str:
    parts = []
    for stroke in strokes:
        keys = sorted(set(stroke))
        if all(k in RESERVED_MARK_KEYS for k in keys):
            parts.append("".join(starboard.keyDisplayName(k) for k in keys))
        elif any(k in RESERVED_MARK_KEYS for k in keys):
            parts.append(_renderMarkedStroke(starboard, keys))
        else:
            parts.append(starboard.strokesToRTFCRE((tuple(keys),)))
    return "/".join(parts)


def parseStroke(text: str, keys: tuple[str, ...]) -> tuple[int, ...]:
    """The key indices of one steno stroke written in the system's key order (`KEYS`), the way
    `renderFinalStrokesToRTFCRE` writes it. Keys are matched left to right, the `-` jumping to the first right-hand key."""
    firstRight = next(i for i, name in enumerate(keys) if name.startswith("-") and name not in ("-i", "-e"))
    pressed: list[int] = []
    pointer = 0
    for char in text:
        if char == "-":
            pointer = max(pointer, firstRight)
            continue
        if char == "#":
            pressed.append(keys.index("#"))
            continue
        index = next((i for i in range(pointer, len(keys)) if keys[i].strip("-") == char), None)
        if index is None:
            raise ValueError(f"cannot parse stroke {text!r} at {char!r}")
        pressed.append(index)
        pointer = index + 1
    return tuple(sorted(pressed))


def parseOutline(text: str, keys: tuple[str, ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(parseStroke(stroke, keys) for stroke in text.split("/"))


def checkedOutline(text: str, keys: tuple[str, ...], starboard: Starboard) -> tuple[tuple[int, ...], ...]:
    outline = parseOutline(text, keys)
    if renderFinalStrokesToRTFCRE(starboard, outline) != text:
        raise ValueError(f"chord {text!r} does not round-trip ({renderFinalStrokesToRTFCRE(starboard, outline)!r})")
    return outline
