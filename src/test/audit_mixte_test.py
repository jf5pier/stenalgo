"""Tests for util/audit_mixte.py on tiny fixtures: matched / edited / misaligned / no reference, and the merge into a decisions file."""
from dataclasses import replace
from pathlib import Path

from src.lexicondecisions import REJECT, Decisions, loadDecisions, mergeMined, saveDecisions
from util._verbreferences import VerbReferences, _Source
from util.audit_mixte import (AuditResult, auditNomAdjRows, auditRows, auditTags, classKeyOf, minedDecisions, nomAdjClassKey,
                              referenceFor, renderReport)

TAG = "ind:pre:3s"


def row(ortho: str, lemme: str, phon: str, syll: str | None = None, infover: str = TAG + ";") -> dict[str, str]:
    units = "_".join(phon)
    return {"ortho": ortho, "lemme": lemme, "cgram": "VER", "infover": infover, "genre": "", "nombre": "",
            "phon": phon, "syll_cv": syll if syll is not None else units, "orthosyll_cv": units}


def references() -> VerbReferences:
    wiktionary, glaff = _Source(), _Source()
    for lemme, ortho, ipa in [("a", "bak", "bak"), ("b", "pal", "pal"), ("c", "tal", "tat"), ("d", "mal", "mat"),
                              ("e", "sal", "sat"), ("f", "nak", "nat"), ("g", "xal", "xat")]:
        wiktionary.add(lemme, ortho, TAG, ipa)
    glaff.add("h", "zak", TAG, "zak")
    return VerbReferences(wiktionary, glaff)


def audit() -> tuple[AuditResult, list[dict[str, str]]]:
    rows = [row("bak", "a", "bak"),                    # exact
            row("pal", "b", "paL"),                    # no: real edit l -> L? (ref has `l`), single row
            row("tal", "c", "tal"), row("mal", "d", "mal"), row("sal", "e", "sal"),   # l -> t, three lemmas
            row("nak", "f", "nak", syll="n_a"),        # misaligned
            row("zak", "h", "zak"),                    # glaff-only exact
            row("qal", "q", "qal"),                    # no reference
            row("xal", "g", "xaL")]
    result, _index = auditRows(rows, [], references(), {}, {}, "mixte")
    return result, rows


def testCounts() -> None:
    result, _rows = audit()
    assert (result.audited, result.noReference, result.withReference) == (9, 1, 8)
    assert result.exact == 2 and result.conventionOnly == 0
    assert result.edited == 5 and len(result.misalignedRows) == 1
    assert result.misalignedRows[0]["ortho"] == "nak"
    assert result.groups[0].slots == 3 and result.groups[0].signature.startswith("l→t @ l [final]")
    assert result.groups[0].level == "L1" and not result.groups[0].heterogeneous
    assert sum(g.typo for g in result.groups) == 2


def testReferenceFallbackAndClassKey() -> None:
    refs = references()
    assert referenceFor(refs, "a", "bak", [TAG]) is not None
    found = referenceFor(refs, "a", "other-spelling", [TAG])        # lemma/tag fallback, ortho ignored
    assert found is not None and found[1] == "wiktionary(lemma)" and found[2] == "lemma"
    assert referenceFor(refs, "nobody", "x", [TAG]) is None
    assert classKeyOf(None, {}, "a", ["ind:pre:3s", "cnd:pre:3s"]) == ("untemplated", "cnd:pre:3s")
    assert classKeyOf("aim:er", {}, "a", ["ind:pre:3s", "par:pas:fs"]) == ("aim:er", "par:pas:fs")


def testTiersAndInfinitive() -> None:
    wiktionary, glaff = _Source(), _Source()
    wiktionary.add("crier", "criions", "ind:imp:1p", "kʁi.jjɔ̃")      # homographic form listed under one tag only
    glaff.add("crier", "crier", "inf", "kʁi.je")
    refs = VerbReferences(wiktionary, glaff)
    slot = referenceFor(refs, "crier", "criions", ["ind:imp:1p"])
    assert slot is not None and slot[2] == "slot"
    other = referenceFor(refs, "crier", "criions", ["sub:pre:1p"])        # same spelling, another tag
    assert other is not None and other[2] == "ortho" and other[0] == slot[0] and other[1].endswith("(ortho)")
    inf = referenceFor(refs, "crier", "crier", auditTags("inf;", "", ""))
    assert inf is not None and inf[2] == "slot" and "kRije" in inf[0]
    assert auditTags("inf;", "", "") == ["inf"] and auditTags("ind:pre:3s;", "", "") == ["ind:pre:3s"]
    rows = [row("criions", "crier", "kRijj§", infover="sub:pre:1p;"), row("crier", "crier", "kRije", infover="inf;")]
    result, _ = auditRows(rows, [], refs, {}, {}, "mixte")
    assert result.audited == 2 and result.tiers == {"ortho": 1, "slot": 1}


