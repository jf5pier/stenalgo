"""Option B (RESUME_2026-09-30-ment-regex-scope.md): automatic search of a learnable regex scope for
the -ment rule, each candidate scored by the REAL simulator (same model as ment_regex_score.py).

A regex is fully matched against the spelling of the syllable before `ment`. Grammar:
  onset  : C+ | C* | C | C{1,2}, optionally minus up to MAX_TWEAKS excluded consonant letters
  nucleus: [subset of vowel letters] or [subset]+
Complexity (learnability) = atoms = vowel letters + excluded onset letters (quantifier choice is free).
Objective = benefit - alpha*hardExcFreq - price*fallbackWords - FORM_COST   (price per fallback word).
Since the fallback price is an open design question, the output is a table: for each price and each
atom budget, the best regex, plus the (atoms, fallbacks) Pareto data.

Usage: env/bin/python scratch/ment_regex_search.py [L|M|H] [on|off]      (defaults H on; ~ minutes)
Outputs: scratch/ment-regex-search-{setting}.md, scratch/ment-regex-search-{setting}.log
"""
import itertools
import pickle
import re
import sys
import time

sys.path.insert(0, ".")
from src import affixes as A  # noqa: E402
from src import affixrules as R  # noqa: E402
from src.affixes import Binding, RULE, SUFFIX, simulate  # noqa: E402
from util import affix_scan as S  # noqa: E402

KEYS = (20, 21, 25)
SETTING = sys.argv[1] if len(sys.argv) > 1 else "H"
PARTIAL = (sys.argv[2] if len(sys.argv) > 2 else "on") == "on"
A.RULE_PARTIAL_OVERLAP = PARTIAL
_, R.EXCEPTION_ALPHA, R.EXCLUSION_COST, R.FORM_COST = next(t for t in S.SWEEP_SETTINGS if t[0] == SETTING)
OUT = f"scratch/ment-regex-search-{SETTING}.md"

VOWELS = "aeiouyàâäéèêëîïôöùûüœ"
PRICES = (0, 5, 20, 50, 150)      # per fallback word (EXCLUSION_COST at L / M / H = 5 / 50 / 150)
ATOM_BUDGETS = (2, 3, 4, 5, 6)
MAX_TWEAKS = 2
ONSETS = {"C+": "+", "C*": "*", "C": "", "C{1,2}": "{1,2}"}


class Scorer:
    def __init__(self) -> None:
        starboard = S.loadStarboard()
        records = S.loadRecords(starboard, False)
        cands = pickle.load(open("scratch/affix-pool.pickle", "rb"))
        self.ctx, _pk, _kp, _lem = S._engine(cands, records, starboard)
        root = next(c for k, c in cands.items() if k[0] == SUFFIX and k[1] == 1 and k[3] == "ment")
        self.ones = [c for c in root.carriers if c.start >= 1 and len(c.rec.orthoSylls) == len(c.rec.base)]
        self.byIdx = {c.rec.idx: c for c in self.ones}
        self.prev = {c.rec.idx: c.rec.orthoSylls[c.start - 1] for c in self.ones}
        self.syllables = sorted(set(self.prev.values()))
        self.binding = Binding(SUFFIX, RULE, KEYS)
        self.cache: dict[frozenset[str], dict] = {}
        self.nScored = 0

    def _run(self, cs):
        (res,) = simulate([(self.binding, cs)], self.ctx, boundaryRisk=False)
        return res

    def score(self, matched: frozenset[str]) -> dict:
        """Result of giving the 2-stroke form to every word whose previous syllable is in `matched`."""
        hit = self.cache.get(matched)
        if hit is not None:
            return hit
        self.nScored += 1
        if self.nScored % 500 == 0:
            print(f"  {self.nScored} scopes scored", flush=True)
        cs = [c._replace(start=c.start - 1, span=2) if self.prev[c.rec.idx] in matched else c
              for c in self.ones]
        res = self._run(cs)
        failed = {r.carrier.rec.idx for r in res if r.carrier.span == 2 and r.gain <= 0}
        if failed:
            cs = [self.byIdx[c.rec.idx] if c.rec.idx in failed else c for c in cs]
            res = self._run(cs)
        _sc, benefit, exc, excFreq, _top = R.ruleScoreFromResults(res, 0, 1)
        fallbackWords = sorted((self.byIdx[i].rec for i in failed), key=lambda r: -r.frequency)
        out = dict(benefit=benefit, exc=exc, excFreq=excFreq, fallbacks=len(failed),
                   fallbackFreq=sum(r.frequency for r in fallbackWords),
                   fallbackTop=[r.ortho for r in fallbackWords[:8]],
                   twoWords=sum(1 for c in self.ones if self.prev[c.rec.idx] in matched))
        self.cache[matched] = out
        return out

    def objective(self, r: dict, price: float) -> float:
        return r["benefit"] - R.EXCEPTION_ALPHA * r["excFreq"] - price * r["fallbacks"] - R.FORM_COST


def consonantLetters(syllables: list[str]) -> str:
    return "".join(sorted({ch for s in syllables for ch in s if ch not in VOWELS and ch.isalpha()}))


def regexOf(vowels: str, plus: bool, onset: str, excluded: str, consonants: str) -> str:
    q = ONSETS[onset]
    if excluded:
        cls = "[" + "".join(ch for ch in consonants if ch not in excluded) + "]"
    else:
        cls = "C"
    return f"{cls}{q}[{vowels}]{'+' if plus else ''}"


def compile_(vowels: str, plus: bool, onset: str, excluded: str, consonants: str) -> re.Pattern:
    q = ONSETS[onset]
    cons = "[" + "".join(ch for ch in consonants if ch not in excluded) + "]"
    return re.compile(f"{cons}{q}[{vowels}]{'+' if plus else ''}")


