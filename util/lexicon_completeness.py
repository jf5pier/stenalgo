#!/usr/bin/env python
# coding: utf-8
"""
Completeness census over the lexicons (T0.1): for every VER, NOM and ADJ lemma of LexiqueMixte.tsv, the slots the
language expects and whether each is attested in Mixte, in Synthetic, ruled out by design (resources/excludedSlots.tsv)
or missing (with a cause when one is cheap to determine).

Expected slots
  VER  with a trusted Verbiste template: allFiniteSlots(template) (sub:imp and the empty endings of defective templates
       are not in it) + inf + par:pre + par:pas in m/f x s/p. Without one: the slot list of the REFERENCE_TEMPLATE
       (aim:er, the regular first group), every unattested slot being missing:no_template. The choice only affects the
       size of the "expected" count of those lemmas; it is the most common template, so it is the best guess.
  NOM/ADJ  expectedSlots/missingSlots of src/nomAdjParadigm.py, on the (lemma, category) slot map; a missing slot is
       excluded:invariable_exception (resources/nomAdjModelExceptions.tsv) or excluded:suspected_invariable
       (isSuspectedInvariableForm: the generator would produce the same spelling) instead of missing.

Attested follows util/completeVerbParadigms.py: finite tags come from the rows without an `inf` tag, a participle slot from
the gender and number of a `par:pas` row, an infinitive from the row whose ortho is the lemma.

Statuses: mixte, synthetic, excluded:<reason>, missing:<cause>. Causes: no_template, no_participle_donor, other;
refineMissingCause refines `other` and `no_participle_donor` from the generator's synthetic_skip_reasons.tsv (--skip-reasons):
no_majority_above_floor, splice_rejected, reference_differs, no_reference, unattested_ending, homograph_tag, lost_nasal,
no_infinitive, infinitive_outlier, no_source_form, not_generated (inf and par:pre when rule `infinitive-participle-present` did not run).

    python -m util.lexicon_completeness [--mixte PATH] [--synthetic PATH] [--out PATH]
"""

import argparse
import csv
import fnmatch
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.nomAdjParadigm import (
    attestedSlots, chooseSourceSlot, isSuspectedInvariableForm, loadExcludedWords, loadNomAdjModelExceptions,
    expectedSlots,
)
from src.verbparadigm import (
    ConjugationTemplate, allFiniteSlots, getTrustedTemplate, loadVerbisteTemplates, loadVerbModelExceptions,
    parseConjugationTemplates,
)
from src.spellingvariants import loadSpellingVariantDrops
from src.word import GramCat, Lemme, Word

MIXTE_PATH = "resources/LexiqueMixte.tsv"
SYNTHETIC_PATH = "resources/LexiqueSynthetic.tsv"
OUT_PATH = "lexicon_completeness.tsv"
EXCLUDED_SLOTS_PATH = "resources/excludedSlots.tsv"
VERBISTE_VERBS_PATH = "resources/verbiste/verbs-fr.xml"
VERBISTE_CONJUGATIONS_PATH = "resources/verbiste/conjugations-fr.xml"
VERB_EXCEPTIONS_PATH = "resources/verbModelExceptions.tsv"
NOMADJ_EXCEPTIONS_PATH = "resources/nomAdjModelExceptions.tsv"
REFERENCE_TEMPLATE = "aim:er"

PARTICIPLE_SLOTS = tuple(f"par:pas:{g}{n}" for g in "mf" for n in "sp")
STATUS_MIXTE = "mixte"
STATUS_SYNTHETIC = "synthetic"
OUT_HEADER = ("lemme", "cgram", "slot", "status", "ortho_if_known")


@dataclass(frozen=True)
class SlotRow:
    lemme: Lemme
    cgram: str
    slot: str
    status: str
    ortho: str


