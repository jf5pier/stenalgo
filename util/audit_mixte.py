"""
The miner of the grouped lexicon decisions (T2.1, spec docs/specs/lexicon-decisions.md, plan docs/SYNTHETIC_LEXICON_STATUS.md 5-6):
compares the VER rows of a lexicon (LexiqueMixte.tsv by default, LexiqueSynthetic.tsv with --lexicon synthetic) with the
reference pronunciations (fr.wiktionary conjugation pages and GLAFF, util/_verbreferences.py) and writes the differences as
grouped `pending` decisions (resources/lexiconDecisions.tsv) plus the examples sidecar the review shows.

Per row (rows filtered like util/lexicon_completeness.py: excluded words and dropped spelling variants removed):

  - references, three tiers: (1) the exact slot `forRow(lemme, ortho, tags)`; (2) the same (lemme, ortho) under ANY tag,
    `forOrtho` (a spelling of one lemma is pronounced the same whatever its tag; Wiktionary lists a homographic form such as
    `criions` under one tag only); (3) the checker's `matchRow(lemme, tags)` (ortho ignored). A conflicting RefSet gives its
    `preferred` variants, else all `variants`. No reference: counted `no_reference`, skipped. The rows each tier served are
    reported. The audited tags are the finite ones plus `inf` for an infinitive (GLAFF only: GRACE Vmn----).
  - class key: the pair (family, slot): family = `endingTemplateKey` or `untemplated`, slot = first tag in sorted order
    (a participle row: its `par:pas:<g><n>` slot).
  - `buildRowDiff`: no real edit (exact, or conventions only) -> the row feeds the CounterIndex; real edits -> a difference
    row; units that do not line up with the phonology (AlignmentError) -> `misaligned`, listed in
    `<lexicon>_audit_misaligned.tsv` (an inconsistency of our own syll_cv/phon, useful in itself).
  - `proposeGroups` (src/diffsignature.py), kind `mixte_typo` for a single-row L4 group else `mixte_rule` (`synth_rule` with
    --lexicon synthetic), `minedDecision`, `mergeMined` into the decisions file, `writeExamplesSidecar`.
    A parent the user split (verdict reject, note `split: ...`) is honoured: its rows are reported as its child groups
    (recursively), the parent itself is only refreshed.

--dry-run writes no decisions and no sidecar (the report and the misaligned list are still written). The `rec:` notes
come from `ProposedGroup.rec`.

NOM and ADJ rows (T2.4b) are audited against Morphalou 3.1 (util/_morphalouphon.py: `morphalouToLexicon` converts its notation,
the final mute e written as a schwa is dropped by the schwa convention). Two tiers: `slot` (lemme, ortho, cgram, genre,
nombre) then `ortho` ((ortho, cgram) under any lemma or slot). The class key is (family, slot): family = cgram + `:` + the
2-letter ortho ending class (`orthoClassKeys`), slot = genre+nombre (`ms`, `fp`, `m`, `-` when both are empty). VER and
NOM/ADJ rows are mined by separate `proposeGroups` calls (counters never mix categories), and the cgram prefix of the
family keeps the group ids apart; the VER signatures are unchanged. `--cgram VER,NOM,ADJ` (default all) selects the categories;
without the (gitignored) Morphalou CSV the NOM/ADJ pass is skipped with a warning.

Run: python -m util.audit_mixte [--lexicon mixte|synthetic] [--cgram VER,NOM,ADJ] [--decisions PATH] [--examples PATH] [--dry-run]
"""
import argparse
import os
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Sequence

from src.diffsignature import (AlignmentError, ClassKey, CounterIndex, ProposedGroup, RowDiff, buildRowDiff,
                               proposeGroups)
from src.lexicondecisions import (DECISIONS_PATH, EXAMPLES_PATH, REJECT, Decision, Decisions, loadDecisions,
                                  loadExamplesSidecar, mergeMined, minedDecision, saveDecisions, writeExamplesSidecar)
