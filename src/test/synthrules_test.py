"""The reference-validated agreement bar for finite verb-form synthesis (T3.1): gating (src/synthrules.py), the
below-bar candidate of generateMissingConjugatedForm, and util.completeVerbParadigms.ReferenceBar."""
from typing import Any

import pytest

from src.lexicondecisions import ACCEPT, PENDING, REJECT, Decision, Decisions
from src.synthrules import (
    DEFAULT_PARAMS, SYNTH_RULES, isRuleActive, parseForcedRules, ruleGroupId,
)
from src.verbparadigm import deriveConjugationEndingTables, generateMissingConjugatedForm
from src.test.verbparadigm_test import _FAKE_TEMPLATE, _make_finite, _make_infinitive
from util._verbreferences import VerbReferences, _Source
from util.completeVerbParadigms import ReferenceBar


def decisionsWith(verdict: str, param: str = "") -> Decisions:
    gid = ruleGroupId("reference-bar")
    return Decisions([Decision(gid, "synth_rule", "-", SYNTH_RULES["reference-bar"], verdict, param)])


class TestGating:

    def test_off_by_default(self) -> None:
        assert isRuleActive("reference-bar", None, {}) == (False, "")
        assert isRuleActive("reference-bar", Decisions(), {}) == (False, "")

    @pytest.mark.parametrize("verdict", [PENDING, REJECT])
    def test_pending_or_rejected_decision_is_off(self, verdict: str) -> None:
        assert isRuleActive("reference-bar", decisionsWith(verdict, "0.7"), {}) == (False, "")

    def test_accepted_decision_gives_its_param_or_the_default(self) -> None:
        assert isRuleActive("reference-bar", decisionsWith(ACCEPT, "0.7"), {}) == (True, "0.7")
        assert isRuleActive("reference-bar", decisionsWith(ACCEPT), {}) == (True, DEFAULT_PARAMS["reference-bar"])

    def test_forced_flag(self) -> None:
        assert parseForcedRules(["reference-bar"]) == {"reference-bar": ""}
        assert parseForcedRules(["reference-bar=0.6"]) == {"reference-bar": "0.6"}
        assert isRuleActive("reference-bar", None, {"reference-bar": ""}) == (True, "0.5")
        assert isRuleActive("reference-bar", decisionsWith(PENDING), {"reference-bar": "0.6"}) == (True, "0.6")
        with pytest.raises(ValueError):
            parseForcedRules(["no-such-rule"])

    def test_group_id_is_the_spec_hash(self) -> None:
        assert len(ruleGroupId("reference-bar")) == 10


def theoryOf(pasEndings: list[str]) -> tuple[Any, dict[str, str]]:
    """One fake-template donor per entry of `pasEndings`, each attesting ind:pas:3p with that ending."""
    theory: dict[Any, list[Any]] = {}
    templates: dict[str, str] = {}
    for i, ending in enumerate(pasEndings):
        lemme = f"{chr(97 + i)}{chr(98 + i)}ir"
        stem = lemme[:-2]
        theory[((i,),)] = [_make_infinitive(lemme, stem + "iR"), _make_finite(lemme, stem + ending, "ind:pas", "3p")]
        templates[lemme] = "fake:ir"
    return theory, templates


def referencesWith(ortho: str, variants: set[str], lemme: str = "efir") -> VerbReferences:
    wiktionary, glaff = _Source(), _Source()
    wiktionary.variants[(lemme, ortho, "ind:pas:3p")] = set(variants)
    wiktionary.lemmaTag[(lemme, "ind:pas:3p")] = set(variants)
    return VerbReferences(wiktionary, glaff)


TARGET = _make_infinitive("efir", "efiR")


def generate(pasEndings: list[str], bar: ReferenceBar | None) -> Any:
    theory, templates = theoryOf(pasEndings)
    tables = deriveConjugationEndingTables(theory, templates, {})
    return generateMissingConjugatedForm(
        "efir", _FAKE_TEMPLATE, TARGET, "ind:pas", "3p", tables,
        barFloor=bar.floor if bar else None, validate=bar.validate if bar else None)


