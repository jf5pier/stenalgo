import pytest
from ..grammar import (
    Phoneme, Biphoneme, Multiphoneme,
    PhonemeCollection, BiphonemeCollection, MultiphonemeCollection,
    Syllable, SyllableCollection,
)
from ..word import Word, GramCat


# ── Fixture: reset Syllable class-level shared state ──────────────────────────

@pytest.fixture(autouse=True)
def reset_syllable_state():
    """Reset all class-level collections on Syllable before each test.
    Without this, phoneme/biphoneme/multiphoneme collections leak between tests."""
    Syllable.allPhonemeCol = PhonemeCollection("all")
    Syllable.phonemeColByPart = {
        "onset": PhonemeCollection("onset"),
        "nucleus": PhonemeCollection("nucleus"),
        "coda": PhonemeCollection("coda"),
    }
    Syllable.biphonemeColByPart = {
        "onset": BiphonemeCollection("onset"),
        "nucleus": BiphonemeCollection("nucleus"),
        "coda": BiphonemeCollection("coda"),
    }
    Syllable.multiphonemeColByPart = {
        "onset": MultiphonemeCollection("onset"),
        "nucleus": MultiphonemeCollection("nucleus"),
        "coda": MultiphonemeCollection("coda"),
    }
    yield


# ── Helper to create minimal Word objects for tracking ────────────────────────

