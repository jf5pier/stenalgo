"""
Affix abbreviation scan: discovery (Part A) then keypress binding (Part B).

MEASUREMENT AND PROPOSALS ONLY -- nothing here changes the pipeline. Every output goes under
scratch/. See PLAN_2026-09-26-affix-abbreviations.md.

    PYTHONPATH=. env/bin/python -m util.affix_scan [--refresh] [--part a|b|all] [--seeds-only]

Outputs: scratch/affix-records.pickle (cache), affix-families.pickle (Part A result, read by
Part B), affix-candidates.tsv, affix-families.tsv, affix_bindings.json, affix-bindings-report.md.
"""
import argparse
import json
import os
import pickle
import resource
import sys
import time

from src import affixbinding as B
from src import affixes as A
from src.keyboard import Starboard, Stroke, Strokes
from util._stenorender import renderFinalStrokesToRTFCRE
from util._theoryio import loadPhoneticAndDisambiguatedTheory

RECORDS = "scratch/affix-records.pickle"
FAMILIES_PICKLE = "scratch/affix-families.pickle"
CANDIDATES_TSV = "scratch/affix-candidates.tsv"
FAMILIES_TSV = "scratch/affix-families.tsv"
BINDINGS_JSON = "scratch/affix_bindings.json"
REPORT_MD = "scratch/affix-bindings-report.md"
LATTICE_TRACE_TXT = "scratch/affix-lattice-trace.txt"
CANDIDATE_RULES_TSV = "scratch/affix-candidate-rules.tsv"
RULE_PREVIEW_MD = "scratch/affix-rules-preview.md"
RULE_PREVIEW_COUNT = 30  # top-N by proxy score that get the expensive exact (keypress) evaluation
RULES_TSV = "scratch/affix-rules.tsv"           # Phase 3+4 final output (DESIGN §7.1)
RULES_REPORT_MD = "scratch/affix-rules-report.md"
POOL_PICKLE = "scratch/affix-pool.pickle"        # non-legacy Part A result, reused by --reuse-pool
SWEEP_DIR = "scratch/affix-sweep"
SWEEP_SETTINGS = (   # plan 2026-09-28 U6; stroke-frequency units, top rules score ~5,000-9,000
    ("L", 1.0, 5.0, 10.0),      # (name, EXCEPTION_ALPHA, EXCLUSION_COST, FORM_COST); L = today's
    ("M", 1.0, 50.0, 100.0),
    ("H", 2.0, 150.0, 300.0),
)

# Prototype strict frequency per seed family (RESUME_2026-09-26-pluvier-affix-scan.md).
PROTOTYPE_STRICT = {
    "suffix -ité": 901.4, "suffix -tion": 589.1, "prefix Latin": 367.5,
    "prefix ex-": 151.3, "suffix -ment": 127.8, "suffix -logie": 101.1,
}


def loadStarboard() -> Starboard:
    sb = Starboard.fromJSONFile("starboard3h.json")
    assert sb is not None
    return sb


def loadRecords(starboard: Starboard, refresh: bool) -> list[A.WordRecord]:
    if os.path.exists(RECORDS) and not refresh:
        with open(RECORDS, "rb") as f:
            return pickle.load(f)  # type: ignore[no-any-return]
    t = time.time()
    phonetic, disambiguated = loadPhoneticAndDisambiguatedTheory(starboard)
    records, skipped = A.extractRecords(phonetic, disambiguated)
    print(f"records: {len(records)} extracted, {skipped} skipped ({time.time() - t:.0f}s)")
    with open(RECORDS, "wb") as f:
        pickle.dump(records, f)
    return records


def _writeLatticeTrace(cands: dict) -> None:  # type: ignore[type-arg]
    """DESIGN §3.6: the full lineage chain for the regression case -- every node whose ortho
    ends in 'té' and whose lineage (grownFromKey chain) contains a slot matching 'li'."""
    byKey = {(c.position, c.k, c.phono, c.ortho): c for c in cands.values()}

    def lineageHasLi(c: A.Candidate) -> bool:
        cur: A.Candidate | None = c
        while cur is not None:
            if any(s.kind == "exact" and s.value == "li" for s in cur.slots):
                return True
            cur = byKey.get(cur.grownFromKey) if cur.grownFromKey else None
        return False

    lines = []
    for c in sorted(cands.values(), key=lambda c: (-c.grownDepth, -c.freq)):
        if not c.ortho.endswith("té") or not lineageHasLi(c):
            continue
        chain = []
        cur: A.Candidate | None = c
        while cur is not None:
            chain.append(cur)
            cur = byKey.get(cur.grownFromKey) if cur.grownFromKey else None
        chain.reverse()
        lines.append("  " * 0 + " -> ".join(
            f"{x.ortho} (k={x.k} lemmas={x.lemmas} freq={x.freq:.1f})" for x in chain))
    with open(LATTICE_TRACE_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))


