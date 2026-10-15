"""Turns out/phoneme_information_raw.tsv into the phoneme x stage table and a ranking (collisions added by removing a phoneme)."""
import csv, os
O = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
rows = list(csv.DictReader(open(os.path.join(O, "phoneme_information_raw.tsv")), delimiter="\t"))
stages = ["S5_phonetic", "S6_feature", "S7_marks", "merged", "plus_affix", "plus_briefs"]
d = {(r["phoneme"], r["stage"]): r for r in rows}
cnt = {r["phoneme"]: f'{r["spellings"]} / {float(r["freq"]):.0f}' for r in csv.DictReader(open(os.path.join(O, "phoneme_word_counts.tsv")), delimiter="\t")}
def g(p, s, k): return float(d[(p, s)][k])
phs = sorted({r["phoneme"] for r in rows} - {"(intact)"}, key=lambda p: g(p, "plus_briefs", "excessFreq") - g("(intact)", "plus_briefs", "excessFreq"))
# keyboard-complexity drop (out/phoneme_cost.tsv from optexp_phoneme_cost.py): sort by the last column when present
cp = os.path.join(O, "phoneme_cost.tsv")
cost = {r["phoneme"]: r for r in csv.DictReader(open(cp), delimiter="\t")} if os.path.exists(cp) else {}
base = float(dict(l.split("\t") for l in open(os.path.join(O, "phoneme_cost_baseline.tsv")).read().split("\n") if l)["meanCostPerWord"]) if cost else 0.0
if cost:
    phs = sorted(phs, key=lambda p: float(cost[p]["keptCost"]))
with open(os.path.join(O, "phoneme_information_by_stage.tsv"), "w") as f:
    f.write("phoneme\t" + "\t".join(f"{s}:{k}" for s in stages for k in ("dGroups", "dWords", "dExcessFreq")) + "\twordsEmptied(merged)\n")
    for p in phs:
        f.write(p + "\t" + "\t".join(str(round(g(p, s, k) - g("(intact)", s, k), 1)) for s in stages
                                      for k in ("groups", "words", "excessFreq")) + f"\t{d[(p,'merged')]['wordsEmptied']}\n")
L = ["# Collisions added by removing one phoneme (existing outputs only)", "",
     "Intact: " + ", ".join(f"{s} {int(g('(intact)', s, 'groups'))} groups" for s in stages), "",
     "Cells: extra colliding groups / extra frequency mass (film freq per million, non-top claimants) vs intact."
     + (" Sorted by increasing last column." if cost else " Sorted by increasing plus_briefs mass."), "",
     *(["Last two columns: drop in keyboard complexity when the phoneme is removed from the words of the final theory (merged + affix + briefs), "
        "each word typed with its most abbreviated outline (fewest strokes, then lowest `getChordCost`). Unit: % of the frequency-weighted mean chord cost per word "
        f"(intact {base:.1f}). **all removed** = removed from every word, collisions ignored; **conflicts kept** = same, but the spellings whose typed outline "
        "then collides with another spelling keep the phoneme (repeated until no collision is left; in brackets, the number of spellings kept). "
        "Affix / brief outlines are rewritten stroke by stroke (heuristic). Script: `optexp_phoneme_cost.py`.", ""] if cost else []),
     "| phoneme | words with it / their frequency (S7) | " + " | ".join(stages) + (" | cost drop, all removed | cost drop, conflicts kept (spellings kept) |" if cost else " |"),
     "|---|---|" + "---|" * len(stages) + ("---|---|" if cost else "")]
for p in phs:
    L.append(f"| {p} | {cnt[p]} | " + " | ".join(f"{int(g(p,s,'groups')-g('(intact)',s,'groups')):+d} / {g(p,s,'excessFreq')-g('(intact)',s,'excessFreq'):+.0f}" for s in stages)
             + (f" | {100 * float(cost[p]['allCost']) / base:.3f}% | {100 * float(cost[p]['keptCost']) / base:.3f}% ({cost[p]['reverted']}) |" if cost else " |"))
open(os.path.join(O, "phoneme_information.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L))

# ---- fusion section (out/phoneme_fusion.tsv from optexp_phoneme_fusion.py)
fp = os.path.join(O, "phoneme_fusion.tsv")
if os.path.exists(fp):
    fr = list(csv.DictReader(open(fp), delimiter="\t"))
    F = ["", "## Fusing a rare phoneme with another phoneme of the same part (same keys)", "",
         "Rare = phoneme variant whose removal creates, at S7, fewer than 100 colliding groups (the collision count of the table above) or less than 1000 colliding frequency (rows marked ★ meet the literal 100 / 100 rule; the 1000 frequency bound adds the others). "
         "Evaluated on the final theory (merged + affix + briefs, 0 collisions when intact). Each cell: "
         "**rare→partner** (every rare phoneme typed with the partner's keys) · **partner→rare** (every partner typed with the rare phoneme's keys); "
         "each as extra colliding groups / extra frequency mass. Feature, mark and merge keys are not re-decided. "
         "`0 / 0` on both sides = the two already share a key.", ""]
    for part in ("onset", "nucleus", "coda"):
        sub = [r for r in fr if r["part"] == part]
        if not sub:
            continue
        partners = sorted({r["partner"] for r in sub})
        rare_ = sorted({r["phoneme"] for r in sub})
        F += [f"### {part}", "", "| rare \\ partner | " + " | ".join(partners) + " |", "|---|" + "---|" * len(partners)]
        for p in rare_:
            cells = []
            for q in partners:
                r = next((x for x in sub if x["phoneme"] == p and x["partner"] == q), None)
                cells.append("" if r is None else f"{r['P_to_Q_groups']} / {float(r['P_to_Q_mass']):.0f} · {r['Q_to_P_groups']} / {float(r['Q_to_P_mass']):.0f}")
            star = " ★" if next(x for x in sub if x["phoneme"] == p)["literal"] == "1" else ""
            F.append(f"| {p}/{part}{star} ({cnt.get(p + '/' + part, cnt.get(p))}) | " + " | ".join(cells) + " |")
        F.append("")
    open(os.path.join(O, "phoneme_information.md"), "a").write("\n".join(F) + "\n")
