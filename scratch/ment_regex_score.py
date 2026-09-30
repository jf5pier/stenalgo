"""Option A (RESUME_2026-09-30-ment-regex-scope.md): score candidate regex scopes for the -ment rule
through the REAL affix simulator, with the keys fixed to the sweep's choice (20, 21, 25).

A -ment word (last syllable spelled `ment`) becomes a 2-stroke carrier (previous syllable + ment)
when the regex fully matches the previous syllable's spelling, else a 1-stroke carrier (ment alone).
The baseline is the enumerated syllable list of the current H-setting rule (read from
scratch/affix-H-partial-by-anchor.json), so the run first checks it reproduces the sweep's numbers.

Usage: env/bin/python scratch/ment_regex_score.py [L|M|H] [on|off]   (defaults H on = the sweep run to reproduce)
Outputs: console table + scratch/ment-regex-scores.md + scratch/ment-syllable-table.md
"""
import json
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
SETTING = sys.argv[1] if len(sys.argv) > 1 else "H"      # L / M / H weight setting of the sweep
PARTIAL = (sys.argv[2] if len(sys.argv) > 2 else "on") == "on"   # RULE_PARTIAL_OVERLAP, as the sweep's H run
A.RULE_PARTIAL_OVERLAP = PARTIAL
_, _alpha, _excl, _form = next(t for t in S.SWEEP_SETTINGS if t[0] == SETTING)
R.EXCEPTION_ALPHA, R.EXCLUSION_COST, R.FORM_COST = _alpha, _excl, _form
POOL = "scratch/affix-pool.pickle"
BY_ANCHOR = "scratch/affix-H-partial-by-anchor.json"
OUT_SCORES = f"scratch/ment-regex-scores-{SETTING}-{'partial' if PARTIAL else 'plain'}.md"
OUT_SYLL = f"scratch/ment-syllable-table-{SETTING}-{'partial' if PARTIAL else 'plain'}.md"

# C = a consonant letter; V sets are spelled out per candidate.
C = "[^aeiouyàâäéèêëîïôöùûüœ]"

CANDIDATES: list[tuple[str, str]] = [   # (label, regex on the previous syllable's spelling)
    ("user A: (C+[eiuéû]+)?", rf"{C}+[eiuéû]+"),
    ("user B: (C+[eiu]+)?", rf"{C}+[eiu]+"),
    ("C+[eiuéû]  (single vowel)", rf"{C}+[eiuéû]"),
    ("C+[eiu]    (single vowel)", rf"{C}+[eiu]"),
    ("C*[eiuéû]+ (onset optional)", rf"{C}*[eiuéû]+"),
    ("C+[eiuéûa]+", rf"{C}+[eiuéûa]+"),
    ("C+[eiuéûaé]+ + oie/ie", rf"{C}+[eiuéûa]+|{C}+[oi]ie?"),
    ("C+ + any vowel letters", rf"{C}+[aeiouyàâäéèêëîïôöùûüœ]+"),
    ("anything (upper bound)", r".+"),
]


def baselineSyllables() -> set[str]:
    data = json.load(open(BY_ANCHOR))
    rule = next(r for r in data if r["root"] == "ment" and r["pos"] == "suffix")
    form = next(a["form"] for a in rule["anchors"] if a["k"] == 2)
    inner = re.match(r"·\[(.*)\]ment$", form).group(1)
    return set(inner.split("|"))


