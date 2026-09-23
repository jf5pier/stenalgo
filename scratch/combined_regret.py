"""
Proof script for the star/hash regret headline (docs/specs/star-hash-marking.md §2):
pool bucket 2 (cross-category clash, same lemme) + bucket 3 (cross-lemma collisions,
different lemmas) into one population, layer in the frequency-ratio rule (R4,
extreme-ratio exemption) and the homograph exemption (R1), and measure the gap% of the
adopted rule stack against the per-pair optimum -- reproducing the ~0.5% gap and the
10x-threshold choice (0.526% at design time, 0.499% on a fresh rebuild, 2026-09-20).
Read-only: loads the pickles, writes nothing.

Run: python scratch/combined_regret.py
"""
import itertools
import json
import os
import pickle
import sys
from collections import defaultdict

sys.path.insert(0, os.getcwd())

from dictionary import Dictionary  # noqa: E402
sys.modules["__main__"].Dictionary = Dictionary  # type: ignore[attr-defined]

from src.ambiguitychecker import (  # noqa: E402
    buildKeypressGroupToWords, buildWordsByOrthoLemme, buildWordToStrokes,
    detectCrossCategoryClash, realizeKeypressGroupsAsExtraStroke,
)
from src.grammar import Syllable  # noqa: E402
from src.keyboard import Starboard  # noqa: E402

with open("Dictionary.pickle", "rb") as pfile:
    _dictionary = pickle.load(pfile)
    Syllable.allPhonemeCol = pickle.load(pfile)
    Syllable.phonemeColByPart = pickle.load(pfile)
    Syllable.biphonemeColByPart = pickle.load(pfile)
    Syllable.multiphonemeColByPart = pickle.load(pfile)

with open("FirstTheory.pickle", "rb") as pfile:
    theory = pickle.load(pfile)

allWords = [w for words in theory.values() for w in words]
starboard = Starboard.fromJSONFile("starboard3h.json")

with open("keypress_groups.json", encoding="utf-8") as f:
    keypressGroups = json.load(f)
markersByKeypress = {int(g): frozenset(m) for g, m in keypressGroups["markersByKeypress"].items()}
with open("resolved_press_sets.json", encoding="utf-8") as f:
    resolvedGroups = json.load(f)

wordToStrokes = buildWordToStrokes(theory)
wordsByOrthoLemme = buildWordsByOrthoLemme(theory)
groupToWords = buildKeypressGroupToWords(resolvedGroups, markersByKeypress, wordToStrokes, wordsByOrthoLemme)
assignment = realizeKeypressGroupsAsExtraStroke(groupToWords, theory, starboard)

# ---------- Build bucket 2 pairs (paradigm-level, as in cross_category_regret.py) ----------
byLemme = defaultdict(lambda: defaultdict(list))
for w in allWords:
    byLemme[w.lemme][w.lemmeGramCat].append(w)

clashLemmas = detectCrossCategoryClash(allWords)
bucket2_raw = []
for lemme in clashLemmas:
    groups = list(byLemme[lemme].items())
    for (lgcA, wordsA), (lgcB, wordsB) in itertools.combinations(groups, 2):
        bucket2_raw.append({
            "source": "b2", "lemme": lemme,
            "catA": wordsA[0].gramCat.name, "catB": wordsB[0].gramCat.name,
            "freqA": sum(w.frequency for w in wordsA), "freqB": sum(w.frequency for w in wordsB),
            "orthoA_set": {w.ortho for w in wordsA}, "orthoB_set": {w.ortho for w in wordsB},
            "orthoA": sorted({w.ortho for w in wordsA}), "orthoB": sorted({w.ortho for w in wordsB}),
        })

print(f"Bucket 2 raw pairs: {len(bucket2_raw)}")

# ---------- Build bucket 3 pairs (word-level, as in cross_lemma_regret.py) ----------
bucket3_raw = []
for w1, w2 in assignment.crossLemmaCollisions:
    bucket3_raw.append({
        "source": "b3", "lemmeA": w1.lemme, "lemmeB": w2.lemme,
        "catA": w1.gramCat.name, "catB": w2.gramCat.name,
        "freqA": w1.frequency, "freqB": w2.frequency,
        "orthoA": w1.ortho, "orthoB": w2.ortho,
    })
print(f"Bucket 3 raw pairs: {len(bucket3_raw)}")

