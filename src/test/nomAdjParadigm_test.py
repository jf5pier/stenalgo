#!/usr/bin/python
# coding: utf-8
"""Tests for src/nomAdjParadigm.py"""

import pytest

from src.nomAdjParadigm import (
    ADJ_SLOTS,
    attestedSlots,
    chooseSourceSlot,
    deriveNomAdjEndingTables,
    expectedSlots,
    generateAuthoritativeForm,
    generateMissingForm,
    isSuspectedInvariableForm,
    loadNomAdjModelExceptions,
    missingSlots,
    orthoClassKeys,
)
from src.word import GramCat, Word


def _make_word(ortho, phon, lemme, gramCat, gender, number):
    return Word(
        ortho=ortho, phonology=phon, lemme=lemme,
        gramCat=gramCat, orthoGramCat=[gramCat],
        gender=gender, number=number, infoVerb=None,
        rawSyllCV="_".join(phon), rawOrthosyllCV="_".join(ortho),
        frequencyBook=1.0, frequencyFilm=1.0,
    )


def _nom(ortho, phon, lemme, gender, number):
    return _make_word(ortho, phon, lemme, GramCat.NOM, gender, number)


def _adj(ortho, phon, lemme, gender, number):
    return _make_word(ortho, phon, lemme, GramCat.ADJ, gender, number)


class TestExpectedAndMissingSlots:

    def test_nom_expects_both_numbers_per_attested_gender(self):
        assert expectedSlots(GramCat.NOM, frozenset({"m"})) == {("m", "s"), ("m", "p")}

    def test_nom_expects_both_genders_when_epicene(self):
        assert expectedSlots(GramCat.NOM, frozenset({"m", "f"})) == {
            ("m", "s"), ("m", "p"), ("f", "s"), ("f", "p"),
        }

    def test_adj_always_expects_all_four_slots(self):
        assert expectedSlots(GramCat.ADJ, frozenset({"m"})) == set(ADJ_SLOTS)

    def test_missing_slots_reports_the_gap(self):
        slotMap = {("m", "s"): _nom("chat", "Sa", "chat", "m", "s")}
        assert missingSlots(slotMap, GramCat.NOM) == frozenset({("m", "p")})

    def test_missing_slots_empty_when_complete(self):
        slotMap = {
            ("m", "s"): _nom("chat", "Sa", "chat", "m", "s"),
            ("m", "p"): _nom("chats", "Sa", "chat", "m", "p"),
        }
        assert missingSlots(slotMap, GramCat.NOM) == frozenset()


class TestAttestedSlots:

    def test_groups_by_lemme_gram_cat_then_slot(self):
        words = [
            _nom("chat", "Sa", "chat", "m", "s"),
            _nom("chats", "Sa", "chat", "m", "p"),
            _adj("petit", "p°ti", "petit", "m", "s"),
        ]
        slots = attestedSlots(words)
        assert set(slots["chat_NOM"]) == {("m", "s"), ("m", "p")}
        assert set(slots["petit_ADJ"]) == {("m", "s")}

    def test_skips_words_missing_gender_or_number(self):
        words = [_nom("chat", "Sa", "chat", None, None)]
        assert attestedSlots(words) == {}


