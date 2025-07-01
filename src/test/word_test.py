import pytest
#import sys,os
#sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) )
from ..word import Word, GramCat

@pytest.fixture
def word_sample() -> Word:
    return Word(
        ortho="enivre",
        phonology="@nivR",
        lemme="enivrer",
        gramCat=GramCat.VER,
        orthoGramCat=[GramCat.VER],
        gender="",
        number="",
        infoVerb="",
        rawSyllCV="@|n_i_v_R_#",
        rawOrthosyllCV="e|n_i_v_r_e",
        frequencyBook=1.0,
        frequencyFilm=2.0,
    )

def test_post_init_sets_frequency(word_sample: Word) -> None:
    assert word_sample.frequency == word_sample.frequencyFilm

def test_fix_e_n_en_applies_replacement():
    w = Word(
        ortho="enivre",
        phonology="@nivR",
        lemme="enivrer",
        gramCat=GramCat.VER,
        orthoGramCat=[GramCat.VER],
        gender="",
        number="",
        infoVerb="",
        rawSyllCV="@|n_i_v_R_#",
        rawOrthosyllCV="e|n_i_v_r_e",
        frequencyBook=1.0,
        frequencyFilm=2.0,
    )
    # After fix_e_n_en called in __post_init__ , rawSyllCV and rawOrthosyllCV should be changed
    assert "@|n_" not in w.rawSyllCV
    assert "e|n_" not in w.rawOrthosyllCV

def test_phonemesToSyllableNames(word_sample: Word) -> None:
    # withSilent True
    result = word_sample.phonemesToSyllableNames()
    assert isinstance(result, list)
    assert all(isinstance(s, str) for s in result)
    assert result == ["@", "ivR#"]
    # withSilent False
    result2 = word_sample.phonemesToSyllableNames(withSilent=False)
    assert all("#" not in s for s in result2)
    assert all(isinstance(s, str) for s in result2)
    assert result2 == ["@", "ivR"]

def test_graphemsToSyllables(word_sample: Word) -> None:
    result = word_sample.graphemsToSyllables()
    assert isinstance(result, list)
    assert all(isinstance(s, str) for s in result)
    assert result == ["en","ivre"]
    result2 = word_sample.graphemsToSyllables(withSilent=False)
    assert all("#" not in s for s in result2)
    assert all(isinstance(s, str) for s in result2)
    assert result2 == ["en","ivre"]

def test_syllablesToWord(word_sample: Word) -> None:
    result = word_sample.syllablesToWord()
    assert isinstance(result, str)
    assert result == "@ivR#"  

def test_parseOrthoSyll(word_sample: Word) -> None:
    parsed = word_sample.parseOrthoSyll()
    assert isinstance(parsed, list)
    assert all(isinstance(s, list) for s in parsed)
    assert parsed == [["en"],["i","v","r","e"]]

def test_parsePhonoSyll(word_sample: Word) -> None:
    parsed = word_sample.parsePhonoSyll()
    assert isinstance(parsed, list)
    assert all(isinstance(s, list) for s in parsed)
    assert parsed == [["@"],["i","v","R","#"]]

def test_replaceSyllables(word_sample: Word) -> None:
    orig = word_sample.phonology
    replaced = word_sample.replaceSyllables("ni", "mi")
    replaced2 = word_sample.replaceSyllables("fa", "ta")
    assert isinstance(replaced, str)
    # If "ni" is not in phonology, should be unchanged
    assert orig != replaced
    assert "mi" in replaced
    assert orig == replaced2

if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__]))
