#!/usr/bin/python
# coding: utf-8
"""Tests for src/verbparadigm.py"""

import pytest
from src.featureextractor import extractDiscriminatingFeatures
from src.verbparadigm import (
    ConjugationTemplate,
    VerbModelException,
    allFiniteSlots,
    attestedInfinitiveWordByLemme,
    crossLemmaFeatureSetCollisions,
    deriveConjugationEndingTables,
    deriveParticipeRadicalOrthosyll,
    detectUndersampledLemmas,
    fullFeatureSpace,
    generateMissingConjugatedForm,
    generateMissingParticiple,
    generateOrthoForm,
    generateParticipeOrthosyll,
    getTrustedTemplate,
    infinitiveRadical,
    lemmeOfVerbLemmeGramCat,
    loadVerbisteTemplates,
    loadVerbModelExceptions,
    newlyCollidingLemmas,
    parseConjugationTemplates,
    spliceParticiplePhon,
)
from src.word import GramCat, Word


def _make_verb_form(ortho, lemme, gender=None, number=None, infoVerb=None):
    return Word(
        ortho=ortho, phonology=ortho, lemme=lemme,
        gramCat=GramCat.VER, orthoGramCat=[GramCat.VER],
        gender=gender, number=number, infoVerb=infoVerb,
        rawSyllCV="_".join(ortho), rawOrthosyllCV="_".join(ortho),
        frequencyBook=0.0, frequencyFilm=0.0,
    )


# ---------------------------------------------------------------------------
# loadVerbisteTemplates / loadVerbModelExceptions
# ---------------------------------------------------------------------------

class TestLoadVerbisteTemplates:

    def test_parses_real_vendored_file(self):
        """Sanity-check against the real vendored resources/verbiste/verbs-fr.xml:
        garnir/regarnir must both resolve to the fin:ir template used as the
        motivating example throughout the design plan."""
        templates = loadVerbisteTemplates("resources/verbiste/verbs-fr.xml")
        assert templates["garnir"] == "fin:ir"
        assert templates["regarnir"] == "fin:ir"
        assert "rechampir" not in templates
        assert len(templates) > 7000


class TestLoadVerbModelExceptions:

    def test_parses_real_vendored_file(self):
        """Sanity-check against the real vendored resources/verbModelExceptions.tsv."""
        exceptions = loadVerbModelExceptions("resources/verbModelExceptions.tsv")
        assert exceptions["rechampir"].template == "fin:ir"
        assert exceptions["rechampir"].status == "needs_review"
        assert exceptions["chaut"].status == "skip_artifact"

    def test_parses_synthetic_file(self, tmp_path):
        tsvFile = tmp_path / "exceptions.tsv"
        tsvFile.write_text(
            "# a comment line\n"
            "lemme\ttemplate\tmodel_sibling\tstatus\tnote\n"
            "foo\tfin:ir\tgarnir\tregular\tsome note\n"
            "bar\t\t\tdefective\t\n"
        )
        exceptions = loadVerbModelExceptions(str(tsvFile))
        assert exceptions["foo"] == VerbModelException("foo", "fin:ir", "garnir", "regular", "some note")
        assert exceptions["bar"] == VerbModelException("bar", "", "", "defective", "")


# ---------------------------------------------------------------------------
# getTrustedTemplate
# ---------------------------------------------------------------------------

class TestGetTrustedTemplate:

    def test_verbiste_takes_priority(self):
        verbiste = {"garnir": "fin:ir"}
        exceptions = {"garnir": VerbModelException("garnir", "wrong:template", "", "regular", "")}
        assert getTrustedTemplate("garnir", verbiste, exceptions) == "fin:ir"

    def test_trusted_exception_status_used_when_not_in_verbiste(self):
        exceptions = {"rechampir": VerbModelException("rechampir", "fin:ir", "garnir", "regular", "")}
        assert getTrustedTemplate("rechampir", {}, exceptions) == "fin:ir"

    def test_untrusted_exception_status_not_used(self):
        """needs_review / defective / skip_artifact entries must never be
        silently trusted for automatic undersampling detection -- they exist
        precisely because a human hasn't confirmed them yet."""
        for status in ("needs_review", "defective", "skip_artifact"):
            exceptions = {"foo": VerbModelException("foo", "fin:ir", "garnir", status, "")}
            assert getTrustedTemplate("foo", {}, exceptions) is None

    def test_unknown_lemma_returns_none(self):
        assert getTrustedTemplate("nonexistent", {}, {}) is None


