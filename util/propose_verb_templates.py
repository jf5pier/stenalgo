#!/usr/bin/env python
# coding: utf-8
"""
Proposes a Verbiste conjugation template for each VER lemma of LexiqueMixte.tsv that has no trusted template (T3.7, proposal
stage only: `missing:no_template` of util/lexicon_completeness.py), grouped so that one decision covers many lemmas.

Method. The candidates of a lemma are the Verbiste templates whose name suffix (after `:`) and infinitive ending are a suffix of
its infinitive. Each candidate generates (generateOrthoForm) the spelling of every slot the lemma has evidence for, and is
scored by matches and mismatches. The evidence of a slot (the infinitive excluded, it matches by construction) is the set of
spellings found for it in Mixte, Synthetic, the French Wiktionary conjugation pages and GLÀFF (optional); a generated spelling
matches when it belongs to that set.

Statuses
  proposed      a candidate has no mismatch, the evidence has at least MIN_EVIDENCE slots, and every other candidate without
                mismatch generates the same paradigm (then the longest suffix, then the template with most Verbiste lemmas, wins)
  ambiguous     several candidates without mismatch generate different paradigms: the evidence does not choose
  contradicted  every candidate has a mismatch (an irregular verb or a lexicon error); the template column is the best one
  no_evidence   fewer than MIN_EVIDENCE evidence slots; the template column is the tie-break choice, unproven
  no_candidate  no template fits the infinitive

Outputs: verb_template_proposals.tsv (one row per lemma), verb_template_groups.tsv (one row per (suffix, template) of the
`proposed` lemmas, with the group id of the `template` decision it would be, level `-`). `--write-decisions` merges the groups
as pending `template` decisions into the decisions file (never run implicitly).

    python -m util.propose_verb_templates [--min-evidence N] [--write-decisions] [--decisions PATH]
"""

import argparse
import csv
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.lexicondecisions import DECISIONS_PATH, Decision, loadDecisions, mergeMined, minedDecision, saveDecisions
from src.nomAdjParadigm import loadExcludedWords
from src.verbparadigm import (
    ConjugationTemplate, VerbModelException, generateOrthoForm, getTrustedTemplate, infinitiveRadical, loadVerbisteTemplates,
    loadVerbModelExceptions, parseConjugationTemplates,
)
from src.word import Lemme
from util._verbreferences import GLAFF_PATH, WIKTIONARY_PATH, loadVerbReferences
from util.lexicon_completeness import (
    EXCLUDED_SLOTS_PATH, MIXTE_PATH, SYNTHETIC_PATH, VERB_EXCEPTIONS_PATH, VERBISTE_CONJUGATIONS_PATH, VERBISTE_VERBS_PATH,
    exclusionReason, loadExcludedSlots, pipelineRows, readRawRows, templateSlots, verbSlotsOfRow,
)

PROPOSALS_PATH = "verb_template_proposals.tsv"
GROUPS_PATH = "verb_template_groups.tsv"
MIN_EVIDENCE = 3
PROPOSALS_HEADER = ("lemme", "status", "template", "suffix", "matches", "mismatches", "evidence", "reason_untemplated",
                    "alternatives", "unlocked_slots")
GROUPS_HEADER = ("group", "template", "lemmas", "slots_unlocked", "examples", "group_id")
SOURCES = ("mixte", "synthetic", "wiktionary", "glaff")

# The references write the 1990 rectified accent in the future and the conditional (cèderai), the lexicon and Verbiste the
# traditional one (céderai): in those slots è and é are not told apart.
RECTIFIED_CODES = ("ind:fut:", "cnd:pre:")

# slot -> (spellings, sources that gave them)
Evidence = dict[str, tuple[set[str], set[str]]]


@dataclass(frozen=True)
class Candidate:
    name: str
    suffix: str
    matches: int
    mismatches: tuple[str, ...]  # "slot:generated>expected"


@dataclass(frozen=True)
class Proposal:
    lemme: Lemme
    status: str
    template: str
    suffix: str
    matches: int
    mismatches: tuple[str, ...]
    evidence: str
    alternatives: tuple[str, ...]


def nameSuffix(templateName: str) -> str:
    """The part of a Verbiste template id after the colon (`aim:er` -> `er`)."""
    return templateName.split(":", 1)[1] if ":" in templateName else ""


def foldGrave(ortho: str) -> str:
    return ortho.replace("è", "é")


