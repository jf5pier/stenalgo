"""
Affix Abbreviation Building (S9), part a: select the 30 affix rules and bind their keypresses.

    python -m util.build_affix_rules [--decisions PATH] [--pickle PATH] [--rules PATH] [--report PATH]

Inputs: the stable theory (as `util.export_plover_dictionary`), `starboard3h.json`, the lexicons, and the committed
`affix_decisions.json` (the user's verdicts: fusions of spelling variants, growth forms, see `src/affixdecisions.py`).
Outputs: `affix_rules.json` (the 30 rules and their keys, read by `util.export_affix_dictionary`),
`affix_rules_report.md` (deterministic, no timings) and the cache `AffixSelection.pickle` (gitignored).

Cache convention (like Dictionary.pickle / elicitation_answers.json):
- `AffixSelection.pickle` absent: full selection (~25 min: exact keypress evaluation of ~40 candidate rules).
  `rm AffixSelection.pickle` forces it; after ANY lexicon or layout change the cached evaluations are wrong. A
  lexicon/layout fingerprint mismatch only WARNS here (never an automatic rerun).
- present and made from the current `affix_decisions.json` (md5 stored with the final selection): the final
  selection is reused as is.
- present but the decisions changed: the selection reruns (seconds) and reuses every cached per-rule evaluation;
  only rules whose forms or verdict changed, and new roots, are evaluated again (~30 s each).
Nothing here asks a question: an undecided growth or fusion gets the safe default (anchor alone, merge kept
apart) and is listed as PENDING; `python -m util.review_affix_rules` is the hand-run command that decides them.
"""
import argparse
import hashlib
import json
import os
import pickle
import sys
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from src import affixbinding as B
from src import affixes as A
from src import affixrules as R
from src.affixdecisions import (
    APART, DECISIONS_PATH, Decisions, fileMd5, inputFingerprint, loadDecisions)
from src.keyboard import Starboard, Stroke, Strokes
from util._stenorender import renderFinalStrokesToRTFCRE

RULES_JSON = "affix_rules.json"
REPORT_MD = "affix_rules_report.md"
STORE_PICKLE = "AffixSelection.pickle"
STORE_VERSION = 1
KEYBOARD_JSON = "starboard3h.json"

RuleKey = tuple[str, int, str, str]


# ═══════════════════════════════════════════════════════════════════════════
# Pending items
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Pending:
    """A growth or fusion decision the user has not made yet, for one of the selected rules."""
    kind: str                # "growth" | "fusion"
    position: str
    spellings: str
    phono: str
    detail: str = ""

    def line(self) -> str:
        return f"{self.kind} {self.position} `{self.spellings}` /{self.phono}/" + (f" -- {self.detail}" if self.detail else "")


def closestDecided(decisions: Decisions, position: str, spellings: str, phono: str) -> str | None:
    """The decided merge (same position and sound) whose spelling set overlaps `spellings` most, for the pending
    line of a merge whose exact set matches no decision (a lexicon change added or dropped a spelling)."""
    mine = set(spellings.split("|"))
    best: tuple[float, str] | None = None
    for e in decisions.entries.values():
        if e.position != position or e.phono != phono or "|" not in e.spellings:
            continue
        theirs = set(e.spellings.split("|"))
        j = len(mine & theirs) / len(mine | theirs)
        if j > 0 and (best is None or (j, e.spellings) > best):
            best = (j, e.spellings)
    return best[1] if best else None


def pendingItems(
    bound: list[R.BoundRule], rivals: list[R.RivalDecision], decisions: Decisions,
) -> list[Pending]:
    """Undecided items among the selected rules: a rule whose anchor has no growth verdict, and an undecided merge
    one of whose spellings is a selected rule's anchor (its parts stay apart until the user decides)."""
    items: list[Pending] = []
    selected = {(b.rule.position, b.rule.root.phono, b.rule.root.ortho) for b in bound}
    for b in bound:
        root = b.rule.root
        if not root.hasDecision:
            items.append(Pending("growth", root.position, root.ortho, root.phono, "no growth verdict: anchor alone"))
    for d in rivals:
        if not d.pending or not any((d.position, d.phono, p) in selected for p in d.parts):
            continue
        near = closestDecided(decisions, d.position, d.merged, d.phono)
        items.append(Pending("fusion", d.position, d.merged, d.phono,
                             "parts " + ", ".join(d.parts) + (f"; closest decided merge `{near}`" if near else "")))
    # growth BEFORE fusion: a fusion is judged with its parts' decided growth (`té` grows into `lité` before it is
    # fused with `ter`), and a fused merge inherits the growth of its parts
    items.sort(key=lambda p: (p.kind != "growth", p.position, p.phono, p.spellings))
    return items