def partA(records: list[A.WordRecord], seedsOnly: bool, legacy: bool) -> tuple[dict, list[A.Family]]:  # type: ignore[type-arg]
    t = time.time()
    seedPairs, seedFams = A.loadSeeds()
    cands = A.buildCandidates(records, seedPairs, seedsOnly, legacy=legacy)
    tA = time.time() - t
    print(f"candidates: {len(cands)} ({tA:.0f}s)")
    if not legacy:
        anchors = [c for c in cands.values() if c.isAnchor]
        mergedKept = [c for c in anchors if c.mergeParts]
        print(f"pool {len(cands)} nodes, {len(anchors)} anchors; variant merges: "
              f"{len(mergedKept)} kept, {A.BUILD_STATS['mergesDropped']} dropped by the conflict test "
              f"({A.BUILD_STATS['mergesProposed']} proposed); key-collision renames "
              f"{A.LATTICE_STATS['renames']}, folded duplicates {A.LATTICE_STATS['duplicates']}, "
              f"generated {A.LATTICE_STATS['generated']}; GROWTH_MIN_EXPAND={A.GROWTH_MIN_EXPAND}; "
              f"Part A {tA:.0f}s, peak RSS {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024:.0f} MB")
        with open(POOL_PICKLE, "wb") as pf:
            pickle.dump(cands, pf)
        if len(cands) > A.MAX_POOL:
            print(f"CHECKPOINT: candidate pool {len(cands)} exceeds MAX_POOL={A.MAX_POOL}; stopping.")
            sys.exit(2)
        if tA > 600:
            print(f"CHECKPOINT: Part A took {tA:.0f}s (> 10 min); stopping.")
            sys.exit(2)
        _writeLatticeTrace(cands)
    with open(CANDIDATES_TSV, "w", encoding="utf-8") as f:
        if legacy:
            f.write("position\tk\tphono\tortho\tisSeed\tcarriers\tlemmas\tfreq\ttopExamples\tgeneralizedFrom\n")
            for c in sorted(cands.values(), key=lambda c: -c.strokeFreq):
                f.write(f"{c.position}\t{c.k}\t{c.phono}\t{c.ortho}\t{int(c.isSeed)}\t{len(c.carriers)}\t"
                        f"{c.lemmas}\t{c.freq:.1f}\t{' '.join(c.examples)}\t{','.join(c.variants)}\n")
        else:
            f.write("position\tk\tphono\tortho\tisSeed\tcarriers\tlemmas\tfreq\ttopExamples\t"
                    "slots\tgrownFrom\troot\taliases\tmarginal\texceptionCount\texceptionFreq\t"
                    "isAnchor\tattestedShare\tmergeParts\tnewConflictFreq\n")
            for c in sorted(cands.values(), key=lambda c: -c.strokeFreq):
                slotsLabel = ",".join(A.slotLabel(s) for s in c.slots)
                grownFrom = "/".join(map(str, c.grownFromKey)) if c.grownFromKey else ""
                root = "/".join(map(str, c.rootKey)) if c.rootKey else ""
                aliases = ";".join("/".join(map(str, a)) for a in c.aliases)
                f.write(f"{c.position}\t{c.k}\t{c.phono}\t{c.ortho}\t{int(c.isSeed)}\t{len(c.carriers)}\t"
                        f"{c.lemmas}\t{c.freq:.1f}\t{' '.join(c.examples)}\t{slotsLabel}\t{grownFrom}\t"
                        f"{root}\t{aliases}\t{c.freq:.1f}\t{c.exceptionCount}\t{c.exceptionFreq:.1f}\t"
                        f"{int(c.isAnchor)}\t{c.attestedShare:.3f}\t"
                        f"{';'.join('/'.join(map(str, k)) for k in c.mergeParts)}\t{c.newConflictFreq:.1f}\n")
    if not legacy:
        return cands, []   # the family/unify machinery only serves --legacy
    t = time.time()
    fams = A.discoverFamilies(cands, seedFams)
    print(f"families: {len(fams)} ({time.time() - t:.0f}s)")
    with open(FAMILIES_TSV, "w", encoding="utf-8") as f:
        f.write("family_id\tposition\tmembers\tstemCompetitionSubgroups\tcompeting_pairs\tcarriers\tfreq\t"
                "upperBoundStrokeFreq\tseedOverlap\treview\n")
        for fam in fams:
            members = " ".join(f"{m.ortho}/{m.phono}/{m.freq:.0f}" for m in fam.members)
            subs = " | ".join(",".join(fam.members[i].ortho for i in g) for g in fam.stemSubgroups)
            comp = " ; ".join(f"{fam.members[i].ortho}~{fam.members[j].ortho}:{m:.0f}({','.join(st[:3])})"
                              for i, j, m, st in fam.competingPairs[:5])
            f.write(f"{fam.familyId}\t{fam.position}\t{members}\t{subs}\t{comp}\t{len(fam.carriers)}\t"
                    f"{fam.freq:.1f}\t{fam.upperBound:.1f}\t{'; '.join(fam.seedOverlap)}\t\n")
    with open(FAMILIES_TSV, "a", encoding="utf-8") as f:   # seed families, as reference rows
        byAffix = {(c.position, c.ortho): c for c in sorted(cands.values(), key=lambda c: c.strokeFreq)}
        for name, aff in seedFams.items():
            ms = [byAffix[a] for a in aff if a in byAffix]
            if not ms:
                continue
            pooled = A.poolCarriers(ms)
            members = " ".join(f"{m.ortho}/{m.phono}/{m.freq:.0f}" for m in ms)
            ub = sum(c.rec.frequency * c.span for c in pooled)
            f.write(f"SEED:{name}\t{ms[0].position}\t{members}\t\t\t{len(pooled)}\t"
                    f"{sum(c.rec.frequency for c in pooled):.1f}\t{ub:.1f}\t\t\n")
    with open(FAMILIES_PICKLE, "wb") as f:
        pickle.dump(fams, f)
    print("top 30 families by upper bound (sum freq x span):")
    for fam in fams[:30]:
        print(f"  {fam.familyId} {fam.upperBound:9.1f} sub={len(fam.stemSubgroups)} "
              + " ".join(m.ortho for m in fam.members[:8]))
    return cands, fams