def generateSlot(radical: str, template: ConjugationTemplate, slot: str) -> str | None:
    """The spelling `template` gives to `slot` (`ind:pre:1s`, `par:pas:fp`, `par:pre`, `inf`), None when it has no such form."""
    parts = slot.split(":")
    if slot in ("inf", "par:pre"):
        return generateOrthoForm(radical, template, slot)
    if parts[:2] == ["par", "pas"] and len(parts) == 3 and len(parts[2]) == 2:
        return generateOrthoForm(radical, template, "par:pas", gender=parts[2][0], number=parts[2][1])
    if len(parts) == 3:
        return generateOrthoForm(radical, template, f"{parts[0]}:{parts[1]}", personNumber=parts[2])
    return None


def candidateTemplates(lemme: Lemme, templates: dict[str, ConjugationTemplate]) -> list[str]:
    """Names of the templates whose name suffix and infinitive ending are both suffixes of `lemme`, sorted by name."""
    return [name for name in sorted(templates)
            if lemme.endswith(nameSuffix(name)) and lemme.endswith(templates[name].infinitiveSuffix)
            and len(lemme) > len(templates[name].infinitiveSuffix)]


def scoreCandidate(lemme: Lemme, name: str, template: ConjugationTemplate, evidence: Evidence) -> Candidate:
    """Matches and mismatches of one template against the evidence slots (the infinitive is not evidence)."""
    radical = infinitiveRadical(lemme, template)
    matches = 0
    mismatches: list[str] = []
    for slot in sorted(evidence):
        if slot == "inf":
            continue
        generated = generateSlot(radical, template, slot)
        spellings = evidence[slot][0]
        if generated is not None and (generated in spellings or (
                slot.startswith(RECTIFIED_CODES) and foldGrave(generated) in {foldGrave(item) for item in spellings})):
            matches += 1
        else:
            mismatches.append(f"{slot}:{generated or '-'}>{'|'.join(sorted(spellings))}")
    return Candidate(name, nameSuffix(name), matches, tuple(mismatches))


def paradigmSignature(lemme: Lemme, template: ConjugationTemplate) -> tuple[str | None, ...]:
    radical = infinitiveRadical(lemme, template)
    return tuple(generateSlot(radical, template, slot) for slot in sorted(templateSlots(template)))


def evidenceText(evidence: Evidence) -> str:
    counts = Counter(source for slot, (_s, sources) in evidence.items() if slot != "inf" for source in sources)
    return " ".join(f"{source}={counts[source]}" for source in SOURCES if counts[source])


def proposeTemplate(
    lemme: Lemme, evidence: Evidence, templates: dict[str, ConjugationTemplate], verbisteCounts: Counter[str],
    minEvidence: int = MIN_EVIDENCE,
) -> Proposal:
    """The proposal for one lemma (statuses in the module docstring)."""
    names = candidateTemplates(lemme, templates)
    evidenceSlots = [slot for slot in evidence if slot != "inf"]
    text = evidenceText(evidence)
    if not names:
        return Proposal(lemme, "no_candidate", "", "", 0, (), text, ())
    scored = [scoreCandidate(lemme, name, templates[name], evidence) for name in names]

    def tieBreak(c: Candidate) -> tuple[int, int, int, str]:
        return (-len(c.suffix), -len(templates[c.name].infinitiveSuffix), -verbisteCounts[c.name], c.name)

    if not evidenceSlots:
        best = min(scored, key=tieBreak)
        return Proposal(lemme, "no_evidence", best.name, best.suffix, 0, (), text, ())
    clean = sorted((c for c in scored if not c.mismatches), key=tieBreak)
    if not clean:
        best = min(scored, key=lambda c: (len(c.mismatches), -c.matches) + tieBreak(c))
        return Proposal(lemme, "contradicted", best.name, best.suffix, best.matches, best.mismatches, text, ())
    best = clean[0]
    signature = paradigmSignature(lemme, templates[best.name])
    others = tuple(c.name for c in clean[1:] if paradigmSignature(lemme, templates[c.name]) != signature)
    if len(evidenceSlots) < minEvidence:
        return Proposal(lemme, "no_evidence", best.name, best.suffix, best.matches, (), text, others)
    if others:
        return Proposal(lemme, "ambiguous", best.name, best.suffix, best.matches, (), text, others)
    return Proposal(lemme, "proposed", best.name, best.suffix, best.matches, (), text, ())