# ---------------------------------------------------------------------------
# lemmeOfVerbLemmeGramCat
# ---------------------------------------------------------------------------

class TestLemmeOfVerbLemmeGramCat:

    def test_extracts_verb_lemma(self):
        assert lemmeOfVerbLemmeGramCat("garnir_VER") == "garnir"

    def test_non_verb_returns_none(self):
        assert lemmeOfVerbLemmeGramCat("chat_NOM") is None


# ---------------------------------------------------------------------------
# fullFeatureSpace / detectUndersampledLemmas
# ---------------------------------------------------------------------------

class TestDetectUndersampledLemmas:

    def _build_strokeLemmeDiscriminators(self, words):
        theory = {((i,),): [word] for i, word in enumerate(words)}
        _, _, strokeLemmeDiscriminators = extractDiscriminatingFeatures(theory)
        return strokeLemmeDiscriminators

    def test_undersampled_lemma_flagged_against_well_sampled_sibling(self):
        """Mirrors the rechampir/regarnir-vs-garnir motivating example: garnir
        has the full participle paradigm (m_s/f_s/m_p/f_p) plus a finite form,
        rechampir only has m_s and a finite form. rechampir's feature space
        should come out as a strict subset of garnir's."""
        garnirWords = [
            _make_verb_form("garni", "garnir", gender="m", number="s"),
            _make_verb_form("garnie", "garnir", gender="f", number="s"),
            _make_verb_form("garnis", "garnir", gender="m", number="p"),
            _make_verb_form("garnies", "garnir", gender="f", number="p"),
            _make_verb_form("garnit", "garnir", infoVerb="ind:pre:3s"),
        ]
        rechampirWords = [
            _make_verb_form("rechampi", "rechampir", gender="m", number="s"),
            _make_verb_form("rechampit", "rechampir", infoVerb="ind:pre:3s"),
        ]
        strokeLemmeDiscriminators = self._build_strokeLemmeDiscriminators(garnirWords + rechampirWords)

        verbiste = {"garnir": "fin:ir"}
        exceptions = {"rechampir": VerbModelException("rechampir", "fin:ir", "garnir", "regular", "")}

        result = detectUndersampledLemmas(strokeLemmeDiscriminators, verbiste, exceptions)

        assert "rechampir_VER" in result
        assert "garnir_VER" not in result
        flagged = result["rechampir_VER"]
        assert flagged.template == "fin:ir"
        assert "garnir_VER" in flagged.siblingLemmeGramCats
        # rechampir is missing f_s/f_p/m_p-shaped features that garnir has
        assert flagged.missingFeatures
        assert flagged.missingFeatures < fullFeatureSpace(strokeLemmeDiscriminators, "garnir_VER")

    def test_untrusted_template_status_prevents_flagging(self):
        """Even a genuinely undersampled lemma is not flagged if its template
        assignment hasn't been manually confirmed (status needs_review/defective/
        skip_artifact) -- automatic detection must never run ahead of curation."""
        garnirWords = [
            _make_verb_form("garni", "garnir", gender="m", number="s"),
            _make_verb_form("garnie", "garnir", gender="f", number="s"),
        ]
        rechampirWords = [
            _make_verb_form("rechampi", "rechampir", gender="m", number="s"),
        ]
        strokeLemmeDiscriminators = self._build_strokeLemmeDiscriminators(garnirWords + rechampirWords)

        verbiste = {"garnir": "fin:ir"}
        exceptions = {"rechampir": VerbModelException("rechampir", "fin:ir", "garnir", "needs_review", "")}

        result = detectUndersampledLemmas(strokeLemmeDiscriminators, verbiste, exceptions)
        assert "rechampir_VER" not in result

    def test_lemma_with_no_siblings_is_not_flagged(self):
        """A lemma is the only one following its template in the current
        lexicon: there's nothing to compare it against, so it must not be
        flagged (that would be comparing a set to the empty set, trivially
        true but meaningless)."""
        words = [_make_verb_form("garni", "garnir", gender="m", number="s")]
        strokeLemmeDiscriminators = self._build_strokeLemmeDiscriminators(words)
        verbiste = {"garnir": "fin:ir"}

        result = detectUndersampledLemmas(strokeLemmeDiscriminators, verbiste, {})
        assert result == {}

    def test_equally_sampled_siblings_not_flagged(self):
        """Two lemmas with identical feature spaces are siblings, not subsets
        of each other, and neither should be flagged."""
        garnirWords = [
            _make_verb_form("garni", "garnir", gender="m", number="s"),
            _make_verb_form("garnie", "garnir", gender="f", number="s"),
        ]
        croupirWords = [
            _make_verb_form("croupi", "croupir", gender="m", number="s"),
            _make_verb_form("croupie", "croupir", gender="f", number="s"),
        ]
        strokeLemmeDiscriminators = self._build_strokeLemmeDiscriminators(garnirWords + croupirWords)
        verbiste = {"garnir": "fin:ir", "croupir": "fin:ir"}

        result = detectUndersampledLemmas(strokeLemmeDiscriminators, verbiste, {})
        assert result == {}

    def test_empty_input(self):
        assert detectUndersampledLemmas({}, {}, {}) == {}


