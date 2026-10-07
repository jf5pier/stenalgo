"""Variant (2026-10-06): the lemma carries the mark only for m/f/s/p families (non-verbs, past participles); conjugated verb forms are
single-word nodes ranked as today. Dry run 2 (2026-10-06): the lemma-level mark as a colouring. Nodes = lemmas (bare `lemme`), merged when two
nodes share a spelling in one cluster (homograph merge) or form a reform doublet. Edge = two nodes with different
spellings sharing one unmarked final stroke. Greedy by lemma frequency; code index r: 0 (), 1 *, 2 #, 3 *#, r>=4 *# x (r-2).
Frequency-only (the R4-R6 rule stack is not modelled). Primary entries only."""
import pickle
from collections import defaultdict, Counter
import sys
from src.ambiguitychecker import loadReform1990DoubletPairs, decideStarHashMark
from src.keyboard import canonicalizeStrokes

with open("DisambiguatedTheory.pickle", "rb") as f:
    _, _, theory, w2s, _ = pickle.load(f)
RES = {10, 15}
doublets = loadReform1990DoubletPairs()

def unmarked(w):
    s = theory[w][0]; last = len(w2s[w]) - 1
    out = [tuple(k for k in st if k not in RES) if i == last else st for i, st in enumerate(s)]
    return canonicalizeStrokes(tuple(st for i, st in enumerate(out) if not (i > last and st and all(k in RES for k in s[i]))))

def codeIndex(w):
    s = theory[w][0]; last = len(w2s[w]) - 1
    first = {k for k in s[last] if k in RES}
    trailing = [st for st in s[last + 1:] if st and all(k in RES for k in st)]
    if not first and not trailing: return 0
    if len(first) == 1 and not trailing: return 1 if 10 in first else 2
    return 2 + len(trailing) + (1 if first else 0) if (len(first) == 2 or trailing) else 1
def cost(idx): return 0 if idx == 0 else (1 if idx <= 2 else 2)  # keys pressed beyond the word: */# = 1, *# = 2 (+1 stroke per escalation ignored)

byStroke = defaultdict(list)
for w in theory: byStroke[unmarked(w)].append(w)
clusters = [ws for ws in byStroke.values() if len({w.lemmeGramCat for w in ws}) >= 2 and len({w.ortho for w in ws}) >= 2]
print("S7 clusters:", len(clusters))

import os
def nodeKey(w):
    if os.environ.get("NOFAMILY"): return ("W", w.ortho, w.lemmeGramCat)
    cat = str(w.gramCat)
    if cat.endswith("VER") or cat.endswith("AUX"):
        if w.gender is not None and "par:pas" in str(w.infoVerb): return ("PP", w.lemme)
        return ("W", w.ortho, w.lemmeGramCat)
    return ("L", w.lemme, cat)
parent = {}
def find(x):
    parent.setdefault(x, x)
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
def union(a, b): parent[find(a)] = find(b)
for ws in clusters:
    byOrtho = defaultdict(list)
    for w in ws: byOrtho[w.ortho].append(w.lemme)
    keyByOrtho = defaultdict(list)
    for w in ws: keyByOrtho[w.ortho].append(nodeKey(w))
    for keys in keyByOrtho.values():
        for k in keys[1:]: union(keys[0], k)
    for x in ws:
        for y in ws:
            if x.lemme < y.lemme and frozenset({x.lemme, y.lemme}) in doublets: union(nodeKey(x), nodeKey(y))
freq = Counter(); size = Counter()
for w in theory:
    n = find(nodeKey(w)); freq[n] += w.frequency; size[n] += 1
edges = defaultdict(set)
for ws in clusters:
    nodes = {}
    for w in ws: nodes.setdefault(find(nodeKey(w)), set()).add(w.ortho)
    for a in nodes:
        for b in nodes:
            if a != b: edges[a].add(b)
print("nodes in a conflict:", len(edges), " merged nodes (>1 lemma):", sum(1 for n in edges if sum(1 for l in parent if find(l) == n) > 1) if False else "-")
# R3-R6 (decideStarHashMark) on every clashing form pair of an edge; node score = weighted wins - losses (Copeland).
MODE = sys.argv[1] if len(sys.argv) > 1 else "rules"
score = Counter(); edgeVotes = defaultdict(float)  # (a,b) -> weight where a is the more canonical
for ws in clusters:
    for i, x in enumerate(ws):
        for y in ws[i + 1:]:
            a, b = find(nodeKey(x)), find(nodeKey(y))
            if a == b or x.ortho == y.ortho: continue
            marked = decideStarHashMark(x, y, doubletPairs=doublets)
            if marked is None: continue
            wt = 1.0 + min(x.frequency, y.frequency)
            win, lose = (b, a) if marked is x else (a, b)   # `marked` loses
            score[win] += wt; score[lose] -= wt
            edgeVotes[(win, lose)] += wt
from functools import cmp_to_key
rep = {}
for w in theory:
    n = find(nodeKey(w))
    if n not in rep or w.frequency > rep[n].frequency: rep[n] = w
def cmpNodes(a, b):   # the rule stack on the two lemmas' dominant forms; no signal -> frequency
    m = decideStarHashMark(rep[a], rep[b], doubletPairs=doublets) if rep[a].ortho != rep[b].ortho else None
    if m is rep[a]: return 1
    if m is rep[b]: return -1
    return -1 if freq[a] >= freq[b] else 1
if MODE == "freq": order = lambda n: -freq[n]
elif MODE == "rules": order = lambda n: (-score[n], -freq[n])
else: order = cmp_to_key(cmpNodes)
assign = {}
for n in sorted(edges, key=order):
    used = {assign[m] for m in edges[n] if m in assign}
    r = 0
    while r in used: r += 1
    assign[n] = r

cur = Counter(); new = Counter(); curMass = newMass = 0.0; changed = 0; totalMass = sum(w.frequency for w in theory)
newMassForm = 0.0
for w in theory:
    c = codeIndex(w); cur[c] += 1; curMass += w.frequency * cost(c)
    n = find(nodeKey(w)); r = assign.get(n, 0); new[r] += 1; newMass += w.frequency * cost(r)
    if r != c: changed += 1
print("code distribution of forms  current:", dict(sorted(cur.items())))
print("code distribution of forms  lemma-level:", dict(sorted(new.items())))
print("mark-key mass (sum freq x extra keys) current %.0f  lemma-level %.0f  (of %.0f word mass)" % (curMass, newMass, totalMass))
print("forms whose code changes:", changed, "of", len(theory))
print("lemma nodes by code:", dict(sorted(Counter(assign.values()).items())), " escalated (>=4):", sum(1 for v in assign.values() if v >= 4))
top = sorted((n for n in assign if assign[n] >= 4), key=lambda n: -freq[n])[:10]
bad = tot = 0.0
for (win, lose), wt in edgeVotes.items():
    tot += wt
    if assign[win] > assign[lose]: bad += wt   # the rule's canonical side got the higher (more marked) code
print("%s ordering: weight of edges where the rule-canonical lemma got the MORE marked code: %.1f%%" % (MODE, 100 * bad / tot))
print("top escalated:", [(n, assign[n], round(freq[n])) for n in top])
import os, json
if os.environ.get("DUMP"):
    json.dump({w.ortho + "|" + w.lemmeGramCat: [codeIndex(w), assign.get(find(nodeKey(w)), 0), round(w.frequency, 1)] for w in theory},
              open(os.environ["DUMP"], "w"), ensure_ascii=False)