from src.nomAdjParadigm import loadExcludedWords, orthoClassKeys
from src.verbparadigm import (endingTemplateKey, getTrustedTemplate, loadVerbisteTemplates, loadVerbModelExceptions)
from util._verbreferences import GLAFF_PATH, INFINITIVE_TAG, WIKTIONARY_PATH, RefSet, VerbReferences, loadVerbReferences
from util._morphalouphon import MORPHALOU_PATH_DEFAULT, Key, byOrthoCgram, loadMorphalouPronunciations, lookup
from util.check_against_wiktionary import rowTags
from util.lexicon_completeness import (MIXTE_PATH, SYNTHETIC_PATH, VERB_EXCEPTIONS_PATH, VERBISTE_VERBS_PATH,
                                       makeWord, pipelineRows, readRawRows)

TOP_GROUPS = 40
UNTEMPLATED = "untemplated"
SPLIT_PREFIX = "split:"


@dataclass
class AuditResult:
    lexicon: str
    label: str = "VER"
    audited: int = 0
    withReference: int = 0
    exact: int = 0
    conventionOnly: int = 0
    edited: int = 0
    misalignedRows: list[dict[str, str]] = field(default_factory=list)
    noReference: int = 0
    tiers: Counter[str] = field(default_factory=Counter)
    groups: list[ProposedGroup] = field(default_factory=list)


TIER_SLOT, TIER_ORTHO, TIER_LEMMA = "slot", "ortho", "lemma"


def auditTags(infover: str, genre: str, nombre: str) -> list[str]:
    """`rowTags` plus `inf` for an infinitive row (the checker leaves it out: Wiktionary has no infinitive rows)."""
    tags = rowTags(infover, genre, nombre)
    if "inf" in infover.split(";"):
        tags.append(INFINITIVE_TAG)
    return tags


def _chosen(ref: RefSet, suffix: str = "") -> tuple[frozenset[str], str]:
    chosen = ref.preferred if ref.conflict else ref.variants
    names = sorted(n for n, v in ref.bySource.items() if v & chosen)
    return chosen, "+".join(names) + suffix


def referenceFor(references: VerbReferences, lemme: str, ortho: str, tags: list[str]
                 ) -> tuple[frozenset[str], str, str] | None:
    """(variants to compare with, source label, tier) for a row, None when no reference exists. Tiers: `slot` (the row's own
    (lemme, ortho, tag) slots), `ortho` (the same spelling under any tag), `lemma` (the checker's (lemme, tag) rule)."""
    ref: RefSet | None = references.forRow(lemme, ortho, tags)
    if ref is not None:
        return (*_chosen(ref), TIER_SLOT)
    ref = references.forOrtho(lemme, ortho)
    if ref is not None:
        return (*_chosen(ref, "(ortho)"), TIER_ORTHO)
    fallback = references.matchRow(lemme, tags)
    if fallback is None:
        return None
    return frozenset(fallback[1]), f"{fallback[0]}(lemma)", TIER_LEMMA


def classKeyOf(template: str | None, infinitivePhon: dict[str, Any], lemme: str, tags: list[str]) -> ClassKey:
    """(family, slot): the family is the `endingTemplateKey` (or `untemplated`), the slot the first tag (a participle row
    keeps its gender and number)."""
    if template is None:
        key = UNTEMPLATED
    else:
        infinitive = infinitivePhon.get(lemme)
        key = endingTemplateKey(template, infinitive) if infinitive is not None else template
    participles = sorted(t for t in tags if t.startswith("par:pas:"))
    return key, participles[0] if participles else sorted(tags)[0]


