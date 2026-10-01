"""COMBINED simulation of the 30 decided affix scopes (scratch/scope-decisions-2026-09-30.md).

For every rule of the H sweep (keys from scratch/affix-sweep-partial/H/affix-rules.tsv) the carriers of its
anchor (pool root, k=1) get the growth form (k=2) when the decided scope matches, else the anchor alone.
Every rule is run ALONE (one group) and then all rules TOGETHER (one `simulate` call, cross-rule collisions
cost marks). A k=2 carrier that gains nothing falls back to k=1 (a "fallback", price 5) and the run is redone.

Usage: env/bin/python scratch/combined_scopes.py [--only RANK[,RANK..]]   (acceptance: --only 3 alone = 227 two-stroke words, benefit 6,035)
Output: scratch/combined-scopes-2026-10-01.md
Objective = benefit - EXCEPTION_ALPHA*exception freq - 5*fallbacks - 100*forms (user's form cost).
"""
import collections
import csv
import pickle
import re
import sys
import time

sys.path.insert(0, ".")
from src import affixes as A  # noqa: E402
from src import affixrules as R  # noqa: E402
from src.affixes import Binding, PREFIX, RULE, SUFFIX, simulate  # noqa: E402
from util import affix_scan as S  # noqa: E402

FORM_COST, FALLBACK_PRICE = 100.0, 5.0
RULES_TSV = "scratch/affix-sweep-partial/H/affix-rules.tsv"
OUT = "scratch/combined-scopes-2026-10-01.md"

C = "ptkbdgfsSvzZmnNlRjw"                      # consonant phonemes
CL = "[^aeiouyàâäéèêëîïôöùûüœ]"                 # consonant letters (rank 1, spelling)
V = f"[^{C}]"                                  # any vowel phoneme
rx = lambda s: re.compile(s)                   # noqa: E731
C12, C0 = f"[{C}]{{1,2}}", f"[{C}]*"
C12bv = "[" + "".join(c for c in C if c not in "bv") + "]{1,2}"
RE = {
    1: rx(f"{CL}{{1,2}}[eui]+"), 3: rx(f"{C12}@"), 6: rx(f"{C0}[ai]"), 10: rx(f"{C12bv}i"),
    17: rx(f"a|fle|vE|{C12}y"), 23: rx(f"{C0}y"), 24: rx(f"{C12}i"), 25: rx("[mn][aeiouy]"),
    26: rx(f"p[aeiouy]|{C0}e|sy"), 27: rx(f"{C12}i|k{V}"), 29: rx(f"{C12}[i°]"),
}
# rank -> k (1 or 2) of a carrier given a = anchor syllable spelling, o = neighbour spelling, p = neighbour sound
SCOPE = {
    1: lambda a, o, p: RE[1].fullmatch(o),
    3: lambda a, o, p: RE[3].fullmatch(p),
    5: lambda a, o, p: o in ("man", "ve"),
    6: lambda a, o, p: RE[6].fullmatch(p),
    7: lambda a, o, p: a == "in" and o == "té",
    10: lambda a, o, p: RE[10].fullmatch(p),
    11: lambda a, o, p: p in ("ZuR", "to", "tR°", "di"),
    13: lambda a, o, p: a == "cé" and p == "m@",
    15: lambda a, o, p: a == "e" and p in ("ksky", "kspli", "sE", "n°"),
    16: lambda a, o, p: a == "dez" and p in ("gaR", "m@"),
    17: lambda a, o, p: a == "ré" and RE[17].fullmatch(p),
    19: lambda a, o, p: a == "vé" and p == "Ri",
    23: lambda a, o, p: p == "li" or (a == "sez" and RE[23].fullmatch(p)),
    24: lambda a, o, p: a == "di" and RE[24].fullmatch(p),
    25: lambda a, o, p: a == "i" and RE[25].fullmatch(p),
    26: lambda a, o, p: a == "rer" and RE[26].fullmatch(p),
    27: lambda a, o, p: RE[27].fullmatch(p),
    29: lambda a, o, p: a == "né" and RE[29].fullmatch(p),
}
FORMS = {1: 1, 3: 1, 5: 1, 6: 1, 7: 1, 10: 1, 11: 1, 13: 1, 15: 1, 16: 1, 17: 1, 19: 1, 23: 2, 24: 1, 25: 1, 26: 1, 27: 1, 29: 1}
PHONO_OVERRIDE = {5: "d°"}                      # several pool roots share the spelling `de`


