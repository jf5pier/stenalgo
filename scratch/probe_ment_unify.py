"""Probe for the -ment / ·°ment orphan-pair problem (RESUME_2026-09-27 §3).

Answers, on the real lexicon:
  [1] how many lattice children silently OVERWRITE a pre-growth pool node with the same key;
  [2] how many same-signature (position, k, tail, rest) A7-pooled vs lattice-grown pairs exist;
  [3] the -ment pair in detail: carrier-set relations + WHY they differ (stem attestation);
  [4] score probe: two separate rules vs one unified rule (word-once-credited objective).

Measurement only. ~3 min. Run: PYTHONPATH=. env/bin/python scratch/probe_ment_unify.py
"""
import dataclasses
import time

from src import affixes as A
from src import affixrules as R
from src import affixbinding as B
from util.affix_scan import loadStarboard, loadRecords

sb = loadStarboard()
recs = loadRecords(sb, False)
seedPairs, _ = A.loadSeeds()

captured: dict = {}
orig = A.growAffixesLattice

def wrap(cands):
    out = orig(cands)
    captured["pre"] = dict(cands)
    return out

A.growAffixesLattice = wrap
t0 = time.time()
pool = A.buildCandidates(recs, seedPairs, legacy=False)
pre = captured["pre"]
print(f"part A {time.time() - t0:.0f}s; pre-growth pool {len(pre)}, final pool {len(pool)}")

def cset(c):
    return {(x.rec.idx, x.start, x.span) for x in c.carriers}

def a7Sig(c):
    """Signature of an A7-pooled seed node: (position, k, tailPhono, 'onset', rest)."""
    if c.grownFromKey is not None or c.rootKey is not None or c.k < 2:
        return None
    if not c.isGeneralized or c.slots:
        return None
    syls = c.phono.split(".")
    if c.position == A.SUFFIX:
        return (c.position, c.k, ".".join(syls[1:]), "onset", syls[0])
    return (c.position, c.k, ".".join(syls[:-1]), "onset", syls[-1])

def grownSig(c):
    """Signature of a one-level lattice onset child: same shape, tail = parent's phono."""
    if c.grownFromKey is None or len(c.slots) != 1 or c.slots[0].kind != "onset":
        return None
    return (c.position, c.k, c.grownFromKey[2], "onset", c.slots[0].value)

# ── [1] key-collision overwrites ─────────────────────────────────────────────
overwrites = [k for k in pool if k in pre and pre[k] is not pool[k]]
print(f"\n[1] grown children overwriting a same-key pre-growth pool node: {len(overwrites)}")
for k in sorted(overwrites, key=lambda k: -len(pool[k].carriers))[:12]:
    p, n = pre[k], pool[k]
    sp, sn = cset(p), cset(n)
    print(f"  {k}  pre: {len(sp)} carriers (seed={p.isSeed}, variants={len(p.variants)})"
          f"  -> child: {len(sn)} carriers, lost {len(sp - sn)}, gained {len(sn - sp)}")

# ── [2] same-signature A7 vs grown conflicts ─────────────────────────────────
bySig: dict = {}
for k, c in pool.items():
    s = a7Sig(c)
    if s:
        bySig.setdefault(s, {})["a7"] = c
for k, c in pool.items():
    s = grownSig(c)
    if s:
        bySig.setdefault(s, {})["grown"] = c
conflicts = {s: d for s, d in bySig.items() if "a7" in d and "grown" in d}
a7Only = [s for s, d in bySig.items() if "a7" in d and "grown" not in d]
print(f"\n[2] same-signature conflicts (A7 node AND grown node for one (pos,k,tail,rest)): "
      f"{len(conflicts)};  A7 nodes with no grown twin (legit roots): {len(a7Only)}")
rows = []
for s, d in conflicts.items():
    a, g = d["a7"], d["grown"]
    sa, sg = cset(a), cset(g)
    rows.append((len(sa & sg) / max(1, min(len(sa), len(sg))), s, a, g, sa, sg))
rows.sort(key=lambda t: -t[0])
for ratio, s, a, g, sa, sg in rows:
    kidsA = [c for c in pool.values() if c.grownFromKey == (a.position, a.k, a.phono, a.ortho)]
    print(f"  overlap {ratio:.2f}  {s[0][:4]} k={s[1]} tail={s[2]!r} rest={s[4]!r}")
    print(f"    A7    {a.ortho!r} {a.phono!r} |{len(sa)}| excl={[len(x.excluded) for x in a.slots]} "
          f"subtree={len(kidsA)} seed={a.isSeed}")
    print(f"    grown {g.ortho!r} {g.phono!r} |{len(sg)}| excl={[len(x.excluded) for x in g.slots]} "
          f"parent={g.grownFromKey[3]!r} a7-only={len(sa - sg)} grown-only={len(sg - sa)}")

# ── [3] the -ment pair in detail ─────────────────────────────────────────────
mentKey = next(k for k in pool if pool[k].ortho == "ment" and pool[k].k == 1
               and pool[k].position == A.SUFFIX and pool[k].grownFromKey is None)
ment = pool[mentKey]
pKey = next(k for k in pool if a7Sig(pool[k]) is not None
            and pool[k].phono == "°.m@" and pool[k].position == A.SUFFIX)
