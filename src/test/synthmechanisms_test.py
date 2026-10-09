"""The synthesis mechanisms beyond the reference bar (participle-from-infinitive, lost-nasal, homograph-tag, slot-map),
the robust infinitive suffix and the skip reasons."""
from typing import Any

from src.word import GramCat, Word
from src.synthrules import SYNTH_RULES, isRuleActive
from src.verbparadigm import (
    deriveConjugationEndingTables, deriveParticiplePresentTables, generateParticiplePresent, deriveParticipleEndingTables, generateMissingConjugatedForm,
    generateParticipleFromInfinitive, majoritySuffix, robustSuffix, pseudoInfinitive, repairLostNasalInfinitive,
)
from src.test.verbparadigm_test import _FAKE_TEMPLATE, _make_finite, _make_infinitive, _make_participle
from util.completeVerbParadigms import (
    INFINITIVE_PRESENT_RULE, Mechanisms, ReferenceJudge, addPresentParticiple, attestedPresentParticipleByLemme,
    classifySkip, copyHomographRow,
)
from util.lexicon_completeness import refineMissingCause
from util._verbreferences import VerbReferences, _Source, decodeGrace


def refs(entries: dict[tuple[str, str, str], set[str]]) -> VerbReferences:
    wiktionary = _Source()
    for slot, variants in entries.items():
        wiktionary.variants[slot] = set(variants)
    return VerbReferences(wiktionary, _Source())


def donors(count: int, outlier: bool = False) -> tuple[Any, dict[str, str]]:
    theory: dict[Any, list[Any]] = {}
    templates: dict[str, str] = {}
    for i in range(count):
        lemme = f"{chr(97 + i)}{chr(98 + i)}ir"
        stem = lemme[:-2]
        theory[((i,),)] = [_make_infinitive(lemme, stem + "iR"), _make_finite(lemme, stem + "X", "ind:pre", "1s"),
                           _make_participle(lemme[:-1], stem + "i", lemme, "m", "s", stem + "i", lemme[:-1])]
        templates[lemme] = "fake:ir"
    if outlier:
        theory[((99,),)] = [_make_infinitive("dealir", "dil9"), _make_finite("dealir", "dilX", "ind:pre", "1s")]
        templates["dealir"] = "fake:ir"
    return theory, templates


class TestRobustSuffix:

    def test_majority_suffix_ignores_one_outlier(self) -> None:
        regular = [f"{c}{c}iR" for c in "abcdefghijklmnopqrs"]
        assert majoritySuffix(regular + ["dil9R"]) == "iR"
        assert majoritySuffix(["abiR", "cdiR"]) == "iR"
        assert majoritySuffix(regular[:9] + ["dil9R"]) == "iR"
        assert majoritySuffix([]) == ""

    def test_robust_suffix_keeps_the_common_suffix_unless_an_outlier_empties_it(self) -> None:
        assert robustSuffix(["abiR", "cdiR", "dil9R"]) == "R"
        assert robustSuffix([f"{c}{c}iR" for c in "abcdefghijklmnopqrs"] + ["dil9"]) == "iR"

    def test_outliers_shortening_the_common_suffix_do_not_win(self) -> None:
        regular = [f"{c}{c}_er" for c in "abcdefghijklmnopqrs"]
        assert robustSuffix(regular + ["dea_e_r"]) == "_er"
        assert robustSuffix(regular[:5] + ["dea_e_r"]) == "r"  # too few donors to call it an outlier

    def test_longer_suffix_shared_by_most_wins_over_the_common_one(self) -> None:
        assert majoritySuffix(["xiR"] * 19 + ["aaa"]) == "xiR"

    def test_outlier_is_kept_out_and_never_generated_for(self) -> None:
        theory, templates = donors(12, outlier=True)
        tables = deriveConjugationEndingTables(theory, templates, {})
        assert tables.infinitiveSuffixByKey[("phonology", "fake:ir")] == "iR"
        assert tables.infinitiveOutliers == frozenset({"dealir"})
        target = _make_infinitive("dealir", "dil9")
        reasons: list[str] = []
        assert generateMissingConjugatedForm("dealir", _FAKE_TEMPLATE, target, "ind:pre", "1s", tables,
                                             onSkip=reasons.append) is None
        assert reasons == ["infinitive_outlier"]
        regular = generateMissingConjugatedForm("zzir", _FAKE_TEMPLATE, _make_infinitive("zzir", "zziR"), "ind:pre", "1s",
                                                tables)
        assert regular is not None and regular.phonology == "zzX"