def loadRules() -> list[dict]:
    rows = []
    for r in csv.DictReader(open(RULES_TSV), delimiter="\t"):
        keys = tuple(int(x) for x in re.findall(r"\d+", r["keys"]))
        rows.append(dict(rank=int(r["rank"]), pos=r["position"], root=r["root"], keys=keys, tsvCarriers=int(r["carriers"])))
    return rows


def main() -> None:
    t0 = time.time()
    only = {int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(",")} if "--only" in sys.argv else None
    A.RULE_PARTIAL_OVERLAP = True
    _, R.EXCEPTION_ALPHA, R.EXCLUSION_COST, _fc = next(t for t in S.SWEEP_SETTINGS if t[0] == "H")
    starboard = S.loadStarboard()
    records = S.loadRecords(starboard, False)
    cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
    ctx, _pk, _kp, _lem = S._engine(cands, records, starboard)
    print(f"engine ready in {time.time() - t0:.0f}s", flush=True)

    rules = [r for r in loadRules() if only is None or r["rank"] in only]
    groups: list[dict] = []
    for r in rules:
        pos = SUFFIX if r["pos"] == "suffix" else PREFIX
        roots = [c for k, c in cands.items() if k[0] == pos and k[1] == 1 and k[3] == r["root"]
                 and (r["rank"] not in PHONO_OVERRIDE or c.phono == PHONO_OVERRIDE[r["rank"]])]
        root = max(roots, key=lambda c: len(c.carriers))
        ones, info = [], {}
        for c in root.carriers:
            syl, ph = c.rec.orthoSylls, c.rec.phonoSylls
            if len(syl) != len(c.rec.base):
                continue
            j = c.start - 1 if pos == SUFFIX else c.start + c.span
            if 0 <= j < len(syl):
                ones.append(c)
                info[c.rec.idx] = (syl[c.start], syl[j], ph[j])
        scope = SCOPE.get(r["rank"])
        wants = {c.rec.idx for c in ones if scope and scope(*info[c.rec.idx])}
        groups.append(dict(r, posC=pos, binding=Binding(pos, RULE, r["keys"]), ones=ones, wants=wants,
                           byIdx={c.rec.idx: c for c in ones}, nForms=FORMS.get(r["rank"], 0),
                           rootPhono=root.phono, nRoot=len(root.carriers)))
        print(f"rank {r['rank']:2} {r['root'][:24]:24} /{root.phono}/ {len(root.carriers)} carriers (tsv {r['tsvCarriers']}), "
              f"{len(ones)} usable, {len(wants)} in scope", flush=True)

    def grow(g, c):
        return c._replace(start=c.start - 1, span=2) if g["posC"] == SUFFIX else c._replace(span=2)

    def run(gs, kOf):
        cs = [[grow(g, c) if kOf[g["rank"]][c.rec.idx] == 2 else c for c in g["ones"]] for g in gs]
        res = simulate([(g["binding"], x) for g, x in zip(gs, cs)], ctx, boundaryRisk=False)
        failed = {g["rank"]: {r.carrier.rec.idx for r in rs if r.carrier.span == 2 and r.gain <= 0} for g, rs in zip(gs, res)}
        return res, failed

    def evaluate(gs):
        kOf = {g["rank"]: {c.rec.idx: (2 if c.rec.idx in g["wants"] else 1) for c in g["ones"]} for g in gs}
        res, failed = run(gs, kOf)
        if any(failed.values()):
            for g in gs:
                for i in failed[g["rank"]]:
                    kOf[g["rank"]][i] = 1
            res, failed2 = run(gs, kOf)
        out = {}
        for g, rs in zip(gs, res):
            _s, ben, exc, ef, top = R.ruleScoreFromResults(rs, 0, 1)
            fb = failed[g["rank"]]
            two = sum(1 for i in g["wants"] if i not in fb)
            o = ben - R.EXCEPTION_ALPHA * ef - FALLBACK_PRICE * len(fb) - FORM_COST * g["nForms"]
            fbf = sum(g["byIdx"][i].rec.frequency for i in fb)
            gains = {(g["posC"], r.carrier.rec.idx): (r.carrier.rec.frequency, r.gain) for r in rs if r.gain > 0}
            out[g["rank"]] = dict(rs=rs, ben=ben, exc=exc, ef=ef, fb=len(fb), fbf=fbf, two=two, obj=o, top=top, gains=gains,
                                  fbTop=[g["byIdx"][i].rec.ortho for i in sorted(fb, key=lambda i: -g["byIdx"][i].rec.frequency)[:4]])
        return out

    alone = {}
    for g in groups:
        alone.update(evaluate([g]))
    print(f"alone done {time.time() - t0:.0f}s", flush=True)
    comb = evaluate(groups)
    print(f"combined done {time.time() - t0:.0f}s", flush=True)

    if "--diag" in sys.argv:
        byRank = {g["rank"]: g for g in groups}
        owners: dict = collections.defaultdict(list)       # outline -> (rank, ortho) over every carrier's tentative new base
        for g in groups:
            for r in comb[g["rank"]]["rs"]:
                nb = A._newBase(g["binding"], r.carrier, ctx)[0]
                if nb is not None:
                    owners[nb].append((g["rank"], r.carrier.rec.ortho))
        for rk in sorted(comb):
            if comb[rk]["obj"] - alone[rk]["obj"] >= -100:
                continue
            g = byRank[rk]
            old = {r.carrier.rec.idx for r in alone[rk]["rs"] if r.reason in R.WORD_EXCEPTION_REASONS}
            new = [r for r in comb[rk]["rs"] if r.reason in R.WORD_EXCEPTION_REASONS and r.carrier.rec.idx not in old]
            new.sort(key=lambda r: -r.carrier.rec.frequency)
            print(f"\nDIAG rank {rk} {g['root'][:20]}: {len(new)} new exception words, top by freq:")
            for r in new[:10]:
                nb = A._newBase(g["binding"], r.carrier, ctx)[0]
                rivals = sorted({(k, o) for k, o in owners.get(nb, []) if o != r.carrier.rec.ortho and k != rk})[:5]
                lex = sorted({o.ortho for o in ctx.baseIndex.get(nb, ()) if o.ortho != r.carrier.rec.ortho})[:4]
                print(f"  {r.carrier.rec.ortho:14} f={r.carrier.rec.frequency:7.1f} {r.reason:16} other rules' words {rivals} lexicon words {lex}")
    credit: dict[tuple[str, int], float] = collections.defaultdict(float)
    for rk in comb:
        for key, (f, gain) in comb[rk]["gains"].items():
            credit[key] = max(credit[key], f * gain)
    lines = ["# Combined simulation of the 30 decided scopes (H, flag on, form cost 100, fallback 5)", "",
             "ALONE = rule simulated by itself; COMBINED = all rules in one `simulate` call. d_obj = combined - alone; "
             "flagged when objective drops by more than 100.", "",
             "| rank | root | keys | scope words (2-stroke) | benefit alone / comb | exc words alone / comb | exc freq alone / comb | fallbacks alone / comb | objective alone | objective comb | d_obj | flag |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for g in groups:
        a, c = alone[g["rank"]], comb[g["rank"]]
        d = c["obj"] - a["obj"]
        lines.append(f"| {g['rank']} | `{g['root'][:30]}` | {g['keys']} | {len(g['wants'])} ({a['two']}/{c['two']}) | {a['ben']:.0f} / {c['ben']:.0f} | "
                     f"{a['exc']} / {c['exc']} | {a['ef']:.1f} / {c['ef']:.1f} | {a['fb']} / {c['fb']} | {a['obj']:.0f} | {c['obj']:.0f} | {d:+.0f} | {'**DROP**' if d < -100 else ''} |")
    sa = sum(alone[r]["obj"] for r in alone)
    sc_ = sum(comb[r]["obj"] for r in comb)
    lines += ["", f"Sum of objectives: alone {sa:.0f}, combined {sc_:.0f} ({sc_ - sa:+.0f}). Benefit credited once per word and position: {sum(credit.values()):.0f} "
              f"(sum of per-rule combined benefits {sum(comb[r]['ben'] for r in comb):.0f}).", "",
              "Top exceptions and fallbacks (combined):", ""]
    for g in groups:
        c = comb[g["rank"]]
        lines.append(f"- {g['rank']} `{g['root'][:20]}`: exceptions {c['top'][:6]}; fallbacks {c['fbTop']}")
    open(OUT, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"wrote {OUT} in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
