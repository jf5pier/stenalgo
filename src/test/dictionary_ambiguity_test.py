"""Dictionary.ensureAmbiguityStats: the ambiguity tables are computed on demand, once (util.build_phonetic_theory no
longer computes them; only the keyboard layout work reads them)."""
from typing import Any

from dictionary import Dictionary


def _bareDictionary(filled: bool) -> Any:
    dictionary = object.__new__(Dictionary)  # no corpus read: only the tables matter here
    table: dict[str, dict[Any, float]] = {"onset": {}, "nucleus": {}, "coda": {}}
    dictionary.syllabicAmbiguity = {part: dict(rows) for part, rows in table.items()}
    dictionary.lexicalAmbiguity = {part: dict(rows) for part, rows in table.items()}
    dictionary.syllabicPartAmbiguity = {part: dict(rows) for part, rows in table.items()}
    if filled:
        for name in ("syllabicAmbiguity", "lexicalAmbiguity", "syllabicPartAmbiguity"):
            setattr(dictionary, name, {part: {("a", "b"): 1.0} for part in ("onset", "nucleus", "coda")})
    return dictionary


def test_empty_tables_are_computed_once() -> None:
    dictionary = _bareDictionary(filled=False)
    calls: list[int] = []

    def fakeAnalysis() -> None:
        calls.append(1)
        for name in ("syllabicAmbiguity", "lexicalAmbiguity", "syllabicPartAmbiguity"):
            setattr(dictionary, name, {part: {("a", "b"): 1.0} for part in ("onset", "nucleus", "coda")})

    dictionary.analyseAmbiguities = fakeAnalysis
    assert not dictionary.hasAmbiguityStats()
    dictionary.ensureAmbiguityStats()
    dictionary.ensureAmbiguityStats()
    assert calls == [1] and dictionary.hasAmbiguityStats()


def test_filled_tables_are_left_alone() -> None:
    dictionary = _bareDictionary(filled=True)

    def mustNotRun() -> None:
        raise AssertionError("must not recompute")

    dictionary.analyseAmbiguities = mustNotRun
    assert dictionary.hasAmbiguityStats()
    dictionary.ensureAmbiguityStats()  # an old Dictionary.pickle that carries them
