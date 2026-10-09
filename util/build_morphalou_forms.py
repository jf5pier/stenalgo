"""
Distills the external Morphalou 3.1 CSV (~670 MB, gitignored) into the small committed resource
resources/morphalouNomAdjForms.tsv, so that Synthetic Lexicon Building (S2.2) is a function of
committed files only: util/generateMissingNomAdjForms.py reads the TSV when the CSV is absent.

Only what the generator can ever ask for is kept: the NOM/ADJ (lemme, slot) pairs that the mixed
lexicon (LexiqueMixte.tsv) lacks, with every Morphalou spelling for them. Synthetic rows only fill
slots Mixte lacks, so this is a superset of the queries of any regeneration.

Morphalou 3.1, ATILF (CNRS & Universite de Lorraine), licence LGPL-LR; attribution in
resources/morphalouNomAdjForms.NOTICE.md.

Run: python -m util.build_morphalou_forms [--morphalou PATH] [--output PATH]   (rare: after a Mixte lemma-set change)
"""
import argparse
import os

from src.nomAdjParadigm import (
    MorphalouIndex,
    attestedSlots,
    loadMorphalouIndex,
    loadWords,
    missingSlots,
    writeMorphalouForms,
)
from src.word import Word

MORPHALOU_PATH_DEFAULT = "morphalou/Morphalou3.1_CSV.csv"
OUTPUT_DEFAULT = "resources/morphalouNomAdjForms.tsv"
LEXIQUE_MIXTE_PATH = "resources/LexiqueMixte.tsv"


def distill(index: MorphalouIndex, mixteWords: list[Word]) -> MorphalouIndex:
    wanted: dict[tuple[str, str], set[tuple[str, str]]] = {}
    for slotMap in attestedSlots(mixteWords).values():
        word = next(iter(slotMap.values()))
        wanted[(word.lemme, word.gramCat.name)] = set(missingSlots(slotMap, word.gramCat))
    distilled: MorphalouIndex = {}
    for key, slots in index.items():
        keep = {slot: orthos for slot, orthos in slots.items() if slot in wanted.get(key, set())}
        if keep:
            distilled[key] = keep
    return distilled


def main() -> None:
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--morphalou", default=MORPHALOU_PATH_DEFAULT)
    parser.add_argument("--output", default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    index = loadMorphalouIndex(args.morphalou)
    distilled = distill(index, loadWords([LEXIQUE_MIXTE_PATH]))
    rows = writeMorphalouForms(distilled, args.output)
    print(f"{len(index)} Morphalou NOM/ADJ lemma groups -> {len(distilled)} kept, {rows} rows, "
          f"{os.path.getsize(args.output) / 1024:.0f} KB in {args.output}")


if __name__ == "__main__":
    main()
