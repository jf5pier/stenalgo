import pytest
from ..word import Word, GramCat, atomicFeatures


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_word(**overrides) -> Word:
    """Create a Word with sensible defaults, overriding any field."""
    defaults = dict(
        ortho="chat",
        phonology="Sa",
        lemme="chat",
        gramCat=GramCat.NOM,
        orthoGramCat=[GramCat.NOM],
        gender="m",
        number="s",
        infoVerb=None,
        rawSyllCV="S_a",
        rawOrthosyllCV="ch_a_t",
        frequencyBook=1.0,
        frequencyFilm=2.0,
    )
    defaults.update(overrides)
    return Word(**defaults)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def word_sample() -> Word:
    """The 'enivre' word triggers fix_e_n_en in __post_init__."""
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


# ═══════════════════════════════════════════════════════════════════════════════
# __post_init__
# ═══════════════════════════════════════════════════════════════════════════════

class TestPostInit:

    def test_frequency_is_film(self, word_sample: Word) -> None:
        assert word_sample.frequency == word_sample.frequencyFilm

    def test_syllCV_set(self, word_sample: Word) -> None:
        assert word_sample.syllCV == [["@"], ["i", "v", "R", "#"]]

    def test_orthosyllCV_set(self, word_sample: Word) -> None:
        assert word_sample.orthosyllCV == [["en"], ["i", "v", "r", "e"]]

    def test_lemmeGramCat_format(self) -> None:
        w = _make_word(lemme="manger", gramCat=GramCat.VER)
        assert w.lemmeGramCat == "manger_VER"

    def test_lemmeGramCat_nom(self) -> None:
        w = _make_word(lemme="chat", gramCat=GramCat.NOM)
        assert w.lemmeGramCat == "chat_NOM"

    def test_infoVerb_none(self) -> None:
        w = _make_word(infoVerb=None)
        assert w._infoVerb is None

    def test_infoVerb_empty_string(self) -> None:
        w = _make_word(infoVerb="")
        assert w._infoVerb == []

    def test_infoVerb_parsed(self) -> None:
        w = _make_word(gramCat=GramCat.VER, infoVerb="ind:pre:1s")
        assert w._infoVerb == [["indicatif", "présent", "pers_1", "nbr_s"]]

    def test_infoVerb_multiple_entries(self) -> None:
        w = _make_word(gramCat=GramCat.VER, infoVerb="ind:pre:1s;ind:pre:3s")
        assert len(w._infoVerb) == 2
        assert w._infoVerb[0] == ["indicatif", "présent", "pers_1", "nbr_s"]
        assert w._infoVerb[1] == ["indicatif", "présent", "pers_3", "nbr_s"]

    def test_hash_consistent(self) -> None:
        w1 = _make_word()
        w2 = _make_word()
        assert hash(w1) == hash(w2)


# ═══════════════════════════════════════════════════════════════════════════════
# splitInfoVerb
# ═══════════════════════════════════════════════════════════════════════════════

class TestSplitInfoVerb:

    def _split(self, infoVerb: str) -> list[str]:
        w = _make_word()
        return w.splitInfoVerb(infoVerb)

    def test_infinitif(self):
        assert self._split("inf") == ["infinitif"]

    def test_indicatif_present(self):
        assert self._split("ind:pre:1p") == [
            "indicatif", "présent", "pers_1", "nbr_p"
        ]

    def test_imperatif_present(self):
        assert self._split("imp:pre:2s") == [
            "impératif", "présent", "pers_2", "nbr_s"
        ]

    def test_subjonctif_imparfait(self):
        assert self._split("sub:imp:3p") == [
            "subjonctif", "imparfait", "pers_3", "nbr_p"
        ]

    def test_conditionnel_present(self):
        assert self._split("cnd:pre:1s") == [
            "conditionnel", "présent", "pers_1", "nbr_s"
        ]

    def test_indicatif_future(self):
        assert self._split("ind:fut:3s") == [
            "indicatif", "future", "pers_3", "nbr_s"
        ]

    def test_indicatif_passe(self):
        assert self._split("ind:pas:2p") == [
            "indicatif", "passé", "pers_2", "nbr_p"
        ]

    def test_participe_present(self):
        """Participe stops after tense — no person/number."""
        assert self._split("par:pre") == ["participe", "présent"]

    def test_participe_passe(self):
        assert self._split("par:pas") == ["participe", "passé"]

    def test_unknown_mode_still_adds_tense_and_person(self):
        """Unknown mode code produces no mode entry but tense/person still added."""
        result = self._split("xyz:pre:1s")
        # No mode recognized, but tense and person/number are still appended
        assert "présent" in result
        assert "pers_1" in result
        assert "nbr_s" in result
        assert len(result) == 3  # no mode entry


