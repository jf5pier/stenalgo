"""Unit tests for util/completeVerbParadigms.py: full-paradigm detection and the candidate filter."""
from collections import Counter
from typing import Any

from src.nomAdjParadigm import deriveNomAdjEndingTables
from src.verbparadigm import VerbModelException
from src.word import GramCat, Word
from util.completeVerbParadigms import allTemplatedVerbLemmas, confirmCandidates
from util.generateMissingNomAdjForms import generateRows


def _word(ortho, lemme, gramCat=GramCat.VER, gender=None, number=None, infoVerb=None, phon="x"):
    return Word(
        ortho=ortho, phonology=phon, lemme=lemme, gramCat=gramCat, orthoGramCat=[gramCat],
        gender=gender, number=number, infoVerb=infoVerb,
        rawSyllCV="_".join(phon), rawOrthosyllCV="_".join(ortho), frequencyBook=1.0, frequencyFilm=1.0,
    )


class TestAllTemplatedVerbLemmas:

    def test_every_verb_with_a_trusted_template_is_returned_with_no_features(self):
        theory: dict[Any, Any] = {
            ("a",): [_word("aime", "aimer", infoVerb="ind:pre:1s;"), _word("aimer", "aimer", infoVerb="inf;")],
            ("b",): [_word("lis", "lire", infoVerb="ind:pre:1s;")],
            ("c",): [_word("table", "table", gramCat=GramCat.NOM, gender="f", number="s")],
        }
        result = allTemplatedVerbLemmas(theory, {"aimer": "aim:er"}, {})
        assert [info.template for info in result.values()] == ["aim:er"]
        info = next(iter(result.values()))
        assert info.missingFeatures == frozenset() and info.siblingLemmeGramCats == frozenset()

    def test_a_verb_without_template_is_left_out_unless_an_exception_is_trusted(self):
        theory: dict[Any, Any] = {("a",): [_word("lis", "lire", infoVerb="ind:pre:1s;")]}
        assert allTemplatedVerbLemmas(theory, {}, {}) == {}
        regular = {"lire": VerbModelException("lire", "lir:e", "", "regular", "")}
        assert [info.template for info in allTemplatedVerbLemmas(theory, {}, regular).values()] == ["lir:e"]
        defective = {"lire": VerbModelException("lire", "lir:e", "", "defective", "")}
        assert allTemplatedVerbLemmas(theory, {}, defective) == {}


class TestConfirmCandidates:

    def test_keeps_every_candidate_by_default(self):
        candidates = [("lemme_VER", "info", "w1", "ref"), ("lemme_VER", "info", "w2", "ref")]
        confirmed, skipped = confirmCandidates(candidates, {}, {})  # type: ignore[arg-type]
        assert confirmed == candidates and skipped == []

    def test_empty_input(self):
        assert confirmCandidates([], {}, {}) == ([], [])


class TestNomAdjGenerateRows:

    @staticmethod
    def _donors():
        donors = []
        for i, stem in enumerate(["ch", "pl", "br", "gr", "tr"]):
            donors += [_word(stem + "at", f"l{i}", GramCat.NOM, "m", "s", None, stem + "a"),
                       _word(stem + "ats", f"l{i}", GramCat.NOM, "m", "p", None, stem + "a")]
        return donors

    def test_generates_the_missing_plural_and_records_the_source(self):
        words = self._donors() + [_word("format", "format", GramCat.NOM, "m", "s", None, "fORma")]
        tables = deriveNomAdjEndingTables(words)
        rows, sources, skipped = generateRows(words, None, {}, tables, {})
        assert [row.ortho for row in rows] == ["formats"]
        assert sources == Counter({"donor_table": 1})

    def test_existing_orthography_blocks_a_regeneration(self):
        words = self._donors() + [_word("format", "format", GramCat.NOM, "m", "s", None, "fORma")]
        tables = deriveNomAdjEndingTables(words)
        rows, _sources, skipped = generateRows(words, None, {}, tables, {"format": {"formats"}})
        assert rows == []
        assert skipped["ortho already exists (likely a tag gap, not a missing form)"] == 1

    def test_a_generated_row_can_be_the_source_of_the_next_round(self):
        words = self._donors() + [_word("format", "format", GramCat.NOM, "m", "s", None, "fORma")]
        tables = deriveNomAdjEndingTables(words)
        first, _s, _k = generateRows(words, None, {}, tables, {})
        second, _s2, _k2 = generateRows(words + first, None, {}, tables, {"format": {"formats"}})
        assert second == []  # nothing left to generate: the fixed point
