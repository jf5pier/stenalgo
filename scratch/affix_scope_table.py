"""Generic version of ment_regex_score.py (RESUME_2026-09-30-ment-regex-scope.md): for ONE sweep rule,
score its current enumerated k=2 scope, "anchor alone", "everything", and every neighbour syllable on its own,
through the REAL simulator, with the keys fixed to the sweep's choice.

The neighbour syllable is the one absorbed by the 2-stroke form: the syllable BEFORE the anchor for a
suffix, the one AFTER it for a prefix. A carrier whose neighbour is in the scope gets the 2-stroke form;
a 2-stroke carrier that gains nothing FALLS BACK to the anchor alone (and is counted as a fallback).

Usage: env/bin/python scratch/affix_scope_table.py RANK [L|M|H] [on|off]      e.g. RANK 2 = `re`
Outputs: scratch/scope-table-rank{RANK}-{setting}.md
"""
import json
import pickle
import re
import sys
import time

sys.path.insert(0, ".")
from src import affixes as A  # noqa: E402
from src import affixrules as R  # noqa: E402
from src.affixes import Binding, PREFIX, RULE, SUFFIX, simulate  # noqa: E402
from util import affix_scan as S  # noqa: E402

BY_ANCHOR = "scratch/affix-H-partial-by-anchor.json"


def loadRule(rank: int) -> dict:
    return next(r for r in json.load(open(BY_ANCHOR)) if r["rank"] == rank)


class Scorer:
    def __init__(self, rule: dict, partial: bool = True, setting: str = "H") -> None:
        A.RULE_PARTIAL_OVERLAP = partial
        _, R.EXCEPTION_ALPHA, R.EXCLUSION_COST, R.FORM_COST = next(t for t in S.SWEEP_SETTINGS if t[0] == setting)
        self.rule = rule
        self.pos = SUFFIX if rule["pos"] == "suffix" else PREFIX
        self.keys = tuple(rule["keys"])
        starboard = S.loadStarboard()
        records = S.loadRecords(starboard, False)
        cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
        self.ctx, _pk, _kp, _lem = S._engine(cands, records, starboard)
        anchor = next(a["anchor"] for a in rule["anchors"] if a["k"] == 1)   # the k=1 spelling(s)
        roots = [c for k, c in cands.items() if k[0] == self.pos and k[1] == 1 and k[3] == anchor]
        self.root = max(roots, key=lambda c: len(c.carriers))
        self.anchorOrtho = anchor
        self.ones = []
        self.neigh: dict[int, str] = {}
        for c in self.root.carriers:
            syl = c.rec.orthoSylls
            if len(syl) != len(c.rec.base):
                continue
            j = c.start - 1 if self.pos == SUFFIX else c.start + c.span
            if 0 <= j < len(syl):
                self.ones.append(c)
                self.neigh[c.rec.idx] = syl[j]
        self.byIdx = {c.rec.idx: c for c in self.ones}
        self.syllables = sorted(set(self.neigh.values()))
        self.binding = Binding(self.pos, RULE, self.keys)
        self.cache: dict[frozenset[str], dict] = {}
        self.nScored = 0

    def two(self, c):
        return c._replace(start=c.start - 1, span=2) if self.pos == SUFFIX else c._replace(span=2)

    def _run(self, cs):
        (res,) = simulate([(self.binding, cs)], self.ctx, boundaryRisk=False)
        return res

    def score(self, matched: frozenset[str]) -> dict:
        hit = self.cache.get(matched)
        if hit is not None:
            return hit
        self.nScored += 1
        if self.nScored % 500 == 0:
            print(f"  {self.nScored} scopes scored", flush=True)
        cs = [self.two(c) if self.neigh[c.rec.idx] in matched else c for c in self.ones]
        res = self._run(cs)
        failed = {r.carrier.rec.idx for r in res if r.carrier.span == 2 and r.gain <= 0}
        if failed:
            cs = [self.byIdx[c.rec.idx] if c.rec.idx in failed else c for c in cs]
            res = self._run(cs)
        _sc, benefit, exc, excFreq, _top = R.ruleScoreFromResults(res, 0, 1)
        fb = sorted((self.byIdx[i].rec for i in failed), key=lambda r: -r.frequency)
        out = dict(benefit=benefit, exc=exc, excFreq=excFreq, fallbacks=len(failed),
                   fallbackFreq=sum(r.frequency for r in fb), fallbackTop=[r.ortho for r in fb[:8]],
                   twoWords=sum(1 for c in self.ones if self.neigh[c.rec.idx] in matched))
        self.cache[matched] = out
        return out

    def objective(self, r: dict, price: float = 5.0) -> float:
        return r["benefit"] - R.EXCEPTION_ALPHA * r["excFreq"] - price * r["fallbacks"] - R.FORM_COST

    def currentScope(self) -> set[str]:
        out: set[str] = set()
        for a in self.rule["anchors"]:
            if a["k"] == 2:
                for grp in re.findall(r"\[(.*?)\]", a["form"]):
                    out |= set(grp.split("|"))
        return out