# ---------------------------------------------------------------------------
# parseConjugationTemplates / infinitiveRadical / generateOrthoForm
#
# Validated directly against real attested rows pulled from LexiqueMixte.tsv
# for garnir/regarnir/rechampir (all fin:ir), so a wrong template-parsing or
# ending-index bug would fail against ground truth, not just internal
# self-consistency.
# ---------------------------------------------------------------------------

class TestConjugationTemplates:

    def test_parses_real_vendored_file(self):
        templates = parseConjugationTemplates("resources/verbiste/conjugations-fr.xml")
        finIr = templates["fin:ir"]
        assert finIr.infinitiveSuffix == "ir"
        assert finIr.forms["ind:pre"] == ["is", "is", "it", "issons", "issez", "issent"]
        assert finIr.forms["par:pas"] == ["i", "is", "ie", "ies"]
        assert finIr.forms["imp:pre"] == ["is", "issons", "issez"]
        assert finIr.forms["inf"] == ["ir"]

    def test_infinitive_radical(self):
        templates = parseConjugationTemplates("resources/verbiste/conjugations-fr.xml")
        finIr = templates["fin:ir"]
        assert infinitiveRadical("garnir", finIr) == "garn"
        assert infinitiveRadical("regarnir", finIr) == "regarn"
        assert infinitiveRadical("rechampir", finIr) == "rechamp"

    def test_infinitive_radical_rejects_mismatched_suffix(self):
        template = ConjugationTemplate(name="fin:ir", forms={"inf": ["ir"]})
        with pytest.raises(ValueError):
            infinitiveRadical("parler", template)

    def test_generates_attested_regarnir_forms(self):
        """Every one of these is a real row already in LexiqueMixte.tsv --
        this is the "cross-check against attested forms" the design plan
        calls for before trusting a template on missing forms."""
        templates = parseConjugationTemplates("resources/verbiste/conjugations-fr.xml")
        finIr = templates["fin:ir"]
        radical = infinitiveRadical("regarnir", finIr)
        assert generateOrthoForm(radical, finIr, "par:pas", gender="m", number="s") == "regarni"
        assert generateOrthoForm(radical, finIr, "par:pas", gender="f", number="p") == "regarnies"
        assert generateOrthoForm(radical, finIr, "inf") == "regarnir"
        assert generateOrthoForm(radical, finIr, "ind:fut", personNumber="2p") == "regarnirez"
        assert generateOrthoForm(radical, finIr, "ind:pre", personNumber="1s") == "regarnis"
        assert generateOrthoForm(radical, finIr, "imp:pre", personNumber="2p") == "regarnissez"

    def test_generates_attested_rechampir_forms(self):
        templates = parseConjugationTemplates("resources/verbiste/conjugations-fr.xml")
        finIr = templates["fin:ir"]
        radical = infinitiveRadical("rechampir", finIr)
        assert generateOrthoForm(radical, finIr, "par:pas", gender="m", number="p") == "rechampis"
        assert generateOrthoForm(radical, finIr, "ind:pre", personNumber="3s") == "rechampit"

    def test_generates_missing_rechampir_forms(self):
        """The actually-missing forms motivating this whole plan: rechampir
        has no attested m_s/f_s/f_p participle rows in LexiqueMixte.tsv."""
        templates = parseConjugationTemplates("resources/verbiste/conjugations-fr.xml")
        finIr = templates["fin:ir"]
        radical = infinitiveRadical("rechampir", finIr)
        assert generateOrthoForm(radical, finIr, "par:pas", gender="m", number="s") == "rechampi"
        assert generateOrthoForm(radical, finIr, "par:pas", gender="f", number="s") == "rechampie"
        assert generateOrthoForm(radical, finIr, "par:pas", gender="f", number="p") == "rechampies"

    def test_unknown_code_returns_none(self):
        template = ConjugationTemplate(name="t", forms={"inf": ["ir"]})
        assert generateOrthoForm("garn", template, "sub:imp", personNumber="1s") is None

    def test_unresolved_person_or_gender_returns_none(self):
        templates = parseConjugationTemplates("resources/verbiste/conjugations-fr.xml")
        finIr = templates["fin:ir"]
        radical = infinitiveRadical("garnir", finIr)
        assert generateOrthoForm(radical, finIr, "ind:pre", personNumber=None) is None
        assert generateOrthoForm(radical, finIr, "par:pas", gender="m", number=None) is None