def _make_word(ortho: str, phonology: str, frequency: float = 1.0) -> Word:
    return Word(
        ortho=ortho,
        phonology=phonology,
        lemme=ortho,
        gramCat=GramCat.NOM,
        orthoGramCat=[GramCat.NOM],
        gender="m",
        number="s",
        infoVerb="",
        rawSyllCV=phonology,
        rawOrthosyllCV=ortho,
        frequencyBook=frequency,
        frequencyFilm=frequency,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Phoneme
# ═══════════════════════════════════════════════════════════════════════════════

class TestPhoneme:

    def test_vowel_classification(self):
        p = Phoneme("a")
        assert p.isVowel() is True
        assert p.isConsonant() is False
        assert p.isTemporaryPhoneme() is False

    def test_consonant_classification(self):
        p = Phoneme("R")
        assert p.isVowel() is False
        assert p.isConsonant() is True
        assert p.isTemporaryPhoneme() is False

    def test_temporary_phoneme_classification(self):
        p = Phoneme("x")
        assert p.isVowel() is False
        assert p.isConsonant() is False
        assert p.isTemporaryPhoneme() is True

    def test_invalid_phoneme_raises_value_error(self):
        with pytest.raises(ValueError, match="not a vowel or consonant"):
            Phoneme("Q")

    def test_post_init_initializes_pos_frequencies(self):
        p = Phoneme("a")
        assert p.posFrequency == [0.0] * 7
        assert p.invPosFrequency == [0.0] * 7

    def test_increase_frequency_accumulates(self):
        p = Phoneme("a")
        p.increaseFrequency(3.0, pos=1, invPos=5)
        p.increaseFrequency(2.0, pos=1, invPos=5)
        assert p.frequency == 5.0
        assert p.posFrequency[1] == 5.0
        assert p.invPosFrequency[5] == 5.0

    def test_increase_frequency_defaults(self):
        p = Phoneme("a")
        p.increaseFrequency(4.0)
        assert p.posFrequency[0] == 4.0
        assert p.invPosFrequency[0] == 4.0

    def test_increase_frequency_boundary_positions(self):
        p = Phoneme("a")
        p.increaseFrequency(1.0, pos=0, invPos=6)
        p.increaseFrequency(2.0, pos=6, invPos=0)
        assert p.posFrequency[0] == 1.0
        assert p.posFrequency[6] == 2.0
        assert p.invPosFrequency[6] == 1.0
        assert p.invPosFrequency[0] == 2.0

    def test_eq_phoneme_to_phoneme(self):
        p1 = Phoneme("a", frequency=10.0)
        p2 = Phoneme("a", frequency=99.0)
        assert p1 == p2

    def test_eq_phoneme_to_string(self):
        p = Phoneme("a")
        assert p == "a"
        assert p != "b"

    def test_eq_phoneme_to_other_type(self):
        p = Phoneme("a")
        assert p != 42
        assert p != None
        assert p != ["a"]

    def test_lt_sorts_by_frequency(self):
        p1 = Phoneme("a", frequency=1.0)
        p2 = Phoneme("R", frequency=3.0)
        p3 = Phoneme("t", frequency=2.0)
        result = sorted([p1, p2, p3])
        assert [p.name for p in result] == ["a", "t", "R"]

    def test_mutual_exclusivity_all_vowels(self):
        """Every vowel phoneme should be vowel only."""
        for c in Phoneme.nucleusPhonemes:
            p = Phoneme(c)
            assert p.isVowel() is True
            assert p.isConsonant() is False

    def test_mutual_exclusivity_all_consonants(self):
        """Every consonant phoneme should be consonant only."""
        for c in Phoneme.consonantPhonemes:
            p = Phoneme(c)
            assert p.isConsonant() is True
            assert p.isVowel() is False

    def test_str_and_repr(self):
        p = Phoneme("R", frequency=12.5)
        assert str(p) == "R"
        assert repr(p) == "R:12.5"


# ═══════════════════════════════════════════════════════════════════════════════
# Biphoneme
# ═══════════════════════════════════════════════════════════════════════════════

class TestBiphoneme:

    def test_eq_same_pair(self):
        b1 = Biphoneme(("a", "b"), frequency=1.0)
        b2 = Biphoneme(("a", "b"), frequency=99.0)
        assert b1 == b2

    def test_eq_reversed_pair_not_equal(self):
        """Biphonemes are ordered — (a,b) != (b,a)."""
        b1 = Biphoneme(("a", "b"))
        b2 = Biphoneme(("b", "a"))
        assert b1 != b2

    def test_eq_non_biphoneme(self):
        b = Biphoneme(("a", "b"))
        assert b != ("a", "b")
        assert b != "ab"
        assert b != 42

    def test_same_phoneme_pair(self):
        b = Biphoneme(("R", "R"))
        assert b.pair == ("R", "R")

    def test_increase_frequency(self):
        b = Biphoneme(("a", "b"))
        b.increaseFrequency(3.0)
        b.increaseFrequency(2.0)
        assert b.frequency == 5.0

    def test_lt_sorts_by_frequency(self):
        b1 = Biphoneme(("a", "b"), frequency=1.0)
        b2 = Biphoneme(("c", "d"), frequency=3.0)
        assert sorted([b2, b1]) == [b1, b2]

    def test_str_and_repr(self):
        b = Biphoneme(("a", "b"), frequency=7.5)
        assert str(b) == "(a, b)"
        assert repr(b) == "ab:7.5"


# ═══════════════════════════════════════════════════════════════════════════════
# Multiphoneme
# ═══════════════════════════════════════════════════════════════════════════════

class TestMultiphoneme:

    def test_eq_same_tuple(self):
        m1 = Multiphoneme(("a", "b"), frequency=1.0)
        m2 = Multiphoneme(("a", "b"), frequency=99.0)
        assert m1 == m2

    def test_eq_different_tuple(self):
        m1 = Multiphoneme(("a", "b"))
        m2 = Multiphoneme(("a", "c"))
        assert m1 != m2

    def test_eq_with_set_order_independent(self):
        """Multiphoneme supports equality with set (order-independent)."""
        m = Multiphoneme(("a", "b"))
        assert m == {"b", "a"}
        assert m == {"a", "b"}

    def test_eq_with_set_different_elements(self):
        m = Multiphoneme(("a", "b"))
        assert m != {"a", "c"}

    def test_eq_with_other_types(self):
        m = Multiphoneme(("a", "b"))
        assert m != ("a", "b")  # tuple, not Multiphoneme
        assert m != ["a", "b"]
        assert m != 42

    def test_eq_empty_tuple(self):
        m1 = Multiphoneme(())
        m2 = Multiphoneme(())
        assert m1 == m2
        assert m1 == set()

    def test_increase_frequency(self):
        m = Multiphoneme(("a", "b"))
        m.increaseFrequency(3.0)
        m.increaseFrequency(4.0)
        assert m.frequency == 7.0

    def test_lt_sorts_by_frequency(self):
        m1 = Multiphoneme(("a",), frequency=2.0)
        m2 = Multiphoneme(("b",), frequency=5.0)
        assert sorted([m2, m1]) == [m1, m2]


# ═══════════════════════════════════════════════════════════════════════════════
# PhonemeCollection
# ═══════════════════════════════════════════════════════════════════════════════

class TestPhonemeCollection:

    def test_get_phonemes_creates_new(self):
        col = PhonemeCollection("test")
        result = col.getPhonemes("aR")
        assert len(result) == 2
        assert result[0].name == "a"
        assert result[1].name == "R"
        assert "a" in col.phonemeNames
        assert "R" in col.phonemeNames
        assert len(col.phonemes) == 2

    def test_get_phonemes_returns_same_object(self):
        """Second call returns the same Phoneme instances (identity)."""
        col = PhonemeCollection("test")
        first = col.getPhonemes("aR")
        second = col.getPhonemes("aR")
        assert first[0] is second[0]
        assert first[1] is second[1]

    def test_get_phonemes_duplicate_chars(self):
        """Duplicate chars in string return the same Phoneme twice in list
        but only one entry in dict."""
        col = PhonemeCollection("test")
        result = col.getPhonemes("aa")
        assert len(result) == 2
        assert result[0] is result[1]
        assert len(col.phonemeNames) == 1
        assert len(col.phonemes) == 1

    def test_get_phonemes_empty_string(self):
        col = PhonemeCollection("test")
        result = col.getPhonemes("")
        assert result == []

    def test_get_phoneme_single(self):
        col = PhonemeCollection("test")
        p = col.getPhoneme("a")
        assert p.name == "a"

    def test_get_phoneme_multi_char_returns_first(self):
        """getPhoneme with multi-char string delegates to getPhonemes
        which iterates chars — returns only the first."""
        col = PhonemeCollection("test")
        p = col.getPhoneme("aR")
        assert p.name == "a"
        # But both are created in the collection
        assert "R" in col.phonemeNames


# ═══════════════════════════════════════════════════════════════════════════════
# BiphonemeCollection — get methods and getPhonemesNames
# ═══════════════════════════════════════════════════════════════════════════════

class TestBiphonemeCollectionGetters:

    def test_get_biphoneme_creates_new(self):
        col = BiphonemeCollection("test")
        bp = col.getBiphoneme(("a", "b"))
        assert bp.pair == ("a", "b")
        assert ("a", "b") in col.biphonemeNames
        assert len(col.biphonemes) == 1

    def test_get_biphoneme_returns_same_object(self):
        col = BiphonemeCollection("test")
        bp1 = col.getBiphoneme(("a", "b"))
        bp2 = col.getBiphoneme(("a", "b"))
        assert bp1 is bp2

    def test_get_biphonemes_multiple(self):
        col = BiphonemeCollection("test")
        result = col.getBiphonemes([("a", "b"), ("c", "d")])
        assert len(result) == 2
        assert len(col.biphonemes) == 2

    def test_get_phonemes_names(self):
        """getPhonemesNames extracts unique single phonemes from all pairs."""
        col = BiphonemeCollection("test")
        col.getBiphoneme(("a", "b")).increaseFrequency(1.0)
        col.getBiphoneme(("b", "c")).increaseFrequency(1.0)
        names = col.getPhonemesNames()
        assert set(names) == {"a", "b", "c"}

    def test_get_phonemes_names_empty(self):
        col = BiphonemeCollection("test")
        assert col.getPhonemesNames() == ""

    def test_get_phonemes_names_same_phoneme_both_sides(self):
        col = BiphonemeCollection("test")
        col.getBiphoneme(("R", "R")).increaseFrequency(1.0)
        names = col.getPhonemesNames()
        assert set(names) == {"R"}


# ═══════════════════════════════════════════════════════════════════════════════
# MultiphonemeCollection
# ═══════════════════════════════════════════════════════════════════════════════

class TestMultiphonemeCollection:

    def test_get_multiphoneme_creates_new(self):
        col = MultiphonemeCollection("test")
        mp = col.getMultiphoneme(("t", "R"))
        assert mp.phonemes == ("t", "R")
        assert ("t", "R") in col.multiphonemeNames

    def test_get_multiphoneme_returns_same_object(self):
        col = MultiphonemeCollection("test")
        mp1 = col.getMultiphoneme(("t", "R"))
        mp2 = col.getMultiphoneme(("t", "R"))
        assert mp1 is mp2

    def test_get_multiphonemes_multiple(self):
        col = MultiphonemeCollection("test")
        result = col.getMultiphonemes([("t", "R"), ("p", "l")])
        assert len(result) == 2
        assert len(col.multiphonemes) == 2

    def test_get_multiphoneme_empty_tuple(self):
        col = MultiphonemeCollection("test")
        mp = col.getMultiphoneme(())
        assert mp.phonemes == ()

    def test_get_multiphoneme_single_element(self):
        col = MultiphonemeCollection("test")
        mp = col.getMultiphoneme(("a",))
        assert mp.phonemes == ("a",)


# ═══════════════════════════════════════════════════════════════════════════════
# Syllable.__init__ — onset / nucleus / coda classification
# ═══════════════════════════════════════════════════════════════════════════════

class TestSyllableInit:
    """Verify that Syllable.__init__ correctly splits phonemes into
    onset (pre-vowel consonants), nucleus (vowels), and coda (post-vowel
    consonants), and populates the shared collections."""

    def test_cvc_syllable(self):
        """Simple consonant-vowel-consonant: 'taR' (like 'tard')"""
        syll = Syllable("taR", "tar", frequency=10.0)
        parts = syll.phonemeNamesByPart()
        assert parts["onset"] == ["t"]
        assert parts["nucleus"] == ["a"]
        assert parts["coda"] == ["R"]

    def test_onset_cluster(self):
        """Onset consonant cluster: 'tRa' (like 'tra-')"""
        syll = Syllable("tRa", "tra", frequency=5.0)
        parts = syll.phonemeNamesByPart()
        assert parts["onset"] == ["t", "R"]
        assert parts["nucleus"] == ["a"]
        assert parts["coda"] == []

    def test_coda_cluster(self):
        """Coda consonant cluster: 'aRt' (like '-art')"""
        syll = Syllable("aRt", "art", frequency=5.0)
        parts = syll.phonemeNamesByPart()
        assert parts["onset"] == []
        assert parts["nucleus"] == ["a"]
        assert parts["coda"] == ["R", "t"]

    def test_single_vowel(self):
        """Bare vowel syllable: 'a'"""
        syll = Syllable("a", "a", frequency=3.0)
        parts = syll.phonemeNamesByPart()
        assert parts["onset"] == []
        assert parts["nucleus"] == ["a"]
        assert parts["coda"] == []

    def test_multi_vowel_nucleus(self):
        """Multiple vowels in nucleus: 'oi' (like in 'toi')"""
        syll = Syllable("toi", "toi", frequency=4.0)
        parts = syll.phonemeNamesByPart()
        assert parts["onset"] == ["t"]
        assert parts["nucleus"] == ["o", "i"]
        assert parts["coda"] == []

    def test_complex_syllable(self):
        """Complex onset+coda: 'stRaRk'"""
        syll = Syllable("stRaRk", "strark", frequency=1.0)
        parts = syll.phonemeNamesByPart()
        assert parts["onset"] == ["s", "t", "R"]
        assert parts["nucleus"] == ["a"]
        assert parts["coda"] == ["R", "k"]

    def test_frequency_propagation(self):
        """Frequency should propagate to the syllable and its phonemes."""
        syll = Syllable("ta", "ta", frequency=7.0)
        assert syll.frequency == 7.0
        # The "all" phoneme collection should have both phonemes
        t = Syllable.allPhonemeCol.phonemeNames["t"]
        a = Syllable.allPhonemeCol.phonemeNames["a"]
        assert t.frequency == 7.0
        assert a.frequency == 7.0

    def test_spelling_recorded(self):
        """The spelling should be recorded with its frequency."""
        syll = Syllable("ka", "ca", frequency=2.0)
        assert "ca" in syll.spellings
        assert syll.spellings["ca"] == 2.0

    def test_onset_biphonemes_extracted(self):
        """Onset with 2+ consonants should produce biphonemes."""
        syll = Syllable("tRa", "tra", frequency=6.0)
        # Should have one onset biphoneme: (t, R)
        assert len(syll.biphonemesByPart["onset"]) == 1
        assert syll.biphonemesByPart["onset"][0].pair == ("t", "R")
        assert syll.biphonemesByPart["onset"][0].frequency == 6.0

    def test_coda_biphonemes_extracted(self):
        """Coda with 2+ consonants should produce biphonemes."""
        syll = Syllable("aRt", "art", frequency=4.0)
        assert len(syll.biphonemesByPart["coda"]) == 1
        assert syll.biphonemesByPart["coda"][0].pair == ("R", "t")

    def test_nucleus_biphonemes_extracted(self):
        """Multi-vowel nucleus should produce nucleus biphonemes."""
        syll = Syllable("toi", "toi", frequency=3.0)
        assert len(syll.biphonemesByPart["nucleus"]) == 1
        assert syll.biphonemesByPart["nucleus"][0].pair == ("o", "i")

    def test_no_biphonemes_for_single_consonant_onset(self):
        """Single consonant onset produces no onset biphonemes."""
        syll = Syllable("ta", "ta", frequency=1.0)
        assert syll.biphonemesByPart["onset"] == []

    def test_multiphonemes_extracted(self):
        """Multiphonemes should be set for non-empty parts."""
        syll = Syllable("tRak", "trac", frequency=2.0)
        assert syll.multiphonemesByPart["onset"] is not None
        assert syll.multiphonemesByPart["onset"].phonemes == ("t", "R")
        assert syll.multiphonemesByPart["nucleus"] is not None
        assert syll.multiphonemesByPart["nucleus"].phonemes == ("a",)
        assert syll.multiphonemesByPart["coda"] is not None
        assert syll.multiphonemesByPart["coda"].phonemes == ("k",)

    def test_multiphoneme_none_for_empty_part(self):
        """Empty syllabic parts should have None multiphoneme."""
        syll = Syllable("ta", "ta", frequency=1.0)
        assert syll.multiphonemesByPart["coda"] is None

    def test_three_consonant_onset_biphonemes(self):
        """Three consonant onset 'stR' should produce 3 biphonemes:
        (s,t), (s,R), (t,R)."""
        syll = Syllable("stRa", "stra", frequency=2.0)
        pairs = [bp.pair for bp in syll.biphonemesByPart["onset"]]
        assert ("s", "t") in pairs
        assert ("s", "R") in pairs
        assert ("t", "R") in pairs
        assert len(pairs) == 3

    def test_shared_collection_accumulates(self):
        """Two syllables sharing a phoneme should accumulate frequency
        in the shared collections."""
        Syllable("ta", "ta", frequency=3.0)
        Syllable("ti", "ti", frequency=5.0)
        t_phoneme = Syllable.allPhonemeCol.phonemeNames["t"]
        assert t_phoneme.frequency == 8.0


# ═══════════════════════════════════════════════════════════════════════════════
# Syllable.replacePhonemeInSyllabicPart
# ═══════════════════════════════════════════════════════════════════════════════

class TestReplacePhonemeInSyllabicPart:

    def test_replace_onset_phoneme(self):
        syll = Syllable("tRak", "trac", frequency=1.0)
        result = syll.replacePhonemeInSyllabicPart("t", "p", "onset")
        assert result == "pRak"

    def test_replace_coda_phoneme(self):
        syll = Syllable("taRk", "tarc", frequency=1.0)
        result = syll.replacePhonemeInSyllabicPart("k", "g", "coda")
        assert result == "taRg"

    def test_replace_nucleus_phoneme(self):
        syll = Syllable("tak", "tac", frequency=1.0)
        result = syll.replacePhonemeInSyllabicPart("a", "o", "nucleus")
        assert result == "tok"

    def test_remove_onset_phoneme(self):
        """Replacing with empty string removes the phoneme."""
        syll = Syllable("tRa", "tra", frequency=1.0)
        result = syll.replacePhonemeInSyllabicPart("t", "", "onset")
        assert result == "Ra"

    def test_remove_coda_phoneme(self):
        syll = Syllable("aRt", "art", frequency=1.0)
        result = syll.replacePhonemeInSyllabicPart("t", "", "coda")
        assert result == "aR"

    def test_invalid_syllabic_part_returns_full(self):
        """An unrecognized syllabicPart should return the full phoneme string."""
        syll = Syllable("tak", "tac", frequency=1.0)
        result = syll.replacePhonemeInSyllabicPart("a", "o", "invalid")
        assert result == "tak"

    def test_phoneme_not_in_part_unchanged(self):
        """Replacing a phoneme that doesn't exist in the part does nothing."""
        syll = Syllable("tak", "tac", frequency=1.0)
        result = syll.replacePhonemeInSyllabicPart("R", "l", "onset")
        assert result == "tak"


# ═══════════════════════════════════════════════════════════════════════════════
# Syllable.replaceMultiphonemeInSyllabicPart
# ═══════════════════════════════════════════════════════════════════════════════

class TestReplaceMultiphonemeInSyllabicPart:

    def test_replace_onset_multiphoneme_tuple(self):
        syll = Syllable("tRak", "trac", frequency=1.0)
        result = syll.replaceMultiphonemeInSyllabicPart(("p", "l"), "onset")
        assert result == "plak"

    def test_replace_onset_multiphoneme_object(self):
        syll = Syllable("tRak", "trac", frequency=1.0)
        mp = Multiphoneme(("p", "l"))
        result = syll.replaceMultiphonemeInSyllabicPart(mp, "onset")
        assert result == "plak"

    def test_replace_coda_multiphoneme(self):
        syll = Syllable("aRt", "art", frequency=1.0)
        result = syll.replaceMultiphonemeInSyllabicPart(("l", "k"), "coda")
        assert result == "alk"

    def test_replace_with_empty_tuple(self):
        syll = Syllable("tRa", "tra", frequency=1.0)
        result = syll.replaceMultiphonemeInSyllabicPart((), "onset")
        assert result == "a"

    def test_invalid_part_returns_full(self):
        syll = Syllable("tak", "tac", frequency=1.0)
        result = syll.replaceMultiphonemeInSyllabicPart(("p",), "invalid")
        assert result == "tak"


# ═══════════════════════════════════════════════════════════════════════════════
# BiphonemeCollection.scorePermutation
# ═══════════════════════════════════════════════════════════════════════════════

class TestScorePermutation:

    def _make_collection(self, pairs_freqs: list[tuple[tuple[str, str], float]]) -> BiphonemeCollection:
        col = BiphonemeCollection("test")
        for pair, freq in pairs_freqs:
            bp = col.getBiphoneme(pair)
            bp.increaseFrequency(freq)
        return col

    def test_all_ordered(self):
        """When all biphonemes are in the correct order, score is positive
        and negScore is 0."""
        col = self._make_collection([
            (("a", "b"), 10.0),
            (("b", "c"), 5.0),
        ])
        score, negScore, badOrder = col.scorePermutation("abc")
        assert score == 15.0
        assert negScore == 0.0
        assert badOrder == []

    def test_all_reversed(self):
        """When all biphonemes are in wrong order, score is fully negative."""
        col = self._make_collection([
            (("a", "b"), 10.0),
            (("b", "c"), 5.0),
        ])
        score, negScore, badOrder = col.scorePermutation("cba")
        assert score == -15.0
        assert negScore == -15.0
        assert len(badOrder) == 2

    def test_mixed_order(self):
        """One biphoneme ordered, one reversed."""
        col = self._make_collection([
            (("a", "b"), 10.0),
            (("b", "c"), 5.0),
        ])
        # Permutation "bac": a is after b (wrong for (a,b)), b before c (correct)
        score, negScore, badOrder = col.scorePermutation("bac")
        assert score == -10.0 + 5.0
        assert negScore == -10.0
        assert len(badOrder) == 1
        assert badOrder[0].pair == ("a", "b")

    def test_single_biphoneme(self):
        col = self._make_collection([(("a", "b"), 7.0)])
        score, negScore, _ = col.scorePermutation("ab")
        assert score == 7.0
        assert negScore == 0.0

        score2, negScore2, _ = col.scorePermutation("ba")
        assert score2 == -7.0
        assert negScore2 == -7.0

    def test_zero_frequency(self):
        col = self._make_collection([(("a", "b"), 0.0)])
        score, negScore, _ = col.scorePermutation("ab")
        assert score == 0.0
        assert negScore == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# BiphonemeCollection.optimizeOrder
# ═══════════════════════════════════════════════════════════════════════════════

class TestOptimizeOrder:

    def test_finds_optimal_for_simple_case(self):
        """With clear frequency preferences, optimizeOrder should find the
        correct ordering."""
        col = BiphonemeCollection("test")
        # a should come before b (freq 10 >> 1)
        bp_ab = col.getBiphoneme(("a", "b"))
        bp_ab.increaseFrequency(10.0)
        bp_ba = col.getBiphoneme(("b", "a"))
        bp_ba.increaseFrequency(1.0)
        col.optimizeOrder()
        # Best permutation should have a before b
        assert col.bestPermutation.index("a") < col.bestPermutation.index("b")
        assert col.bestPermutationScore > 0.0

    def test_two_phonemes_trivial(self):
        col = BiphonemeCollection("test")
        bp = col.getBiphoneme(("a", "b"))
        bp.increaseFrequency(5.0)
        col.optimizeOrder()
        assert col.bestPermutation == "ab"


# ═══════════════════════════════════════════════════════════════════════════════
# BiphonemeCollection.generateBiphonemeOrderMatrix
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenerateBiphonemeOrderMatrix:

    def test_symmetry(self):
        """If (a,b) is '>', then (b,a) must be '<'."""
        col = BiphonemeCollection("test")
        bp = col.getBiphoneme(("a", "b"))
        bp.increaseFrequency(10.0)
        col.optimizeOrder()
        col.generateBiphonemeOrderMatrix()

        if ("a", "b") in col.pairwiseBiphonemeOrder:
            ab = col.pairwiseBiphonemeOrder[("a", "b")]
            ba = col.pairwiseBiphonemeOrder[("b", "a")]
            if ab == ">":
                assert ba == "<"
            elif ab == "<":
                assert ba == ">"
            elif ab == "=":
                assert ba == "="

    def test_entries_exist_for_all_pairs(self):
        col = BiphonemeCollection("test")
        col.getBiphoneme(("a", "b")).increaseFrequency(10.0)
        col.getBiphoneme(("b", "c")).increaseFrequency(5.0)
        col.optimizeOrder()
        col.generateBiphonemeOrderMatrix()
        # All 6 ordered pairs of {a,b,c} should be present
        phonemes = list(col.bestPermutation)
        for p1 in phonemes:
            for p2 in phonemes:
                if p1 != p2:
                    assert (p1, p2) in col.pairwiseBiphonemeOrder


# ═══════════════════════════════════════════════════════════════════════════════
# SyllableCollection.syllabicAmbiguityScore
# ═══════════════════════════════════════════════════════════════════════════════

class TestSyllabicAmbiguityScore:

    def _build_collection(self, syllable_data: list[tuple[str, str, float]]) -> SyllableCollection:
        """Build a SyllableCollection from (phonemes, spelling, frequency) tuples."""
        col = SyllableCollection()
        for phonemes, spelling, freq in syllable_data:
            col.updateSyllable(phonemes, spelling, freq)
        return col

    def test_pair_ambiguity_both_exist(self):
        """Two syllables 'pa' and 'la' — assigning p and l to same key
        creates ambiguity. The function only iterates over syllables
        containing phoneme1 ('p'), so score = min(freq(pa), freq(la))."""
        col = self._build_collection([
            ("pa", "pa", 10.0),
            ("la", "la", 3.0),
        ])
        score = col.syllabicAmbiguityScore("p", "l", "onset")
        # Only syllables with "p" in onset: ["pa"]
        # pa: p->l gives "la" (freq 3), min(10, 3) = 3
        assert score == 3.0

    def test_pair_ambiguity_substitution_missing(self):
        """If 'pa' exists but 'la' does not, substituting p->l yields
        a non-existent syllable with freq 0. Score contribution = min(10, 0) = 0."""
        col = self._build_collection([
            ("pa", "pa", 10.0),
        ])
        score = col.syllabicAmbiguityScore("p", "l", "onset")
        assert score == 0.0

    def test_no_syllable_with_phoneme(self):
        """If no syllable contains phoneme1, score = 0."""
        col = self._build_collection([
            ("ta", "ta", 5.0),
        ])
        score = col.syllabicAmbiguityScore("p", "l", "onset")
        assert score == 0.0

    def test_triple_ambiguity(self):
        """When both phonemes appear in the same syllable, it's a triple
        ambiguity with the shortened syllables.
        Only syllables containing phoneme1 ('p') are iterated."""
        col = self._build_collection([
            ("pla", "pla", 6.0),
            ("pa", "pa", 10.0),
            ("la", "la", 3.0),
        ])
        score = col.syllabicAmbiguityScore("p", "l", "onset")
        # Syllables with "p" in onset: ["pla", "pa"]
        # "pla": both p and l present → triple case
        #   remove p → "la" (freq 3), remove l → "pa" (freq 10)
        #   freqs = [6, 10, 3], sum - max = 6+3+10-10 = 9
        # "pa": pair case, p->l → "la" (freq 3), min(10, 3) = 3
        assert score == 9.0 + 3.0

    def test_coda_ambiguity(self):
        """Ambiguity computation works for coda part too."""
        col = self._build_collection([
            ("aR", "ar", 8.0),
            ("ak", "ac", 4.0),
        ])
        score = col.syllabicAmbiguityScore("R", "k", "coda")
        # Only syllables with "R" in coda: ["aR"]
        # aR: R->k gives "ak" (freq 4), min(8, 4) = 4
        assert score == 4.0


# ═══════════════════════════════════════════════════════════════════════════════
# SyllableCollection.lexicalPhonemeAmbiguityScore
# ═══════════════════════════════════════════════════════════════════════════════

class TestLexicalPhonemeAmbiguityScore:

    def _build_collection_with_words(
        self,
        entries: list[tuple[str, str, str, float]],
    ) -> SyllableCollection:
        """Build collection from (syllable_phonemes, spelling, word_ortho, frequency).
        Each entry creates a syllable and tracks a word against it."""
        col = SyllableCollection()
        for syll_phonemes, spelling, ortho, freq in entries:
            word = _make_word(ortho, syll_phonemes, freq)
            col.updateSyllable(syll_phonemes, spelling, freq, word)
        return col

    def test_pair_ambiguity_words_exist(self):
        """Two words differing by one onset phoneme. Only syllables
        containing phoneme1 are iterated."""
        col = self._build_collection_with_words([
            ("pa", "pa", "pas", 10.0),
            ("la", "la", "la", 3.0),
        ])
        score = col.lexicalPhonemeAmbiguityScore("p", "l", "onset")
        # Only syllables with "p" in onset: ["pa"]
        # "pa" word "pas" (freq 10) → mutated "la", word "la" (freq 3)
        # min(10, 3) = 3
        assert score == 3.0

    def test_no_ambiguity_when_mutated_word_missing(self):
        """If the mutated phonology doesn't match any tracked word, no ambiguity."""
        col = self._build_collection_with_words([
            ("pa", "pa", "pas", 10.0),
        ])
        score = col.lexicalPhonemeAmbiguityScore("p", "l", "onset")
        assert score == 0.0

    def test_no_syllable_with_phoneme(self):
        """If no syllable contains phoneme1, score is 0."""
        col = self._build_collection_with_words([
            ("ta", "ta", "ta", 5.0),
        ])
        score = col.lexicalPhonemeAmbiguityScore("p", "l", "onset")
        assert score == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# SyllableCollection.lexicalSyllabicPartAmbiguityScore
# ═══════════════════════════════════════════════════════════════════════════════

class TestLexicalSyllabicPartAmbiguityScore:

    def _build_collection_with_words(
        self,
        entries: list[tuple[str, str, str, float]],
    ) -> SyllableCollection:
        col = SyllableCollection()
        for syll_phonemes, spelling, ortho, freq in entries:
            word = _make_word(ortho, syll_phonemes, freq)
            col.updateSyllable(syll_phonemes, spelling, freq, word)
        return col

    def test_multiphoneme_pair_ambiguity(self):
        """Only syllables matching multiphoneme1 are iterated."""
        col = self._build_collection_with_words([
            ("tRa", "tra", "tra", 8.0),
            ("pla", "pla", "pla", 4.0),
        ])
        score = col.lexicalSyllabicPartAmbiguityScore(
            ("t", "R"), ("p", "l"), "onset"
        )
        # Only syllables with onset ("t","R"): ["tRa"]
        # tRa → replace onset with (p,l) → "pla", word "pla" (freq 4)
        # min(8, 4) = 4
        assert score == 4.0

    def test_no_ambiguity_when_no_match(self):
        """No ambiguity when substituted syllable has no tracked words."""
        col = self._build_collection_with_words([
            ("tRa", "tra", "tra", 8.0),
        ])
        score = col.lexicalSyllabicPartAmbiguityScore(
            ("t", "R"), ("p", "l"), "onset"
        )
        assert score == 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# SyllableCollection helper methods
# ═══════════════════════════════════════════════════════════════════════════════

class TestSyllableCollection:

    def test_update_and_get(self):
        col = SyllableCollection()
        col.updateSyllable("ta", "ta", 5.0)
        syll = col.getSyllable("ta")
        assert syll is not None
        assert syll.frequency == 5.0

    def test_update_accumulates_frequency(self):
        col = SyllableCollection()
        col.updateSyllable("ta", "ta", 5.0)
        col.updateSyllable("ta", "ta", 3.0)
        syll = col.getSyllable("ta")
        assert syll is not None
        assert syll.frequency == pytest.approx(8.0)

    def test_update_adds_new_spelling(self):
        col = SyllableCollection()
        col.updateSyllable("ta", "ta", 5.0)
        col.updateSyllable("ta", "tha", 2.0)
        syll = col.getSyllable("ta")
        assert syll is not None
        assert "ta" in syll.spellings
        assert "tha" in syll.spellings

    def test_get_missing_returns_none(self):
        col = SyllableCollection()
        assert col.getSyllable("zz") is None

    def test_get_frequency_by_string(self):
        col = SyllableCollection()
        col.updateSyllable("ta", "ta", 5.0)
        assert col.getFrequency("ta") == 5.0

    def test_get_frequency_by_syllable(self):
        col = SyllableCollection()
        col.updateSyllable("ta", "ta", 5.0)
        syll = col.getSyllable("ta")
        assert col.getFrequency(syll) == 5.0

    def test_get_frequency_missing(self):
        col = SyllableCollection()
        assert col.getFrequency("zz") == 0.0

    def test_track_word(self):
        col = SyllableCollection()
        word = _make_word("pas", "pa", 10.0)
        col.updateSyllable("pa", "pa", 10.0, word)
        syll = col.getSyllable("pa")
        assert "pa" in syll.phonoWords
        assert syll.phonoWords["pa"][0].ortho == "pas"


# ═══════════════════════════════════════════════════════════════════════════════
# Syllable.increaseFrequency
# ═══════════════════════════════════════════════════════════════════════════════

class TestSyllableIncreaseFrequency:

    def test_frequency_accumulates(self):
        syll = Syllable("ta", "ta", frequency=5.0)
        syll.increaseFrequency(3.0)
        assert syll.frequency == pytest.approx(8.0)

    def test_propagates_to_phonemes(self):
        syll = Syllable("ta", "ta", frequency=5.0)
        syll.increaseFrequency(3.0)
        # "t" is in both allPhonemeCol and onset part
        t_all = Syllable.allPhonemeCol.phonemeNames["t"]
        assert t_all.frequency == pytest.approx(8.0)

    def test_propagates_to_part_phonemes(self):
        syll = Syllable("taR", "tar", frequency=4.0)
        syll.increaseFrequency(2.0)
        onset_t = Syllable.phonemeColByPart["onset"].phonemeNames["t"]
        coda_R = Syllable.phonemeColByPart["coda"].phonemeNames["R"]
        nucleus_a = Syllable.phonemeColByPart["nucleus"].phonemeNames["a"]
        assert onset_t.frequency == pytest.approx(6.0)
        assert coda_R.frequency == pytest.approx(6.0)
        assert nucleus_a.frequency == pytest.approx(6.0)

    def test_propagates_to_biphonemes(self):
        syll = Syllable("tRa", "tra", frequency=4.0)
        syll.increaseFrequency(2.0)
        bp = syll.biphonemesByPart["onset"][0]
        assert bp.pair == ("t", "R")
        assert bp.frequency == pytest.approx(6.0)


# ═══════════════════════════════════════════════════════════════════════════════
# Syllable.increaseSpellingFrequency
# ═══════════════════════════════════════════════════════════════════════════════

class TestSyllableIncreaseSpellingFrequency:

    def test_new_spelling_creates_entry(self):
        syll = Syllable("ta", "ta", frequency=5.0)
        syll.increaseSpellingFrequency("tha", 3.0)
        assert "tha" in syll.spellings
        assert syll.spellings["tha"] == 3.0

    def test_existing_spelling_accumulates(self):
        syll = Syllable("ta", "ta", frequency=5.0)
        syll.increaseSpellingFrequency("ta", 3.0)
        assert syll.spellings["ta"] == pytest.approx(8.0)

    def test_also_increases_syllable_frequency(self):
        syll = Syllable("ta", "ta", frequency=5.0)
        syll.increaseSpellingFrequency("tha", 3.0)
        assert syll.frequency == pytest.approx(8.0)


# ═══════════════════════════════════════════════════════════════════════════════
# Syllable.sortedSpellings
# ═══════════════════════════════════════════════════════════════════════════════

class TestSyllableSortedSpellings:

    def test_sorted_by_descending_frequency(self):
        syll = Syllable("ta", "ta", frequency=5.0)
        syll.increaseSpellingFrequency("tha", 10.0)
        syll.increaseSpellingFrequency("tah", 1.0)
        result = syll.sortedSpellings()
        freqs = [freq for _, freq in result]
        assert freqs == sorted(freqs, reverse=True)

    def test_single_spelling(self):
        syll = Syllable("ta", "ta", frequency=5.0)
        result = syll.sortedSpellings()
        assert len(result) == 1
        assert result[0] == ("ta", 5.0)


# ═══════════════════════════════════════════════════════════════════════════════
# Syllable static methods
# ═══════════════════════════════════════════════════════════════════════════════

class TestSyllableStaticMethods:

    def test_sort_phonemes_collections(self):
        """After creating syllables, sorting should order phonemes by
        descending frequency."""
        Syllable("ta", "ta", frequency=3.0)
        Syllable("Ra", "ra", frequency=7.0)
        Syllable.sortPhonemesCollections()
        onset_names = [p.name for p in Syllable.phonemeColByPart["onset"].phonemes]
        assert onset_names[0] == "R"  # higher frequency
        assert onset_names[1] == "t"

    def test_get_sorted_phonemes_names(self):
        Syllable("ta", "ta", frequency=3.0)
        Syllable("Ra", "ra", frequency=7.0)
        names = Syllable.getSortedPhonemesNames("onset")
        assert names[0] == "R"
        assert names[1] == "t"

    def test_phoneme_collection_by_part(self):
        Syllable("ta", "ta", frequency=1.0)
        col = Syllable.phonemeCollectionByPart("onset")
        assert isinstance(col, PhonemeCollection)
        assert "t" in col.phonemeNames

    def test_biphoneme_collection_by_part(self):
        Syllable("tRa", "tra", frequency=1.0)
        col = Syllable.biphonemeCollectionByPart("onset")
        assert isinstance(col, BiphonemeCollection)
        assert len(col.biphonemes) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# Syllable.__eq__ / __lt__
# ═══════════════════════════════════════════════════════════════════════════════

class TestSyllableComparison:

    def test_eq_same_phonemes(self):
        s1 = Syllable("ta", "ta", frequency=1.0)
        s2 = Syllable("ta", "tha", frequency=99.0)
        # Both have same phonemes (same Phoneme objects from shared collection)
        assert s1 == s2

    def test_eq_different_phonemes(self):
        s1 = Syllable("ta", "ta", frequency=1.0)
        s2 = Syllable("Ra", "ra", frequency=1.0)
        assert s1 != s2

    def test_eq_non_syllable(self):
        s = Syllable("ta", "ta", frequency=1.0)
        assert s != "ta"

    def test_lt_by_frequency(self):
        s1 = Syllable("ta", "ta", frequency=2.0)
        s2 = Syllable("Ra", "ra", frequency=8.0)
        result = sorted([s2, s1])
        assert result[0].name == "ta"
        assert result[1].name == "Ra"


# ═══════════════════════════════════════════════════════════════════════════════
# SyllableCollection — additional edge cases
# ═══════════════════════════════════════════════════════════════════════════════

class TestSyllableCollectionEdgeCases:

    def test_str_and_repr(self):
        col = SyllableCollection()
        col.updateSyllable("ta", "ta", 5.0)
        col.updateSyllable("Ra", "ra", 3.0)
        s = str(col)
        assert "2 syllables" in s
        assert "2 syllable_names" in s

    def test_get_multiphoneme_names(self):
        col = SyllableCollection()
        col.updateSyllable("tRa", "tra", 5.0)
        col.updateSyllable("pla", "pla", 3.0)
        onset_names = col.getMultiphonemeNames("onset")
        assert ("t", "R") in onset_names
        assert ("p", "l") in onset_names

    def test_get_multiphoneme_names_empty(self):
        col = SyllableCollection()
        assert col.getMultiphonemeNames("onset") == []

    def test_track_multiple_words_same_phonology(self):
        col = SyllableCollection()
        w1 = _make_word("ver", "vR", 5.0)
        w2 = _make_word("verre", "vR", 3.0)
        col.updateSyllable("vR", "ver", 5.0, w1)
        col.updateSyllable("vR", "verre", 3.0, w2)
        syll = col.getSyllable("vR")
        assert len(syll.phonoWords["vR"]) == 2
        orthos = [w.ortho for w in syll.phonoWords["vR"]]
        assert "ver" in orthos
        assert "verre" in orthos


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