def loadExcludedSlots(path: str | Path) -> list[tuple[str, str, str, str]]:
    """(lemme, cgram, slot pattern, reason) rows of excludedSlots.tsv; '#' lines and the header are skipped."""
    rows: list[tuple[str, str, str, str]] = []
    if not Path(path).exists():
        return rows
    with open(path, encoding="utf-8") as tsvFile:
        lines = [line.rstrip("\n") for line in tsvFile if line.strip() and not line.startswith("#")]
    for line in lines[1:]:
        fields = line.split("\t") + [""] * 4
        rows.append((fields[0], fields[1], fields[2], fields[3]))
    return rows


def exclusionReason(
    excluded: list[tuple[str, str, str, str]], lemme: Lemme, cgram: str, slot: str
) -> str | None:
    """The reason of the first excludedSlots row matching (lemme, cgram, slot); `*` wildcards (fnmatch) in lemme and slot."""
    for ruleLemme, ruleCgram, ruleSlot, reason in excluded:
        if ruleCgram == cgram and fnmatch.fnmatchcase(lemme, ruleLemme) and fnmatch.fnmatchcase(slot, ruleSlot):
            return reason
    return None


SkipReasons = dict[tuple[Lemme, str], str]
SKIP_REASONS_PATH = "synthetic_skip_reasons.tsv"
# causes the skip file may refine; no_template and no_participle_donor are decided by the census itself
REFINABLE_CAUSES = ("other", "no_participle_donor")


def loadSkipReasons(path: str | Path) -> SkipReasons:
    """(lemme, slot) -> reason of util.completeVerbParadigms' synthetic_skip_reasons.tsv (empty when absent). A slot is
    a census slot name; `finite:*` stands for every finite slot of the lemma, `par:pas:*` for every participle."""
    reasons: SkipReasons = {}
    if not Path(path).exists():
        return reasons
    with open(path, encoding="utf-8") as tsvFile:
        for line in tsvFile.read().splitlines()[1:]:
            lemme, slot, reason = line.split("\t")
            reasons[(lemme, slot)] = reason
    return reasons


def refineMissingCause(lemme: Lemme, cgram: str, slot: str, cause: str, skipReasons: SkipReasons | None = None) -> str:
    """The finer cause of a missing slot (no_majority_above_floor, splice_rejected, reference_differs, no_reference,
    unattested_ending, homograph_tag, lost_nasal, no_infinitive, ...) from the generator's skip reasons; `cause`
    unchanged when there are none for the slot. A missing slot the generator never attempts (`inf`, `par:pre`) is
    `not_generated`."""
    if skipReasons is None or cgram != "VER" or cause not in REFINABLE_CAUSES:
        return cause
    if slot in ("inf", "par:pre"):
        return skipReasons.get((lemme, slot)) or "not_generated"
    wildcard = "par:pas:*" if slot.startswith("par:pas:") else "finite:*"
    return skipReasons.get((lemme, slot)) or skipReasons.get((lemme, wildcard)) or cause


def readRawRows(path: str | Path) -> list[dict[str, str]]:
    """Rows of a lexicon TSV without the '#' rows; none if the file is absent."""
    if not Path(path).exists():
        return []
    with open(path, encoding="utf-8", newline="") as tsvFile:
        return [row for row in csv.DictReader(tsvFile, delimiter="\t")
                if row.get("ortho") and not row["ortho"].startswith("#")]


def pipelineRows(rawRowLists: list[list[dict[str, str]]], excludedWords: set[str]) -> list[list[dict[str, str]]]:
    """The rows the pipeline keeps (Dictionary.readCorpus): excluded words and the dropped spelling variants removed."""
    carriers: dict[str, set[str]] = {}
    for rawRows in rawRowLists:
        for row in rawRows:
            carriers.setdefault(row["ortho"], set()).add(row["lemme"])
    drops = loadSpellingVariantDrops().withCanonicalCarriers({ortho: frozenset(l) for ortho, l in carriers.items()})
    return [[row for row in rawRows
             if row["ortho"] not in excludedWords
             and not drops.isDroppedOrthoRow(row["ortho"], row["lemme"], row["cgram"])
             and not drops.isDroppedLemme(row["lemme"])]
            for rawRows in rawRowLists]


