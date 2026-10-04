"""Stroke primitives shared by the pipeline and the Plover plugin (stdlib only, so the decoder's vendored
copy in `plover_stenalgo/_core` needs nothing else). `src.keyboard` re-exports these names."""

from functools import lru_cache
from typing import TypeAlias

Keypress: TypeAlias = tuple[int, ...]
Stroke: TypeAlias = tuple[int, ...]
Strokes: TypeAlias = tuple[Stroke, ...]


# maxsize=None: callers present ~80k distinct stroke tuples per step (one per word
# group), so the default 128-entry cache thrashed and recomputed on nearly every
# call (perf round 2, 2026-09-29). Pure tuple-in/tuple-out, unbounded is safe.
@lru_cache(maxsize=None)
def canonicalizeStrokes(strokes: Strokes) -> Strokes:
    """
    Collapse each Stroke to the physically-realized chord it produces: a stroke is a
    set of simultaneously-pressed keys, so a key can be pressed at most once per
    stroke and has no ordering relative to the others. `theory`'s raw Strokes tuples
    preserve per-phoneme insertion order (useful for `strokesToString`'s human-
    readable rendering), so two words whose phoneme sequences differ only in key
    order or in an incidental repeated key (e.g. one phoneme's dedicated key already
    covered by another phoneme's multi-key digraph) get distinct raw tuples despite
    typing identically. Anything that decides whether two words COLLIDE on the same
    physical stroke (elicitation-cluster discovery, the */# reserved-key grouping)
    must compare this canonical form, not the raw tuple -- matching what
    `Starboard.strokesToRTFCRE`'s `sorted(set(stroke))` already does at render time.

    lru_cache'd: pure tuple-in/tuple-out, called per word across several steps.
    """
    return tuple(tuple(sorted(set(stroke))) for stroke in strokes)
