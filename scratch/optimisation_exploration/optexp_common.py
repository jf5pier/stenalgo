"""Shared loaders for the optimisation exploration scripts (read-only on the pipeline outputs)."""
import json
import os
import sys
from typing import Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.keyboard import Starboard  # noqa: E402
from util._theoryio import loadDictionary, loadDisambiguatedTheory, loadPhoneticTheory  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
MARKS = frozenset({0, 1, 10, 15})


def canon(strokes: Any) -> tuple[tuple[int, ...], ...]:
    """Canonical outline: strokes with sorted keys, empty strokes dropped."""
    return tuple(tuple(sorted(set(s))) for s in strokes if s)


def loadAll() -> tuple[Starboard, Any, dict[Any, list[Any]], dict[Any, Any]]:
    kb = Starboard.fromJSONFile("starboard3h.json")
    assert kb is not None
    dictionary = loadDictionary()
    dis = loadDisambiguatedTheory(kb)
    phon = loadPhoneticTheory()
    base: dict[Any, Any] = {}
    for strokes, words in phon.items():
        for w in words:
            base[w] = strokes
    return kb, dictionary, dis, base


def loadPlover(path: str) -> dict[str, str]:
    with open(path, encoding="utf8") as f:
        data: dict[str, str] = json.load(f)
    return data
