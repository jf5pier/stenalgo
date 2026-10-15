"""Number of words and summed frequency (per million, films+books as Word.frequency) (distinct spellings) whose S7 stenogram contains each phoneme (and each onset-only / coda-only variant)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import optexp_phoneme_information as m
from optexp_common import OUT
m.prepare()
with open(os.path.join(OUT, "phoneme_word_counts.tsv"), "w") as f:
    f.write("phoneme\tspellings\treadings\tfreq\n")
    for ph, idx in sorted(m.G["byPh"].items()):
        f.write(f"{ph}\t{len({m.G['wOrtho'][i] for i in idx})}\t{len(idx)}\t{sum(m.G['wFreq'][i] for i in idx):.1f}\n")
