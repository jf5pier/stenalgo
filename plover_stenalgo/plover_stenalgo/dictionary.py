"""Plover dictionary plugin: reads the expression outlines of Stenalgo's abbreviation layer.

Registered as the `stenalgo` dictionary extension: add `plover_stenalgo_expressions.stenalgo` (written by
`util/export_expression_data.py`) to Plover's dictionary list, ABOVE the stock JSON dictionary. The two files
travel together: the word index is read from the JSON named in the data (same folder), and a fingerprint
refuses a JSON built from another theory. A stroke that is a plain word still reads as that word. The dictionary answers only keys that decode, best reading first, as
ONE expression piece (a brief, a merged attach, a standalone keypress or a cluster); longer keys return None
and the translator falls back to shorter windows, one piece at a time.
"""
from __future__ import annotations

import json
import os

from plover.steno_dictionary import StenoDictionary

from ._core.elision import ELISION_PAIRS
from ._core.expressiondata import loadBundle
from ._core.expressionranking import normalizedSignature, rankedDecode
from ._core.strokes import canonicalizeStrokes
from .render import isExpression, render
from .stroke import parseOutline
from .wordindex import readWordIndex


CACHE_LIMIT = 50000


def _fold(sig: tuple) -> tuple:
    """A reading with every elided particle replaced by its base form: a hostless chord cannot tell `l'` from
    `le` (one chord for the pair), so an attested text answers for both."""
    fold = lambda rules: tuple((tuple(ELISION_PAIRS.get(u, u) for u in e), pos) for e, pos in rules)  # noqa: E731
    return tuple((p[0], p[1], p[2], fold(p[3]), fold(p[4]), fold(p[5])) for p in sig)


class StenalgoExpressionDictionary(StenoDictionary):
    readonly = True

    def __init__(self) -> None:
        super().__init__()
        self._decoder = None
        self._ranker = None
        self._ban: frozenset = frozenset()
        self._text: dict = {}
        self._cache: dict[tuple[str, ...], str | None] = {}

    def _load(self, filename: str) -> None:
        with open(filename, encoding="utf-8") as fh:
            data = json.load(fh)
        words = None
        if "words" not in data:       # the word index is the stock dictionary named next to this file
            words = readWordIndex(os.path.join(os.path.dirname(os.path.abspath(filename)), data["wordIndex"]["file"]))
        self._decoder, self._ranker = loadBundle(data, words)
        self._ban = self._decoder.rules.orderBan
        self._longest_key = self._decoder._maxLen
        self._cache = {}
        text: dict = {}
        for (o, sig), t in sorted(self._ranker.attestedText.items(), key=lambda kv: self._ranker.attested.get(kv[0], 0.0)):
            text[(o, _fold(sig))] = t          # ascending frequency: the most frequent twin wins
        self._text = text

    def _save(self, filename: str) -> None:
        raise NotImplementedError("the expression dictionary is generated, not edited")

    def get(self, key, fallback=None):
        if self._decoder is None or "" in key:     # '' is Plover's prefix stroke: cheap miss
            return fallback
        try:
            return self._cache[key] if self._cache[key] is not None else fallback
        except KeyError:
            pass
        if len(self._cache) >= CACHE_LIMIT:
            self._cache.clear()
        self._cache[key] = value = self._translate(key)
        return fallback if value is None else value

    def _translate(self, key: tuple[str, ...]) -> str | None:
        outline = parseOutline(key)
        if outline is None:
            return None
        reading = rankedDecode(self._decoder, self._ranker, outline)
        if reading is None or not isExpression(reading):
            return None
        text = self._text.get(
            (canonicalizeStrokes(outline), _fold(normalizedSignature(tuple(p.signature() for p in reading)))))
        if text is None:
            return render(reading, self._ban)
        return text + "{^}" if text.endswith("'") else text

    def __getitem__(self, key):
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value
