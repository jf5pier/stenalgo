from dataclasses import dataclass
from typing import Any

from src.mergedfeaturekeys import mergeFeatureKeys

PERS_1 = ["indicatif", "nbr_s", "pers_1", "présent"]
SUBJ_1 = ["nbr_s", "pers_1", "présent", "subjonctif"]


@dataclass(frozen=True)
class FakeWord:
    ortho: str
    lemmeGramCat: str
    frequency: float = 1.0


class FakeKeyboard:
    def getStrokeCost(self, stroke: Any, part: str) -> int:
        return 1


def record(ortho: str, base: tuple[int, ...], readings: list[list[str]]) -> dict[str, Any]:
    return {"lemmeGramCat": f"{ortho}_VER", "strokes": [list(base)], "pressSets": {ortho: [["pers_1"]]},
            "readings": {ortho: [[readings[0]]]}}


def run(words: dict[Any, list[Any]], resolved: list[dict[str, Any]]) -> dict[Any, list[Any]]:
    wordToStrokes: dict[Any, Any] = {w: (outlines[0][0],) for w, outlines in words.items()}
    byOrthoLemme = {(w.ortho, w.lemmeGramCat): [w] for w in words}
    keyboard: Any = FakeKeyboard()
    merged, _entries = mergeFeatureKeys(words, wordToStrokes, byOrthoLemme, resolved, {4: frozenset({"pers_1"})},
                                        keyboard, {}, lambda s: "/".join("".join(map(str, k)) for k in s))
    return merged


class TestMergeFeatureKeys:
    def test_merged_primary_then_long(self) -> None:
        aa = FakeWord("aa", "aa_VER")
        merged = run({aa: [((1, 2), (18,))]}, [record("aa", (1, 2), [PERS_1])])
        assert merged[aa] == [((1, 2, 18),), ((1, 2), (18,))]

    def test_occupied_keeps_long(self) -> None:
        aa, bb = FakeWord("aa", "aa_VER"), FakeWord("bb", "bb_VER")
        merged = run({aa: [((1, 2), (18,))], bb: [((1, 2, 18),)]}, [record("aa", (1, 2), [PERS_1])])
        assert merged[aa] == [((1, 2), (18,))]
        assert merged[bb] == [((1, 2, 18),)]

    def test_excluded_tense_keeps_long(self) -> None:
        aa = FakeWord("aa", "aa_VER")
        merged = run({aa: [((1, 2), (18,))]}, [record("aa", (1, 2), [SUBJ_1])])
        assert merged[aa] == [((1, 2), (18,))]
