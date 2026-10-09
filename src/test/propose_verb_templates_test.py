import os
import tempfile
from collections import Counter
from typing import Any

from src.lexicondecisions import Decisions, groupIdFor, loadDecisions, saveDecisions
from src.verbparadigm import ConjugationTemplate, VerbModelException
from util.propose_verb_templates import (
    Evidence, buildGroups, candidateTemplates, collectEvidence, generateSlot, proposeTemplate, untemplatedReason,
    writeDecisions,
)


def template(name: str, inf: str, present: list[str | None], participle: list[str | None] | None = None) -> ConjugationTemplate:
    forms: dict[str, list[str | None]] = {"inf": [inf], "ind:pre": present}
    if participle is not None:
        forms["par:pas"] = participle
    return ConjugationTemplate(name, forms)


def templates() -> dict[str, ConjugationTemplate]:
    return {
        "aim:er": template("aim:er", "er", ["e", "es", "e", "ons", "ez", "ent"], ["é", "és", "ée", "ées"]),
        "fin:ir": template("fin:ir", "ir", ["is", "is", "it", "issons", "issez", "issent"], ["i", "is", "ie", "ies"]),
        "ach:eter": template("ach:eter", "eter", ["ète", "ètes", "ète", "etons", "etez", "ètent"]),
        "j:eter": template("j:eter", "eter", ["ette", "ettes", "ette", "etons", "etez", "ettent"]),
    }


def evidenceOf(**slots: str) -> Evidence:
    return {slot.replace("_", ":"): ({ortho}, {"mixte"}) for slot, ortho in slots.items()}


COUNTS: Counter[str] = Counter({"aim:er": 100, "fin:ir": 50, "ach:eter": 2, "j:eter": 3})


def test_generateSlot() -> None:
    aim = templates()["aim:er"]
    assert generateSlot("march", aim, "ind:pre:3p") == "marchent"
    assert generateSlot("march", aim, "par:pas:fp") == "marchées"
    assert generateSlot("march", aim, "inf") == "marcher"
    assert generateSlot("march", aim, "sub:pre:1s") is None
    assert generateSlot("march", aim, "bogus") is None


def test_candidatesNeedSuffix() -> None:
    assert candidateTemplates("jeter", templates()) == ["ach:eter", "aim:er", "j:eter"]
    assert candidateTemplates("finir", templates()) == ["fin:ir"]
    assert candidateTemplates("er", templates()) == []


def test_proposedWhenSingleCandidate() -> None:
    evidence = evidenceOf(ind_pre_1s="gare", ind_pre_3p="garent", par_pas_ms="garé")
    p = proposeTemplate("garer", evidence, templates(), COUNTS)
    assert (p.status, p.template, p.matches, p.mismatches) == ("proposed", "aim:er", 3, ())


def test_evidenceDecidesBetweenTemplates() -> None:
    evidence = evidenceOf(ind_pre_1s="achète", ind_pre_3p="achètent", ind_pre_1p="achetons")
    p = proposeTemplate("acheter", evidence, templates(), COUNTS)
    assert (p.status, p.template) == ("proposed", "ach:eter")


def test_ambiguousListsAlternatives() -> None:
    evidence = evidenceOf(ind_pre_1p="jetons", ind_pre_2p="jetez", ind_pre_3p="x")
    del evidence["ind:pre:3p"]
    evidence["par:pas:ms"] = ({"x"}, {"mixte"})
    del evidence["par:pas:ms"]
    p = proposeTemplate("jeter", evidence, templates(), COUNTS, minEvidence=2)
    # ach:eter and j:eter agree on the 1p and 2p but differ elsewhere (and aim:er says jeter+ons = jetons too)
    assert p.status == "ambiguous"
    assert p.template == "j:eter" or p.template == "ach:eter" or p.template == "aim:er"
    assert len(p.alternatives) == 2


