"""Unit tests for src/phonologyrewrite.py: the override file, the in-memory rewrite and the elided-form pair overrides."""
from typing import Any

import pytest

from src.keyboard import Starboard
from src.phonologyrewrite import ElidedRow, PhonologyRules, applyPhonologyRewrite, loadPhonologyRules, overridesMd5
from src.word import GramCat, Word


def _word(ortho: str, phon: str, freq: float, lemme: str = "x", gramCat: GramCat = GramCat["PRO:per"]) -> Word:
    return Word(
        ortho=ortho, phonology=phon, lemme=lemme, gramCat=gramCat, orthoGramCat=[gramCat], gender=None, number=None, infoVerb=None,
        rawSyllCV="_".join(phon), rawOrthosyllCV="_".join(ortho), frequencyBook=freq, frequencyFilm=freq,
    )


def _keyboard() -> Starboard:
    keyboard = Starboard.fromJSONFile("starboard3h.json")
    assert keyboard is not None
    return keyboard


class TestLoadRules:
    def test_the_committed_file_loads(self) -> None:
        rules = loadPhonologyRules()
        assert rules.phonology["je"] == "Z" and rules.phonology["ce"] == "s" and rules.phonology["se"] == "s"
        assert ElidedRow("c'", "ce", "s") in rules.elided and ElidedRow("l'", "le", "") in rules.elided
        assert overridesMd5() is not None

    def test_marking_overrides_mark_the_elided_form(self) -> None:
        rules = PhonologyRules({}, (ElidedRow("c'", "ce", "s"), ElidedRow("s'", "se", "")))
        assert rules.markingOverrides() == {frozenset({"ce", "c'"}): "c'", frozenset({"se", "s'"}): "s'"}

    def test_a_malformed_row_is_refused(self, tmp_path: Any) -> None:
        path = tmp_path / "o.tsv"
        path.write_text("kind\tspelling\tphonology\tbase\tnote\nphonology\tje\t\t\t\n", encoding="utf-8")
        with pytest.raises(ValueError):
            loadPhonologyRules(str(path))
        path.write_text("kind\tspelling\tphonology\tbase\tnote\nbogus\tje\tZ\t\t\n", encoding="utf-8")
        with pytest.raises(ValueError):
            loadPhonologyRules(str(path))


class TestApply:
    def test_an_overridden_spelling_moves_to_its_new_outline_and_the_input_is_untouched(self) -> None:
        keyboard = _keyboard()
        je = _word("je", "Z°", 100.0)
        theory: dict[Any, Any] = {(((1,),),): [je]}
        rules = PhonologyRules({"je": "Z"}, ())
        result = applyPhonologyRewrite(theory, keyboard, rules)
        (strokes, words), = result.items()
        assert [w.ortho for w in words] == ["je"] and words[0].phonology == "Z"
        assert strokes == (keyboard.getStrokeOfSyllableByPart({"onset": ["Z"], "nucleus": [], "coda": []}),)
        assert je.phonology == "Z°" and list(theory.values()) == [[je]]

    def test_a_missing_elided_form_is_created_from_the_frequent_readings_only(self) -> None:
        keyboard = _keyboard()
        theory: dict[Any, Any] = {(((1,),),): [_word("je", "Z°", 100.0), _word("je", "Z°", 0.0, gramCat=GramCat.NOM)]}
        rules = PhonologyRules({"je": "Z"}, (ElidedRow("j'", "je", "Z"),))
        words = [w for ws in applyPhonologyRewrite(theory, keyboard, rules).values() for w in ws]
        elided = [w for w in words if w.ortho == "j'"]
        assert len(elided) == 1 and elided[0].phonology == "Z" and elided[0].frequency == 0.0

    def test_an_elided_form_the_lexicon_has_is_not_created_again(self) -> None:
        keyboard = _keyboard()
        theory: dict[Any, Any] = {(((1,),),): [_word("le", "l°", 100.0)], (((2,),),): [_word("l'", "l", 50.0)]}
        rules = PhonologyRules({"le": "l"}, (ElidedRow("l'", "le", ""),))
        words = [w for ws in applyPhonologyRewrite(theory, keyboard, rules).values() for w in ws]
        assert sorted(w.ortho for w in words) == ["l'", "le"]


    def test_a_dropped_reading_leaves_the_theory_and_the_other_readings_stay(self) -> None:
        keyboard = _keyboard()
        theory: dict[Any, Any] = {(((1,),),): [_word("me", "m°", 100.0), _word("me", "m°", 2.0, gramCat=GramCat.NOM)]}
        rules = PhonologyRules({"me": "m"}, (), frozenset({("me", "NOM")}))
        words = [w for ws in applyPhonologyRewrite(theory, keyboard, rules).values() for w in ws]
        assert [(w.ortho, w.gramCat.name) for w in words] == [("me", "PRO:per")]

    def test_a_drop_row_without_a_gramcat_is_refused(self, tmp_path: Any) -> None:
        path = tmp_path / "o.tsv"
        path.write_text("kind\tspelling\tphonology\tbase\tgramcat\tnote\ndrop\tme\t\t\t\t\n")
        with pytest.raises(ValueError):
            loadPhonologyRules(str(path))


class TestElidedPlacement:
    def test_an_elided_form_takes_the_code_right_after_its_base(self) -> None:
        from src import ambiguitychecker as ac

        def w(ortho: str, freq: float) -> Word:
            return _word(ortho, "s", freq, lemme=ortho)

        words = [w("ce", 8000.0), w("se", 3000.0), w("s'", 2500.0), w("c'", 0.0)]
        nodes: dict[Any, list[Word]] = {ac.markFamilyKey(x): [x] for x in words}
        saved = dict(ac.ELIDED_BASES)
        ac.ELIDED_BASES.update({"c'": "ce", "s'": "se"})
        try:
            codes = ac.assignMarkNodeCodes(nodes, [words])
        finally:
            ac.ELIDED_BASES.clear()
            ac.ELIDED_BASES.update(saved)
        byOrtho = {x.ortho: codes[ac.markFamilyKey(x)] for x in words}
        assert byOrtho == {"ce": (), "c'": ("*",), "se": ("#",), "s'": ("*#",)}
