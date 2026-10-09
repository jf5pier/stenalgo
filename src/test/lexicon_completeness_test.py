import io
from pathlib import Path
from typing import Any

import pytest

import util.lexicon_completeness as lc
from src.verbparadigm import parseConjugationTemplates

HEADER = "ortho\tphon\tlemme\tcgram\tcgramortho\tgenre\tnombre\tinfover\tsyll_cv\torthosyll_cv\tfreqlivres\tfreqfilms2"

CONJUGATIONS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<conjugation-fr>
<template name="aim:er">
<Infinitif><infinitif-présent><p><i>er</i></p></infinitif-présent></Infinitif>
<Indicatif><présent><p><i>e</i></p><p><i>es</i></p><p><i>e</i></p><p><i>ons</i></p><p><i>ez</i></p><p><i>ent</i></p></présent></Indicatif>
</template>
</conjugation-fr>
"""


def row(ortho: str, lemme: str, cgram: str, genre: str = "", nombre: str = "", infover: str = "") -> str:
    return "\t".join([ortho, "p", lemme, cgram, cgram, genre, nombre, infover, "s", "o", "0.0", "0.0"])


def write(path: Path, rows: list[str]) -> Path:
    path.write_text("\n".join([HEADER] + rows) + "\n", encoding="utf-8")
    return path


def census(tmp_path: Path, mixte: list[str], synthetic: list[str], excludedLines: list[str]) -> dict[tuple[str, str, str], str]:
    mixteRows = lc.readRawRows(write(tmp_path / "m.tsv", mixte))
    syntheticRows = lc.readRawRows(write(tmp_path / "s.tsv", synthetic))
    xmlPath = tmp_path / "conj.xml"
    xmlPath.write_text(CONJUGATIONS_XML, encoding="utf-8")
    templates = parseConjugationTemplates(xmlPath)
    excludedPath = tmp_path / "ex.tsv"
    excludedPath.write_text("# comment\nlemme\tcgram\tslot\treason\n" + "\n".join(excludedLines) + "\n", encoding="utf-8")
    excluded = lc.loadExcludedSlots(excludedPath)
    verbs = lc.verbCensus(mixteRows, syntheticRows, {"aimer": "aim:er", "parler": "aim:er"}, {}, templates, excluded)
    nomAdj = lc.nomAdjCensus(mixteRows, syntheticRows, excluded, {})
    return {(r.lemme, r.cgram, r.slot): r.status for r in verbs + nomAdj}


def testVerbStatuses(tmp_path: Path) -> None:
    mixte = [
        row("aimer", "aimer", "VER", infover="inf;"),
        row("aime", "aimer", "VER", infover="ind:pre:1s;ind:pre:3s;"),
        row("aimé", "aimer", "VER", "m", "s", "par:pas;"),
        row("aimant", "aimer", "VER", infover="par:pre;"),
        row("parler", "parler", "VER", infover="inf;"),
        row("zorgner", "zorgner", "VER", infover="inf;"),
    ]
    synthetic = [row("aimes", "aimer", "VER", infover="ind:pre:2s;"), row("aimées", "aimer", "VER", "f", "p", "par:pas;")]
    result = census(tmp_path, mixte, synthetic, ["aimer\tVER\tind:pre:3p\tby_design", "*\tVER\tpar:pas:mp\twildcard_rule"])
    assert result[("aimer", "VER", "inf")] == "mixte"
    assert result[("aimer", "VER", "ind:pre:3s")] == "mixte"
    assert result[("aimer", "VER", "ind:pre:2s")] == "synthetic"
    assert result[("aimer", "VER", "par:pas:fp")] == "synthetic"
    assert result[("aimer", "VER", "ind:pre:3p")] == "excluded:by_design"
    assert result[("aimer", "VER", "par:pas:mp")] == "excluded:wildcard_rule"
    assert result[("aimer", "VER", "ind:pre:2p")] == "missing:other"
    # partial paradigm with no participle at all: its participle slots have no donor
    assert result[("parler", "VER", "par:pas:ms")] == "missing:no_participle_donor"
    assert result[("parler", "VER", "ind:pre:1s")] == "missing:other"
    # no trusted template: the reference slot list, every unattested slot missing:no_template
    assert result[("zorgner", "VER", "inf")] == "mixte"
    assert result[("zorgner", "VER", "ind:pre:1s")] == "missing:no_template"


def testSpuriousInfTagDoesNotAttestFiniteSlots(tmp_path: Path) -> None:
    mixte = [row("aimer", "aimer", "VER", infover="inf;"), row("aimez", "aimer", "VER", infover="inf;ind:pre:2p;")]
    result = census(tmp_path, mixte, [], [])
    assert result[("aimer", "VER", "ind:pre:2p")] == "missing:other"


def testPrefixWildcardAndEmptyExcludedFile(tmp_path: Path) -> None:
    excluded = [("*", "VER", "sub:imp:*", "archaic"), ("neiger", "VER", "ind:pre:1s", "weather")]
    assert lc.exclusionReason(excluded, "aimer", "VER", "sub:imp:3s") == "archaic"
    assert lc.exclusionReason(excluded, "aimer", "VER", "sub:pre:3s") is None
    assert lc.exclusionReason(excluded, "neiger", "VER", "ind:pre:1s") == "weather"
    assert lc.exclusionReason(excluded, "aimer", "NOM", "sub:imp:3s") is None
    assert lc.loadExcludedSlots(tmp_path / "absent.tsv") == []


def testCommittedExcludedSlotsFileParses() -> None:
    rows = lc.loadExcludedSlots("resources/excludedSlots.tsv")
    assert ("*", "VER", "sub:imp:*", "archaic_out_of_scope_2026-09-21") in rows
    assert all(len(r) == 4 and all(r) for r in rows)


def testNomAdjGapAndExclusions(tmp_path: Path) -> None:
    mixte = [
        row("chat", "chat", "NOM", "m", "s"),
        row("table", "table", "NOM", "f", "s"),
        row("tables", "table", "NOM", "f", "p"),
        row("bras", "bras", "NOM", "m", "s"),
        row("petit", "petit", "ADJ", "m", "s"),
        row("petits", "petit", "ADJ", "m", "p"),
    ]
    synthetic = [row("petite", "petit", "ADJ", "f", "s")]
    result = census(tmp_path, mixte, synthetic, [])
    assert result[("chat", "NOM", "ms")] == "mixte"
    assert result[("chat", "NOM", "mp")] == "missing:other"
    assert result[("table", "NOM", "fp")] == "mixte"
    assert result[("bras", "NOM", "mp")] == "excluded:suspected_invariable"
    assert result[("petit", "ADJ", "fs")] == "synthetic"
    assert result[("petit", "ADJ", "fp")] == "missing:other"


def testSummaryAndOutput(tmp_path: Path) -> None:
    rows = [lc.SlotRow("aimer", "VER", "inf", "mixte", "aimer"), lc.SlotRow("aimer", "VER", "ind:pre:1s", "missing:other", ""),
            lc.SlotRow("zorgner", "VER", "inf", "missing:no_template", "")]
    out = io.StringIO()
    lc.summarize(rows, out)
    text = out.getvalue()
    assert "VER: 2 lemmas, 3 expected slots" in text
    assert "missing after synthesis" in text
    lc.writeCensus(rows, tmp_path / "out.tsv")
    lines = (tmp_path / "out.tsv").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "lemme\tcgram\tslot\tstatus\tortho_if_known"
    assert lines[1] == "aimer\tVER\tinf\tmixte\taimer"


def testRefineHookReturnsCause() -> None:
    assert lc.refineMissingCause("aimer", "VER", "inf", "other") == "other"