def partRules(cands: dict, records: list[A.WordRecord], starboard: Starboard) -> list:  # type: ignore[type-arg]
    """Phase 2 (DESIGN §4): build one proxy-scored candidate rule per pool node (cheap, every
    root), then run the expensive exact (keypress) evaluation lazily on just the top
    `RULE_PREVIEW_COUNT` by proxy score, as a preview of what Phase 3's selection heap would do.
    Phase 3 (budgeted selection) and Phase 4 (keypress binding with sharing) are NOT run here."""
    from src import affixrules as R

    t = time.time()
    idx = R.childrenIndex(cands)
    rules = [R.buildCandidateRule(root, idx) for root in cands.values()]
    rules.sort(key=lambda r: -r.score)
    print(f"phase 2: {len(rules)} candidate rules (proxy score) ({time.time() - t:.0f}s)")
    with open(CANDIDATE_RULES_TSV, "w", encoding="utf-8") as f:
        f.write("position\troot\trootK\tforms\tnumForms\tproxyScore\n")
        for r in rules:
            formsLabel = " | ".join(f"{fm.ortho}(k={fm.k})" for fm in r.forms)
            f.write(f"{r.position}\t{r.root.ortho}\t{r.root.k}\t{formsLabel}\t{len(r.forms)}\t{r.score:.1f}\n")

    t = time.time()
    ctx = A.SimContext(starboard, records)
    pk = B.PhonemeKeys(starboard)
    keypresses = B.enumerateKeypresses(starboard, ctx)
    print(f"{len(keypresses)} legal keypresses ({time.time() - t:.0f}s)")
    preview = [r for r in rules if r.score > 0][:RULE_PREVIEW_COUNT]
    t = time.time()
    for r in preview:
        R.chooseRuleKeypress(r, pk, ctx, keypresses)
    print(f"phase 2 preview: exact-scored top {len(preview)} roots ({time.time() - t:.0f}s)")

    lines = ["# Phase 2 preview: candidate rules, exact-scored (top by proxy score, DESIGN §4.4)",
             "", "Phase 3 (budgeted selection) and Phase 4 (keypress sharing) are not run here -- "
             "these are standalone one-rule-at-a-time evaluations, not a selection.", ""]
    for r in preview:
        rtfcre = rtfcreOfKeys(starboard, r.keys) if r.keys else "(no legal key found)"
        lines.append(f"## {r.position} root `{r.root.ortho}` (k={r.root.k}) -- keys {r.keys} = `{rtfcre}`")
        lines.append("")
        lines.append("forms: " + ", ".join(f"`{fm.ortho}`(k={fm.k})" for fm in r.forms))
        lines.append(f"- score {r.score:.1f}, strokeFreqSaved {r.strokeFreqSaved:.1f}, "
                     f"word exceptions {r.wordExceptions} (freq {r.exceptionFreq:.1f})")
        if r.topExceptions:
            lines.append(f"- top exceptions: {', '.join(r.topExceptions[:10])}")
        for res in sorted(r.results, key=lambda x: -x.carrier.rec.frequency)[:8]:
            w = res.carrier.rec
            if res.gain <= 0 or res.newBase is None:
                continue
            new = A.withMarks(res.newBase, w.markKeys) + w.extra
            lines.append(f"    {w.ortho}: {_render(starboard, A.fullStrokesOf(w))} -> {_render(starboard, new)}")
        lines.append("")
    with open(RULE_PREVIEW_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {CANDIDATE_RULES_TSV}, {RULE_PREVIEW_MD}")
    return rules


def _topGramCats(rule, n: int = 3) -> str:  # type: ignore[no-untyped-def]
    """Frequency share of the rule's top-`n` grammatical categories among its carriers."""
    shares: dict[str, float] = {}
    carriers = A.poolCarriers(rule.forms)
    total = sum(c.rec.frequency for c in carriers) or 1.0
    for c in carriers:
        cat = c.rec.gramCat.replace("GramCat.", "")
        shares[cat] = shares.get(cat, 0.0) + c.rec.frequency
    top = sorted(shares.items(), key=lambda kv: -kv[1])[:n]
    return ", ".join(f"{cat} {v / total:.0%}" for cat, v in top)


def selectAndBind(cands: dict, records: list[A.WordRecord], starboard: Starboard,  # type: ignore[type-arg]
                  ctx: A.SimContext, pk: B.PhonemeKeys, keypresses: list[Stroke], lemmas: A.LemmaIndex,
                  rulesTsv: str, reportMd: str) -> dict:  # type: ignore[type-arg]
    """Variant-rival resolution, Phase 3 (§5, budgeted selection) + Phase 4 (§6, keypress binding
    with sharing) over the pool, at the CURRENT `affixrules` weights. Writes `rulesTsv` and
    `reportMd`; returns a summary for the sweep comparison."""
    from src import affixrules as R

    ruleCache: dict = {}  # type: ignore[type-arg]
    t = time.time()
    anchors, decisions = R.resolveVariantRivals(cands, pk, ctx, keypresses, ruleCache)
    print(f"variant rivals: {sum(d.outcome == 'fused' for d in decisions)} fused, "
          f"{sum(d.outcome == 'apart' for d in decisions)} apart, "
          f"{sum(d.outcome == 'outOfReach' for d in decisions)} out of reach; "
          f"{len(anchors)} anchors remain ({time.time() - t:.0f}s)")
    t = time.time()
    result = R.selectRules(cands, pk, ctx, keypresses, budget=R.RULE_BUDGET, curveLength=40,
                           anchors=anchors, ruleCache=ruleCache)
    print(f"phase 3: {len(result.selected)} rules selected, "
          f"{result.evaluatedExactCount} roots exact-evaluated ({time.time() - t:.0f}s)")
    t = time.time()
    result = R.swapPass(result)
    print(f"phase 3 swap pass: done ({time.time() - t:.0f}s)")

    t = time.time()
    bound = R.bindKeypresses(result.selected, ctx)
    print(f"phase 4: {len(bound)} rules bound ({time.time() - t:.0f}s)")

    # Sibling-pair list (§4.1 "out of scope for v1"): selected rules whose roots look related by
    # A3's own candidateSim but aren't in a grow lineage of one another.
    def _stemsOf(root: A.Candidate) -> frozenset:  # type: ignore[type-arg]
        return frozenset(sorted(root.stemFreq, key=lambda s: -root.stemFreq[s])[:A.MAX_STEMS_FOR_JACCARD])

    siblingPairs = []
    for i, br1 in enumerate(bound):
        for br2 in bound[i + 1:]:
            if br1.rule.position != br2.rule.position:
                continue
            sim = A.candidateSim(br1.rule.root, br2.rule.root, _stemsOf(br1.rule.root), _stemsOf(br2.rule.root))
            if sim >= A.FAMILY_LINK_SIM:
                siblingPairs.append((sim, br1.rule.root.ortho, br2.rule.root.ortho))
    siblingPairs.sort(key=lambda t: -t[0])

    bound.sort(key=lambda b: -(b.rule.score or 0.0))
    attested = {id(b.rule): A.attestedShareOf(b.rule.position, A.poolCarriers(b.rule.forms), lemmas)
                for b in bound}
    exceptionRates = {}
    for b in bound:
        cov = sum(1 for r in b.rule.results if r.gain > 0)
        exc = sum(1 for r in b.rule.results if r.reason in R.WORD_EXCEPTION_REASONS)
        exceptionRates[id(b.rule)] = exc / (cov + exc) if cov + exc else 0.0
    pseudo = [b for b in bound if attested[id(b.rule)] < 0.5]
    os.makedirs(os.path.dirname(rulesTsv), exist_ok=True)
    with open(rulesTsv, "w", encoding="utf-8") as f:
        f.write("rank\tposition\troot\tforms\tkeys\trtfcre\tsharedWith\tscore\tstrokeFreqSaved\t"
                "keySimilarity\twordExceptions\texceptionFreq\ttopExceptions\tcarriers\tlemmas\texamples\t"
                "attestedShare\n")
        for rank, b in enumerate(bound, 1):
            r = b.rule
            forms = " | ".join(f"{fm.ortho}(k={fm.k})" for fm in r.forms)
            carriers = A.poolCarriers(r.forms)
            lemmaCount = len({c.rec.lemme for c in carriers})
            f.write(f"{rank}\t{r.position}\t{r.root.ortho}\t{forms}\t{b.keys}\t"
                    f"{rtfcreOfKeys(starboard, b.keys)}\t{';'.join(b.sharedWith)}\t{r.score:.1f}\t"
                    f"{r.strokeFreqSaved:.1f}\t{r.keySimilarity:.2f}\t{r.wordExceptions}\t{r.exceptionFreq:.1f}\t"
                    f"{','.join(r.topExceptions[:10])}\t{len(carriers)}\t{lemmaCount}\t"
                    f"{' '.join(c.rec.ortho for c in carriers[:6])}\t{attested[id(r)]:.3f}\n")

    lines = ["# Affix rules (Phase 3 + 4 result, DESIGN_2026-09-27-affix-rule-selection.md; "
             "single-generator pool, PLAN_2026-09-28)", "",
             f"Constants: RULE_BUDGET={R.RULE_BUDGET}, MAX_RULE_FORMS={R.MAX_RULE_FORMS}, "
             f"EXCEPTION_ALPHA={R.EXCEPTION_ALPHA}, EXCLUSION_COST={R.EXCLUSION_COST}, "
             f"FORM_COST={R.FORM_COST}, SWAP_CANDIDATES={R.SWAP_CANDIDATES}, "
             f"SWAP_PASSES={R.SWAP_PASSES}, RULE_OVERLAP_MAX={R.RULE_OVERLAP_MAX}, "
             f"MAX_EXCEPTION_RATE={R.MAX_EXCEPTION_RATE}, GROWTH_MIN_EXPAND={A.GROWTH_MIN_EXPAND}, "
             f"GROWTH_MAX_DEPTH={A.GROWTH_MAX_DEPTH}, MAX_SLOT_EXCLUSIONS={A.MAX_SLOT_EXCLUSIONS}, "
             f"GROWTH_MAX_EXCEPTION_SHARE={A.GROWTH_MAX_EXCEPTION_SHARE}.", "",
             "Note: bare verb-infinitive-ending candidates (isVerbEndingFragment) are left "
             "UNFILTERED, per the user's 2026-09-27 decision to let them compete on score.", "",
             f"Selected rules with attestedShare < 0.5 (the old stem-attestation filter would have "
             f"rejected most of their carriers; candidate pseudo-affixes like `ma-`): **{len(pseudo)}**"
             + (" -- " + ", ".join(f"`{b.rule.root.ortho}`" for b in pseudo) if pseudo else ""), "",
             "## Savings curve (cumulative total after each acceptance, 1..40)", "",
             ", ".join(f"{v:.0f}" for v in result.curve), ""]
    for rank, b in enumerate(bound, 1):
        r = b.rule
        lines.append(f"## {rank}. {r.position} `{r.root.ortho}` -- keys {b.keys} = "
                     f"`{rtfcreOfKeys(starboard, b.keys)}`" + (f" (shares with {', '.join(b.sharedWith)})" if b.sharedWith else ""))
        lines.append("")
        lines.append("forms: " + ", ".join(f"`{fm.ortho}`(k={fm.k})" for fm in r.forms))
        mnemonicFlag = " -- NOT phonetically motivated (SIM_TOP_N pick below SIM_MIN)" if r.keySimilarity < 0.5 else ""
        lines.append(f"- score {r.score:.1f}, strokeFreqSaved {r.strokeFreqSaved:.1f}, "
                     f"keySimilarity {r.keySimilarity:.2f}{mnemonicFlag}")
        lines.append(f"- attestedShare {attested[id(r)]:.2f}; exception rate {exceptionRates[id(r)]:.1%}; "
                     f"top categories: {_topGramCats(r)}")
        if r.root.mergeParts:
            lines.append(f"- fused spelling variants: {', '.join(r.root.variants)} "
                         f"(new conflict freq {r.root.newConflictFreq:.1f})")
        lines.append(f"- word exceptions {r.wordExceptions} (freq {r.exceptionFreq:.1f})")
        if r.topExceptions:
            lines.append(f"- top exceptions: {', '.join(r.topExceptions[:10])}")
        for res in sorted(r.results, key=lambda x: -x.carrier.rec.frequency)[:6]:
            w = res.carrier.rec
            if res.gain <= 0 or res.newBase is None:
                continue
            new = A.withMarks(res.newBase, w.markKeys) + w.extra
            lines.append(f"    {w.ortho}: {_render(starboard, A.fullStrokesOf(w))} -> {_render(starboard, new)}")
        lines.append("")
    lines += ["## Sibling pairs (candidateSim >= FAMILY_LINK_SIM, out of scope for v1)", ""]
    for sim, a, bo in siblingPairs[:20]:
        lines.append(f"- {a} ~ {bo} (sim {sim:.2f})")

    lines += ["", "## Variant rivals (merged spelling-variant anchors vs their parts, U3b)", ""]
    for d in decisions:
        scores = ("" if d.mergedScore is None and d.mainScore is None else
                  f"; merged score {d.mergedScore if d.mergedScore is None else round(d.mergedScore)} vs "
                  f"main {d.mainScore if d.mainScore is None else round(d.mainScore)}")
        lines.append(f"- `{d.merged}` (parts {', '.join(d.parts)}; new conflict freq "
                     f"{d.newConflictFreq:.1f}){scores}: **{d.outcome}**")
        if d.mergedForms or d.mainForms:
            lines.append(f"    merged forms: {', '.join(d.mergedForms)}; main forms: {', '.join(d.mainForms)}")
    if not decisions:
        lines.append("- none")

    # No two selected same-position rules may overlap this much (R.RULE_OVERLAP_MAX): regression check.
    overlaps = sorted(((R.territoryOverlap(b1.rule, b2.rule), b1.rule.root.ortho, b2.rule.root.ortho)
                       for i, b1 in enumerate(bound) for b2 in bound[i + 1:]), reverse=True)
    lines += ["", f"## Overlaps among selected rules (must all be < {R.RULE_OVERLAP_MAX})", ""]
    lines += [f"- {a} ~ {bo}: {ov:.2f}" for ov, a, bo in overlaps if ov >= 0.05] or ["- none >= 0.05"]
    lines += ["", f"## Overlap skips during selection ({len(result.overlapSkips)})", ""]
    lines += [f"- {sk.skippedRoot} skipped for overlapping {sk.selectedRoot} ({sk.overlap:.2f})"
              for sk in result.overlapSkips] or ["- none"]
    with open(reportMd, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {rulesTsv}, {reportMd}")
    return {
        "curve20": result.curve[19] if len(result.curve) >= 20 else None,
        "curve30": result.curve[29] if len(result.curve) >= 30 else None,
        "rules": [(b.rule.position, b.rule.root.ortho) for b in bound],
        "forms": {(b.rule.position, b.rule.root.ortho): [fm.ortho for fm in b.rule.forms] for b in bound},
        "numForms": sum(len(b.rule.forms) for b in bound),
        "exclusions": sum(R.exclusionCountOf(b.rule.forms) for b in bound),
        "wordExceptions": sum(b.rule.wordExceptions for b in bound),
        "pseudo": [(b.rule.position, b.rule.root.ortho) for b in pseudo],
        "maxExceptionRate": max(exceptionRates.values(), default=0.0),
        "maxOverlap": max((ov for ov, _a, _b in overlaps), default=0.0),
    }


def _engine(cands: dict, records: list[A.WordRecord], starboard: Starboard):  # type: ignore[no-untyped-def,type-arg]
    ctx = A.SimContext(starboard, records)
    pk = B.PhonemeKeys(starboard)
    keypresses = B.enumerateKeypresses(starboard, ctx)
    print(f"{len(keypresses)} legal keypresses")
    return ctx, pk, keypresses, A.LemmaIndex({r.lemme for r in records})


def partSelectAndBind(cands: dict, records: list[A.WordRecord], starboard: Starboard) -> None:  # type: ignore[type-arg]
    """One selection + binding at the module's current weights -- the STOP deliverable."""
    ctx, pk, keypresses, lemmas = _engine(cands, records, starboard)
    selectAndBind(cands, records, starboard, ctx, pk, keypresses, lemmas, RULES_TSV, RULES_REPORT_MD)


def partSweep(cands: dict, records: list[A.WordRecord], starboard: Starboard) -> None:  # type: ignore[type-arg]
    """U6: run rival resolution + Phases 3-4 once per weight setting, reusing the pool, sim
    context, phoneme keys and keypress list; every Rule is rebuilt per setting (scores depend on
    the weights, which are module globals). Writes scratch/affix-sweep/<name>/... + comparison.md."""
    from src import affixrules as R

    ctx, pk, keypresses, lemmas = _engine(cands, records, starboard)
    saved = (R.EXCEPTION_ALPHA, R.EXCLUSION_COST, R.FORM_COST)
    summaries: dict[str, dict] = {}  # type: ignore[type-arg]
    try:
        for name, alpha, exclCost, formCost in SWEEP_SETTINGS:
            R.EXCEPTION_ALPHA, R.EXCLUSION_COST, R.FORM_COST = alpha, exclCost, formCost
            print(f"=== sweep {name}: EXCEPTION_ALPHA={alpha} EXCLUSION_COST={exclCost} FORM_COST={formCost}")
            outDir = os.path.join(SWEEP_DIR, name)
            summaries[name] = selectAndBind(cands, records, starboard, ctx, pk, keypresses, lemmas,
                                            os.path.join(outDir, "affix-rules.tsv"),
                                            os.path.join(outDir, "affix-rules-report.md"))
    finally:
        R.EXCEPTION_ALPHA, R.EXCLUSION_COST, R.FORM_COST = saved
    writeComparison(summaries)


def writeComparison(summaries: dict) -> None:  # type: ignore[type-arg]
    names = list(summaries)
    weights = {n: (a, e, f) for n, a, e, f in SWEEP_SETTINGS}
    L = ["# Weight sweep comparison (U6)", "",
         "Credited saving = cumulative word-once-credited total from the selection curve (before the "
         "swap pass), in stroke-frequency units.", "",
         "| setting | EXCEPTION_ALPHA | EXCLUSION_COST | FORM_COST | saving @20 | saving @30 | forms | "
         "exclusions | word exceptions | attestedShare<0.5 | max exception rate | max overlap |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for n in names:
        s = summaries[n]
        c20 = "n/a" if s["curve20"] is None else f"{s['curve20']:.0f}"
        c30 = "n/a" if s["curve30"] is None else f"{s['curve30']:.0f}"
        L.append(f"| {n} | {weights[n][0]} | {weights[n][1]} | {weights[n][2]} | {c20} | {c30} | "
                 f"{s['numForms']} | {s['exclusions']} | {s['wordExceptions']} | {len(s['pseudo'])} | "
                 f"{s['maxExceptionRate']:.1%} | {s['maxOverlap']:.2f} |")
    L += ["", "## Rules selected in any setting, by rank", "",
          "| rule | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    everyRule = sorted({r for s in summaries.values() for r in s["rules"]},
                       key=lambda r: min((summaries[n]["rules"].index(r) if r in summaries[n]["rules"] else 999)
                                         for n in names))
    for r in everyRule:
        cells = [str(summaries[n]["rules"].index(r) + 1) if r in summaries[n]["rules"] else "—" for n in names]
        L.append(f"| {r[0]} `{r[1]}` | " + " | ".join(cells) + " |")
    L += ["", "## Rules selected in every setting whose forms differ between settings", ""]
    common = [r for r in everyRule if all(r in summaries[n]["rules"] for n in names)]
    differing = [r for r in common if len({tuple(summaries[n]["forms"][r]) for n in names}) > 1]
    for r in differing:
        L.append(f"- {r[0]} `{r[1]}`")
        for n in names:
            L.append(f"    - {n}: {', '.join(summaries[n]['forms'][r])}")
    if not differing:
        L.append("- none")
    L += ["", "## Pseudo-affix rules (attestedShare < 0.5) per setting", ""]
    for n in names:
        L.append(f"- {n}: " + (", ".join(f"`{o}`" for _p, o in summaries[n]["pseudo"]) or "none"))
    path = os.path.join(SWEEP_DIR, "comparison.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print(f"wrote {path}")


def rtfcreOfKeys(starboard: Starboard, keys: Stroke) -> str:
    try:
        return str(starboard.strokesToRTFCRE((tuple(keys),)))
    except Exception:
        return "".join(starboard.keyDisplayName(k) for k in keys)


def partB(records: list[A.WordRecord], fams: list[A.Family], starboard: Starboard, unify: bool = True) -> None:
    t0 = time.time()
    ctx = A.SimContext(starboard, records)
    pk = B.PhonemeKeys(starboard)
    keypresses = B.enumerateKeypresses(starboard, ctx)
    allKeys = B.phonemeKeys(starboard)
    print(f"{len(keypresses)} legal keypresses ({time.time() - t0:.0f}s)")
    options: dict[str, list[B.Option]] = {}
    for n, fam in enumerate(fams, 1):
        t = time.time()
        options[fam.familyId] = B.familyOptions(fam, pk, ctx, keypresses, allKeys)
        best = options[fam.familyId][0].metrics.strokeFreqSaved if options[fam.familyId] else 0.0
        print(f"  [{n}/{len(fams)}] {fam.familyId} best={best:.1f} ({time.time() - t:.1f}s)", flush=True)
    merges: list[B.Merge] = []
    if unify:
        t = time.time()
        fams, options, growthMerged, growthRejected = B.growthMerges(fams, options, pk, ctx, keypresses, allKeys)
        print(f"growth merges: {len(growthMerged)} accepted, {len(growthRejected)} rejected ({time.time() - t:.0f}s)")
        t = time.time()
        fams, options, merges, rejected = B.unifyFamilies(fams, options, pk, ctx, keypresses, allKeys)
        print(f"unified: {len(merges)} merges accepted, {len(rejected)} rejected ({time.time() - t:.0f}s)")
        with open("scratch/affix-merges.tsv", "w", encoding="utf-8") as f:
            f.write("verdict\ta\tb\tcosine\tseparateGain\tunionGain\torphanMembers\n")
            for verdict, ms in (("growth-merged", growthMerged), ("growth-rejected", growthRejected),
                                ("merged", merges), ("rejected", rejected)):
                for m in ms:
                    f.write(f"{verdict}\t{m.a}\t{m.b}\t{m.cosine:.2f}\t{m.separateGain:.1f}\t{m.unionGain:.1f}\t"
                            f"{','.join(m.orphans)}\n")
    assigned, unbound = B.assignGreedy(fams, options, ctx)
    assigned.sort(key=lambda a: -a.option.metrics.strokeFreqSaved)
    print(f"bound {len(assigned)} families, unbound {len(unbound)} ({time.time() - t0:.0f}s)")

    def rec(a: B.Assigned) -> dict:  # type: ignore[type-arg]
        fam, opt = a.fam, a.option
        m = opt.metrics
        return {
            "family_id": fam.familyId, "position": fam.position,
            "members": [f"{x.ortho}/{x.phono}/{x.freq:.0f}" for x in fam.members],
            "subgroups": [{
                "members": [fam.members[i].ortho for i in s.members], "kind": s.binding.kind,
                "keys": list(s.binding.keys), "rtfcre": rtfcreOfKeys(starboard, s.binding.keys),
                "sim": round(s.sim, 3), "comfortCost": round(s.comfort, 1)} for s in opt.subgroups],
            "strokeFreqSaved": round(m.strokeFreqSaved, 1), "freqBenefiting": round(m.freqBenefiting, 1),
            "familyFreq": round(fam.freq, 1), "benefitShare": round(m.benefitShare, 3),
            "benefitShareCount": round(m.benefitShareCount, 3),
            "fallbacks": m.fallbacks, "boundaryRisks": m.boundaryRisks,
            "alternatives": [{"keys": [list(s.binding.keys) for s in o.subgroups],
                              "kind": o.subgroups[0].binding.kind, "sim": round(o.sim, 3),
                              "strokeFreqSaved": round(o.metrics.strokeFreqSaved, 1)}
                             for o in options[fam.familyId]],
            "alternativeIndex": a.alternativeIndex,
        }

    out = {"constants": B.constantsHeader(), "bound": [rec(a) for a in assigned],
           "unbound": [{"family_id": f.familyId, "position": f.position,
                        "members": [x.ortho for x in f.members[:8]], "upperBound": round(f.upperBound, 1),
                        "hadOptions": bool(options.get(f.familyId))} for f in unbound]}
    with open(BINDINGS_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    writeReport(assigned, unbound, options, starboard, ctx, out)


def _render(starboard: Starboard, strokes: Strokes) -> str:
    return str(renderFinalStrokesToRTFCRE(starboard, strokes))


def writeReport(assigned: list[B.Assigned], unbound: list[A.Family], options: dict[str, list[B.Option]],
                starboard: Starboard, ctx: A.SimContext, out: dict) -> None:  # type: ignore[type-arg]
    L: list[str] = ["# Affix abbreviation bindings (measurement and proposals only)", "",
                    "Constants: " + ", ".join(f"{k}={v}" for k, v in out["constants"].items()), "",
                    "Words carrying both a prefix and a suffix binding are simulated independently.", ""]
    for a, r in zip(assigned, out["bound"]):
        fam, opt = a.fam, a.option
        L.append(f"## {fam.familyId} ({fam.position}) -- {', '.join(x.ortho for x in fam.members[:10])}")
        L.append("")
        for s, sj in zip(opt.subgroups, r["subgroups"]):
            L.append(f"- {sj['kind']} keys {sj['keys']} = `{sj['rtfcre']}` for "
                     f"{', '.join(sj['members'])} (sim {sj['sim']}, comfort {sj['comfortCost']})")
        L.append(f"- strokeFreqSaved {r['strokeFreqSaved']}, freqBenefiting {r['freqBenefiting']} of {r['familyFreq']} "
                 f"(share by freq {r['benefitShare']}, by count {r['benefitShareCount']}), "
                 f"boundary risks {r['boundaryRisks']}")
        L.append(f"- fallbacks: {r['fallbacks']}")
        L.append("- alternatives: " + "; ".join(
            f"{alt['kind']} {alt['keys']} sim {alt['sim']} saved {alt['strokeFreqSaved']}" for alt in r["alternatives"]))
        L.append("")
        ex = sorted((x for res in opt.results for x in res if x.gain > 0),
                    key=lambda x: -x.carrier.rec.frequency)[:10]
        for x in ex:
            w = x.carrier.rec
            assert x.newBase is not None
            new = A.withMarks(x.newBase, w.markKeys) + w.extra
            L.append(f"    {w.ortho}: {_render(starboard, A.fullStrokesOf(w))} -> {_render(starboard, new)}")
        L.append("")
    L += ["## Unbound families", ""]
    for uf in unbound[:40]:
        why = "no positive-gain option" if not options.get(uf.familyId) else "all alternatives conflicted"
        L.append(f"- {uf.familyId} ({uf.position}) {' '.join(m.ortho for m in uf.members[:6])}: "
                 f"upper bound {uf.upperBound:.0f}, {why}")
    L += ["", "## Prototype seed families", "",
          "| seed family | prototype strict freq | bound family | new freqBenefiting | note |", "|---|---|---|---|---|"]
    for seed, proto in PROTOTYPE_STRICT.items():
        hit = [r for r in out["bound"]
               if any(seed in name for name in _overlap(assigned, r["family_id"]))]
        if hit:
            best = max(hit, key=lambda r: r["freqBenefiting"])
            note = (f"{best['subgroups'][0]['kind']} binding; benefit share {best['benefitShare']}; "
                    f"fallbacks {best['fallbacks']}")
            L.append(f"| {seed} | {proto} | {best['family_id']} | {best['freqBenefiting']} | {note} |")
        else:
            ub = [u for u in unbound if any(seed in n for n in u.seedOverlap)]
            L.append(f"| {seed} | {proto} | unbound | 0 | "
                     f"{'no positive-gain option or conflict (' + ub[0].familyId + ')' if ub else 'no family'} |")
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print(f"wrote {REPORT_MD}, {BINDINGS_JSON}")


def _overlap(assigned: list[B.Assigned], familyId: str) -> list[str]:
    for a in assigned:
        if a.fam.familyId == familyId:
            return a.fam.seedOverlap
    return []


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--part", choices=["a", "b", "all"], default="all")
    ap.add_argument("--seeds-only", action="store_true")
    ap.add_argument("--no-unify", action="store_true", help="skip the family unification study")
    ap.add_argument("--legacy", action="store_true",
                     help="run the old growth+unify+assign pipeline unchanged, for comparison "
                          "(DESIGN_2026-09-27-affix-rule-selection.md); the lattice path is the default")
    ap.add_argument("--max-pool", type=int, default=None, help="override src.affixes.MAX_POOL")
    ap.add_argument("--growth-min-expand", type=float, default=None,
                    help="override src.affixes.GROWTH_MIN_EXPAND (lattice path)")
    ap.add_argument("--preview-only", action="store_true",
                     help="Phase 2 only (top-30 exact-scored preview); skip Phase 3/4")
    ap.add_argument("--reuse-pool", action="store_true",
                     help=f"--part b: load {POOL_PICKLE} (written by --part a) instead of rebuilding Part A")
    ap.add_argument("--sweep", action="store_true",
                     help="--part b: run selection at each SWEEP_SETTINGS weight setting "
                          f"and write {SWEEP_DIR}/")
    args = ap.parse_args()
    if args.max_pool is not None:
        A.MAX_POOL = args.max_pool
    if args.growth_min_expand is not None:
        A.GROWTH_MIN_EXPAND = args.growth_min_expand
    t = time.time()
    starboard = loadStarboard()
    records = loadRecords(starboard, args.refresh)
    cands: dict | None = None  # type: ignore[type-arg]
    fams: list[A.Family] = []
    if args.legacy:
        if args.part in ("a", "all") or not os.path.exists(FAMILIES_PICKLE):
            cands, fams = partA(records, args.seeds_only, True)
            if len(fams) < 5 or len(fams) > 300:
                print(f"CHECKPOINT: {len(fams)} families (outside 5..300); thresholds are probably wrong. Stopping.")
                sys.exit(2)
        else:
            with open(FAMILIES_PICKLE, "rb") as f:
                fams = pickle.load(f)
        if args.part in ("b", "all"):
            partB(records, fams, starboard, not args.no_unify)
    else:
        if args.part in ("a", "all"):
            cands, _ = partA(records, args.seeds_only, False)
        if args.part in ("b", "all"):
            if cands is None and args.reuse_pool and os.path.exists(POOL_PICKLE):
                with open(POOL_PICKLE, "rb") as f:
                    cands = pickle.load(f)
            elif cands is None:
                seedPairs, _seedFams = A.loadSeeds()
                cands = A.buildCandidates(records, seedPairs, args.seeds_only, legacy=False)
            if args.preview_only:
                partRules(cands, records, starboard)
            elif args.sweep:
                partSweep(cands, records, starboard)
            else:
                partSelectAndBind(cands, records, starboard)
    print(f"total {time.time() - t:.0f}s")


if __name__ == "__main__":
    main()