def auditRows(
    rows: list[dict[str, str]], infinitiveRows: list[dict[str, str]], references: VerbReferences,
    verbisteTemplates: dict[str, str], verbExceptions: dict[str, Any], lexicon: str,
) -> tuple[AuditResult, CounterIndex]:
    """Compares the VER rows with the references (steps 2-4 of the module docstring)."""
    infinitives: dict[str, Any] = {}
    for r in infinitiveRows:
        if r["cgram"] == "VER" and r["ortho"] == r["lemme"] and r["lemme"] not in infinitives:
            infinitives[r["lemme"]] = makeWord(r)
    result = AuditResult(lexicon)
    counterIndex = CounterIndex()
    diffRows: list[RowDiff] = []
    for row in rows:
        if row["cgram"] != "VER":
            continue
        tags = auditTags(row["infover"], row["genre"], row["nombre"])
        if not tags:
            continue
        result.audited += 1
        found = referenceFor(references, row["lemme"], row["ortho"], tags)
        if found is None:
            result.noReference += 1
            continue
        result.withReference += 1
        refs, source, tier = found
        result.tiers[tier] += 1
        template = getTrustedTemplate(row["lemme"], verbisteTemplates, verbExceptions)
        classKey = classKeyOf(template, infinitives, row["lemme"], tags)
        phon, syll, orthosyll = row["phon"], row["syll_cv"], row["orthosyll_cv"]
        try:
            diff = buildRowDiff(row["ortho"], phon, refs, syll, orthosyll, classKey, row["lemme"], source,
                                f"{row['ortho']} {row['lemme']} {row['infover']}", row["cgram"], row["genre"], row["nombre"])
        except AlignmentError as e:
            result.misalignedRows.append({"ortho": row["ortho"], "lemme": row["lemme"], "tags": ";".join(tags),
                                          "ours": phon, "ref": "|".join(sorted(refs)), "syll_cv": syll,
                                          "orthosyll_cv": orthosyll, "error": str(e)})
            continue
        if diff is None:
            if phon in refs:
                result.exact += 1
            else:
                result.conventionOnly += 1
            counterIndex.addMatchedRow(phon, syll, orthosyll, classKey, row["lemme"], row["ortho"])
        else:
            result.edited += 1
            diffRows.append(diff)
    result.groups = proposeGroups(diffRows, counterIndex)
    return result, counterIndex


NOMADJ_LABEL = "NOM/ADJ"
NOMADJ_CGRAMS = ("NOM", "ADJ")
ALL_CGRAMS = ("VER", "NOM", "ADJ")


def nomAdjClassKey(cgram: str, ortho: str, genre: str, nombre: str) -> ClassKey:
    """(family, slot) of a NOM/ADJ row: family = cgram + `:` + the 2-letter ortho ending class (the longest available for a
    one-letter ortho), slot = genre + nombre (`-` when both are empty)."""
    keys = orthoClassKeys(ortho)
    two = [k for k in keys if len(k) == 2]
    ending = two[0] if two else keys[0]
    return f"{cgram}:{ending}", genre + nombre or "-"


def auditNomAdjRows(
    rows: list[dict[str, str]], index: dict[Key, set[str]], lexicon: str, cgrams: Sequence[str] = NOMADJ_CGRAMS,
) -> tuple[AuditResult, CounterIndex]:
    """Compares the NOM/ADJ rows with Morphalou (tiers `slot` and `ortho`); same machinery as `auditRows`."""
    coarse = byOrthoCgram(index)
    result = AuditResult(lexicon, NOMADJ_LABEL)
    counterIndex = CounterIndex()
    diffRows: list[RowDiff] = []
    for row in rows:
        if row["cgram"] not in cgrams:
            continue
        result.audited += 1
        found, tier = lookup(index, coarse, row["lemme"], row["ortho"], row["cgram"], row["genre"], row["nombre"])
        if not found:
            result.noReference += 1
            continue
        result.withReference += 1
        result.tiers[tier] += 1
        refs = frozenset(found)
        source = "morphalou" if tier == TIER_SLOT else "morphalou(ortho)"
        classKey = nomAdjClassKey(row["cgram"], row["ortho"], row["genre"], row["nombre"])
        phon, syll, orthosyll = row["phon"], row["syll_cv"], row["orthosyll_cv"]
        tags = f"{row['genre']}{row['nombre']}"
        try:
            diff = buildRowDiff(row["ortho"], phon, refs, syll, orthosyll, classKey, row["lemme"], source,
                                f"{row['ortho']} {row['lemme']} {row['infover']}", row["cgram"], row["genre"], row["nombre"])
        except AlignmentError as e:
            result.misalignedRows.append({"ortho": row["ortho"], "lemme": row["lemme"], "tags": f"{row['cgram']}:{tags}",
                                          "ours": phon, "ref": "|".join(sorted(refs)), "syll_cv": syll,
                                          "orthosyll_cv": orthosyll, "error": str(e)})
            continue
        if diff is None:
            if phon in refs:
                result.exact += 1
            else:
                result.conventionOnly += 1
            counterIndex.addMatchedRow(phon, syll, orthosyll, classKey, row["lemme"], row["ortho"])
        else:
            result.edited += 1
            diffRows.append(diff)
    result.groups = proposeGroups(diffRows, counterIndex)
    return result, counterIndex