# ═══════════════════════════════════════════════════════════════════════════
# Per-rule cache
# ═══════════════════════════════════════════════════════════════════════════

def ruleSignature(rule: R.Rule, decisions: Decisions) -> tuple[str, ...]:
    """What an exact evaluation of this rule depends on: its anchor, its verdict and growth forms (as strings),
    and the exact carrier set (so a lexicon change that moves one carrier is a different signature)."""
    root = rule.root
    entry = decisions.get(root.position, root.ortho, root.phono)
    growth = None if entry is None or entry.verdict == APART or entry.growth is None else [f.toJson() for f in entry.growth]
    carriers = sorted((c.rec.idx, c.start, c.span, c.member) for c in A.poolCarriers(rule.forms))
    digest = hashlib.md5(repr(carriers).encode()).hexdigest()
    return (root.position, root.phono, root.ortho, entry.verdict if entry else "?",
            json.dumps(growth, sort_keys=True, ensure_ascii=False), digest)


def compactEvaluation(rule: R.Rule) -> dict[str, Any]:
    """The exact evaluation of an evaluated rule as plain tuples (no object graph)."""
    return {
        "keys": rule.keys, "score": rule.score, "strokeFreqSaved": rule.strokeFreqSaved,
        "wordExceptions": rule.wordExceptions, "exceptionFreq": rule.exceptionFreq,
        "topExceptions": list(rule.topExceptions), "fallbacks": rule.fallbacks,
        "keySimilarity": rule.keySimilarity, "alternatives": list(rule.alternatives),
        "results": [(r.carrier.rec.idx, r.carrier.start, r.carrier.span, r.carrier.member, r.gain, r.reason,
                     r.newBase, r.markCost, r.boundaryRisk, list(r.partners), r.mergedSaving)
                    for r in rule.results],
    }


def restoreEvaluation(rule: R.Rule, ev: dict[str, Any]) -> None:
    """Fill `rule` (freshly built from the pool) with a cached exact evaluation."""
    lookup: dict[tuple[int, int, int], A.Carrier] = {}
    for form in rule.forms:
        for c in form.carriers:
            lookup[(c.rec.idx, c.start, c.span)] = c
    rule.exactDone = True
    rule.keys, rule.score, rule.strokeFreqSaved = ev["keys"], ev["score"], ev["strokeFreqSaved"]
    rule.wordExceptions, rule.exceptionFreq = ev["wordExceptions"], ev["exceptionFreq"]
    rule.topExceptions, rule.fallbacks = list(ev["topExceptions"]), ev["fallbacks"]
    rule.keySimilarity, rule.alternatives = ev["keySimilarity"], list(ev["alternatives"])
    rule.results = [
        A.CarrierResult(lookup[(idx, start, span)]._replace(member=member), gain, reason, newBase, markCost,
                        boundaryRisk, list(partners), mergedSaving)
        for idx, start, span, member, gain, reason, newBase, markCost, boundaryRisk, partners, mergedSaving
        in ev["results"]]


def currentWeights() -> dict[str, float]:
    """The code constants every cached evaluation and the selection depend on."""
    return {"alpha": R.EXCEPTION_ALPHA, "exclusion": R.EXCLUSION_COST, "form": R.FORM_COST,
            "maxExceptionRate": R.MAX_EXCEPTION_RATE, "budget": R.RULE_BUDGET, "overlapMax": R.RULE_OVERLAP_MAX,
            "swapCandidates": R.SWAP_CANDIDATES, "swapPasses": R.SWAP_PASSES,
            "keyShortlist": R.MAX_ALTERNATIVES}


# ═══════════════════════════════════════════════════════════════════════════
# Selection
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Outcome:
    bound: list[R.BoundRule]
    result: R.SelectionResult
    rivals: list[R.RivalDecision]
    pending: list[Pending]
    evaluations: dict[tuple[str, ...], dict[str, Any]]    # the evaluations used or made in this run
    evaluatedNow: int = 0                                  # rules evaluated by chooseRuleKeypress in this run
    log: list[str] = field(default_factory=list)