class TestIsSuspectedInvariableForm:

    def test_true_for_singular_ending_in_s(self):
        word = _nom("bras", "bRa", "bras", "m", "s")
        assert isSuspectedInvariableForm(word, ("m", "p"))

    def test_true_for_plural_ending_in_s_generating_singular(self):
        # "s"/"z" endings are safe bidirectionally: unlike "x", they're never
        # produced by an irregular plural alternation.
        word = _nom("hachis", "aSi", "hachis", "m", "p")
        assert isSuspectedInvariableForm(word, ("m", "s"))

    def test_false_for_plural_ending_in_x_generating_singular(self):
        # "x" is NOT safe in this direction: it's routinely the *irregular*
        # -al -> -aux alternation (cheval/chevaux), whose singular doesn't
        # end in "x" at all -- must fall through to the donor-table check
        # instead of assuming "abdominaux" is its own singular.
        word = _nom("abdominaux", "abdomino", "abdominal", "m", "p")
        assert not isSuspectedInvariableForm(word, ("m", "s"))

    def test_false_for_singular_not_ending_in_sxz(self):
        word = _nom("chat", "Sa", "chat", "m", "s")
        assert not isSuspectedInvariableForm(word, ("m", "p"))

    def test_true_for_adj_masculine_ending_in_s(self):
        # "gris" is genuinely plural-invariant on the masculine side.
        word = _adj("gris", "gRi", "gris", "m", "s")
        assert isSuspectedInvariableForm(word, ("m", "p"))

    def test_true_for_adj_masculine_ending_in_x_either_direction(self):
        # Unlike NOM, ADJ "-eux" has no competing irregular pattern landing
        # on "x" from a different ending, so both directions are safe
        # (confirmed against Morphalou -- see conversation).
        singular = _adj("chitineux", "SitinP", "chitineux", "m", "s")
        plural = _adj("chitineux", "SitinP", "chitineux", "m", "p")
        assert isSuspectedInvariableForm(singular, ("m", "p"))
        assert isSuspectedInvariableForm(plural, ("m", "s"))

    def test_false_for_adj_number_not_ending_in_sxz(self):
        word = _adj("grand", "grA", "grand", "m", "s")
        assert not isSuspectedInvariableForm(word, ("m", "p"))

    def test_true_for_adj_invariant_gender_suffix(self):
        word = _adj("antisolaire", "@tisolER", "antisolaire", "f", "s")
        assert isSuspectedInvariableForm(word, ("m", "s"))

    def test_false_for_adj_gender_when_no_known_invariant_suffix(self):
        word = _adj("grand", "grA", "grand", "m", "s")
        assert not isSuspectedInvariableForm(word, ("f", "s"))


class TestOrthoClassKeys:

    def test_longest_first(self):
        assert orthoClassKeys("cheval") == ["val", "al", "l"]

    def test_short_word_only_yields_keys_it_can(self):
        assert orthoClassKeys("nu") == ["nu", "u"]


class TestDeriveAndGenerate:

    def test_regular_plural_derived_from_donors_and_applied_to_new_lemma(self):
        # "chat"/"plat" only share the (less specific) 2-letter class "at", not a
        # 3-letter class with the target "format" -- exercises the length-2 donor
        # threshold (>=2 donors), not length-3's (>=1).
        donors = [
            _nom("chat", "Sa", "chat", "m", "s"),
            _nom("chats", "Sa", "chat", "m", "p"),
            _nom("plat", "pla", "plat", "m", "s"),
            _nom("plats", "pla", "plat", "m", "p"),
        ]
        target = _nom("format", "fORma", "format", "m", "s")
        tables = deriveNomAdjEndingTables(donors + [target])
        candidate = generateMissingForm(target, ("m", "p"), tables)
        assert candidate is not None
        assert candidate.ortho == "formats"
        assert candidate.phonology == "fORma"
        assert candidate.gender == "m"
        assert candidate.number == "p"
        assert candidate.frequencyBook == 0.0 and candidate.frequencyFilm == 0.0

    def test_irregular_al_aux_class_learned_from_its_own_donors(self):
        donors = [
            _nom("journal", "ZuRnal", "journal", "m", "s"),
            _nom("journaux", "ZuRno", "journal", "m", "p"),
            _nom("canal", "kanal", "canal", "m", "s"),
            _nom("canaux", "kano", "canal", "m", "p"),
        ]
        target = _nom("signal", "sipal", "signal", "m", "s")
        tables = deriveNomAdjEndingTables(donors + [target])
        candidate = generateMissingForm(target, ("m", "p"), tables)
        assert candidate is not None
        assert candidate.ortho == "signaux"
        assert candidate.phonology == "sipo"

    def test_no_confident_class_returns_none(self):
        # "truc" shares no class key at all with "chat" (different ending
        # letters at every length) -- no table entry exists to look up.
        donors = [_nom("chat", "Sa", "chat", "m", "s"), _nom("chats", "Sa", "chat", "m", "p")]
        target = _nom("truc", "tRyk", "truc", "m", "s")
        tables = deriveNomAdjEndingTables(donors + [target])
        assert generateMissingForm(target, ("m", "p"), tables) is None

    def test_adjective_feminine_derived_from_donors(self):
        donors = [
            _adj("grand", "grA", "grand", "m", "s"),
            _adj("grande", "grAd", "grand", "f", "s"),
            _adj("gourmand", "guRmA", "gourmand", "m", "s"),
            _adj("gourmande", "guRmAd", "gourmand", "f", "s"),
        ]
        target = _adj("marchand", "maRSA", "marchand", "m", "s")
        tables = deriveNomAdjEndingTables(donors + [target])
        candidate = generateMissingForm(target, ("f", "s"), tables)
        assert candidate is not None
        assert candidate.ortho == "marchande"
        assert candidate.phonology == "maRSAd"
        assert candidate.gender == "f"