def _isSplit(decisions: Decisions, decision: Decision) -> bool:
    existing = decisions.get(decision.groupId)
    return existing is not None and existing.verdict == REJECT and existing.note.startswith(SPLIT_PREFIX)


def _descend(kind: str, child: dict[str, Any], decisions: Decisions, mined: list[Decision],
             sidecar: dict[str, dict[str, Any]]) -> None:
    """One child subgroup of a split parent: mined as a decision of the parent's kind; itself descended when split."""
    d = minedDecision(kind, child["level"], child["signature"], int(child["slots"]), int(child["counter"]),
                      child["examples"], "rec: review (heterogeneous)" if child.get("heterogeneous") else "rec: review")
    mined.append(d)
    sidecar[d.groupId] = {k: child[k] for k in ("members", "counters", "children", "heterogeneous") if k in child}
    if _isSplit(decisions, d):
        for grandchild in child.get("children", []):
            _descend(kind, grandchild, decisions, mined, sidecar)


def minedDecisions(groups: list[ProposedGroup], decisions: Decisions, ruleKind: str) -> tuple[list[Decision], dict[str, dict[str, Any]]]:
    """The mined decisions and sidecar entries of the proposed groups; a split parent is honoured (section 5.1)."""
    mined: list[Decision] = []
    sidecar: dict[str, dict[str, Any]] = {}
    for g in groups:
        kind = "mixte_typo" if g.typo and ruleKind == "mixte_rule" else ruleKind
        d = minedDecision(kind, g.level, g.signature, g.slots, g.counter, g.examples, g.rec)
        mined.append(d)
        sidecar[d.groupId] = g.sidecarEntry()
        if _isSplit(decisions, d):
            for child in g.children:
                _descend(kind, child, decisions, mined, sidecar)
    return mined, sidecar


def renderReport(result: AuditResult, mined: list[Decision]) -> str:
    """The summary as text (stdout and `<lexicon>_audit_report.md`); a pure function of the result."""
    n = result.withReference
    lines = [f"# Audit of the {result.lexicon} lexicon ({result.label}) against the reference pronunciations", "",
             f"- {result.label} rows audited: {result.audited}",
             f"- with a reference: {n}", f"  - matched exactly: {result.exact}",
             f"  - matched up to conventions: {result.conventionOnly}",
             f"  - with real edits: {result.edited}", f"  - misaligned (own syll_cv/phon inconsistent): {len(result.misalignedRows)}",
             f"- no reference: {result.noReference}", ""]
    if result.label == "VER":
        lines.insert(9, f"- reference tiers: slot {result.tiers[TIER_SLOT]}, same spelling under another tag "
                         f"{result.tiers[TIER_ORTHO]}, lemma+tag {result.tiers[TIER_LEMMA]}")
    else:
        lines.insert(9, f"- reference tiers: slot {result.tiers[TIER_SLOT]}, same spelling under another lemma or slot "
                         f"{result.tiers[TIER_ORTHO]}")
    def kindOf(g: ProposedGroup) -> str:
        return "typo" if g.typo else "heterogeneous" if g.heterogeneous else "homogeneous"
    byKind = Counter((g.level, kindOf(g)) for g in result.groups)
    lines.append(f"## {result.label} groups: {len(result.groups)}")
    for (level, what), count in sorted(byKind.items()):
        lines.append(f"- {level} {what}: {count} groups, "
                     f"{sum(g.slots for g in result.groups if g.level == level and kindOf(g) == what)} slots")
    lines += ["", f"## Top {TOP_GROUPS} {result.label} groups", "",
              "| slots | counter | precision | level | het | signature | examples |", "|---|---|---|---|---|---|---|"]
    for g in result.groups[:TOP_GROUPS]:
        lines.append(f"| {g.slots} | {g.counter} | {g.precision:.2f} | {g.level} | {'het' if g.heterogeneous else ''} | {g.signature} | "
                     f"{'; '.join(g.examples[:2])} |")
    lines.append("")
    return "\n".join(lines)