# ═══════════════════════════════════════════════════════════════════════════════
# mergeInfoVerb
# ═══════════════════════════════════════════════════════════════════════════════

class TestMergeInfoVerb:

    def test_appends_to_existing_infoVerb(self):
        """Result matches Lexique383's own multi-tag row convention (";"-separated,
        trailing ";"), the same format "parle" already carries natively."""
        w = _make_word(gramCat=GramCat.VER, infoVerb="ind:pre:3s")
        w.mergeInfoVerb("sub:pre:3s")
        assert w.infoVerb == "ind:pre:3s;sub:pre:3s;"

    def test_strips_each_side_s_own_trailing_semicolon(self):
        """Both the raw LexiqueMixte and LexiqueSynthetic infover columns already end in
        ";" -- merging must not produce a stray ";;" in the middle."""
        w = _make_word(gramCat=GramCat.VER, infoVerb="ind:pre:3s;")
        w.mergeInfoVerb("sub:pre:3s;")
        assert w.infoVerb == "ind:pre:3s;sub:pre:3s;"

    def test_sets_infoVerb_when_previously_none(self):
        w = _make_word(gramCat=GramCat.VER, infoVerb=None)
        w.mergeInfoVerb("sub:pre:3s")
        assert w.infoVerb == "sub:pre:3s;"

    def test_parsed_features_include_both_readings(self):
        """Mirrors how Lexique383 natively packs several readings of a common verb
        (e.g. "parle") into one row -- after merging, getFeatures() must see both,
        exactly as if they had arrived together in a single ";"-separated infoVerb."""
        w = _make_word(gramCat=GramCat.VER, infoVerb="ind:pre:3s")
        w.mergeInfoVerb("sub:pre:3s")
        features = w.getFeatures()
        assert "indicatif" in features
        assert "subjonctif" in features

    def test_duplicate_tag_not_added_twice(self):
        w = _make_word(gramCat=GramCat.VER, infoVerb="ind:pre:3s;")
        w.mergeInfoVerb("ind:pre:3s;")
        assert w.infoVerb == "ind:pre:3s;"


# ═══════════════════════════════════════════════════════════════════════════════
# __hash__ / __eq__
# ═══════════════════════════════════════════════════════════════════════════════

class TestHashAndEq:

    def test_same_identity_fields_equal(self):
        w1 = _make_word()
        w2 = _make_word()
        assert w1 == w2

    def test_different_ortho_not_equal(self):
        w1 = _make_word(ortho="chat")
        w2 = _make_word(ortho="chien")
        assert w1 != w2

    def test_different_gender_not_equal(self):
        w1 = _make_word(gender="m")
        w2 = _make_word(gender="f")
        assert w1 != w2

    def test_different_number_not_equal(self):
        w1 = _make_word(number="s")
        w2 = _make_word(number="p")
        assert w1 != w2

    def test_different_frequency_still_equal(self):
        """Frequency is excluded from identity — words with different
        frequencies but same identity fields should be equal."""
        w1 = _make_word(frequencyFilm=1.0)
        w2 = _make_word(frequencyFilm=99.0)
        assert w1 == w2

    def test_eq_with_non_word_returns_not_implemented(self):
        w = _make_word()
        assert w.__eq__("not a word") is NotImplemented
        assert w.__eq__(42) is NotImplemented
        assert w.__eq__(None) is NotImplemented

    def test_usable_in_set(self):
        w1 = _make_word()
        w2 = _make_word()
        w3 = _make_word(ortho="chien", phonology="Sj5")
        s = {w1, w2, w3}
        assert len(s) == 2

    def test_usable_as_dict_key(self):
        w = _make_word()
        d = {w: "value"}
        w2 = _make_word()
        assert d[w2] == "value"


