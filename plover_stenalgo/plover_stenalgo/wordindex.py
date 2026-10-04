"""The word index of the expression decoder, read from the stock Stenalgo dictionary (no Plover import)."""
from __future__ import annotations

import json

from .stroke import parseOutline


def readWordIndex(path: str) -> dict:
    """The stock dictionary as an outline -> written words index (key ids, one entry per outline)."""
    with open(path, encoding="utf-8") as fh:
        stock = json.load(fh)
    index: dict = {}
    for steno, word in stock.items():
        outline = parseOutline(tuple(steno.split("/")))
        if outline is None:
            raise ValueError(f"{path}: `{steno}` is not a stroke of the Stenalgo system (is the Stenalgo French "
                             f"system active?)")
        index.setdefault(outline, set()).add(word)
    return index