def testMergeAndSplit(tmp_path: Path) -> None:
    result, _rows = audit()
    mined, sidecar = minedDecisions(result.groups, Decisions(), "mixte_rule")
    assert {d.kind for d in mined} == {"mixte_rule", "mixte_typo"}
    assert set(sidecar) == {d.groupId for d in mined}
    path = str(tmp_path / "decisions.tsv")
    saveDecisions(mergeMined(Decisions(), mined), path)
    first = Path(path).read_text(encoding="utf-8")
    again = mergeMined(loadDecisions(path), minedDecisions(result.groups, loadDecisions(path), "mixte_rule")[0])
    saveDecisions(again, path)
    assert Path(path).read_text(encoding="utf-8") == first          # idempotent
    assert renderReport(result, mined) == renderReport(result, mined)
    # a split parent is honoured: its children are mined too, and the parent keeps its verdict
    parent = next(d for d in mined if d.level == "L1" and d.slots == 3)
    split = Decisions([replace(parent, verdict=REJECT, note="split: L2")])
    mined2, sidecar2 = minedDecisions(result.groups, split, "mixte_rule")
    assert len(mined2) > len(mined) and {d.level for d in mined2} >= {"L1", "L2"}
    assert set(sidecar2) == {d.groupId for d in mined2}
    merged = mergeMined(split, mined2)
    kept = merged.get(parent.groupId)
    assert kept is not None and kept.verdict == REJECT and kept.note == "split: L2"
    assert len(merged.pending()) == len(mined2) - 1


def nomRow(ortho: str, lemme: str, phon: str, genre: str = "m", nombre: str = "s", cgram: str = "NOM") -> dict[str, str]:
    units = "_".join(phon)
    return {"ortho": ortho, "lemme": lemme, "cgram": cgram, "infover": "", "genre": genre, "nombre": nombre,
            "phon": phon, "syll_cv": units, "orthosyllCV": units, "orthosyll_cv": units}


def testNomAdj() -> None:
    assert nomAdjClassKey("NOM", "poli", "m", "s") == ("NOM:li", "ms")
    assert nomAdjClassKey("ADJ", "a", "", "") == ("ADJ:a", "-")
    index = {("kal", "kal", "NOM", "m", "s"): {"kal"}, ("pol", "pol", "NOM", "m", "s"): {"pOl"},
             ("sal", "sal", "NOM", "m", "s"): {"sOl"}, ("mal", "mal", "NOM", "m", "s"): {"mOl"},
             ("tal", "tal", "NOM", "m", "s"): {"tal"}, ("pale", "pale", "NOM", "f", "s"): {"pal"}}
    rows = [nomRow("kal", "kal", "kal"),                      # exact
            nomRow("pol", "pol", "pol"),                      # o -> O is a convention
            nomRow("sal", "sal", "sal"), nomRow("mal", "mal", "mal"),   # a -> O twice... (sub a->O)
            nomRow("pale", "pale", "pal", "f"),               # schwa-free: exact through the ortho tier? (slot)
            nomRow("tal", "tal", "tal", "f", "p"),            # slot mismatch: ortho tier, exact
            nomRow("zzz", "zzz", "zzz"),                      # no reference
            nomRow("pal", "pal", "pal", cgram="ADJ")]         # ADJ is not NOM: no reference
    result, _counters = auditNomAdjRows(rows, index, "mixte")
    assert result.label == "NOM/ADJ" and result.audited == 8 and result.noReference == 2
    assert result.tiers == {"slot": 5, "ortho": 1}
    assert result.exact == 3 and result.conventionOnly == 1 and result.edited == 2
    assert all(g.signature.endswith("| NOM:al ms") or "NOM:" in g.signature for g in result.groups)
    assert all(g.signature.count("NOM:") == 1 for g in result.groups)
    mined, _ = minedDecisions(result.groups, Decisions(), "mixte_rule")
    assert mined and renderReport(result, mined).count("NOM/ADJ rows audited: 8") == 1