# ═══════════════════════════════════════════════════════════════════════════════
# getFeatures
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetFeatures:

    def test_nom_masculin_singulier(self):
        w = _make_word(gramCat=GramCat.NOM, gender="m", number="s")
        features = w.getFeatures()
        assert "NOM" in features
        assert "m" in features
        assert "s" in features
        assert "m:s" in features
        assert "not_m_s" not in features

    def test_nom_feminin_pluriel(self):
        w = _make_word(gramCat=GramCat.NOM, gender="f", number="p")
        features = w.getFeatures()
        assert "NOM" in features
        assert "f" in features
        assert "p" in features
        assert "f:p" in features
        assert "not_m_s" in features

    def test_adj_masculin_pluriel_has_not_m_s(self):
        w = _make_word(gramCat=GramCat.ADJ, gender="m", number="p")
        features = w.getFeatures()
        assert "m:p" in features
        assert "not_m_s" in features

    def test_gender_none_number_none(self):
        """With None gender/number, no gender/number features are added."""
        w = _make_word(gramCat=GramCat.ADV, gender=None, number=None)
        features = w.getFeatures()
        assert "ADV" in features
        assert "m" not in features
        assert "s" not in features
        # No gender_number combo
        assert not any(":" in f and f.count(":") == 1 and f[0] in "mf"
                       for f in features)

    def test_ver_with_gender_number_has_combo(self):
        """VER with gender/number adds VER:gender:number feature."""
        w = _make_word(gramCat=GramCat.VER, gender="m", number="s",
                       infoVerb="par:pas")
        features = w.getFeatures()
        assert "VER:m:s" in features

    def test_ver_without_gender_no_combo(self):
        w = _make_word(gramCat=GramCat.VER, gender=None, number=None,
                       infoVerb="inf")
        features = w.getFeatures()
        assert not any(f.startswith("VER_") for f in features)

    def test_verb_features_combinations(self):
        """infoVerb features should include all combinations of the parsed parts."""
        w = _make_word(gramCat=GramCat.VER, gender=None, number=None,
                       infoVerb="ind:pre:1s")
        features = w.getFeatures()
        # Single elements
        assert "indicatif" in features
        assert "présent" in features
        assert "pers_1" in features
        assert "nbr_s" in features
        # Pairs
        assert "indicatif:présent" in features
        assert "indicatif:pers_1" in features
        assert "présent:nbr_s" in features
        # Triple
        assert "indicatif:présent:pers_1" in features
        # Full
        assert "indicatif:présent:pers_1:nbr_s" in features

    def test_infinitif_features(self):
        w = _make_word(gramCat=GramCat.VER, gender=None, number=None,
                       infoVerb="inf")
        features = w.getFeatures()
        assert "infinitif" in features

    def test_no_infoVerb_no_verb_combos(self):
        w = _make_word(gramCat=GramCat.NOM, infoVerb=None)
        features = w.getFeatures()
        assert "indicatif" not in features
        assert "infinitif" not in features

    def test_multiple_infoVerb_entries(self):
        """Multiple semicolon-separated infoVerb entries each produce combinations."""
        w = _make_word(gramCat=GramCat.VER, gender=None, number=None,
                       infoVerb="ind:pre:1s;ind:pre:3s")
        features = w.getFeatures()
        assert "pers_1" in features
        assert "pers_3" in features
        assert "nbr_s" in features

    def test_empty_string_gender_is_included_as_feature(self):
        """Empty string gender/number pass the '!= None' check and are
        included as features. This documents current behavior."""
        w = _make_word(gramCat=GramCat.NOM, gender="", number="")
        features = w.getFeatures()
        # Empty strings are truthy for != None, so they get added
        assert "" in features
        # The combo is ":" (empty:empty)
        assert ":" in features