class TestSkipReasons:

    def test_classify(self) -> None:
        assert classifySkip("validation_failed", "differs", False, False) == "reference_differs"
        assert classifySkip("validation_failed", "no-reference", False, False) == "no_reference"
        assert classifySkip("splice_rejected", None, True, False) == "lost_nasal"
        assert classifySkip("splice_rejected", None, False, True) == "homograph_tag"
        assert classifySkip("unattested_ending", None, False, False) == "unattested_ending"
        assert classifySkip("weird", None, False, False) == "other"

    def test_refine_missing_cause(self) -> None:
        reasons = {("aimer", "ind:pre:1s"): "no_reference", ("aimer", "finite:*"): "no_infinitive",
                   ("aimer", "par:pas:*"): "no_participle_donor"}
        assert refineMissingCause("aimer", "VER", "ind:pre:1s", "other", reasons) == "no_reference"
        assert refineMissingCause("aimer", "VER", "ind:pre:2s", "other", reasons) == "no_infinitive"
        assert refineMissingCause("aimer", "VER", "par:pas:ms", "other", reasons) == "no_participle_donor"
        assert refineMissingCause("aimer", "VER", "inf", "other", reasons) == "not_generated"
        reasons[("aimer", "par:pre")] = "reference_differs"
        assert refineMissingCause("aimer", "VER", "par:pre", "other", reasons) == "reference_differs"
        assert refineMissingCause("aimer", "VER", "ind:pre:1s", "no_template", reasons) == "no_template"
        assert refineMissingCause("aimer", "VER", "ind:pre:1s", "other") == "other"


class TestGatingAndJudge:

    def test_new_rules_are_registered_and_off_by_default(self) -> None:
        for name in ("participle-from-infinitive", "lost-nasal", "homograph-tag", "slot-map", INFINITIVE_PRESENT_RULE):
            assert name in SYNTH_RULES and isRuleActive(name, None, {}) == (False, "")
        assert isRuleActive("participle-from-infinitive", None, {"participle-from-infinitive": ""}) == (True, "strict")

    def test_accepts_by_mode(self) -> None:
        word = _make_finite("efir", "efX", "ind:pre", "1s")
        word.ortho = "efis"
        judge = ReferenceJudge(refs({("efir", "efis", "ind:pre:1s"): {"efX"}}))
        mech = Mechanisms(judge=judge)
        assert mech.accepts("m", word, "ind:pre:1s", "strict")
        other = ReferenceJudge(refs({("efir", "efis", "ind:pre:1s"): {"zzz"}}))
        assert not Mechanisms(judge=other).accepts("m", word, "ind:pre:1s", "unvalidated")
        assert len(other.rejectionLines()) == 1 and other.rejectionLines()[0].endswith("\tm\n")
        none = ReferenceJudge(refs({}))
        assert not Mechanisms(judge=none).accepts("m", word, "ind:pre:1s", "strict")
        assert Mechanisms(judge=none).accepts("m", word, "ind:pre:1s", "unvalidated", plain=True)
        assert not Mechanisms(judge=none).accepts("m", word, "ind:pre:1s", "unvalidated", plain=False)