def test_contradicted() -> None:
    evidence = evidenceOf(ind_pre_1s="garre", ind_pre_3p="garrent", par_pas_ms="garré")
    p = proposeTemplate("garer", evidence, templates(), COUNTS)
    assert p.status == "contradicted"
    assert p.template == "aim:er"
    assert len(p.mismatches) == 3 and p.mismatches[0].startswith("ind:pre:1s:gare>garre")


def test_noEvidenceAndNoCandidate() -> None:
    assert proposeTemplate("garer", {}, templates(), COUNTS).status == "no_evidence"
    assert proposeTemplate("garer", evidenceOf(ind_pre_1s="gare"), templates(), COUNTS).status == "no_evidence"
    assert proposeTemplate("garer", evidenceOf(ind_pre_1s="gare"), templates(), COUNTS, minEvidence=1).status == "proposed"
    assert proposeTemplate("xyz", evidenceOf(ind_pre_1s="x"), templates(), COUNTS).status == "no_candidate"


def test_rectifiedAccentInFutureDoesNotContradict() -> None:
    fut = template("réf:érer", "érer", [], None)
    fut.forms["ind:fut"] = ["érerai", "éreras", "érera", "érerons", "érerez", "éreront"]
    fut.forms["ind:pre"] = ["ère", "ères", "ère", "érons", "érez", "èrent"]
    evidence: Evidence = {"ind:fut:1s": ({"gèrerai"}, {"wiktionary"}), "ind:pre:1s": ({"gère"}, {"mixte"}),
                          "ind:pre:1p": ({"gérons"}, {"mixte"})}
    p = proposeTemplate("gérer", evidence, {"réf:érer": fut}, COUNTS)
    assert p.status == "proposed"


def test_collectEvidenceMergesSources() -> None:
    row: dict[str, str] = {"cgram": "VER", "lemme": "garer", "ortho": "gare", "infover": "ind:pre:1s;ind:pre:3s;",
                           "genre": "", "nombre": ""}
    refs = {"garer": {"wiktionary": {"ind:pre:1s": {"gare"}, "ind:pre:2s": {"gares"}}}}
    ev = collectEvidence([row], [], refs, {"garer"})["garer"]
    assert ev["ind:pre:1s"] == ({"gare"}, {"mixte", "wiktionary"})
    assert ev["ind:pre:2s"] == ({"gares"}, {"wiktionary"})


def test_groupsAndDecisions() -> None:
    evidence = evidenceOf(ind_pre_1s="gare", ind_pre_3p="garent", par_pas_ms="garé")
    ps = [proposeTemplate("garer", evidence, templates(), COUNTS),
          proposeTemplate("barer", evidenceOf(ind_pre_1s="bare", ind_pre_3p="barent", par_pas_ms="baré"), templates(), COUNTS)]
    ps.append(proposeTemplate("xyz", evidence, templates(), COUNTS))
    groups, decisions = buildGroups(ps, {"garer": 10, "barer": 5})
    assert len(groups) == 1
    assert groups[0] == ("-er → aim:er", "aim:er", ["barer", "garer"], 15)
    assert decisions[0].groupId == groupIdFor("template", "-", "-er → aim:er")
    assert (decisions[0].kind, decisions[0].level, decisions[0].slots) == ("template", "-", 15)


def test_writeDecisionsMergesPending() -> None:
    evidence = evidenceOf(ind_pre_1s="gare", ind_pre_3p="garent", par_pas_ms="garé")
    _groups, decisions = buildGroups([proposeTemplate("garer", evidence, templates(), COUNTS)], {"garer": 10})
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "decisions.tsv")
        saveDecisions(Decisions(), path)
        writeDecisions(decisions, path)
        writeDecisions(decisions, path)
        loaded = loadDecisions(path)
        assert [d.verdict for d in loaded.all()] == ["pending"]
        assert loaded.all()[0].slots == 10


def test_untemplatedReason() -> None:
    exceptions: Any = {"x": VerbModelException("x", "", "", "defective", "")}
    assert untemplatedReason("y", exceptions) == "absent"
    assert untemplatedReason("x", exceptions) == "exception:defective"
