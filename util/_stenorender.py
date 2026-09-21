"""
Shared safe RTFCRE rendering for theory 2 (base strokes + Phase P's same-lemma
marks + the `*`/`#` lemma-homophone track), used by both
`util/export_plover_dictionary.py` and `util/export_practice_words.py`.

`Starboard.strokesToRTFCRE` only handles base (onset/nucleus/coda) strokes: a
stroke containing STAR_KEY/HASH_KEY (10/15) carries no syllabic part, which
crashes its per-key bucketing (see that method's own docstring, and
`Dictionary.writeFinalTheory`'s, for why). Such strokes are always bare
star/hash marks with no onset/nucleus/coda keys mixed in -- Phase P's coda
marks and the `*`/`#` track's marks are concatenated as separate whole
strokes, never merged into one (`src.ambiguitychecker.composeReservedKeyStrokes`)
-- so they're safe to render as a plain concatenation of key display names
instead of going through the syllable-bucketed path at all.
"""
from src.ambiguitychecker import HASH_KEY, STAR_KEY
from src.keyboard import Starboard, Strokes


def renderFinalStrokesToRTFCRE(starboard: Starboard, strokes: Strokes) -> str:
    parts = []
    for stroke in strokes:
        keys = sorted(set(stroke))
        if any(k in (STAR_KEY, HASH_KEY) for k in keys):
            parts.append("".join(starboard.keyDisplayName(k) for k in keys))
        else:
            parts.append(starboard.strokesToRTFCRE((tuple(keys),)))
    return "/".join(parts)