def main() -> None:
    t0 = time.time()
    rank = int(sys.argv[1])
    setting = sys.argv[2] if len(sys.argv) > 2 else "H"
    partial = (sys.argv[3] if len(sys.argv) > 3 else "on") == "on"
    rule = loadRule(rank)
    sc = Scorer(rule, partial, setting)
    cur = sc.currentScope() & set(sc.syllables)
    print(f"rank {rank} {rule['pos']} {rule['root']} keys {sc.keys}: {len(sc.ones)} carriers with a neighbour syllable, "
          f"{len(sc.syllables)} distinct neighbours, current list {len(cur)} syllables", flush=True)
    rows = [("anchor alone (no k=2)", frozenset()), ("current enumerated list", frozenset(cur)),
            ("every neighbour", frozenset(sc.syllables))]
    lines = [f"# rank {rank}: {rule['pos']} `{rule['root']}` keys {sc.keys}, setting {setting}, partial overlap {partial}", "",
             f"{len(sc.ones)} carriers; objective price 5 per fallback word.", "",
             "| scope | 2-stroke words | fallbacks | fallback freq | benefit | hard exc | exc freq | objective(5) |",
             "|---|---|---|---|---|---|---|---|"]
    for label, m in rows:
        r = sc.score(m)
        lines.append(f"| {label} | {r['twoWords']} | {r['fallbacks']} | {r['fallbackFreq']:.0f} | {r['benefit']:.0f} | "
                     f"{r['exc']} | {r['excFreq']:.1f} | {sc.objective(r):.0f} |")
    zero = sc.score(frozenset())
    bySyll: dict[str, list[int]] = {}
    for i, s in sc.neigh.items():
        bySyll.setdefault(s, []).append(i)
    fq = {c.rec.idx: c.rec.frequency for c in sc.ones}
    order = sorted(bySyll, key=lambda s: -sum(fq[i] for i in bySyll[s]))
    lines += ["", f"## marginal value of each neighbour syllable (alone vs anchor alone: objective {sc.objective(zero):.0f})", "",
              "| neighbour | words | freq | d objective(5) | fallbacks | in list | examples |", "|---|---|---|---|---|---|---|"]
    for s in order:
        ids = bySyll[s]
        r = sc.score(frozenset([s]))
        ex = ", ".join(c.rec.ortho for c in sorted((sc.byIdx[i] for i in ids), key=lambda c: -c.rec.frequency)[:4])
        lines.append(f"| `{s}` | {len(ids)} | {sum(fq[i] for i in ids):.1f} | {sc.objective(r) - sc.objective(zero):+.0f} | "
                     f"{r['fallbacks']} | {'yes' if s in cur else 'NO'} | {ex} |")
    out = f"scratch/scope-table-rank{rank}-{setting}.md"
    open(out, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines[:12]))
    print(f"wrote {out} ({len(order)} neighbours) in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