# ---------- Dedup check across buckets ----------
b3_same_lemme = [p for p in bucket3_raw if p["lemmeA"] == p["lemmeB"]]
print(f"Bucket-3 pairs with lemmeA==lemmeB (would overlap bucket 2 definition): {len(b3_same_lemme)}")

# ---------- Rule 2: drop homograph pairs ----------
b2_dropped = [p for p in bucket2_raw if p["orthoA_set"] == p["orthoB_set"]]
b2_partial_overlap = [p for p in bucket2_raw if p["orthoA_set"] != p["orthoB_set"] and (p["orthoA_set"] & p["orthoB_set"])]
b2_kept = [p for p in bucket2_raw if p not in b2_dropped]
print(f"\nRule 2 (bucket 2, paradigm-level, conservative -- drop only if ortho SETS fully equal):")
print(f"  fully-homograph paradigm pairs dropped: {len(b2_dropped)}  "
      f"(volume removed: {sum(p['freqA']+p['freqB'] for p in b2_dropped):.1f})")
print(f"  partial-overlap pairs (kept, NOT dropped -- some forms homograph, some not, approximation caveat): "
      f"{len(b2_partial_overlap)}")

b3_dropped = [p for p in bucket3_raw if p["orthoA"] == p["orthoB"]]
b3_kept = [p for p in bucket3_raw if p["orthoA"] != p["orthoB"]]
print(f"\nRule 2 (bucket 3, word-level, exact): dropped {len(b3_dropped)} homograph pairs "
      f"(volume removed: {sum(p['freqA']+p['freqB'] for p in b3_dropped):.1f})")

nom_pro_per = [p for p in bucket3_raw if tuple(sorted([p["catA"], p["catB"]])) == ("NOM", "PRO:per")]
print(f"\nNOM/PRO:per outlier check: {len(nom_pro_per)} pair(s)")
for p in nom_pro_per:
    print(f"  {p['orthoA']!r}({p['catA']}, freq={p['freqA']:.1f}) vs {p['orthoB']!r}({p['catB']}, freq={p['freqB']:.1f}) "
          f"-- homograph={p['orthoA']==p['orthoB']}")

# ---------- Pool remaining pairs (uniform shape) ----------
pool = []
for p in b2_kept:
    pool.append({"catA": p["catA"], "catB": p["catB"], "freqA": p["freqA"], "freqB": p["freqB"],
                 "orthoA": p["orthoA"], "orthoB": p["orthoB"], "source": "b2"})
for p in b3_kept:
    pool.append({"catA": p["catA"], "catB": p["catB"], "freqA": p["freqA"], "freqB": p["freqB"],
                 "orthoA": p["orthoA"], "orthoB": p["orthoB"], "source": "b3"})
print(f"\nPooled population after Rule 2: {len(pool)} pairs "
      f"(b2 kept={len(b2_kept)}, b3 kept={len(b3_kept)})")

EPS = 1e-9
def ratio(p):
    lo = min(p["freqA"], p["freqB"])
    hi = max(p["freqA"], p["freqB"])
    return hi / max(lo, EPS)

# ---------- Rule 1 sensitivity ----------
for thresh in (10, 100):
    qualifying = [p for p in pool if ratio(p) >= thresh]
    qvol = sum(p["freqA"] + p["freqB"] for p in qualifying)
    # regret these pairs WOULD have contributed under the old categorical-only approach
    # (approximate: regret vs today's per-type direction is computed later; here just
    # report how much of the *raw* per-pair max-min gap they represent)
    qregret_proxy = sum(abs(p["freqA"] - p["freqB"]) for p in qualifying)
    total_vol = sum(p["freqA"] + p["freqB"] for p in pool)
    print(f"\nRule 1 @ ratio>={thresh}x: {len(qualifying)} pairs qualify "
          f"({qvol:.1f} volume = {qvol/total_vol*100:.1f}% of pooled volume); "
          f"their own freqA-freqB gap sums to {qregret_proxy:.1f}")

RULE1_THRESHOLD = 10
rule1_exempt = [p for p in pool if ratio(p) >= RULE1_THRESHOLD]
residual = [p for p in pool if ratio(p) < RULE1_THRESHOLD]
rule1_optimum_contrib = sum(min(p["freqA"], p["freqB"]) for p in rule1_exempt)
print(f"\n=== Using Rule 1 threshold = {RULE1_THRESHOLD}x for headline numbers ===")
print(f"Rule-1-exempted pairs: {len(rule1_exempt)}  (contribute optimum={rule1_optimum_contrib:.1f} to grand total, 0 regret)")
print(f"Residual population for categorical-rule fitting: {len(residual)} pairs")

