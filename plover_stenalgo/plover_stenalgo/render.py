"""A decoded reading rendered as one Plover translation string."""
from __future__ import annotations

from itertools import permutations

from ._core.elision import elisionAgrees
from ._core.expressiondecoder import Decoding, Piece
from ._core.expressionmodel import AttachRule

OrderBan = frozenset  # of (expression, expression) pairs


def _order(rules: tuple[AttachRule, ...], following: str | None, ban: OrderBan) -> list[AttachRule]:
    """The particles in French order: the stroke lost it (the union of keypresses is commutative). The first
    order (rules sorted, so deterministic) in which no adjacent pair is banned and every elision-pair form
    agrees with the word after it; failing that, the first without banned pairs, then the first."""
    candidates = list(permutations(sorted(rules, key=lambda r: (r.expression, r.keypress))))

    def fine(order: tuple[AttachRule, ...], elision: bool) -> bool:
        for i, rule in enumerate(order):
            nxt = order[i + 1].expression[0] if i + 1 < len(order) else following
            if i + 1 < len(order) and (rule.expression, order[i + 1].expression) in ban:
                return False
            if elision and rule.elision and nxt is not None and not elisionAgrees(rule.elision, nxt):
                return False
        return True

    for elision in (True, False):
        for order in candidates:
            if fine(order, elision):
                return list(order)
    return list(candidates[0])


def _words(piece: Piece, ban: OrderBan) -> list[str]:
    if piece.kind == "content":
        host = piece.units[0] if piece.units else None
        before = _order(piece.prefix, host, ban) if piece.prefix else []
        after = _order(piece.suffix, None, ban) if piece.suffix else []
        return ([w for r in before for w in r.expression] + list(piece.units)
                + [w for r in after for w in r.expression])
    if piece.kind == "standalone":
        return list(piece.rules[0].expression)
    return [w for r in _order(piece.rules, None, ban) for w in r.expression]


def render(reading: Decoding, ban: OrderBan = frozenset()) -> str:
    """Words joined by spaces, an elided word (`qu'`) glued to the next one. A reading that ends on an elided
    word is closed with `{^}`, which attaches the next stroke's word to it."""
    words = [w for piece in reading for w in _words(piece, ban)]
    text = ""
    for word in words:
        text += word if not text or text.endswith("'") else " " + word
    return text + "{^}" if text.endswith("'") else text


def isExpression(reading: Decoding) -> bool:
    """One piece that is not a plain word: a brief, a merged attach, a standalone keypress or a cluster."""
    if len(reading) != 1:
        return False
    piece = reading[0]
    return piece.kind != "content" or piece.brief or bool(piece.prefix or piece.suffix)