def collectEvidence(
    mixteRows: list[dict[str, str]], syntheticRows: list[dict[str, str]],
    referenceOrthos: dict[Lemme, dict[str, dict[str, set[str]]]], lemmas: set[Lemme],
) -> dict[Lemme, Evidence]:
    """lemma -> slot -> (spellings, sources), from the lexicon rows and the references (referenceOrthos: lemma -> source -> tag -> spellings)."""
    evidence: dict[Lemme, Evidence] = {lemme: {} for lemme in lemmas}

    def add(lemme: Lemme, slot: str, ortho: str, source: str) -> None:
        spellings, sources = evidence[lemme].setdefault(slot, (set(), set()))
        spellings.add(ortho)
        sources.add(source)

    for source, rows in (("mixte", mixteRows), ("synthetic", syntheticRows)):
        for row in rows:
            if row["cgram"] == "VER" and row["lemme"] in lemmas:
                for slot in verbSlotsOfRow(row):
                    add(row["lemme"], slot, row["ortho"], source)
    for lemme in lemmas:
        for source in ("wiktionary", "glaff"):
            for tag, orthos in referenceOrthos.get(lemme, {}).get(source, {}).items():
                for ortho in orthos:
                    add(lemme, tag, ortho, source)
    return evidence


def referenceIndex(wiktionaryPath: str, glaffPath: str, lemmas: set[Lemme]) -> dict[Lemme, dict[str, dict[str, set[str]]]]:
    """lemma -> source -> tag -> spellings, for the given lemmas."""
    references = loadVerbReferences(wiktionaryPath, glaffPath)
    index: dict[Lemme, dict[str, dict[str, set[str]]]] = {}
    for lemme, ortho, tag in references.slots():
        if lemme not in lemmas:
            continue
        for source in ("wiktionary", "glaff"):
            if (lemme, ortho, tag) in references.sources[source].variants:
                index.setdefault(lemme, {}).setdefault(source, {}).setdefault(tag, set()).add(ortho)
    return index


def untemplatedReason(lemme: Lemme, exceptions: dict[Lemme, VerbModelException]) -> str:
    """Why the lemma has no trusted template: absent from Verbiste and the exceptions, or an exception with a non-trusted status."""
    exception = exceptions.get(lemme)
    if exception is None:
        return "absent"
    return f"exception:{exception.status or 'none'}"


def unlockedSlots(
    lemme: Lemme, template: ConjugationTemplate, attested: set[str], excluded: list[tuple[str, str, str, str]],
) -> int:
    """The slots of `template` that the lemma lacks and that no exclusion rule rules out."""
    return sum(1 for slot in templateSlots(template)
               if slot not in attested and exclusionReason(excluded, lemme, "VER", slot) is None)


def groupSignature(proposal: Proposal) -> str:
    return f"-{proposal.suffix} → {proposal.template}"


def buildGroups(
    proposals: list[Proposal], unlocked: dict[Lemme, int],
) -> tuple[list[tuple[str, str, list[Lemme], int]], list[Decision]]:
    """The groups of the `proposed` lemmas: (signature, template, sorted lemmas, slots unlocked), by size, and the matching
    pending `template` decisions."""
    members: dict[tuple[str, str], list[Lemme]] = defaultdict(list)
    for proposal in proposals:
        if proposal.status == "proposed":
            members[(groupSignature(proposal), proposal.template)].append(proposal.lemme)
    groups = [(signature, template, sorted(lemmas), sum(unlocked.get(lemme, 0) for lemme in lemmas))
              for (signature, template), lemmas in members.items()]
    groups.sort(key=lambda g: (-len(g[2]), g[0], g[1]))
    decisions = [minedDecision("template", "-", signature, slots, 0, lemmas[:3], f"rec:{template}")
                 for signature, template, lemmas, slots in groups]
    return groups, decisions


def writeProposals(proposals: list[Proposal], reasons: dict[Lemme, str], unlocked: dict[Lemme, int], path: str | Path) -> None:
    with open(path, "w", encoding="utf-8", newline="") as tsvFile:
        writer = csv.writer(tsvFile, delimiter="\t", lineterminator="\n")
        writer.writerow(PROPOSALS_HEADER)
        for p in sorted(proposals, key=lambda item: item.lemme):
            detail = p.evidence + (" | mismatches: " + "; ".join(p.mismatches) if p.mismatches else "")
            writer.writerow((p.lemme, p.status, p.template, p.suffix, p.matches, len(p.mismatches), detail,
                             reasons.get(p.lemme, ""), ",".join(p.alternatives), unlocked.get(p.lemme, 0)))


