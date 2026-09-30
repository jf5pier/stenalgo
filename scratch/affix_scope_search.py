"""Generic regex-scope search for ONE sweep rule (generalises ment_regex_search.py): the regex is fully
matched against the neighbour syllable absorbed by the 2-stroke form (see affix_scope_table.py).

Grammar: onset {C+, C*, C, C{1,2}} x nucleus [subset of the rule's commonest vowel letters] (+ or not)
x coda {none, r, l, n, rs..., C?, C*}; atoms = vowel letters + coda letters (quantifier free).
Every distinct matched-syllable set is scored once by the real simulator. Fallback price default 5.

Usage: env/bin/python scratch/affix_scope_search.py RANK [PRICE] [L|M|H] [on|off]
Outputs: scratch/scope-search-rank{RANK}-{setting}.md
"""
import itertools
import re
import sys
import time

sys.path.insert(0, ".")
from scratch.affix_scope_table import Scorer, loadRule  # noqa: E402

VOWELS = "aeiouyàâäéèêëîïôöùûüœ"
C = f"[^{VOWELS}]"
ONSETS = {"C+": "+", "C*": "*", "C": "", "C{1,2}": "{1,2}"}
CODAS = ["", "r", "l", "n", "s", "t", "C?", "C*", "[rl]", "[rn]", "[rst]"]   # written after the nucleus
CODA_ATOMS = {"": 0, "r": 1, "l": 1, "n": 1, "s": 1, "t": 1, "C?": 1, "C*": 1, "[rl]": 2, "[rn]": 2, "[rst]": 3}


def main() -> None:
    t0 = time.time()
    rank = int(sys.argv[1])
    price = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
    setting = sys.argv[3] if len(sys.argv) > 3 else "H"
    partial = (sys.argv[4] if len(sys.argv) > 4 else "on") == "on"
    rule = loadRule(rank)
    sc = Scorer(rule, partial, setting)
    pos = rule["pos"]
    cur = sc.currentScope() & set(sc.syllables)
    count: dict[str, float] = {}
    for c in sc.ones:
        for ch in sc.neigh[c.rec.idx]:
            if ch in VOWELS:
                count[ch] = count.get(ch, 0) + c.rec.frequency
    pool = "".join(sorted(count, key=lambda ch: -count[ch])[:7])
    print(f"rank {rank} {pos} {rule['root']}: {len(sc.ones)} carriers, {len(sc.syllables)} neighbours, vowel pool {pool}", flush=True)

    found: dict[frozenset[str], tuple[str, int]] = {}
    for n in range(1, len(pool) + 1):
        for sub in itertools.combinations(pool, n):
            for plus in (True, False):
                for onset, q in ONSETS.items():
                    for coda in CODAS:
                        body = f"[{''.join(sub)}]{'+' if plus else ''}"
                        if coda.startswith("C"):
                            coda_re = C + coda[1:]
                        else:
                            coda_re = coda
                        pat = re.compile(f"{C}{q}{body}{coda_re}")
                        matched = frozenset(s for s in sc.syllables if pat.fullmatch(s))
                        if not matched:
                            continue
                        atoms = n + CODA_ATOMS[coda]
                        text = f"C{q}{body}{coda}"
                        old = found.get(matched)
                        if old is None or atoms < old[1] or (atoms == old[1] and len(text) < len(old[0])):
                            found[matched] = (text, atoms)
    print(f"{len(found)} distinct scopes ({time.time() - t0:.0f}s)", flush=True)

    scored = []
    for m, (text, atoms) in found.items():
        r = sc.score(m)
        scored.append((sc.objective(r, price), text, atoms, r, m))
    base = sc.score(frozenset())
    curR = sc.score(frozenset(cur))
    lines = [f"# rank {rank}: {pos} `{rule['root']}` keys {sc.keys}: regex scope search (setting {setting}, price {price}, "
             f"partial {partial})", "",
             f"{len(found)} distinct scopes. Anchor alone: objective {sc.objective(base, price):.0f} (benefit {base['benefit']:.0f}, "
             f"hard exc {base['exc']}). Current list ({len(cur)} syllables): objective {sc.objective(curR, price):.0f} "
             f"(benefit {curR['benefit']:.0f}, {curR['fallbacks']} fallbacks).", "",
             "| atoms <= | regex | objective | d vs anchor alone | benefit | 2-stroke words | fallbacks | fallback freq | hard exc | top fallbacks |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for budget in (2, 3, 4, 5, 6, 8):
        cand = [t for t in scored if t[2] <= budget]
        if not cand:
            continue
        o, text, atoms, r, _m = max(cand, key=lambda t: t[0])
        lines.append(f"| {budget} | `{text}` | {o:.0f} | {o - sc.objective(base, price):+.0f} | {r['benefit']:.0f} | {r['twoWords']} | "
                     f"{r['fallbacks']} | {r['fallbackFreq']:.0f} | {r['exc']} | {', '.join(r['fallbackTop'][:5])} |")
    lines += ["", "## top 12 overall (any complexity <= 8 atoms)", "", "| regex | atoms | objective | benefit | words | fallbacks |", "|---|---|---|---|---|---|"]
    for o, text, atoms, r, _m in sorted((t for t in scored if t[2] <= 8), key=lambda t: -t[0])[:12]:
        lines.append(f"| `{text}` | {atoms} | {o:.0f} | {r['benefit']:.0f} | {r['twoWords']} | {r['fallbacks']} |")
    out = f"scratch/scope-search-rank{rank}-{setting}.md"
    open(out, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"wrote {out} ({sc.nScored} simulator runs) in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