# ---------------------------------------------------------------------------
# Participle phonology splicing
#
# The strongest validation available: reconstruct garnie/garnies/garnis from
# the attested garni (m_s) row and compare directly against the real attested
# phon/rawOrthosyllCV for those forms already in LexiqueMixte.tsv (design
# plan's own risk-mitigation: "compare spliced phonology against attested
# phonology for forms that already exist"). Then generate rechampir's
# genuinely missing forms, which have no ground truth to compare against.
# ---------------------------------------------------------------------------

def _make_participle(ortho, phonology, lemme, gender, number, rawSyllCV, rawOrthosyllCV):
    return Word(
        ortho=ortho, phonology=phonology, lemme=lemme,
        gramCat=GramCat.VER, orthoGramCat=[GramCat.VER],
        gender=gender, number=number, infoVerb="par:pas;",
        rawSyllCV=rawSyllCV, rawOrthosyllCV=rawOrthosyllCV,
        frequencyBook=0.0, frequencyFilm=0.0,
    )


class TestParticipleSplicing:

    # Real attested LexiqueMixte.tsv rows for garnir's past participle.
    GARNI = ("garni", "gaRni", "garnir", "m", "s", "g_a_R|n_i", "g_a_r|n_i")
    GARNIE = ("garnie", "gaRni", "garnir", "f", "s", "g_a_R|n_i_#", "g_a_r|n_i_e")
    GARNIS = ("garnis", "gaRni", "garnir", "m", "p", "g_a_R|n_i_#", "g_a_r|n_i_s")
    GARNIES = ("garnies", "gaRni", "garnir", "f", "p", "g_a_R|n_i_#", "g_a_r|n_i_es")

    def test_splice_phon_reuses_verbatim_and_strips_hash(self):
        garni = _make_participle(*self.GARNI)
        phon, rawSyllCV = spliceParticiplePhon(garni)
        assert phon == "gaRni"
        assert rawSyllCV == "g_a_R|n_i"

        garnie = _make_participle(*self.GARNIE)
        phon, rawSyllCV = spliceParticiplePhon(garnie)
        assert phon == "gaRni"
        assert "#" not in rawSyllCV
        assert rawSyllCV == "g_a_R|n_i"  # '#' stripped

    def test_derive_radical_orthosyll_from_any_gender_number(self):
        assert deriveParticipeRadicalOrthosyll(_make_participle(*self.GARNI)) == "g_a_r|n_i"
        assert deriveParticipeRadicalOrthosyll(_make_participle(*self.GARNIE)) == "g_a_r|n_i"
        assert deriveParticipeRadicalOrthosyll(_make_participle(*self.GARNIS)) == "g_a_r|n_i"
        assert deriveParticipeRadicalOrthosyll(_make_participle(*self.GARNIES)) == "g_a_r|n_i"

    def test_reconstructs_attested_forms_from_m_s(self):
        """Reconstruct f_s/f_p/m_p from the m_s attested row and check against
        the real attested rawOrthosyllCV for those forms."""
        garni = _make_participle(*self.GARNI)
        assert generateParticipeOrthosyll(garni, "f", "s") == self.GARNIE[6]
        assert generateParticipeOrthosyll(garni, "f", "p") == self.GARNIES[6]
        assert generateParticipeOrthosyll(garni, "m", "p") == self.GARNIS[6]

    def test_reconstructs_attested_m_s_from_a_non_m_s_form(self):
        """Splicing must work starting from ANY attested gender/number, not
        just m_s -- reconstruct garni (m_s) starting from garnies (f_p)."""
        garnies = _make_participle(*self.GARNIES)
        assert generateParticipeOrthosyll(garnies, "m", "s") == self.GARNI[6]

    def test_generate_missing_participle_reconstructs_attested_garnir_forms(self):
        templates = parseConjugationTemplates("resources/verbiste/conjugations-fr.xml")
        finIr = templates["fin:ir"]
        garni = _make_participle(*self.GARNI)
        for expected in (self.GARNIE, self.GARNIS, self.GARNIES):
            ortho, phon, lemme, gender, number, _rawSyllCV, rawOrthosyllCV = expected
            generated = generateMissingParticiple("garnir", finIr, garni, gender, number)
            assert generated.ortho == ortho
            assert generated.phonology == phon
            assert generated.rawOrthosyllCV == rawOrthosyllCV
            assert generated.frequencyBook == 0.0
            assert generated.frequencyFilm == 0.0

    def test_generate_missing_rechampir_participles(self):
        """The actual motivating gap: rechampir only has an attested m_p
        (rechampis) past-participle row; generate the missing m_s/f_s/f_p."""
        templates = parseConjugationTemplates("resources/verbiste/conjugations-fr.xml")
        finIr = templates["fin:ir"]
        rechampis = _make_participle(
            "rechampis", "R°S@pi", "rechampir", "m", "p",
            "R_°|S_@|p_i", "r_e|ch_am|p_is",
        )
        m_s = generateMissingParticiple("rechampir", finIr, rechampis, "m", "s")
        assert m_s.ortho == "rechampi"
        assert m_s.phonology == "R°S@pi"
        assert m_s.rawOrthosyllCV == "r_e|ch_am|p_i"

        f_s = generateMissingParticiple("rechampir", finIr, rechampis, "f", "s")
        assert f_s.ortho == "rechampie"
        assert f_s.rawOrthosyllCV == "r_e|ch_am|p_i_e"

        f_p = generateMissingParticiple("rechampir", finIr, rechampis, "f", "p")
        assert f_p.ortho == "rechampies"
        assert f_p.rawOrthosyllCV == "r_e|ch_am|p_i_es"

    def test_derive_radical_rejects_mismatched_suffix(self):
        badWord = _make_participle("garnie", "gaRni", "garnir", "f", "s", "g_a_R|n_i", "g_a_r|n_x")
        with pytest.raises(ValueError):
            deriveParticipeRadicalOrthosyll(badWord)