# ---------- Split residual into same-category vs different-category ----------
sameCat = [p for p in residual if p["catA"] == p["catB"]]
diffCat = [p for p in residual if p["catA"] != p["catB"]]
print(f"\nResidual same-category (no categorical signal): {len(sameCat)} pairs")
print(f"Residual different-category: {len(diffCat)} pairs")

sameCat_volume = sum(p["freqA"] + p["freqB"] for p in sameCat)
sameCat_optimum = sum(min(p["freqA"], p["freqB"]) for p in sameCat)
print(f"Same-category residual: volume={sameCat_volume:.1f}  cost(=optimum, per-pair-optimal)={sameCat_optimum:.1f}")

# ---------- Categorical rule table on residual different-category pairs ----------
byType = defaultdict(list)
for p in diffCat:
    key = tuple(sorted([p["catA"], p["catB"]]))
    byType[key].append(p)

print(f"\n=== Categorical-rule table on residual different-category pairs ({len(byType)} types) ===")
grand_volume = grand_optimum = grand_best = 0.0
grand_aligned = grand_misaligned = 0
per_type = {}
for catpair, plist in sorted(byType.items(), key=lambda kv: -len(kv[1])):
    c1, c2 = catpair
    volume = sum(p["freqA"] + p["freqB"] for p in plist)
    optimum = sum(min(p["freqA"], p["freqB"]) for p in plist)

    def cost_marking(cat_to_mark, plist=plist):
        return sum(p["freqA"] if p["catA"] == cat_to_mark else p["freqB"] for p in plist)

    cost1, cost2 = cost_marking(c1), cost_marking(c2)
    best_dir = c1 if cost1 <= cost2 else c2
    best_cost = min(cost1, cost2)
    gap = best_cost - optimum
    gap_pct = (gap / volume * 100) if volume > 0 else 0.0

    aligned = misaligned = 0
    for p in plist:
        marked = p["freqA"] if p["catA"] == best_dir else p["freqB"]
        other = p["freqB"] if p["catA"] == best_dir else p["freqA"]
        (aligned := aligned + 1) if marked <= other else (misaligned := misaligned + 1)  # noqa

    per_type[catpair] = {"plist": plist, "best_dir": best_dir, "best_cost": best_cost,
                          "optimum": optimum, "volume": volume}
    print(f"  {c1}/{c2}: n={len(plist)}  mark-{c1}={cost1:.1f}  mark-{c2}={cost2:.1f}  "
          f"best=mark-{best_dir} (cost={best_cost:.1f})  optimum={optimum:.1f}  volume={volume:.1f}  "
          f"gap={gap:.1f} ({gap_pct:.2f}%)  aligned={aligned}  misaligned={misaligned}")

    grand_volume += volume
    grand_optimum += optimum
    grand_best += best_cost
    grand_aligned += aligned
    grand_misaligned += misaligned

print(f"\nDiff-category residual TOTALS: volume={grand_volume:.1f}  optimum={grand_optimum:.1f}  "
      f"best_cost={grand_best:.1f}  gap={grand_best-grand_optimum:.1f} "
      f"({(grand_best-grand_optimum)/grand_volume*100 if grand_volume else 0:.2f}%)  "
      f"aligned={grand_aligned}  misaligned={grand_misaligned}")

# ADJ/NOM resolution
adjnom = per_type.get(("ADJ", "NOM"))
if adjnom:
    print(f"\nADJ/NOM pooled resolution: best_dir=mark-{adjnom['best_dir']}  "
          f"(cost={adjnom['best_cost']:.1f} vs optimum={adjnom['optimum']:.1f}, n={len(adjnom['plist'])})")

# ---------- Consistency check ----------
edges = set()
for catpair, res in per_type.items():
    c1, c2 = catpair
    marked = res["best_dir"]
    winner = c2 if marked == c1 else c1
    edges.add((winner, marked))

nodes = set()
for w, l in edges:
    nodes.add(w); nodes.add(l)

def has_cycle(edges, nodes):
    graph = defaultdict(list)
    for w, l in edges:
        graph[w].append(l)
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in nodes}
    cyc = []
    def dfs(n):
        color[n] = GRAY
        for nxt in graph[n]:
            if color[nxt] == GRAY:
                cyc.append((n, nxt)); return True
            if color[nxt] == WHITE and dfs(nxt):
                return True
        color[n] = BLACK
        return False
    for n in list(nodes):
        if color[n] == WHITE and dfs(n):
            return True, cyc
    return False, []

