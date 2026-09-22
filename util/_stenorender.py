"""
Shared safe RTFCRE rendering for theory 2 (base strokes + Phase P's same-lemma
marks + the `*`/`#` lemma-homophone track), used by `util/export_plover_dictionary.py`
and the steno-trainer exporters.

`Starboard.strokesToRTFCRE` only handles base (onset/nucleus/coda) strokes: a
stroke containing STAR_KEY/HASH_KEY (10/15) carries no syllabic part, which
crashes its per-key bucketing (see that method's own docstring, and
`Dictionary.writeFinalTheory`'s, for why). Two shapes of stroke carry them:

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