# ---------------------------------------------------------------------------
# crossLemmaFeatureSetCollisions / newlyCollidingLemmas
#
# The actual "conflicting feature set" bug motivating this whole design plan:
# two unrelated lemmas independently getting assigned the identical minimal
# discriminator by greedyOptimizeDiscriminator (e.g. rechampir and regarnir
# both landing on ('p', 'indicatif')). This is a collision in the
# discriminator-*feature* space, not in the raw keystroke (Strokes) space --
# a candidate can be phonetically unique yet still cause this kind of
# collision, which is exactly what happened for rechampir/regarnir.
# ---------------------------------------------------------------------------

def _featureset_entry(featureSet, *lemmeWords):
    """One featuresetWords entry: featureSet -> [(word1, word2, ...)]."""
    return {featureSet: [tuple(lemmeWords)]}


# ---------------------------------------------------------------------------
# allFiniteSlots / deriveConjugationEndingTables / generateMissingConjugatedForm
# ---------------------------------------------------------------------------

_FAKE_TEMPLATE = ConjugationTemplate(
    name="fake:ir",
    forms={
        "inf": ["ir"],
        "ind:pre": ["is", "is", "it", "issons", "issez", "issent"],
        "ind:pas": ["is", "is", "it", "îmes", "îtes", "irent"],
        "par:pre": ["issant"],
        "par:pas": ["i", "is", "ie", "ies"],
    },
)