# ═══════════════════════════════════════════════════════════════════════════════
# fix_e_n_en
# ═══════════════════════════════════════════════════════════════════════════════

class TestFixEnEn:

    def test_exact_output(self):
        """Verify the exact transformed strings, not just absence of pattern."""
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
        assert w.rawSyllCV == "@|i_v_R_#"
        assert w.rawOrthosyllCV == "en|i_v_r_e"

    def test_no_pattern_unchanged(self):
        """Word without the @|n_ pattern should not be modified."""
        w = _make_word(rawSyllCV="m_a_Z_e", rawOrthosyllCV="m_a_n_g_e_r")
        assert w.rawSyllCV == "m_a_Z_e"
        assert w.rawOrthosyllCV == "m_a_n_g_e_r"

    def test_only_syll_pattern_not_ortho(self):
        """If rawSyllCV has @|n_ but rawOrthosyllCV does NOT have e|n_,
        no fix is applied."""
        w = _make_word(rawSyllCV="@|n_a", rawOrthosyllCV="a_n_a")
        assert w.rawSyllCV == "@|n_a"

    def test_multiple_occurrences(self):
        """Recursive fix should handle multiple occurrences."""
        w = _make_word(
            rawSyllCV="@|n_a|@|n_i",
            rawOrthosyllCV="e|n_a|e|n_i",
        )
        assert "@|n_" not in w.rawSyllCV
        assert "e|n_" not in w.rawOrthosyllCV


# ═══════════════════════════════════════════════════════════════════════════════
# phonemesToSyllableNames
# ═══════════════════════════════════════════════════════════════════════════════

class TestPhonemesToSyllableNames:

    def test_with_silent(self, word_sample: Word) -> None:
        result = word_sample.phonemesToSyllableNames()
        assert result == ["@", "ivR#"]

    def test_without_silent(self, word_sample: Word) -> None:
        result = word_sample.phonemesToSyllableNames(withSilent=False)
        assert result == ["@", "ivR"]

    def test_symbol_separator(self, word_sample: Word) -> None:
        result = word_sample.phonemesToSyllableNames(symbol="-")
        assert result == ["@", "i-v-R-#"]

    def test_single_syllable(self) -> None:
        w = _make_word(rawSyllCV="S_a", rawOrthosyllCV="ch_a_t")
        assert w.phonemesToSyllableNames() == ["Sa"]


# ═══════════════════════════════════════════════════════════════════════════════
# graphemsToSyllables
# ═══════════════════════════════════════════════════════════════════════════════

class TestGraphemsToSyllables:

    def test_with_silent(self, word_sample: Word) -> None:
        assert word_sample.graphemsToSyllables() == ["en", "ivre"]

    def test_without_silent(self, word_sample: Word) -> None:
        assert word_sample.graphemsToSyllables(withSilent=False) == ["en", "ivre"]

    def test_symbol_separator(self, word_sample: Word) -> None:
        result = word_sample.graphemsToSyllables(symbol="-")
        assert result == ["en", "i-v-r-e"]

    def test_single_syllable(self) -> None:
        w = _make_word(rawSyllCV="S_a", rawOrthosyllCV="ch_a_t")
        assert w.graphemsToSyllables() == ["chat"]


# ═══════════════════════════════════════════════════════════════════════════════
# syllablesToWord
# ═══════════════════════════════════════════════════════════════════════════════

class TestSyllablesToWord:

    def test_multi_syllable(self, word_sample: Word) -> None:
        assert word_sample.syllablesToWord() == "@ivR#"

    def test_single_syllable(self) -> None:
        w = _make_word(rawSyllCV="S_a", rawOrthosyllCV="ch_a_t")
        assert w.syllablesToWord() == "Sa"


# ═══════════════════════════════════════════════════════════════════════════════
# parseOrthoSyll / parsePhonoSyll
# ═══════════════════════════════════════════════════════════════════════════════