def writeGroups(groups: list[tuple[str, str, list[Lemme], int]], decisions: list[Decision], path: str | Path) -> None:
    with open(path, "w", encoding="utf-8", newline="") as tsvFile:
        writer = csv.writer(tsvFile, delimiter="\t", lineterminator="\n")
        writer.writerow(GROUPS_HEADER)
        for (signature, template, lemmas, slots), decision in zip(groups, decisions):
            writer.writerow((signature, template, len(lemmas), slots, ",".join(lemmas[:8]), decision.groupId))


def writeDecisions(decisions: list[Decision], path: str) -> None:
    """Merges the groups as pending `template` decisions into the decisions file at `path`."""
    saveDecisions(mergeMined(loadDecisions(path), decisions), path)


def run(
    mixtePath: str, syntheticPath: str, wiktionaryPath: str, glaffPath: str, minEvidence: int,
    exceptions: dict[Lemme, VerbModelException] | None = None,
) -> tuple[list[Proposal], dict[Lemme, str], dict[Lemme, int]]:
    excludedWords = loadExcludedWords("excluded_words.txt")
    mixteRows, syntheticRows = pipelineRows([readRawRows(mixtePath), readRawRows(syntheticPath)], excludedWords)
    verbisteTemplates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
    if exceptions is None:
        exceptions = loadVerbModelExceptions(VERB_EXCEPTIONS_PATH)
    templates = parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
    excluded = loadExcludedSlots(EXCLUDED_SLOTS_PATH)
    lemmas = {row["lemme"] for row in mixteRows if row["cgram"] == "VER"}
    untemplated = {lemme for lemme in lemmas if getTrustedTemplate(lemme, verbisteTemplates, exceptions) is None}
    evidence = collectEvidence(mixteRows, syntheticRows, referenceIndex(wiktionaryPath, glaffPath, untemplated), untemplated)
    verbisteCounts = Counter(verbisteTemplates.values())
    proposals = [proposeTemplate(lemme, evidence[lemme], templates, verbisteCounts, minEvidence) for lemme in sorted(untemplated)]
    reasons = {lemme: untemplatedReason(lemme, exceptions) for lemme in untemplated}
    unlocked: dict[Lemme, int] = {}
    for proposal in proposals:
        if proposal.template:
            attested = {slot for slot, (_s, sources) in evidence[proposal.lemme].items() if sources & {"mixte", "synthetic"}}
            unlocked[proposal.lemme] = unlockedSlots(proposal.lemme, templates[proposal.template], attested, excluded)
    return proposals, reasons, unlocked


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mixte", default=MIXTE_PATH)
    parser.add_argument("--synthetic", default=SYNTHETIC_PATH)
    parser.add_argument("--wiktionary", default=WIKTIONARY_PATH)
    parser.add_argument("--glaff", default=GLAFF_PATH)
    parser.add_argument("--min-evidence", type=int, default=MIN_EVIDENCE)
    parser.add_argument("--proposals", default=PROPOSALS_PATH)
    parser.add_argument("--groups", default=GROUPS_PATH)
    parser.add_argument("--write-decisions", action="store_true", help="merge the groups as pending template decisions")
    parser.add_argument("--decisions", default=DECISIONS_PATH)
    args = parser.parse_args()
    started = time.time()
    proposals, reasons, unlocked = run(args.mixte, args.synthetic, args.wiktionary, args.glaff, args.min_evidence)
    groups, decisions = buildGroups(proposals, unlocked)
    writeProposals(proposals, reasons, unlocked, args.proposals)
    writeGroups(groups, decisions, args.groups)
    print(f"{len(proposals)} untemplated VER lemmas")
    for status, count in sorted(Counter(p.status for p in proposals).items()):
        print(f"  {status:<13} {count:>5}")
    print("why untemplated: " + ", ".join(f"{reason}={count}" for reason, count in sorted(Counter(reasons.values()).items())))
    print(f"{len(groups)} groups written to {args.groups}, proposals to {args.proposals} ({time.time() - started:.1f} s)")
    if args.write_decisions:
        writeDecisions(decisions, args.decisions)
        print(f"merged {len(decisions)} pending template decisions into {args.decisions}", file=sys.stderr)


if __name__ == "__main__":
    main()