def _make_infinitive(lemme, phon):
    return Word(
        ortho=lemme, phonology=phon, lemme=lemme,
        gramCat=GramCat.VER, orthoGramCat=[GramCat.VER],
        gender=None, number=None, infoVerb="inf;",
        rawSyllCV=phon, rawOrthosyllCV=phon,
        frequencyBook=1.0, frequencyFilm=1.0,
    )


def _make_finite(lemme, phon, code, personNumber):
    return Word(
        ortho=phon, phonology=phon, lemme=lemme,
        gramCat=GramCat.VER, orthoGramCat=[GramCat.VER],
        gender=None, number=None, infoVerb=f"{code}:{personNumber};",
        rawSyllCV=phon, rawOrthosyllCV=phon,
        frequencyBook=1.0, frequencyFilm=1.0,
    )


class TestAllFiniteSlots:

    def test_excludes_invariant_and_participle_codes(self):
        slots = allFiniteSlots(_FAKE_TEMPLATE)
        codes = {code for code, _pn in slots}
        assert codes == {"ind:pre", "ind:pas"}

    def test_includes_every_person_number_for_each_finite_code(self):
        slots = allFiniteSlots(_FAKE_TEMPLATE)
        personNumbers = {pn for code, pn in slots if code == "ind:pre"}
        assert personNumbers == {"1s", "2s", "3s", "1p", "2p", "3p"}