def main() -> None:
    t0 = time.time()
    starboard = S.loadStarboard()
    records = S.loadRecords(starboard, False)
    cands = pickle.load(open(POOL, "rb"))
    ctx, _pk, _keypresses, _lemmas = S._engine(cands, records, starboard)
    root = next(c for k, c in cands.items() if k[0] == SUFFIX and k[1] == 1 and k[3] == "ment")
    ones = [c for c in root.carriers if c.start >= 1 and len(c.rec.orthoSylls) == len(c.rec.base)]
    print(f"{len(root.carriers)} ment carriers, {len(ones)} usable (start>=1, syllables aligned)")
    prevOf = {c.rec.idx: c.rec.orthoSylls[c.start - 1] for c in ones}
    binding = Binding(SUFFIX, RULE, KEYS)
    ones_by_idx = {c.rec.idx: c for c in ones}

    def score(twoSpan: set[int], nForms: int = 2):
        """2-stroke carriers that gain nothing retry as plain `ment` (1-stroke), as the real rule's
        lattice does; each such word is an EXCLUSION (EXCLUSION_COST) -- a word the pattern names
        that the learner must know is an exception. Exceptions = words failing even as 1-stroke."""
        def run(cs):
            (res,) = simulate([(binding, cs)], ctx, boundaryRisk=False)
            return res
        cs = [c._replace(start=c.start - 1, span=2) if c.rec.idx in twoSpan else c for c in ones]
        res = run(cs)
        failed = [r.carrier for r in res if r.carrier.span == 2 and r.gain <= 0]
        if failed:
            retry = {c.rec.idx for c in failed}
            cs = [ones_by_idx[c.rec.idx] if c.rec.idx in retry else c for c in cs]
            res = run(cs)
        excluded = [c.rec.ortho for c in sorted(failed, key=lambda c: -c.rec.frequency)]
        sc, benefit, exc, excFreq, top = R.ruleScoreFromResults(res, len(failed), nForms)
        covered = sum(1 for r in res if r.gain > 0)
        twoCovered = sum(1 for r in res if r.gain > 0 and r.carrier.span == 2)
        failedFreq = sum(c.rec.frequency for c in failed)
        return dict(score=sc, score0=sc + R.EXCLUSION_COST * len(failed), failedFreq=failedFreq, benefit=benefit, exc=exc, excFreq=excFreq, top=top, excluded=excluded,
                    covered=covered, twoCovered=twoCovered, twoWords=len(twoSpan))

    base = baselineSyllables()
    rows = []
    idxOfBase = {i for i, s in prevOf.items() if s in base}
    rows.append(("BASELINE enumerated list (%d syllables)" % len(base), score(idxOfBase)))
    rows.append(("no k=2 form (ment alone)", score(set(), nForms=1)))
    for label, rx in CANDIDATES:
        pat = re.compile(rx)
        rows.append((label, score({i for i, s in prevOf.items() if pat.fullmatch(s)})))
    ref = rows[0][1]
    lines = ["# -ment regex scope scores (real simulator, keys (20, 21, 25), setting %s, partial overlap %s)" % (SETTING, PARTIAL) + "", "",
             f"{len(ones)} carriers whose last syllable is `ment`. `k2 words` = words given the 2-stroke form;",
             "`gain>0 k2` = of those, how many really gain (rest fall back). Exceptions = collision fallbacks.", "",
             "| scope | k2 words | kept as k2 | fallbacks (words) | fallbacks (freq) | benefit | hard exc | score, fallback free | score, fallback %g each |" % R.EXCLUSION_COST,
             "|---|---|---|---|---|---|---|---|---|"]
    for label, r in rows:
        lines.append(f"| {label} | {r['twoWords']} | {r['twoCovered']} | {len(r['excluded'])} | {r['failedFreq']:.0f} | "
                     f"{r['benefit']:.0f} | {r['exc']} | {r['score0']:.0f} | {r['score']:.0f} |")
    lines += ["", "Most frequent excluded words (named by the pattern, fall back to plain `ment`) per scope:"]
    for label, r in rows:
        lines.append(f"- {label}: {', '.join(r['excluded'][:8]) or '-'}")
    open(OUT_SCORES, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))

    # per-syllable marginal: all-1-stroke baseline + this one previous syllable as 2-stroke
    zero = score(set())
    bySyll: dict[str, list[int]] = {}
    for i, s in prevOf.items():
        bySyll.setdefault(s, []).append(i)
    freqOf = {c.rec.idx: c.rec.frequency for c in ones}
    order = sorted(bySyll, key=lambda s: -sum(freqOf[i] for i in bySyll[s]))
    out = ["# -ment: marginal value of giving each previous syllable the 2-stroke form", "",
           f"Reference (nobody 2-stroke): score {zero['score']:.0f}. d = score with only this syllable 2-stroke minus that.",
           "`in list` = the syllable is in the current enumerated rule.", "",
           "| prev syllable | words | freq | d score | excluded | in list | examples |", "|---|---|---|---|---|---|---|"]
    for s in order:
        ids = bySyll[s]
        r = score(set(ids))
        ex = ", ".join(c.rec.ortho for c in sorted((c for c in ones if c.rec.idx in set(ids)),
                                                     key=lambda c: -c.rec.frequency)[:4])
        out.append(f"| `{s}` | {len(ids)} | {sum(freqOf[i] for i in ids):.1f} | {r['score'] - zero['score']:+.0f} | "
                   f"{len(r['excluded'])} excl | {'yes' if s in base else 'NO'} | {ex} |")
    open(OUT_SYLL, "w").write("\n".join(out) + "\n")
    print(f"wrote {OUT_SCORES}, {OUT_SYLL} ({len(order)} syllables) in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