class TestHomograph:

    def test_copy_under_the_missing_tag(self) -> None:
        carrier = _make_finite("efir", "efX", "ind:pre", "2s")
        carrier.ortho = "efis"
        judge = ReferenceJudge(refs({("efir", "efis", "sub:pre:2s"): {"efX"}}))
        copy = copyHomographRow("efir", "sub:pre", "2s", [carrier], Mechanisms(judge=judge, homograph="strict"))
        assert copy is not None and copy.infoVerb == "sub:pre:2s;" and copy.phonology == "efX"
        none = ReferenceJudge(refs({}))
        assert copyHomographRow("efir", "sub:pre", "2s", [carrier], Mechanisms(judge=none, homograph="strict")) is None

    def test_disagreeing_carriers_are_not_copied(self) -> None:
        a, b = _make_finite("efir", "efX", "ind:pre", "2s"), _make_finite("efir", "efY", "ind:pre", "3s")
        assert copyHomographRow("efir", "sub:pre", "2s", [a, b], Mechanisms(judge=ReferenceJudge(refs({})), homograph="strict")) is None


class TestParticipleAndInfinitive:

    def test_participle_from_the_infinitive(self) -> None:
        theory, templates = donors(12)
        tables = deriveConjugationEndingTables(theory, templates, {})
        ptables = deriveParticipleEndingTables(theory, templates, {}, tables)
        built = generateParticipleFromInfinitive("zzir", _FAKE_TEMPLATE, _make_infinitive("zzir", "zziR"), ptables, tables)
        assert built is not None and built.word.ortho == "zzi" and built.word.phonology == "zzi"
        assert built.rate == 1.0 and built.donors == 12 and built.plain

    def test_pseudo_infinitive_from_a_finite_form(self) -> None:
        theory, templates = donors(12)
        tables = deriveConjugationEndingTables(theory, templates, {})
        form = _make_finite("zzir", "zzX", "ind:pre", "1s")
        (pseudo, donor), *_ = list(pseudoInfinitive("zziR", _FAKE_TEMPLATE, {("ind:pre", "1s"): form}, tables))
        assert pseudo.phonology == "zziR" and pseudo.infoVerb == "inf;" and donor is form

    def test_repair_lost_nasal(self) -> None:
        word = Word(
            ortho="enivrer", phonology="@nivRe", lemme="enivrer", gramCat=GramCat.VER, orthoGramCat=[GramCat.VER],
            gender=None, number=None, infoVerb="inf;", rawSyllCV="@|i_v_R|e", rawOrthosyllCV="en|i_v_r|er",
            frequencyBook=1.0, frequencyFilm=1.0)
        fixed = repairLostNasalInfinitive(word)
        assert fixed is not None and fixed.rawSyllCV == "@|n_i_v_R|e"
        assert repairLostNasalInfinitive(_make_infinitive("aimer", "Eme")) is None


def presentDonors(count: int) -> tuple[Any, dict[str, str]]:
    theory, templates = donors(count)
    for words, lemme in zip(list(theory.values()), templates):
        stem = lemme[:-2]
        words.append(Word(
            ortho=stem + "issant", phonology=stem + "isA", lemme=lemme, gramCat=GramCat.VER, orthoGramCat=[GramCat.VER],
            gender=None, number=None, infoVerb="par:pre;", rawSyllCV=stem + "isA", rawOrthosyllCV=stem + "issant",
            frequencyBook=1.0, frequencyFilm=1.0))
    return theory, templates