def main() -> None:
    t0 = time.time()
    sc = Scorer()
    cons = consonantLetters(sc.syllables)
    vowelCount: dict[str, int] = {}
    for s in sc.prev.values():
        for ch in s:
            if ch in VOWELS:
                vowelCount[ch] = vowelCount.get(ch, 0) + 1
    vowelPool = "".join(sorted(vowelCount, key=lambda ch: -vowelCount[ch])[:9])
    print(f"{len(sc.ones)} carriers, {len(sc.syllables)} distinct previous syllables, "
          f"consonants {cons}, vowel pool {vowelPool}", flush=True)

    # (regex string, atoms, matched set)
    found: dict[frozenset[str], tuple[str, int]] = {}

    def consider(vowels: str, plus: bool, onset: str, excluded: str) -> frozenset[str]:
        pat = compile_(vowels, plus, onset, excluded, cons)
        matched = frozenset(s for s in sc.syllables if pat.fullmatch(s))
        atoms = len(vowels) + len(excluded)
        text = regexOf(vowels, plus, onset, excluded, cons)
        if excluded:
            text = text.replace("[" + "".join(ch for ch in cons if ch not in excluded) + "]", f"C\\{{{excluded}}}")
        old = found.get(matched)
        if old is None or atoms < old[1] or (atoms == old[1] and len(text) < len(old[0])):
            found[matched] = (text, atoms)
        return matched

    # stage 1: every vowel subset x quantifier x onset form, no onset tweak
    for n in range(1, len(vowelPool) + 1):
        for sub in itertools.combinations(vowelPool, n):
            for plus in (True, False):
                for onset in ONSETS:
                    consider("".join(sub), plus, onset, "")
    print(f"stage 1: {len(found)} distinct scopes ({time.time() - t0:.0f}s)", flush=True)

    def best(price: float, budget: int):
        top = None
        for matched, (text, atoms) in found.items():
            if atoms > budget:
                continue
            r = sc.score(matched)
            o = sc.objective(r, price)
            if top is None or o > top[0]:
                top = (o, text, atoms, r, matched)
        return top

    # stage 2: onset tweaks (exclude up to MAX_TWEAKS consonant letters) around the best of each cell
    seeds: set[tuple[str, bool, str, str]] = set()
    for price in PRICES:
        for budget in ATOM_BUDGETS:
            pool = sorted(((sc.objective(sc.score(m), price), t, a) for m, (t, a) in found.items() if a <= budget),
                          reverse=True)[:3]
            for _o, t, _a in pool:
                mm = re.match(r"C(\*|\+|\{1,2\})?\[([^\]]*)\](\+?)$", t)
                if mm:
                    seeds.add((mm.group(2), mm.group(3) == "+", next(k for k, v in ONSETS.items() if v == (mm.group(1) or "")), ""))
    print(f"stage 2: tweaking {len(seeds)} seeds ({time.time() - t0:.0f}s)", flush=True)
    for vowels, plus, onset, _ in seeds:
        for k in range(1, MAX_TWEAKS + 1):
            for excl in itertools.combinations(cons, k):
                consider(vowels, plus, onset, "".join(excl))
    print(f"after tweaks: {len(found)} distinct scopes, {sc.nScored} scored ({time.time() - t0:.0f}s)", flush=True)

    lines = [f"# -ment regex scope search (real simulator, keys (20,21,25), setting {SETTING}, "
             f"partial overlap {PARTIAL})", "",
             f"{len(found)} distinct scopes from the grammar, {sc.nScored} simulator runs. Atoms = vowel letters + "
             "excluded onset letters. `C\\{xy}` = consonants except x, y. Objective = benefit - alpha*excFreq - "
             "price*fallbackWords - form cost.", ""]
    ref = sc.score(frozenset(s for s in sc.syllables if re.fullmatch(r"[^aeiouyàâäéèêëîïôöùûüœ]+[eiu]+", s)))
    lines += [f"Reference `(C+[eiu]+)?`: benefit {ref['benefit']:.0f}, fallbacks {ref['fallbacks']} "
              f"(freq {ref['fallbackFreq']:.0f}), exceptions {ref['exc']}, 2-stroke words {ref['twoWords']}.", ""]
    for price in PRICES:
        lines += [f"## price {price} per fallback word", "",
                  "| atoms <= | regex | objective | benefit | 2-stroke words | fallbacks | fallback freq | hard exc | top fallbacks |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for budget in ATOM_BUDGETS:
            top = best(price, budget)
            if top is None:
                continue
            o, text, atoms, r, _m = top
            lines.append(f"| {budget} | `{text}` | {o:.0f} | {r['benefit']:.0f} | {r['twoWords']} | {r['fallbacks']} | "
                         f"{r['fallbackFreq']:.0f} | {r['exc']} | {', '.join(r['fallbackTop'][:6])} |")
        lines.append("")
    # Pareto: fewest fallbacks reachable per benefit floor
    lines += ["## Pareto (benefit vs fallback words), any complexity <= 5 atoms", "",
              "| regex | atoms | benefit | fallbacks | fallback freq |", "|---|---|---|---|---|"]
    pts = sorted(((sc.score(m), t, a) for m, (t, a) in found.items() if a <= 5),
                 key=lambda p: (p[0]["fallbacks"], -p[0]["benefit"]))
    bestBenefit = -1.0
    for r, t, a in pts:
        if r["benefit"] > bestBenefit:
            bestBenefit = r["benefit"]
            lines.append(f"| `{t}` | {a} | {r['benefit']:.0f} | {r['fallbacks']} | {r['fallbackFreq']:.0f} |")
    open(OUT, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"wrote {OUT} in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