cyc, cyc_edges = has_cycle(edges, nodes)
print(f"\n=== Consistency check (residual, pooled) ===")
print(f"Edges (winner>loser): {sorted(edges)}")
if cyc:
    print(f"NOT CONSISTENT with single linear ranking -- cycle: {cyc_edges}")
else:
    graph = defaultdict(set)
    indeg = defaultdict(int)
    for w, l in edges:
        graph[w].add(l)
        indeg[l] += 1
        indeg.setdefault(w, indeg.get(w, 0))
    order = []
    remaining = set(nodes)
    avail = [n for n in nodes if indeg.get(n, 0) == 0]
    while avail:
        n = avail.pop()
        order.append(n)
        remaining.discard(n)
        for m in list(graph[n]):
            indeg[m] -= 1
            if indeg[m] == 0 and m in remaining:
                avail.append(m)
    if remaining:
        order.extend(remaining)
        print(f"PARTIAL order only, disconnected/unordered remainder: {remaining}")
    print(f"CONSISTENT single linear ranking (canonical-first): {order}")

# ---------- Grand totals ----------
b2_dropped_vol = sum(p["freqA"] + p["freqB"] for p in b2_dropped)
b3_dropped_vol = sum(p["freqA"] + p["freqB"] for p in b3_dropped)
total_dropped_vol = b2_dropped_vol + b3_dropped_vol

combined_volume = rule1_optimum_contrib * 0  # placeholder, recompute properly below
counted_volume = sum(p["freqA"] + p["freqB"] for p in pool)  # after rule 2, before rule 1
overall_optimum = sum(min(p["freqA"], p["freqB"]) for p in pool)  # true optimum over Rule-2-surviving pool
overall_achievable = rule1_optimum_contrib + sameCat_optimum + grand_best
overall_gap = overall_achievable - overall_optimum
overall_gap_pct = overall_gap / counted_volume * 100 if counted_volume else 0.0

print(f"\n=== GRAND TOTAL (Rule 2 applied first, Rule 1 @ {RULE1_THRESHOLD}x, categorical rule on residual diff-cat, "
      f"per-pair-optimal on residual same-cat) ===")
print(f"Volume dropped entirely by Rule 2 (homographs, not counted at all): {total_dropped_vol:.1f} "
      f"(b2={b2_dropped_vol:.1f}, b3={b3_dropped_vol:.1f})")
print(f"Counted volume (post Rule 2): {counted_volume:.1f}")
print(f"True optimum over counted volume: {overall_optimum:.1f}")
print(f"Achievable cost (rule1-exempt optimum {rule1_optimum_contrib:.1f} + sameCat-residual optimum "
      f"{sameCat_optimum:.1f} + diffCat-residual best-rule {grand_best:.1f}) = {overall_achievable:.1f}")
print(f"GAP = {overall_gap:.1f}  =>  {overall_gap_pct:.3f}% of counted volume")
print(f"\nFor comparison, prior single-bucket headline gaps (no rule 1/2): bucket2 alone=2.69%, bucket3 alone=3.23% (overall)")

# ---------- Top 10 residual regret pairs ----------
all_regrets = []
for catpair, res in per_type.items():
    best_dir = res["best_dir"]
    for p in res["plist"]:
        marked = p["freqA"] if p["catA"] == best_dir else p["freqB"]
        other = p["freqB"] if p["catA"] == best_dir else p["freqA"]
        regret = max(0.0, marked - other)
        if regret > 0:
            all_regrets.append((regret, p, best_dir))
all_regrets.sort(key=lambda t: -t[0])
print(f"\n=== Final top 10 residual regret pairs (after Rule 1 + Rule 2 + categorical rule) ===")
for regret, p, best_dir in all_regrets[:10]:
    print(f"  [{p['source']}] {p['catA']}({p['orthoA']}, freq={p['freqA']:.1f}) vs "
          f"{p['catB']}({p['orthoB']}, freq={p['freqB']:.1f})  marks={best_dir}  regret={regret:.2f}")
print(f"\n(total residual misaligned pairs: {len(all_regrets)}; total residual regret: {sum(r for r,_,_ in all_regrets):.1f})")