class TestDeriveConjugationEndingTablesAndGenerate:

    def _build_theory_and_templates(self):
        # Two donor lemmas of the same fake template, agreeing on ind:pre:1s's
        # ending ("X") but disagreeing on ind:pas:3p's ("Y" vs "Z").
        donor1Inf = _make_infinitive("abir", "abiR")
        donor2Inf = _make_infinitive("cdir", "cdiR")
        donor1Pre = _make_finite("abir", "abX", "ind:pre", "1s")
        donor2Pre = _make_finite("cdir", "cdX", "ind:pre", "1s")
        donor1Pas = _make_finite("abir", "abY", "ind:pas", "3p")
        donor2Pas = _make_finite("cdir", "cdZ", "ind:pas", "3p")
        theory = {
            ((1,),): [donor1Inf, donor1Pre, donor1Pas],
            ((2,),): [donor2Inf, donor2Pre, donor2Pas],
        }
        verbisteTemplates = {"abir": "fake:ir", "cdir": "fake:ir"}
        exceptions: dict = {}
        return theory, verbisteTemplates, exceptions

    def test_infinitive_suffix_derived_across_donors(self):
        theory, verbisteTemplates, exceptions = self._build_theory_and_templates()
        tables = deriveConjugationEndingTables(theory, verbisteTemplates, exceptions)
        assert tables.infinitiveSuffixByKey[("phonology", "fake:ir")] == "iR"

    def test_agreeing_slot_has_full_match_rate(self):
        theory, verbisteTemplates, exceptions = self._build_theory_and_templates()
        tables = deriveConjugationEndingTables(theory, verbisteTemplates, exceptions)
        key = ("phonology", "fake:ir", "ind:pre", "1s")
        assert tables.slotEndingByKey[key] == "X"
        assert tables.slotMatchRateByKey[key] == 1.0

    def test_disagreeing_slot_has_partial_match_rate(self):
        theory, verbisteTemplates, exceptions = self._build_theory_and_templates()
        tables = deriveConjugationEndingTables(theory, verbisteTemplates, exceptions)
        key = ("phonology", "fake:ir", "ind:pas", "3p")
        assert tables.slotEndingByKey[key] in ("Y", "Z")
        assert tables.slotMatchRateByKey[key] == 0.5

    def test_generate_missing_form_for_confident_slot(self):
        theory, verbisteTemplates, exceptions = self._build_theory_and_templates()
        tables = deriveConjugationEndingTables(theory, verbisteTemplates, exceptions)
        targetInfinitive = _make_infinitive("efir", "efiR")
        generated = generateMissingConjugatedForm(
            "efir", _FAKE_TEMPLATE, targetInfinitive, "ind:pre", "1s", tables
        )
        assert generated is not None
        assert generated.phonology == "efX"
        assert generated.rawSyllCV == "efX"
        assert generated.rawOrthosyllCV == "efX"
        assert generated.ortho == "efis"
        assert generated.frequencyBook == 0.0
        assert generated.frequencyFilm == 0.0

    def test_low_confidence_slot_rejected_by_default_min_match_rate(self):
        theory, verbisteTemplates, exceptions = self._build_theory_and_templates()
        tables = deriveConjugationEndingTables(theory, verbisteTemplates, exceptions)
        targetInfinitive = _make_infinitive("efir", "efiR")
        generated = generateMissingConjugatedForm(
            "efir", _FAKE_TEMPLATE, targetInfinitive, "ind:pas", "3p", tables
        )
        assert generated is None

    def test_low_confidence_slot_accepted_with_lower_min_match_rate(self):
        theory, verbisteTemplates, exceptions = self._build_theory_and_templates()
        tables = deriveConjugationEndingTables(theory, verbisteTemplates, exceptions)
        targetInfinitive = _make_infinitive("efir", "efiR")
        generated = generateMissingConjugatedForm(
            "efir", _FAKE_TEMPLATE, targetInfinitive, "ind:pas", "3p", tables,
            minMatchRate=0.5,
        )
        assert generated is not None

    def test_slot_never_attested_for_template_returns_none(self):
        theory, verbisteTemplates, exceptions = self._build_theory_and_templates()
        tables = deriveConjugationEndingTables(theory, verbisteTemplates, exceptions)
        targetInfinitive = _make_infinitive("efir", "efiR")
        generated = generateMissingConjugatedForm(
            "efir", _FAKE_TEMPLATE, targetInfinitive, "ind:pas", "2p", tables
        )
        assert generated is None

    def test_untrusted_lemma_excluded_from_derivation(self):
        """A lemma with no entry in verbisteTemplates/exceptions contributes
        nothing to the derived tables."""
        donorInf = _make_infinitive("abir", "abiR")
        donorPre = _make_finite("abir", "abX", "ind:pre", "1s")
        theory = {((1,),): [donorInf, donorPre]}
        tables = deriveConjugationEndingTables(theory, verbisteTemplates={}, exceptions={})
        assert tables.infinitiveSuffixByKey == {}
        assert tables.slotEndingByKey == {}