class TestParseSyll:

    def test_parseOrthoSyll(self, word_sample: Word) -> None:
        assert word_sample.parseOrthoSyll() == [["en"], ["i", "v", "r", "e"]]

    def test_parsePhonoSyll(self, word_sample: Word) -> None:
        assert word_sample.parsePhonoSyll() == [["@"], ["i", "v", "R", "#"]]

    def test_single_syllable(self) -> None:
        w = _make_word(rawSyllCV="S_a", rawOrthosyllCV="ch_a_t")
        assert w.parsePhonoSyll() == [["S", "a"]]
        assert w.parseOrthoSyll() == [["ch", "a", "t"]]

    def test_three_syllables(self) -> None:
        w = _make_word(rawSyllCV="a|l_i|m_@", rawOrthosyllCV="a|l_i|m_ent")
        assert w.parsePhonoSyll() == [["a"], ["l", "i"], ["m", "@"]]
        assert w.parseOrthoSyll() == [["a"], ["l", "i"], ["m", "ent"]]


# ═══════════════════════════════════════════════════════════════════════════════
# replaceSyllables
# ═══════════════════════════════════════════════════════════════════════════════

class TestReplaceSyllables:

    def test_basic_replacement(self, word_sample: Word) -> None:
        # word_sample.phonology is "@nivR" (after fix_e_n_en, phonology unchanged)
        result = word_sample.replaceSyllables("ni", "mi")
        assert result == "@mivR"

    def test_no_match_unchanged(self, word_sample: Word) -> None:
        result = word_sample.replaceSyllables("fa", "ta")
        assert result == word_sample.phonology

    def test_same_orig_and_final_returns_unchanged(self) -> None:
        w = _make_word(phonology="abcabc")
        assert w.replaceSyllables("ab", "ab") == "abcabc"

    def test_multiple_occurrences(self) -> None:
        w = _make_word(phonology="abcabc")
        result = w.replaceSyllables("ab", "xy")
        assert result == "xycxyc"

    def test_replacement_with_empty_string_deletes(self) -> None:
        w = _make_word(phonology="abcabc")
        result = w.replaceSyllables("ab", "")
        assert result == "cc"

    def test_replacement_longer_than_original(self) -> None:
        w = _make_word(phonology="abc")
        result = w.replaceSyllables("b", "xyz")
        assert result == "axyzc"

    def test_replacement_does_not_re_match(self) -> None:
        """Replacement that introduces the pattern again should not
        cause re-replacement (the cursor advances past the replacement)."""
        w = _make_word(phonology="aab")
        result = w.replaceSyllables("ab", "aab")
        assert result == "aaab"

    def test_overlapping_pattern(self) -> None:
        """With phonology 'aaa', replacing 'aa' should replace the first
        occurrence and leave the rest."""
        w = _make_word(phonology="aaa")
        result = w.replaceSyllables("aa", "b")
        assert result == "ba"


# ═══════════════════════════════════════════════════════════════════════════════
# atomicFeatures
# ═══════════════════════════════════════════════════════════════════════════════

class TestAtomicFeatures:

    def test_single_atom_with_internal_underscore_stays_whole(self):
        """'_' is internal to one atom's own name -- pers_3 must split to
        {"pers_3"}, not {"pers", "3"}."""
        assert atomicFeatures("pers_3") == frozenset({"pers_3"})

    def test_gender_number_combo_splits_on_colon(self):
        """'m:s' is a genuine compound of two independent atoms, ':'-joined."""
        assert atomicFeatures("m:s") == frozenset({"m", "s"})

    def test_compound_splits_only_on_colon(self):
        assert atomicFeatures("subjonctif:présent:pers_3:nbr_s") == frozenset(
            {"subjonctif", "présent", "pers_3", "nbr_s"}
        )

    def test_not_prefix_stripped_before_split(self):
        assert atomicFeatures("not_pers_3:nbr_s") == frozenset({"pers_3", "nbr_s"})

    def test_not_m_s_is_its_own_indivisible_atom(self):
        """"not_m_s" is a standalone flag ("not the canonical masc-singular form"), not
        a ':'-joined compound -- stripping "not_" leaves "m_s" with no colon to split."""
        assert atomicFeatures("not_m_s") == frozenset({"m_s"})


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