def selectAndBind(
    pool: dict[RuleKey, A.Candidate], decisions: Decisions, ctx: A.SimContext, pk: B.PhonemeKeys,
    keypresses: list[Stroke], evaluations: dict[tuple[str, ...], dict[str, Any]] | None = None,
) -> Outcome:
    """Rivals by verdict, budgeted selection over the anchors (cached evaluations reused), swap pass, binding."""
    anchors, rivals = R.resolveVariantRivals(pool, decisions)
    cached = evaluations or {}
    cache: dict[RuleKey, R.Rule] = {}
    evaluatedNow = 0

    def evaluate(rule: R.Rule) -> None:
        """The exact evaluation of one rule: restored from the cache when its signature is known, else computed."""
        nonlocal evaluatedNow
        ev = cached.get(ruleSignature(rule, decisions))
        if ev is not None:
            restoreEvaluation(rule, ev)
        else:
            R.chooseRuleKeypress(rule, pk, ctx, keypresses)
            evaluatedNow += 1

    result = R.selectRules(pool, pk, ctx, keypresses, budget=R.RULE_BUDGET, curveLength=40,
                           anchors=anchors, ruleCache=cache, evaluate=evaluate)
    result = R.swapPass(result)
    bound = R.bindKeypresses(result.selected, ctx)
    bound.sort(key=lambda b: -(b.rule.score or 0.0))
    used = {ruleSignature(r, decisions): compactEvaluation(r) for r in cache.values() if r.exactDone}
    return Outcome(bound, result, rivals, pendingItems(bound, rivals, decisions), used, evaluatedNow)


# ═══════════════════════════════════════════════════════════════════════════
# Outputs
# ═══════════════════════════════════════════════════════════════════════════

def rtfcreOfKeys(starboard: Starboard, keys: Stroke) -> str:
    try:
        return str(starboard.strokesToRTFCRE((tuple(keys),)))
    except Exception:
        return "".join(starboard.keyDisplayName(k) for k in keys)


def _render(starboard: Starboard, strokes: Strokes) -> str:
    return str(renderFinalStrokesToRTFCRE(starboard, strokes))


def _topGramCats(rule: R.Rule, n: int = 3) -> str:
    shares: dict[str, float] = {}
    carriers = A.poolCarriers(rule.forms)
    total = sum(c.rec.frequency for c in carriers) or 1.0
    for c in carriers:
        cat = c.rec.gramCat.replace("GramCat.", "")
        shares[cat] = shares.get(cat, 0.0) + c.rec.frequency
    top = sorted(shares.items(), key=lambda kv: (-kv[1], kv[0]))[:n]
    return ", ".join(f"{cat} {v / total:.0%}" for cat, v in top)


def rulesJson(bound: list[R.BoundRule]) -> list[dict[str, Any]]:
    return [{"rank": rank, "position": b.rule.position, "ortho": b.rule.root.ortho, "phono": b.rule.root.phono,
             "keys": list(b.keys)} for rank, b in enumerate(bound, 1)]