def makeWord(row: dict[str, str]) -> Word:
    """Word of a NOM/ADJ row (only what the paradigm helpers read matters)."""
    return Word(
        ortho=row["ortho"], phonology=row["phon"], lemme=row["lemme"], gramCat=GramCat[row["cgram"]],
        orthoGramCat=[GramCat[gc] for gc in row["cgramortho"].split(",")],
        gender=row["genre"] or None, number=row["nombre"] or None, infoVerb=row["infover"] or None,
        rawSyllCV=row["syll_cv"], rawOrthosyllCV=row["orthosyll_cv"],
        frequencyBook=float(row["freqlivres"] or 0), frequencyFilm=float(row["freqfilms2"] or 0),
    )


def verbSlotsOfRow(row: dict[str, str]) -> list[str]:
    """The slot names a VER row attests, by the rules of attestedFiniteFormsByLemme / attestedParticipleFormsByLemme."""
    tags = [tag for tag in row["infover"].split(";") if tag]
    slots: list[str] = []
    if "inf" in tags:
        # a spurious "inf" poisons the other tags of the row: only a true infinitive counts
        if row["ortho"] == row["lemme"]:
            slots.append("inf")
        return slots
    for tag in tags:
        parts = tag.split(":")
        if len(parts) == 3:
            slots.append(tag)
        elif tag == "par:pre":
            slots.append(tag)
        elif tag == "par:pas" and row["genre"] in ("m", "f") and row["nombre"] in ("s", "p"):
            slots.append(f"par:pas:{row['genre']}{row['nombre']}")
    return slots


def templateSlots(template: ConjugationTemplate) -> list[str]:
    """Every slot of a template: finite slots, inf, par:pre, the four participles."""
    finite = [f"{code}:{personNumber}" for code, personNumber in allFiniteSlots(template)]
    return finite + ["inf", "par:pre"] + list(PARTICIPLE_SLOTS)


def verbCensus(
    mixteRows: list[dict[str, str]], syntheticRows: list[dict[str, str]],
    verbisteTemplates: dict[Lemme, str], verbExceptions: dict[Lemme, object],
    conjugationTemplates: dict[str, ConjugationTemplate], excluded: list[tuple[str, str, str, str]],
    skipReasons: SkipReasons | None = None,
) -> list[SlotRow]:
    """One SlotRow per (VER lemma of Mixte, expected slot)."""
    attested: dict[str, dict[Lemme, dict[str, str]]] = {STATUS_MIXTE: defaultdict(dict), STATUS_SYNTHETIC: defaultdict(dict)}
    lemmas: set[Lemme] = set()
    for source, rows in ((STATUS_MIXTE, mixteRows), (STATUS_SYNTHETIC, syntheticRows)):
        for row in rows:
            if row["cgram"] != "VER":
                continue
            if source == STATUS_MIXTE:
                lemmas.add(row["lemme"])
            for slot in verbSlotsOfRow(row):
                attested[source][row["lemme"]].setdefault(slot, row["ortho"])
    reference = conjugationTemplates[REFERENCE_TEMPLATE]
    result: list[SlotRow] = []
    for lemme in sorted(lemmas):
        templateName = getTrustedTemplate(lemme, verbisteTemplates, verbExceptions)  # type: ignore[arg-type]
        template = conjugationTemplates.get(templateName) if templateName is not None else None
        slots = templateSlots(template if template is not None else reference)
        mixteSlots = attested[STATUS_MIXTE].get(lemme, {})
        syntheticSlots = attested[STATUS_SYNTHETIC].get(lemme, {})
        hasParticiple = any(slot.startswith("par:pas:") for slot in list(mixteSlots) + list(syntheticSlots))
        for slot in slots:
            reason = exclusionReason(excluded, lemme, "VER", slot)
            if reason is not None:
                status, ortho = f"excluded:{reason}", ""
            elif slot in mixteSlots:
                status, ortho = STATUS_MIXTE, mixteSlots[slot]
            elif slot in syntheticSlots:
                status, ortho = STATUS_SYNTHETIC, syntheticSlots[slot]
            else:
                if template is None:
                    cause = "no_template"
                elif slot.startswith("par:pas:") and not hasParticiple:
                    cause = "no_participle_donor"
                else:
                    cause = "other"
                status, ortho = f"missing:{refineMissingCause(lemme, 'VER', slot, cause, skipReasons)}", ""
            result.append(SlotRow(lemme, "VER", slot, status, ortho))
    return result


