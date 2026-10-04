"""
Decode-time ranking of the readings of one stroke tuple (user decision 2026-10-04).

`ExpressionDecoder.decode` returns EVERY reading; a Plover dictionary must answer with one. The
choice is a fixed, precomputed order, a pure function of the reading:

  0  plain live words only            (`dans` beats `ce` + `pan`: a stroke that is a word is that word;
                                       an attested plain reading first, then fewer pieces)
  1  a pure brief                     (no attach merged into it)
  2  an ATTESTED reading              (the composed reading of a pool expression, by frequency)
  3  anything else                    (the more probable reading, then a fixed tie-break)

Probability is the independence estimate: the product of the unigram probabilities of every word of the
reading (host, attach particles, words), so a reading that needs more or rarer words loses (`en je` beats
`d'` + `en` + `avec`). Inside class 0 an attested reading wins first, then the more probable (the stock
theory's own segmentation ambiguity, `et les` against the word `hélé`, is not this layer's).

The composer needs no `loses` check for ATTESTED expressions: the pool audit is shadow- and
collision-free, so no rival outranks an attested reading (measured: 0 of 611 layered pool
expressions lose). For an expression outside the pool the ranking just decides what the chord
reads as; the other reading becomes unreachable and is written longform.

The attested table is the only data the ranking needs besides the rules: `composedReading` and
`attestedTable` build it from the pool; the plugin loads it.
"""

from __future__ import annotations

from bisect import bisect_left
from math import log
from collections import defaultdict
from collections.abc import Iterable, Mapping

from src.affixes import PREFIX
from src.expressiondecoder import Decoding, ExpressionDecoder, Piece
from src.expressions import (EXCEPTION, MERGED, STANDALONE, AttachRule, Composition, Rules, Token,
                             planStream)
from src.keyboard import Strokes

__all__ = ["normalizedSignature", "composedReading", "attestedTable", "unitProbabilities", "ReadingRanker",
           "rankedDecode"]

Signature = tuple


_UNSEEN = 1e-12


def _fix(unit: str) -> str:
    return unit.replace("'", "").replace("œ", "oe")


def normalizedSignature(sig: Signature) -> Signature:
    """Spelling-insensitive reading signature: a pool unit (`j'`, `œil`) is the theory word (`j`, `oeil`)."""
    return tuple((p[0], tuple(_fix(u) for u in p[1])) + p[2:] for p in sig)


def unitProbabilities(frequencies: Iterable[tuple[str, float]]) -> dict[str, float]:
    """Unigram probabilities by spelling-normalized word, from (word, frequency) pairs."""
    mass: dict[str, float] = defaultdict(float)
    for word, freq in frequencies:
        mass[_fix(word)] += freq
    total = sum(mass.values()) or 1.0
    return {w: f / total for w, f in mass.items()}