class TestPresentParticiple:

    def test_grace_tag(self) -> None:
        assert decodeGrace("Vmpp---") == "par:pre"

    def test_present_participle_from_the_infinitive(self) -> None:
        theory, templates = presentDonors(12)
        tables = deriveConjugationEndingTables(theory, templates, {})
        present = deriveParticiplePresentTables(theory, templates, {}, tables)
        assert present.rateByKey[("fake:ir", "", "")] == 1.0 and present.donorsByKey[("fake:ir", "", "")] == 12
        built = generateParticiplePresent("zzir", _FAKE_TEMPLATE, _make_infinitive("zzir", "zziR"), present, tables)
        assert built is not None and built.word.ortho == "zzissant" and built.word.phonology == "zzisA"
        assert built.word.infoVerb == "par:pre;" and built.plain

    def test_no_donor_ending_is_a_skip_reason(self) -> None:
        theory, templates = donors(12)
        tables = deriveConjugationEndingTables(theory, templates, {})
        present = deriveParticiplePresentTables(theory, templates, {}, tables)
        reasons: list[str] = []
        assert generateParticiplePresent("zzir", _FAKE_TEMPLATE, _make_infinitive("zzir", "zziR"), present, tables,
                                         reasons.append) is None
        assert reasons == ["unattested_ending"]

    def test_attested_present_participles(self) -> None:
        theory, _templates = presentDonors(3)
        assert set(attestedPresentParticipleByLemme(theory)) == {"abir", "bcir", "cdir"}

    def test_add_is_judged_by_the_references(self) -> None:
        theory, templates = presentDonors(12)
        tables = deriveConjugationEndingTables(theory, templates, {})
        present = deriveParticiplePresentTables(theory, templates, {}, tables)
        source = _make_infinitive("zzir", "zziR")
        info = None  # not read by the helper
        for entries, expected, reason in (({("zzir", "zzissant", "par:pre"): {"zzisA"}}, 1, None),
                                          ({("zzir", "zzissant", "par:pre"): {"zzizA"}}, 0, "reference_differs"),
                                          ({}, 0, "no_reference")):
            mech = Mechanisms(judge=ReferenceJudge(refs(entries)), infinitivePresent=True)
            found: list[Any] = []
            skips: list[tuple[str, str, str]] = []
            addPresentParticiple("zzir", info, "zzir", _FAKE_TEMPLATE, source, source, present, tables, set(), mech, found,  # type: ignore[arg-type]
                                 lambda lemme, slot, why: skips.append((lemme, slot, why)))
            assert len(found) == expected
            assert (skips[0][2] if skips else None) == reason
        skips = []
        addPresentParticiple("zzir", info, "zzir", _FAKE_TEMPLATE, None, None, present, tables, set(),  # type: ignore[arg-type]
                             Mechanisms(), [], lambda lemme, slot, why: skips.append((lemme, slot, why)))
        assert skips == [("zzir", "par:pre", "no_infinitive")]

    def test_pseudo_infinitive_from_the_present_participle(self) -> None:
        theory: dict[Any, list[Any]] = {}
        templates: dict[str, str] = {}
        for i in range(12):
            lemme = f"{chr(97 + i)}{chr(98 + i)}ir"
            stem = lemme[:-2]
            infinitive = _make_infinitive(lemme, stem + "iR")
            infinitive.rawOrthosyllCV = lemme  # the spelling, so that a derived infinitive can be checked against the lemma
            theory[((i,),)] = [infinitive, Word(
                ortho=stem + "issant", phonology=stem + "isA", lemme=lemme, gramCat=GramCat.VER, orthoGramCat=[GramCat.VER],
                gender=None, number=None, infoVerb="par:pre;", rawSyllCV=stem + "isA", rawOrthosyllCV=stem + "issant",
                frequencyBook=1.0, frequencyFilm=1.0)]
            templates[lemme] = "fake:ir"
        tables = deriveConjugationEndingTables(theory, templates, {})
        present = deriveParticiplePresentTables(theory, templates, {}, tables)
        form = Word(
            ortho="zzissant", phonology="zzisA", lemme="zzir", gramCat=GramCat.VER, orthoGramCat=[GramCat.VER], gender=None,
            number=None, infoVerb="par:pre;", rawSyllCV="zzisA", rawOrthosyllCV="zzissant", frequencyBook=0.0, frequencyFilm=0.0)
        assert list(pseudoInfinitive("zzir", _FAKE_TEMPLATE, {}, tables, presentParticiple=form)) == []  # no tables: no source
        (pseudo, donor), *_ = list(pseudoInfinitive("zzir", _FAKE_TEMPLATE, {}, tables, presentParticiple=form, presentTables=present))
        assert pseudo.phonology == "zziR" and pseudo.infoVerb == "inf;" and donor is form