class TestChooseSourceSlot:

    def test_adj_prefers_masculine_singular(self):
        slotMap = {
            ("f", "s"): _adj("petite", "p°tit", "petit", "f", "s"),
            ("m", "s"): _adj("petit", "p°ti", "petit", "m", "s"),
        }
        assert chooseSourceSlot(slotMap, GramCat.ADJ) == ("m", "s")

    def test_nom_prefers_singular_of_the_attested_gender(self):
        slotMap = {("f", "p"): _nom("fleurs", "flOR", "fleur", "f", "p")}
        assert chooseSourceSlot(slotMap, GramCat.NOM) == ("f", "p")

    def test_empty_returns_none(self):
        assert chooseSourceSlot({}, GramCat.ADJ) is None


class TestGenerateAuthoritativeForm:

    def test_no_morphalou_falls_back_to_donor_table(self):
        donors = [
            _nom("chat", "Sa", "chat", "m", "s"), _nom("chats", "Sa", "chat", "m", "p"),
            _nom("plat", "pla", "plat", "m", "s"), _nom("plats", "pla", "plat", "m", "p"),
        ]
        target = _nom("format", "fORma", "format", "m", "s")
        tables = deriveNomAdjEndingTables(donors + [target])
        candidate, source = generateAuthoritativeForm(target, ("m", "p"), tables, None)
        assert source == "donor_table"
        assert candidate is not None and candidate.ortho == "formats"

    def test_morphalou_confirms_donor_table_answer(self):
        donors = [
            _nom("chat", "Sa", "chat", "m", "s"), _nom("chats", "Sa", "chat", "m", "p"),
            _nom("plat", "pla", "plat", "m", "s"), _nom("plats", "pla", "plat", "m", "p"),
        ]
        target = _nom("format", "fORma", "format", "m", "s")
        tables = deriveNomAdjEndingTables(donors + [target])
        morphalou = {("format", "NOM"): {("m", "p"): {"formats"}}}
        candidate, source = generateAuthoritativeForm(target, ("m", "p"), tables, morphalou)
        assert source == "morphalou"
        assert candidate is not None and candidate.ortho == "formats"

    def test_morphalou_overrides_a_wrong_donor_table_answer(self):
        donors = [
            _nom("chat", "Sa", "chat", "m", "s"), _nom("chats", "Sa", "chat", "m", "p"),
            _nom("plat", "pla", "plat", "m", "s"), _nom("plats", "pla", "plat", "m", "p"),
        ]
        target = _nom("format", "fORma", "format", "m", "s")
        tables = deriveNomAdjEndingTables(donors + [target])
        # Morphalou disagrees with the donor table's "formats" guess.
        morphalou = {("format", "NOM"): {("m", "p"): {"formatz"}}}
        candidate, source = generateAuthoritativeForm(target, ("m", "p"), tables, morphalou)
        assert source == "morphalou_override"
        assert candidate is not None
        assert candidate.ortho == "formatz"
        # phon/syll still come from the donor table, not invented from Morphalou.
        assert candidate.phonology == "fORma"

    def test_morphalou_answer_with_no_donor_table_phon_is_reported_not_guessed(self):
        target = _nom("truc", "tRyk", "truc", "m", "s")
        tables = deriveNomAdjEndingTables([target])  # no donors at all -> no phon derivation possible
        morphalou = {("truc", "NOM"): {("m", "p"): {"trucs"}}}
        candidate, source = generateAuthoritativeForm(target, ("m", "p"), tables, morphalou)
        assert candidate is None
        assert source == "morphalou_no_phon"

    def test_no_answer_from_either_source(self):
        target = _nom("truc", "tRyk", "truc", "m", "s")
        tables = deriveNomAdjEndingTables([target])
        candidate, source = generateAuthoritativeForm(target, ("m", "p"), tables, {})
        assert candidate is None
        assert source == "none"


class TestLoadNomAdjModelExceptions:

    def test_parses_real_vendored_file(self):
        exceptions = loadNomAdjModelExceptions("resources/nomAdjModelExceptions.tsv")
        assert exceptions[("cheval", "NOM")].status == "irregular"
        assert exceptions[("cheval", "NOM")].overrideOrtho == "cheval;chevaux"
        assert exceptions[("bras", "NOM")].status == "invariable"
        assert exceptions[("beau", "ADJ")].overrideOrtho == "beau;beaux;belle;belles"