def composedReading(rules: Rules, tokens: tuple[Token, ...], traced: Composition) -> Signature:
    """The (normalized) reading a composition produced, as the decoder would report it: words and briefs
    with the attaches merged into them, standalone keypresses, hostless clusters. An attach that fell to
    an exception leaves its particle as plain words."""
    plan = planStream(rules, list(tokens))
    prefix: dict[int, list[AttachRule]] = defaultdict(list)
    suffix: dict[int, list[AttachRule]] = defaultdict(list)
    clusterMember: set[int] = set()         # MERGED without a host target: a cluster follower
    for n, seg in enumerate(traced.segments):
        if seg.kind == "attach" and seg.outcome == MERGED and isinstance(seg.rule, AttachRule):
            start, end = seg.span
            target: int | None
            if seg.rule.position == PREFIX:
                i = bisect_left(plan.residual, end)
                target = plan.contentPosOf.get(plan.residual[i]) if i < len(plan.residual) else None
                if target is not None:
                    prefix[target].append(seg.rule)
            else:
                i = bisect_left(plan.residual, start) - 1
                target = plan.contentPosOf.get(plan.residual[i]) if i >= 0 else None
                if target is not None:
                    suffix[target].append(seg.rule)
            if target is None:
                clusterMember.add(n)
    pieces: list[Piece] = []
    pos = 0
    cluster: list[AttachRule] = []

    def flush() -> None:
        nonlocal cluster
        if cluster:
            pieces.append(Piece("cluster", rules=tuple(cluster)))
            cluster = []

    for n, seg in enumerate(traced.segments):
        if seg.kind == "attach" and isinstance(seg.rule, AttachRule):
            if seg.reason == "attachCluster" or n in clusterMember:
                if seg.outcome == STANDALONE:
                    flush()
                    cluster = [seg.rule]
                else:
                    cluster.append(seg.rule)
                continue
            flush()
            if seg.outcome == STANDALONE:
                pieces.append(Piece("standalone", rules=(seg.rule,)))
            elif seg.outcome == EXCEPTION:
                pieces.extend(Piece("content", (u,), False) for u in seg.units)
        elif seg.kind != "attach":
            flush()
            pieces.append(Piece("content", seg.units, seg.kind == "brief",
                                tuple(prefix[pos]), tuple(suffix[pos])))
            pos += 1
    flush()
    return normalizedSignature(tuple(p.signature() for p in pieces))


def attestedTable(entries: Iterable[tuple[Strokes, Signature, float]]) -> dict[tuple[Strokes, Signature], float]:
    """(outline, normalized reading) -> frequency, summing duplicates."""
    table: dict[tuple[Strokes, Signature], float] = {}
    for outline, sig, freq in entries:
        table[(outline, sig)] = table.get((outline, sig), 0.0) + freq
    return table


def _kind(sig: Signature) -> int:
    """0 plain words, 1 pure brief, 3 anything with an attach, standalone or cluster."""
    if any(p[0] != "content" or p[3] or p[4] for p in sig):
        return 3
    return 1 if any(p[2] for p in sig) else 0


class ReadingRanker:
    def __init__(self, attested: Mapping[tuple[Strokes, Signature], float],
                 unitProbability: Mapping[str, float]) -> None:
        """`unitProbability`: word (spelling-normalized: no apostrophe, `oe`) -> unigram probability."""
        self.attested = attested
        self.unitProbability = unitProbability

    def logProbability(self, sig: Signature) -> float:
        total = 0.0
        for piece in sig:
            units = list(piece[1])
            for rule in piece[3] + piece[4] + piece[5]:
                units.extend(rule[0])
            for unit in units:
                total += log(max(self.unitProbability.get(_fix(unit), 0.0), _UNSEEN))
        return total

    def key(self, outline: Strokes, sig: Signature) -> tuple:
        kind = _kind(sig)
        if kind == 0:
            # plain words: an attested one first (the pool's own `et les` against the word `hélé`: the stock
            # theory writes both alike), then fewer pieces
            return (0, -self.attested.get((outline, sig), 0.0), -self.logProbability(sig), sig)
        if kind == 1:
            return (1, 0.0, sig)
        freq = self.attested.get((outline, sig), 0.0)
        if freq:
            return (2, -freq, sig)
        return (3, -self.logProbability(sig), sig)

    def rank(self, outline: Strokes, readings: Iterable[Decoding]) -> list[Decoding]:
        """Readings best first (a total order: ties end on the signature)."""
        keyed = [(self.key(outline, normalizedSignature(tuple(p.signature() for p in r))), r)
                 for r in readings]
        return [r for _k, r in sorted(keyed, key=lambda kr: kr[0])]


def rankedDecode(decoder: ExpressionDecoder, ranker: ReadingRanker, strokes: Strokes) -> Decoding | None:
    """The single reading a dictionary answers with, None when the strokes are no expression outline."""
    from src.keyboard import canonicalizeStrokes
    outline = canonicalizeStrokes(strokes)
    ranked = ranker.rank(outline, decoder.decode(outline))
    return ranked[0] if ranked else None