class TestCrossLemmaFeatureSetCollisions:

    def test_no_collision_within_single_lemma(self):
        w1 = _make_verb_form("rechampi", "rechampir")
        w2 = _make_verb_form("rechampit", "rechampir")
        featuresetWords = _featureset_entry(("p", "indicatif"), w1, w2)
        assert crossLemmaFeatureSetCollisions(featuresetWords) == {}

    def test_collision_detected_across_lemmas(self):
        """Mirrors the motivating bug: rechampir and regarnir both end up
        needing the identical minimal discriminator."""
        rechampiWords = (_make_verb_form("rechampis", "rechampir"), _make_verb_form("rechampit", "rechampir"))
        regarniWords = (_make_verb_form("regarnis", "regarnir"), _make_verb_form("regarnie", "regarnir"))
        featureSet = ("p", "indicatif")
        featuresetWords = {featureSet: [rechampiWords, regarniWords]}

        collisions = crossLemmaFeatureSetCollisions(featuresetWords)
        assert featureSet in collisions
        assert collisions[featureSet] == {"rechampir_VER", "regarnir_VER"}

    def test_no_collision_when_lemmes_differ_across_unrelated_featuresets(self):
        rechampiWords = (_make_verb_form("rechampis", "rechampir"),)
        regarniWords = (_make_verb_form("regarnis", "regarnir"),)
        featuresetWords = {
            ("p", "indicatif"): [rechampiWords],
            ("m_s",): [regarniWords],
        }
        assert crossLemmaFeatureSetCollisions(featuresetWords) == {}


class TestNewlyCollidingLemmas:

    def test_empty_when_no_augmented_collisions(self):
        baseline = {}
        augmented = _featureset_entry(("p", "indicatif"), _make_verb_form("rechampis", "rechampir"))
        assert newlyCollidingLemmas(baseline, augmented) == set()

    def test_detects_brand_new_collision(self):
        baseline = {
            ("p", "indicatif"): [(_make_verb_form("rechampis", "rechampir"),)],
        }
        rechampiWords = (_make_verb_form("rechampis", "rechampir"), _make_verb_form("rechampit", "rechampir"))
        regarniWords = (_make_verb_form("regarnis", "regarnir"), _make_verb_form("regarnie", "regarnir"))
        augmented = {("p", "indicatif"): [rechampiWords, regarniWords]}

        assert newlyCollidingLemmas(baseline, augmented) == {"rechampir_VER", "regarnir_VER"}

    def test_ignores_collision_already_present_in_baseline(self):
        rechampiWords = (_make_verb_form("rechampis", "rechampir"),)
        regarniWords = (_make_verb_form("regarnis", "regarnir"),)
        featureSet = ("p", "indicatif")
        baseline = {featureSet: [rechampiWords, regarniWords]}
        augmented = {featureSet: [rechampiWords, regarniWords]}

        assert newlyCollidingLemmas(baseline, augmented) == set()

    def test_new_pair_with_one_lemma_already_colliding_elsewhere(self):
        """rechampir already collides with garnir in the baseline; augmented
        adds a NEW collision between rechampir and regarnir. Only the new
        pair's lemmas should be reported."""
        garniWords = (_make_verb_form("garnis", "garnir"),)
        rechampiWords = (_make_verb_form("rechampis", "rechampir"),)
        regarniWords = (_make_verb_form("regarnis", "regarnir"),)
        baseline = {("p", "indicatif"): [garniWords, rechampiWords]}
        augmented = {
            ("p", "indicatif"): [garniWords, rechampiWords],
            ("m_s",): [rechampiWords, regarniWords],
        }
        assert newlyCollidingLemmas(baseline, augmented) == {"rechampir_VER", "regarnir_VER"}

    def test_large_shared_feature_group_no_quadratic_blowup(self):
        """A feature shared by hundreds of unrelated lemmas (e.g. a plural
        marker) must be handled without enumerating pairs -- this is the
        scenario that caused the original out-of-memory crash."""
        featureSet = ("p",)
        baselineWords = [
            (_make_verb_form(f"mot{i}s", f"mot{i}"),) for i in range(500)
        ]
        baseline = {featureSet: baselineWords}
        newWord = (_make_verb_form("regarnis", "regarnir"),)
        augmented = {featureSet: baselineWords + [newWord]}

        result = newlyCollidingLemmas(baseline, augmented)
        assert "regarnir_VER" in result
        assert result == {f"mot{i}_VER" for i in range(500)} | {"regarnir_VER"}