def nomAdjCensus(
    mixteRows: list[dict[str, str]], syntheticRows: list[dict[str, str]],
    excluded: list[tuple[str, str, str, str]], nomAdjExceptions: dict[tuple[Lemme, str], object],
) -> list[SlotRow]:
    """One SlotRow per (NOM/ADJ lemma, category, expected slot); slots are gender+number (ms, fp...)."""
    mixteWords = [makeWord(row) for row in mixteRows if row["cgram"] in ("NOM", "ADJ")]
    allWords = mixteWords + [makeWord(row) for row in syntheticRows if row["cgram"] in ("NOM", "ADJ")]
    fromMixte = attestedSlots(mixteWords)
    fromAll = attestedSlots(allWords)
    result: list[SlotRow] = []
    for lemmeGramCat in sorted(fromMixte):
        slotMap = fromAll[lemmeGramCat]
        mixteMap = fromMixte[lemmeGramCat]
        gramCat = next(iter(slotMap.values())).gramCat
        lemme = next(iter(slotMap.values())).lemme
        cgram = gramCat.name
        # the expected set follows the Mixte genders: a Synthetic gender must not enlarge the census
        wanted = expectedSlots(gramCat, frozenset(gender for gender, _n in mixteMap))
        sourceSlot = chooseSourceSlot(mixteMap, gramCat)
        for slot in sorted(wanted):
            name = f"{slot[0]}{slot[1]}"
            reason = exclusionReason(excluded, lemme, cgram, name)
            ortho = ""
            if reason is not None:
                status = f"excluded:{reason}"
            elif slot in mixteMap:
                status, ortho = STATUS_MIXTE, mixteMap[slot].ortho
            elif slot in slotMap:
                status, ortho = STATUS_SYNTHETIC, slotMap[slot].ortho
            elif nomAdjExceptions.get((lemme, cgram)) is not None and getattr(
                nomAdjExceptions[(lemme, cgram)], "status") == "invariable":
                status = "excluded:invariable_exception"
            elif sourceSlot is not None and isSuspectedInvariableForm(mixteMap[sourceSlot], slot):
                status = "excluded:suspected_invariable"
            else:
                status = f"missing:{refineMissingCause(lemme, cgram, name, 'other')}"
            result.append(SlotRow(lemme, cgram, name, status, ortho))
    return result


def statusFamily(status: str) -> str:
    """mixte / synthetic / excluded / missing, the part before the colon."""
    return status.split(":")[0]