def buildReport(
    outcome: Outcome, decisions: Decisions, pool: dict[RuleKey, A.Candidate], starboard: Starboard,
    lemmas: A.LemmaIndex,
) -> str:
    """The deterministic markdown report (no timings, no dates): rules, their forms and examples, rivals, pending."""
    bound, result = outcome.bound, outcome.result
    attested = {id(b.rule): A.attestedShareOf(b.rule.position, A.poolCarriers(b.rule.forms), lemmas) for b in bound}
    exceptionRates: dict[int, float] = {}
    for b in bound:
        cov = sum(1 for r in b.rule.results if r.gain > 0)
        exc = sum(1 for r in b.rule.results if r.reason in R.WORD_EXCEPTION_REASONS)
        exceptionRates[id(b.rule)] = exc / (cov + exc) if cov + exc else 0.0
    pseudo = [b for b in bound if attested[id(b.rule)] < 0.5]
    lines = ["# Affix rules (selection and keypress binding)", "",
             f"Constants: RULE_BUDGET={R.RULE_BUDGET}, EXCEPTION_ALPHA={R.EXCEPTION_ALPHA}, "
             f"EXCLUSION_COST={R.EXCLUSION_COST}, FORM_COST={R.FORM_COST}, SWAP_CANDIDATES={R.SWAP_CANDIDATES}, "
             f"SWAP_PASSES={R.SWAP_PASSES}, RULE_OVERLAP_MAX={R.RULE_OVERLAP_MAX}, "
             f"MAX_EXCEPTION_RATE={R.MAX_EXCEPTION_RATE}. Growth forms and fusions come from `affix_decisions.json`.", "",
             f"Pending decisions: **{len(outcome.pending)}**" + ("" if outcome.pending else " (none)"), ""]
    lines += [f"- {p.line()}" for p in outcome.pending]
    lines += ["", f"Selected rules with attestedShare < 0.5 (candidate pseudo-affixes like `ma-`): **{len(pseudo)}**"
              + (" -- " + ", ".join(f"`{b.rule.root.ortho}`" for b in pseudo) if pseudo else ""), "",
              "## Savings curve (cumulative total after each acceptance, 1..40)", "",
              ", ".join(f"{v:.0f}" for v in result.curve), ""]
    for rank, b in enumerate(bound, 1):
        r = b.rule
        lines.append(f"## {rank}. {r.position} `{r.root.ortho}` -- keys {b.keys} = "
                     f"`{rtfcreOfKeys(starboard, b.keys)}`"
                     + (f" (shares with {', '.join(b.sharedWith)})" if b.sharedWith else ""))
        lines.append("")
        lines.append("forms: " + ", ".join(f"`{fm.ortho}`(k={fm.k})" for fm in r.forms))
        lines.append(f"- score {r.score:.1f}, strokeFreqSaved {r.strokeFreqSaved:.1f}, keySimilarity {r.keySimilarity:.2f}"
                     + (" -- NOT phonetically motivated" if r.keySimilarity < 0.5 else ""))
        lines.append(f"- attestedShare {attested[id(r)]:.2f}; exception rate {exceptionRates[id(r)]:.1%}; "
                     f"top categories: {_topGramCats(r)}")
        if r.root.mergeParts:
            lines.append(f"- fused spelling variants: {', '.join(r.root.variants)} "
                         f"(new conflict freq {r.root.newConflictFreq:.1f})")
        lines.append(f"- word exceptions {r.wordExceptions} (freq {r.exceptionFreq:.1f}); scope fallbacks {r.fallbacks}")
        if r.topExceptions:
            lines.append(f"- top exceptions: {', '.join(r.topExceptions[:10])}")
        for res in sorted(r.results, key=lambda x: (-x.carrier.rec.frequency, x.carrier.rec.idx))[:6]:
            w = res.carrier.rec
            if res.gain <= 0 or res.newBase is None:
                continue
            new = A.withMarks(res.newBase, w.markKeys) + w.extra
            lines.append(f"    {w.ortho}: {_render(starboard, A.fullStrokesOf(w))} -> {_render(starboard, new)}")
        lines.append("")
    lines += ["## Variant merges (verdicts of `affix_decisions.json`)", ""]
    for d in outcome.rivals:
        lines.append(f"- `{d.merged}` /{d.phono}/ (parts {', '.join(d.parts)}; new conflict freq "
                     f"{d.newConflictFreq:.1f}): **{d.outcome}**" + (" (undecided)" if d.pending else ""))
    if not outcome.rivals:
        lines.append("- none")
    poolMerges = {(c.position, c.ortho, c.phono) for c in pool.values() if c.mergeParts}
    stale = sorted(e.key for e in decisions.entries.values() if "|" in e.spellings and e.key not in poolMerges)
    lines += ["", "## Decided merges that are no longer in the pool (lexicon change?)", ""]
    lines += [f"- {pos} `{sp}` /{ph}/" for pos, sp, ph in stale] or ["- none"]
    overlaps = sorted(((R.territoryOverlap(b1.rule, b2.rule), b1.rule.root.ortho, b2.rule.root.ortho)
                       for i, b1 in enumerate(bound) for b2 in bound[i + 1:]), reverse=True)
    lines += ["", f"## Overlaps among selected rules (must all be < {R.RULE_OVERLAP_MAX})", ""]
    lines += [f"- {a} ~ {bo}: {ov:.2f}" for ov, a, bo in overlaps if ov >= 0.05] or ["- none >= 0.05"]
    lines += ["", f"## Overlap skips during selection ({len(result.overlapSkips)})", ""]
    lines += [f"- {sk.skippedRoot} skipped for overlapping {sk.selectedRoot} ({sk.overlap:.2f})"
              for sk in result.overlapSkips] or ["- none"]
    return "\n".join(lines) + "\n"


def writeText(path: str, text: str) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def writeOutputs(rules: list[dict[str, Any]], report: str, rulesPath: str, reportPath: str) -> None:
    writeText(rulesPath, json.dumps(rules, ensure_ascii=False, indent=1))
    writeText(reportPath, report)


# ═══════════════════════════════════════════════════════════════════════════
# The store (AffixSelection.pickle)
# ═══════════════════════════════════════════════════════════════════════════