class TestBelowBarCandidate:

    def test_without_the_bar_a_split_slot_is_not_generated(self) -> None:
        assert generate(["Y", "Y", "Z"], None) is None

    def test_accepted_when_the_reference_matches(self) -> None:
        bar = ReferenceBar(referencesWith("efirent", {"efY"}), 0.5)
        word = generate(["Y", "Y", "Z"], bar)
        assert word is not None and word.phonology == "efY" and word.ortho == "efirent"
        assert bar.rejections() == [] and bar.acceptedByRank[0] == 1

    def test_reference_found_by_lemma_and_tag_when_the_ortho_differs(self) -> None:
        bar = ReferenceBar(referencesWith("autre", {"efY"}), 0.5)
        assert generate(["Y", "Y", "Z"], bar) is not None

    def test_rejected_and_recorded_when_the_reference_differs(self) -> None:
        bar = ReferenceBar(referencesWith("efirent", {"efQ"}), 0.5)
        assert generate(["Y", "Y", "Z"], bar) is None
        (row,) = bar.rejections()
        assert row[:6] == ("efir", "efirent", "ind:pas:3p", "efY", "efQ", "differs")
        assert row[6] == "fake:ir" and abs(row[7] - 2 / 3) < 1e-9

    def test_rejected_and_recorded_when_there_is_no_reference(self) -> None:
        bar = ReferenceBar(referencesWith("efirent", {"efY"}, lemme="autre"), 0.5)
        assert generate(["Y", "Y", "Z"], bar) is None
        (row,) = bar.rejections()
        assert row[4:6] == ("", "no-reference")

    def test_majority_below_the_floor_is_not_built(self) -> None:
        bar = ReferenceBar(referencesWith("efirent", {"efY"}), 0.8)
        assert generate(["Y", "Y", "Z"], bar) is None
        assert bar.rejections() == []

    def test_competing_ending_validated_by_the_reference(self) -> None:
        # majority Z (3 donors), but the reference wants Y (2 donors): the second ending is tried and kept
        bar = ReferenceBar(referencesWith("efirent", {"efY"}), 0.5)
        word = generate(["Z", "Z", "Z", "Y", "Y"], bar)
        assert word is not None and word.phonology == "efY"
        assert bar.rejections() == [] and bar.acceptedByRank[1] == 1

    def test_single_donor_alternative_is_not_tried(self) -> None:
        bar = ReferenceBar(referencesWith("efirent", {"efY"}), 0.5)
        assert generate(["Z", "Z", "Z", "Y"], bar) is None

    def test_full_agreement_is_unchanged_and_unvalidated(self) -> None:
        bar = ReferenceBar(referencesWith("autre", {"zzz"}), 0.5)
        word = generate(["Y", "Y"], bar)
        assert word is not None and word.phonology == "efY"
        assert bar.rejections() == [] and not bar.acceptedByRank

    def test_conflicting_sources_use_the_preferred_variants(self) -> None:
        wiktionary, glaff = _Source(), _Source()
        for source, variant in ((wiktionary, "efY"), (glaff, "efQ")):
            source.variants[("efir", "efirent", "ind:pas:3p")] = {variant}
        # make Wiktionary the plausible side, GLAFF the conflicting one
        references = VerbReferences(wiktionary, glaff)
        ref = references.get("efir", "efirent", "ind:pas:3p")
        assert ref is not None and ref.conflict and ref.preferred == frozenset({"efY"})
        assert generate(["Y", "Y", "Z"], ReferenceBar(references, 0.5)) is not None


def test_write_synthetic_never_appends_a_line_the_file_already_has(tmp_path: Any) -> None:
    from util.completeVerbParadigms import writeSynthetic
    word = generate(["Y", "Y"], None)
    path = str(tmp_path / "LexiqueSynthetic.tsv")
    candidates: Any = [("efir_VER", None, word, TARGET)]
    assert writeSynthetic(path, candidates) == 1
    assert writeSynthetic(path, candidates) == 0
    with open(path, encoding="utf-8") as f:
        assert len(f.readlines()) == 2  # header + one row
