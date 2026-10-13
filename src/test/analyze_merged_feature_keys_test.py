from types import SimpleNamespace
from typing import Any

from src.mergedfeaturekeys import beats, comboTense, mergeStroke, stripMarks
from util.analyze_merged_feature_keys import Entry, comboReading


def entry(ortho: str, lemmeGramCat: str, lastBase: tuple[int, ...], featureKeys: set[int]) -> Entry:
    word: Any = SimpleNamespace(ortho=ortho, lemmeGramCat=lemmeGramCat, frequency=1.0)
    return Entry(word, 0, (lastBase, tuple(sorted(featureKeys))), 1, frozenset(), frozenset({"présent"}), frequency=1.0,
                 featureKeys=frozenset(featureKeys), mergeKeys=frozenset(featureKeys))


class TestReadings:
    def test_tense(self) -> None:
        assert comboTense(["impératif", "nbr_s", "pers_2", "présent"]) == "impératif"
        assert comboTense(["indicatif", "nbr_s", "pers_1", "présent"]) == "présent"
        assert comboTense(["indicatif", "nbr_s", "passé", "pers_1"]) == "passé simple"
        assert comboTense(["indicatif", "imparfait", "nbr_s", "pers_1"]) == "imparfait"
        assert comboTense(["indicatif", "future", "nbr_p", "pers_3"]) == "future"
        assert comboTense(["nbr_s", "pers_1", "présent", "subjonctif"]) == "subjonctif"
        assert comboTense(["VER", "m", "participe", "passé", "s"]) == "participe"
        assert comboTense(["infinitif", "présent"]) == "infinitif"
        assert comboTense(["f", "p"]) == "nominal"

    def test_reading(self) -> None:
        assert comboReading(["impératif", "nbr_s", "pers_2", "présent"]) == "imp:pre:2s"
        assert comboReading(["indicatif", "nbr_p", "pers_3", "présent"]) == "ind:pre:3p"
        assert comboReading(["indicatif", "nbr_s", "passé", "pers_1"]) == "ind:pas:1s"
        assert comboReading(["conditionnel", "nbr_s", "pers_1", "présent"]) == "cnd:pre:1s"
        assert comboReading(["VER", "m", "participe", "passé", "s"]) == "par:pas"
        assert comboReading(["m", "p"]) == "nom:mp"
        assert comboReading(["f"]) == "nom:f"


class TestLadder:
    def test_level1_sounds_win(self) -> None:
        dites = entry("dites", "dire_VER", (4, 5, 13, 20), {18})
        dis = entry("dis", "dire_VER", (4, 5, 13), {18, 20})
        assert beats(dites, dis) == "level 1"
        assert beats(dis, dites) == ""

    def test_level2_absorbed_key_loses(self) -> None:
        fasse = entry("fasse", "faire_VER", (2, 4, 12, 17), {23})
        fassent = entry("fassent", "faire_VER", (2, 4, 12, 17), {17, 23})
        assert beats(fasse, fassent) == "level 2"
        assert beats(fassent, fasse) == ""

    def test_tie(self) -> None:
        laisses = entry("laisses", "laisser_VER", (6, 7, 13, 14, 17), {19})
        laides = entry("laides", "laid_ADJ", (6, 7, 13, 14, 19), {17})
        assert beats(laisses, laides) == "" and beats(laides, laisses) == ""


class TestStrokes:
    def test_merge_and_strip(self) -> None:
        assert mergeStroke((3, 13, 14), (18,)) == (3, 13, 14, 18)
        assert stripMarks(((6, 7, 13, 14, 19, 15), (17,), (10, 15))) == ((6, 7, 13, 14, 19), (17,))


class TestReservedChords:
    def test_sources(self) -> None:
        from src.keyboard import Starboard
        from util._reservedchords import attachKeypressesOf, reservedChords
        keyboard = Starboard.fromJSONFile("starboard3h.json")
        assert keyboard is not None
        reserved = reservedChords(keyboard)
        sources = set(reserved.values())
        assert {"punctuation", "commands", "pluvier punctuation", "pluvier numbers", "lapwing numbers", "spelling",
                "brief", "expression attach"} <= sources
        assert sum(1 for s in reserved.values() if s == "pluvier numbers") == 1023
        assert len(attachKeypressesOf()) == sum(1 for s in reserved.values() if s == "expression attach")