def summarize(rows: list[SlotRow], out: object = sys.stdout) -> None:
    """Per cgram: lemmas, expected slots, by status; for VER also missing from Mixte and after synthesis."""
    def emit(text: str = "") -> None:
        print(text, file=out)  # type: ignore[call-overload]
    for cgram in ("VER", "NOM", "ADJ"):
        subset = [row for row in rows if row.cgram == cgram]
        if not subset:
            continue
        lemmas = {row.lemme for row in subset}
        families = Counter(statusFamily(row.status) for row in subset)
        emit(f"{cgram}: {len(lemmas):,} lemmas, {len(subset):,} expected slots")
        for family in (STATUS_MIXTE, STATUS_SYNTHETIC, "excluded", "missing"):
            emit(f"  {family:<10} {families[family]:>9,}")
        for status, count in sorted(Counter(row.status for row in subset).items()):
            if ":" in status:
                emit(f"    {status:<48} {count:>9,}")
        notInMixte = [row for row in subset if statusFamily(row.status) in (STATUS_SYNTHETIC, "missing")]
        afterSynthesis = [row for row in subset if statusFamily(row.status) == "missing"]
        emit(f"  missing from Mixte (not mixte, not excluded): {len(notInMixte):,} slots, "
             f"{len({row.lemme for row in notInMixte}):,} lemmas")
        emit(f"  missing after synthesis:                     {len(afterSynthesis):,} slots, "
             f"{len({row.lemme for row in afterSynthesis}):,} lemmas")
        if cgram == "VER":
            noTemplate = {row.lemme for row in subset if row.status == "missing:no_template"}
            emit(f"  lemmas with a no_template gap: {len(noTemplate):,}")
            # the figures of docs/SYNTHETIC_LEXICON_STATUS.md 6.1: templated lemmas, slots a donor could serve
            comparable = [row for row in notInMixte
                          if row.lemme not in noTemplate and row.status != "missing:no_participle_donor"]
            remaining = [row for row in comparable if statusFamily(row.status) == "missing"]
            emit(f"  as the status doc counts (templated lemmas, no_participle_donor left out): "
                 f"missing from Mixte {len(comparable):,} slots / {len({row.lemme for row in comparable}):,} lemmas, "
                 f"after synthesis {len(remaining):,} / {len({row.lemme for row in remaining}):,}")
        emit()


def writeCensus(rows: list[SlotRow], path: str | Path) -> None:
    with open(path, "w", encoding="utf-8", newline="") as tsvFile:
        writer = csv.writer(tsvFile, delimiter="\t", lineterminator="\n")
        writer.writerow(OUT_HEADER)
        for row in rows:
            writer.writerow((row.lemme, row.cgram, row.slot, row.status, row.ortho))


def runCensus(mixtePath: str | Path, syntheticPath: str | Path, excludedSlotsPath: str | Path = EXCLUDED_SLOTS_PATH,
              excludedWordsPath: str = "excluded_words.txt",
              skipReasonsPath: str | Path | None = None) -> list[SlotRow]:
    excludedWords = loadExcludedWords(excludedWordsPath)
    mixteRows, syntheticRows = pipelineRows([readRawRows(mixtePath), readRawRows(syntheticPath)], excludedWords)
    excluded = loadExcludedSlots(excludedSlotsPath)
    verbisteTemplates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
    verbExceptions = loadVerbModelExceptions(VERB_EXCEPTIONS_PATH)
    conjugationTemplates = parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
    nomAdjExceptions = loadNomAdjModelExceptions(NOMADJ_EXCEPTIONS_PATH)
    rows = verbCensus(mixteRows, syntheticRows, verbisteTemplates, verbExceptions, conjugationTemplates, excluded,  # type: ignore[arg-type]
                      loadSkipReasons(skipReasonsPath) if skipReasonsPath is not None else None)
    rows += nomAdjCensus(mixteRows, syntheticRows, excluded, nomAdjExceptions)  # type: ignore[arg-type]
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mixte", default=MIXTE_PATH)
    parser.add_argument("--synthetic", default=SYNTHETIC_PATH)
    parser.add_argument("--out", default=OUT_PATH)
    parser.add_argument("--skip-reasons", default=SKIP_REASONS_PATH,
                        help="the generator's synthetic_skip_reasons.tsv, refining the causes of the missing VER slots "
                        "(only meaningful for the Synthetic file it was written with; ignored when absent)")
    args = parser.parse_args()
    rows = runCensus(args.mixte, args.synthetic, skipReasonsPath=args.skip_reasons)
    writeCensus(rows, args.out)
    summarize(rows)
    print(f"wrote {args.out} ({len(rows):,} rows)")


if __name__ == "__main__":
    main()
