"""Unit tests for src/layoutstatistics.py: the layout statistics rebuilt from a list of words (docs/PHONOLOGY_REWRITE_PLAN.md PRP11)."""
from collections.abc import Iterator
from typing import Any

import pytest

from src.grammar import Syllable
from src.keyboard import Starboard
from src.layoutstatistics import (
    buildSyllableStatistics, canonicalStatistics, layoutInput, loadFrequentWords, loadLayoutStatistics, saveLayoutStatistics, wordsOfTheory,
)
from src.word import GramCat, Word


def _word(ortho: str, phon: str, freq: float, lemme: str = "x", gramCat: GramCat = GramCat.NOM) -> Word:
    return Word(
        ortho=ortho, phonology=phon, lemme=lemme, gramCat=gramCat, orthoGramCat=[gramCat], gender=None, number=None, infoVerb=None,
        rawSyllCV="_".join(phon), rawOrthosyllCV="_".join(ortho), frequencyBook=freq, frequencyFilm=freq,
    )


@pytest.fixture(autouse=True)
def restoreSyllableState() -> Iterator[None]:
    """The statistics are class-level state of Syllable: leave it as other tests expect it."""
    saved = (Syllable.allPhonemeCol, Syllable.phonemeColByPart, Syllable.biphonemeColByPart, Syllable.multiphonemeColByPart)
    yield
    Syllable.allPhonemeCol, Syllable.phonemeColByPart, Syllable.biphonemeColByPart, Syllable.multiphonemeColByPart = saved


def _weights(part: str) -> dict[str, float]:
    return {name: values[0] for name, values in canonicalStatistics()[part]["phonemes"].items()}


TOY = [_word("ba", "ba", 10.0), _word("pa", "pa", 5.0), _word("jo", "Z°", 100.0, gramCat=GramCat["PRO:per"])]


class TestBuild:
    def test_frequencies_are_added_per_syllabic_part(self) -> None:
        buildSyllableStatistics(TOY, set())
        assert _weights("onset") == {"b": 10.0, "p": 5.0, "Z": 100.0}
        assert _weights("nucleus") == {"a": 15.0, "°": 100.0}
        assert _weights("coda") == {}

    def test_an_excluded_spelling_adds_nothing_but_is_still_tracked(self) -> None:
        collection = buildSyllableStatistics(TOY, {"jo"})
        assert _weights("onset")["Z"] == 0.0 and _weights("nucleus")["°"] == 0.0
        syllable = collection.getSyllable("Z°")
        assert syllable is not None and syllable.frequency == 0.0 and list(syllable.phonoWords) == ["Z°"]

    def test_a_second_build_in_the_same_process_starts_from_scratch(self) -> None:
        buildSyllableStatistics(TOY, set())
        first = canonicalStatistics()
        buildSyllableStatistics(TOY, set())
        assert canonicalStatistics() == first

    def test_the_order_of_the_words_does_not_change_the_content(self) -> None:
        buildSyllableStatistics(TOY, set())
        first = canonicalStatistics()
        buildSyllableStatistics(list(reversed(TOY)), set())
        assert canonicalStatistics() == first

    def test_a_forced_phonology_moves_the_weight_to_the_new_phonemes(self) -> None:
        forced = _word("jo", "Z", 100.0, gramCat=GramCat["PRO:per"])
        buildSyllableStatistics([TOY[0], TOY[1], forced], set())
        assert _weights("onset")["Z"] == 100.0 and "°" not in _weights("nucleus")


class TestWords:
    def test_a_word_under_several_outlines_counts_once(self) -> None:
        ba = TOY[0]
        theory: dict[Any, Any] = {((1,),): [ba], ((2,),): [ba, TOY[1]]}
        assert wordsOfTheory(theory) == [ba, TOY[1]]

    def test_the_frequent_words_file_gives_the_top_spellings(self) -> None:
        words = loadFrequentWords()
        assert len(words) == 200 and "je" in words

    def test_the_rewrite_weighs_the_overridden_spellings_and_keeps_the_other_frequent_words_out(self) -> None:
        keyboard = Starboard.fromJSONFile("starboard3h.json")
        assert keyboard is not None
        frequent = ["je", "de", "avec"]
        je = _word("je", "Z°", 100.0, lemme="je", gramCat=GramCat["PRO:per"])
        theory: dict[Any, Any] = {((1,),): [je]}
        plainWords, plainExcluded = layoutInput(theory, frequent, keyboard, rewrite=False)
        assert plainWords == [je] and plainExcluded == {"je", "de", "avec"}
        rewrittenWords, excluded = layoutInput(theory, frequent, keyboard, rewrite=True)
        # j' is created from je (the toy theory lacks it), typed with the same forced phonology
        assert sorted((w.ortho, w.phonology) for w in rewrittenWords) == [("j'", "Z"), ("je", "Z")] and excluded == {"avec"}


class TestSaveLoad:
    def test_the_file_restores_the_collections(self, tmp_path: Any) -> None:
        buildSyllableStatistics(TOY, set())
        Syllable.optimizeBiphonemeOrder()
        expected = canonicalStatistics()
        path = str(tmp_path / "stats.pickle")
        saveLayoutStatistics(path, {"syllabicPartAmbiguity": {"onset": {}}}, {"rewrite": False})
        buildSyllableStatistics([], set())
        envelope = loadLayoutStatistics(path)
        assert canonicalStatistics() == expected
        assert envelope["meta"] == {"rewrite": False} and envelope["tables"] == {"syllabicPartAmbiguity": {"onset": {}}}

    def test_an_unknown_format_is_refused(self, tmp_path: Any) -> None:
        import pickle
        path = tmp_path / "old.pickle"
        path.write_bytes(pickle.dumps({"format": 0}))
        with pytest.raises(RuntimeError):
            loadLayoutStatistics(str(path))