def loadStore(path: str) -> dict[str, Any] | None:
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        store = pickle.load(f)
    if store.get("version") != STORE_VERSION:
        print(f"{path}: unknown version {store.get('version')!r}, ignored")
        return None
    return store  # type: ignore[no-any-return]


def saveStore(path: str, store: dict[str, Any]) -> None:
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        pickle.dump(store, f, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(tmp, path)


def fingerprintWarnings(stored: dict[str, str], current: dict[str, str]) -> list[str]:
    return [f"{p} changed since the affix selection was made" for p in sorted(current)
            if stored.get(p) is not None and stored[p] != current[p]]


def printPending(pending: list[Pending]) -> None:
    if not pending:
        print("affix decisions: nothing pending")
        return
    print(f"affix decisions PENDING ({len(pending)}; safe default applied; run `python -m util.review_affix_rules`):")
    for p in pending:
        print("  - " + p.line())


# ═══════════════════════════════════════════════════════════════════════════
# Driver
# ═══════════════════════════════════════════════════════════════════════════

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--decisions", default=DECISIONS_PATH)
    ap.add_argument("--pickle", default=STORE_PICKLE)
    ap.add_argument("--rules", default=RULES_JSON)
    ap.add_argument("--report", default=REPORT_MD)
    args = ap.parse_args(argv)
    t0 = time.time()
    decisions = loadDecisions(args.decisions)
    decisionsMd5 = fileMd5(args.decisions)
    fingerprint = inputFingerprint()
    weights = currentWeights()
    store = loadStore(args.pickle)
    evaluations: dict[tuple[str, ...], dict[str, Any]] = {}
    if store is not None:
        for w in fingerprintWarnings(store["fingerprint"], fingerprint):
            print(f"WARNING: {w}: `rm {args.pickle}` for a full recompute (cached evaluations are of the old input)")
        if store["weights"] != weights:
            print("affix prices/budget changed in the code: cached evaluations ignored")
        else:
            evaluations = store["evaluations"]
        sel = store["selection"]
        if sel["decisionsMd5"] == decisionsMd5 and store["weights"] == weights:
            writeOutputs(sel["rules"], sel["report"], args.rules, args.report)
            print(f"affix selection reused from {args.pickle} ({len(sel['rules'])} rules, {time.time() - t0:.0f}s)")
            printPending([Pending(**d) for d in sel["pending"]])
            return 0
        print(f"affix decisions changed: reselecting with {len(evaluations)} cached rule evaluations")
    else:
        print(f"{args.pickle} absent: full selection (~25 min)")

    from util._theoryio import loadPhoneticAndDisambiguatedTheory
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; it is a committed input -- run from the repo root.")
    phonetic, disambiguated, _wordToStrokes, _wordsByOrthoLemme = loadPhoneticAndDisambiguatedTheory(starboard)
    records, skipped = A.extractRecords(phonetic, disambiguated)
    seedPairs, _fams = A.loadSeeds()
    pool = A.buildCandidates(records, seedPairs, decisions=decisions)
    print(f"{len(records)} records ({skipped} skipped), pool {len(pool)} nodes ({time.time() - t0:.0f}s)", flush=True)
    ctx = A.SimContext(starboard, records)
    pk = B.PhonemeKeys(starboard)
    keypresses = B.enumerateKeypresses(starboard, ctx)
    print(f"{len(keypresses)} legal keypresses ({time.time() - t0:.0f}s)", flush=True)
    t1 = time.time()
    outcome = selectAndBind(pool, decisions, ctx, pk, keypresses, evaluations)
    print(f"{len(outcome.bound)} rules selected and bound; {outcome.evaluatedNow} rules evaluated now, "
          f"{len(outcome.evaluations) - outcome.evaluatedNow} from the cache ({time.time() - t1:.0f}s)", flush=True)
    lemmas = A.LemmaIndex({r.lemme for r in records})
    report = buildReport(outcome, decisions, pool, starboard, lemmas)
    rules = rulesJson(outcome.bound)
    writeOutputs(rules, report, args.rules, args.report)
    saveStore(args.pickle, {
        "version": STORE_VERSION, "fingerprint": fingerprint, "weights": weights,
        "evaluations": outcome.evaluations,
        "selection": {"decisionsMd5": decisionsMd5, "rules": rules, "report": report,
                      "pending": [asdict(p) for p in outcome.pending]}})   # plain dicts: a pickled class would be __main__.Pending
    print(f"wrote {args.rules}, {args.report}, {args.pickle} ({time.time() - t0:.0f}s)")
    printPending(outcome.pending)
    return 0


if __name__ == "__main__":
    sys.exit(main())
