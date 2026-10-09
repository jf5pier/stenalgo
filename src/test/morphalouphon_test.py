import warnings
from collections import Counter
from pathlib import Path

import pytest

from util._morphalouphon import byOrthoCgram, loadMorphalouPronunciations, lookup, morphalouToLexicon

HEADER = ("LEMME;;;;;;;;;FLEXION;;;;;;;;\n"
          "GRAPHIE;ID;CATÉGORIE;SOUS CATÉGORIE;LOCUTION;GENRE;AUTRES LEMMES LIÉS;PHONÉTIQUE;ORIGINES;GRAPHIE;ID;NOMBRE;MODE;GENRE;TEMPS;PERSONNE;PHONÉTIQUE;ORIGINES\n")


def testNasalsAndPlainLetters() -> None:
    assert morphalouToLexicon("a b a d a~ ") == {"abad@"}
    assert morphalouToLexicon("a b a d a s j o~ ") == {"abadasj§"}
    assert morphalouToLexicon("a l e n j e~ ") == {"alenj5"}
    assert morphalouToLexicon("a l 9~ ") == {"al1"}


def testSpecialSymbols() -> None:
    assert morphalouToLexicon("a k a J a R d e ") == {"akaNaRde"}
    assert morphalouToLexicon("b a s t i N ") == {"bastiG"}
    assert morphalouToLexicon("a k H i t e ") == {"ak8ite"}
    assert morphalouToLexicon("p O l i s @ ") == {"pOlis°"}
    assert morphalouToLexicon("a b E s 9 R ") == {"abEs9R"}
    assert morphalouToLexicon("a b a~ d O n 2 z @ ") == {"ab@dOn2z°"}


def testAlternativesAndMarkers() -> None:
    assert morphalouToLexicon("a l e n j e~ OU a l E/ n j e~ ") == {"alenj5", "alEnj5"}
    assert morphalouToLexicon("a b R 2 v a Z @ OU a b R 6 v a Z @ ") == {"abR2vaZ°", "abR9vaZ°"}
    assert morphalouToLexicon("a p s E OU a p s E/ ") == {"apsE"}


def testUnknownSymbols() -> None:
    unknown: Counter[str] = Counter()
    assert morphalouToLexicon("c p e s e OU p e s e ", unknown) == {"pese"}
    assert unknown == Counter({"c": 1})
    assert morphalouToLexicon("") == set()


def testIndexAndLookup(tmp_path: Path) -> None:
    csv = tmp_path / "m.csv"
    csv.write_text(HEADER
                   + "abalobé;1;Nom commun;;;masculine;;a b a l O b e OU a b a l O/ b e ;x;abalobé;2;singular;-;-;-;-;a b a l O b e ;x\n"
                   + ";;;;;;;;;abalobés;3;plural;-;-;-;-;a b a l O b e ;x\n"
                   + "abaisser;4;Verbe;;;-;;a b E s e ;x;abaisser;5;-;infinitive;-;-;-;a b E s e ;x\n", encoding="utf-8")
    index = loadMorphalouPronunciations(csv)
    assert index == {("abalobé", "abalobé", "NOM", "m", "s"): {"abalObe"}, ("abalobé", "abalobés", "NOM", "m", "p"): {"abalObe"}}
    coarse = byOrthoCgram(index)
    assert lookup(index, coarse, "abalobé", "abalobés", "NOM", "m", "p") == ({"abalObe"}, "slot")
    assert lookup(index, coarse, "autre", "abalobés", "NOM", "f", "p") == ({"abalObe"}, "ortho")
    assert lookup(index, coarse, "x", "inconnu", "NOM", "m", "s") == (set(), "none")


def testMissingCsv(tmp_path: Path) -> None:
    missing = tmp_path / "absent.csv"
    with pytest.raises(FileNotFoundError, match="README"):
        loadMorphalouPronunciations(missing)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert loadMorphalouPronunciations(missing, required=False) == {}
    assert len(caught) == 1
