import os
import subprocess
import sys
import tempfile
from dataclasses import replace

import pytest

from src.lexicondecisions import Decision, Decisions, groupIdFor
from src.verbparadigm import VerbModelException, getTrustedTemplate, loadVerbModelExceptions
from util.apply_template_decisions import (
    MARKER, acceptedGroupIds, desiredRows, groupMembers, handExceptions, handLines, isManaged, render,
)
from util.propose_verb_templates import Proposal

GID = groupIdFor("template", "-", "-er → aim:er")
GID2 = groupIdFor("template", "-", "-ir → fin:ir")
HAND = (
    "# comment\n"
    "lemme\ttemplate\tmodel_sibling\tstatus\tnote\n"
    "raidir\tfin:ir\tgarnir\tregular\tby hand\n"
    "agonir\t\t\tneeds_review\tunsure\n"
    "avenir\t\t\tdefective\tno paradigm\n"
)


def proposal(lemme: str, template: str, suffix: str) -> Proposal:
    return Proposal(lemme, "proposed", template, suffix, 3, (), "", ())


def members() -> dict[str, tuple[str, list[str]]]:
    return {GID: ("aim:er", ["garer", "marcher"]), GID2: ("fin:ir", ["agonir", "brunir"])}


def decision(kind: str, signature: str, verdict: str, param: str = "") -> Decision:
    return Decision(groupIdFor(kind, "-", signature), kind, "-", signature, verdict, param)


def hand(text: str = HAND) -> dict[str, VerbModelException]:
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "e.tsv")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return loadVerbModelExceptions(path)


def test_groupMembers() -> None:
    proposals = [proposal("garer", "aim:er", "er"), proposal("marcher", "aim:er", "er"), proposal("brunir", "fin:ir", "ir")]
    found = groupMembers(proposals)
    assert found[GID] == ("aim:er", ["garer", "marcher"])
    assert found[GID2] == ("fin:ir", ["brunir"])


def test_acceptedGroupIds() -> None:
    decisions = Decisions([decision("template", "-er → aim:er", "accept"), decision("template", "-ir → fin:ir", "pending"),
                           decision("mixte_rule", "x", "accept")])
    assert acceptedGroupIds(decisions) == {GID: ""}
    assert acceptedGroupIds(decisions, "all") == {GID: "", GID2: ""}
    assert acceptedGroupIds(decisions, [GID2]) == {GID: "", GID2: ""}


def test_managedRowsAddedAndNonTrustedNotOverridden() -> None:
    rows, individual = desiredRows(members(), {GID: "", GID2: ""}, hand())
    assert [(r.lemme, r.template, r.groupId) for r in rows] == [
        ("brunir", "fin:ir", GID2), ("garer", "aim:er", GID), ("marcher", "aim:er", GID)]
    assert individual == [("agonir", GID2, "needs_review")]


def test_paramOverridesTemplate() -> None:
    rows, _ = desiredRows(members(), {GID: "j:eter"}, hand())
    assert {r.template for r in rows} == {"j:eter"}


def test_unknownTemplateRefused() -> None:
    with pytest.raises(SystemExit):
        desiredRows(members(), {GID: "nope:er"}, hand(), {"aim:er"})


def test_renderKeepsHandLinesAndLoaderTrustsRows() -> None:
    rows, _ = desiredRows(members(), {GID: ""}, hand())
    text = render(HAND, rows)
    assert text.startswith(HAND)
    assert MARKER in text
    loaded = hand(text)
    assert getTrustedTemplate("garer", {}, loaded) == "aim:er"
    assert loaded["garer"].note == f"group {GID}"
    assert getTrustedTemplate("agonir", {}, loaded) is None
    assert getTrustedTemplate("raidir", {}, loaded) == "fin:ir"


def test_idempotentAndRemovalOfRejectedGroup() -> None:
    rows, _ = desiredRows(members(), {GID: "", GID2: ""}, hand())
    once = render(HAND, rows)
    assert render(once, rows) == once
    assert handLines(once) == handLines(HAND)
    rowsAfter, _ = desiredRows(members(), {GID: ""}, handExceptions(once, "e.tsv"))
    twice = render(once, rowsAfter)
    assert "brunir" not in twice and "garer" in twice
    assert render(twice, []) == HAND
    assert handExceptions(once, "e.tsv").keys() == hand().keys()


def test_handRowWithGroupLikeNoteIsOnlyManagedWhenFamilyTemplate() -> None:
    assert isManaged(f"x\taim:er\t\tfamily_template\tgroup {GID}")
    assert not isManaged(f"x\taim:er\t\tregular\tgroup {GID}")
    assert not isManaged("x\taim:er\t\tfamily_template\tgroup of hand verbs")


def test_checkExitsOneWhenFileWouldChange() -> None:
    # --assume-accepted without --out is refused (never writes the real file) and --check refuses it too
    result = subprocess.run([sys.executable, "-m", "util.apply_template_decisions", "--assume-accepted", "all"],
                            capture_output=True, text=True)
    assert result.returncode == 2
    assert "--out" in result.stderr


def test_checkAndApplyEndToEnd() -> None:
    """Accepts the smallest-id template group in a temp decisions copy: --check fails on the real file, an --out copy
    passes --check, and applying again changes nothing."""
    from src.lexicondecisions import loadDecisions, saveDecisions
    template = loadDecisions().all()
    template = [d for d in template if d.kind == "template"]
    if not template:
        pytest.skip("no template decision")
    chosen = replace(template[0], verdict="accept")
    with tempfile.TemporaryDirectory() as tmp:
        decisionsPath = os.path.join(tmp, "decisions.tsv")
        saveDecisions(Decisions([chosen]), decisionsPath)
        base = [sys.executable, "-m", "util.apply_template_decisions", "--decisions", decisionsPath]
        failing = subprocess.run([*base, "--check"], capture_output=True, text=True)
        assert failing.returncode == 1, failing.stderr
        outPath = os.path.join(tmp, "out.tsv")
        written = subprocess.run([*base, "--out", outPath], capture_output=True, text=True)
        assert written.returncode == 0, written.stderr
        with open(outPath, encoding="utf-8") as f:
            assert f"group {chosen.groupId}" in f.read()
        passing = subprocess.run([*base, "--check", "--exceptions", outPath], capture_output=True, text=True)
        assert passing.returncode == 0, passing.stderr