def writeMisaligned(path: str, rows: list[dict[str, str]]) -> None:
    cols = ("ortho", "lemme", "tags", "ours", "ref", "syll_cv", "orthosyll_cv", "error")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(cols) + "\n")
        for r in sorted(rows, key=lambda r: (r["lemme"], r["ortho"], r["tags"])):
            f.write("\t".join(r[c] for c in cols) + "\n")


def runAudit(lexicon: str, wiktionaryPath: str, glaffPath: str, requireGlaff: bool = True,
             mixtePath: str = MIXTE_PATH, syntheticPath: str = SYNTHETIC_PATH, cgrams: Sequence[str] = ALL_CGRAMS,
             morphalouPath: str = MORPHALOU_PATH_DEFAULT) -> list[AuditResult]:
    """One AuditResult per audited category family: VER (Wiktionary/GLAFF) then NOM/ADJ (Morphalou)."""
    excludedWords = loadExcludedWords("excluded_words.txt")
    mixteRows, syntheticRows = pipelineRows([readRawRows(mixtePath), readRawRows(syntheticPath)], excludedWords)
    rows = mixteRows if lexicon == "mixte" else syntheticRows
    results: list[AuditResult] = []
    if "VER" in cgrams:
        references = loadVerbReferences(wiktionaryPath, glaffPath, requireGlaff=requireGlaff)
        result, _index = auditRows(rows, mixteRows + syntheticRows if lexicon == "synthetic" else mixteRows, references,
                                   loadVerbisteTemplates(VERBISTE_VERBS_PATH),
                                   loadVerbModelExceptions(VERB_EXCEPTIONS_PATH), lexicon)
        results.append(result)
    nomAdj = [c for c in NOMADJ_CGRAMS if c in cgrams]
    if nomAdj:
        index = loadMorphalouPronunciations(morphalouPath, required=False)
        if index:
            results.append(auditNomAdjRows(rows, index, lexicon, nomAdj)[0])
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lexicon", choices=("mixte", "synthetic"), default="mixte")
    parser.add_argument("--cgram", default=",".join(ALL_CGRAMS), help="categories to audit, comma-separated (VER,NOM,ADJ)")
    parser.add_argument("--decisions", default=DECISIONS_PATH)
    parser.add_argument("--examples", default=EXAMPLES_PATH)
    parser.add_argument("--dry-run", action="store_true", help="write neither the decisions nor the examples sidecar")
    args = parser.parse_args()
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    start = time.time()
    cgrams = [c for c in args.cgram.split(",") if c]
    unknownCgrams = set(cgrams) - set(ALL_CGRAMS)
    if unknownCgrams:
        sys.exit(f"unknown --cgram {sorted(unknownCgrams)}")
    results = runAudit(args.lexicon, WIKTIONARY_PATH, GLAFF_PATH, cgrams=cgrams)
    decisions = loadDecisions(args.decisions) if os.path.exists(args.decisions) else Decisions()
    ruleKind = "mixte_rule" if args.lexicon == "mixte" else "synth_rule"
    mined: list[Decision] = []
    sidecar: dict[str, dict[str, Any]] = {}
    reports: list[str] = []
    for result in results:
        resultMined, resultSidecar = minedDecisions(result.groups, decisions, ruleKind)
        mined += resultMined
        sidecar.update(resultSidecar)
        reports.append(renderReport(result, resultMined))
    report = "\n".join(reports)
    with open(f"{args.lexicon}_audit_report.md", "w", encoding="utf-8", newline="\n") as f:
        f.write(report)
    writeMisaligned(f"{args.lexicon}_audit_misaligned.tsv", [r for result in results for r in result.misalignedRows])
    print(report)
    if args.dry_run:
        print("dry run: decisions and examples sidecar not written")
    else:
        merged = mergeMined(decisions, mined)
        saveDecisions(merged, args.decisions)
        existing = loadExamplesSidecar(args.examples)
        existing.update(sidecar)
        writeExamplesSidecar(args.examples, existing)
        print(f"wrote {args.decisions} ({len(merged)} groups, {len(merged.pending())} pending) and {args.examples}")
    print(f"runtime {time.time() - start:.0f} s", file=sys.stderr)


if __name__ == "__main__":
    main()