P = pool[pKey]
dKey = next(k for k in pool if grownSig(pool[k]) == (A.SUFFIX, 2, "m@", "onset", "°"))
D = pool[dKey]
print(f"\n[3] -ment pair:  ment |{len(ment.carriers)}|   ·°ment(A7) |{len(P.carriers)}|   "
      f"[C]°.m@(grown) |{len(D.carriers)}|  D exclusions={D.slots}")
sM, sP, sD = cset(ment), cset(P), cset(D)
print(f"    P∩D={len(sP & sD)}  P-only={len(sP - sD)}  D-only={len(sD - sP)}  D⊆P={sD <= sP}")
idxOf = {r.idx: r for r in recs}
def topSliver(difference, label, n=10):
    print(f"    {label} (top by freq):")
    items = sorted(difference, key=lambda t: -idxOf[t[0]].frequency)[:n]
    for t in items:
        w = idxOf[t[0]]
        print(f"      {w.ortho:22s} syls={w.phonoSylls} lemma={w.lemme} f={w.frequency:.1f}")

topSliver(sP - sD, "A7-only (in ·°ment, NOT in grown node)")
topSliver(sD - sP, "grown-only (in [C]°.m@, NOT in ·°ment)")
# attestation check on the A7-only sliver: is any of them a k=1 'ment' carrier?
inMent = [t for t in (sP - sD) if t in sM]
print(f"    A7-only carriers that ARE k=1 ment carriers: {len(inMent)} / {len(sP - sD)}")
# exception share of the union vs the growth cap
union = [c for t in (sP | sD)
         for c in P.carriers + D.carriers if (c.rec.idx, c.start, c.span) == t]
denom = sum(c.rec.frequency for c in union) or 1.0
share, excSet = A._exceptionShare(A.SUFFIX, union, denom)
print(f"    union: {len(union)} carriers, freq {denom:.0f}, exception share {share:.4f} "
      f"(cap {A.GROWTH_MAX_EXCEPTION_SHARE})")

# ── [4] score probe: separate vs unified ─────────────────────────────────────
print(f"\n[4] score probe (exact keypress evaluation, ~1 min)")
t0 = time.time()
ctx = A.SimContext(sb, recs)
pk = B.PhonemeKeys(sb)
keypresses = B.enumerateKeypresses(sb, ctx)
print(f"  ctx+keypresses {time.time() - t0:.0f}s ({len(keypresses)} keys)")
idx = R.childrenIndex(pool)
t0 = time.time()
ruleA = R.buildCandidateRule(ment, idx)
R.chooseRuleKeypress(ruleA, pk, ctx, keypresses)
print(f"  rule A (root ment, forms {[f.ortho for f in ruleA.forms]}): exact {ruleA.score:.1f} "
      f"keys={ruleA.keys} exc={ruleA.wordExceptions} ({time.time() - t0:.0f}s)")
t0 = time.time()
ruleB = R.buildCandidateRule(P, idx)
R.chooseRuleKeypress(ruleB, pk, ctx, keypresses)
print(f"  rule B (root ·°ment, forms {[f.ortho for f in ruleB.forms]}): exact {ruleB.score:.1f} "
      f"keys={ruleB.keys} exc={ruleB.wordExceptions} ({time.time() - t0:.0f}s)")

# unified pool: D' = D with union carriers; P removed; P's subtree re-parented onto D'
Dp = dataclasses.replace(D, carriers=list(union))
A._finishStats(Dp)
dKeyP = (Dp.position, Dp.k, Dp.phono, Dp.ortho)
pool2 = dict(pool)
pool2[dKeyP] = Dp
del pool2[pKey]
for c in pool2.values():
    if c.grownFromKey == pKey:
        c.grownFromKey = dKeyP
    if c.rootKey == pKey:
        c.rootKey = (A.SUFFIX, 1, "m@", "ment")
idx2 = R.childrenIndex(pool2)
ruleC = R.buildCandidateRule(ment, idx2)
t0 = time.time()
R.chooseRuleKeypress(ruleC, pk, ctx, keypresses)
print(f"  rule C (unified, forms {[f.ortho for f in ruleC.forms]}): exact {ruleC.score:.1f} "
      f"keys={ruleC.keys} exc={ruleC.wordExceptions} ({time.time() - t0:.0f}s)")

def onceCredited(rules):
    best: dict[int, tuple[float, int]] = {}
    for r in rules:
        for res in r.results:
            if res.gain > 0:
                i = res.carrier.rec.idx
                if i not in best or res.gain > best[i][1]:
                    best[i] = (res.carrier.rec.frequency, res.gain)
    benefit = sum(f * g for f, g in best.values())
    costs = sum(R.EXCEPTION_ALPHA * r.exceptionFreq
                + R.EXCLUSION_COST * R.exclusionCountOf(r.forms)
                + R.FORM_COST * (len(r.forms) - 1) for r in rules)
    return benefit - costs, len(best), benefit, costs

sep, nSep, bSep, cSep = onceCredited([ruleA, ruleB])
uni, nUni, bUni, cUni = onceCredited([ruleC])
print(f"\n  word-once-credited objective:  {ruleA.root.ortho}+{P.ortho} separate = {sep:.1f} "
      f"({nSep} words, benefit {bSep:.0f}, costs {cSep:.0f})")
print(f"  word-once-credited objective:  unified single rule          = {uni:.1f} "
      f"({nUni} words, benefit {bUni:.0f}, costs {cUni:.0f})")
print(f"  delta (unified - separate) = {uni - sep:+.1f}  "
      f"[plus: one budget slot freed, one key to learn instead of two]")
