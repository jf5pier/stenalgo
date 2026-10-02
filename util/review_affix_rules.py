"""
Interactive review of the undecided affix fusions and growth forms (hand-run; the only affix command that asks
questions). It reads the pending items that `util.build_affix_rules` left in `AffixSelection.pickle` (only the
30 selected rules are reviewed), shows each proposal with how much it helps and hurts, and writes your verdicts
to the committed `affix_decisions.json` after EVERY answer. It never deletes the pickle: rerun
`python -m util.build_affix_rules` afterwards (cheap: cached rule evaluations are reused) and repeat until
nothing is pending.

    PYTHONPATH=. env/bin/python -m util.review_affix_rules [--only growth|fusion] [--limit N]

For each proposal:  `helps N words freq F | hurts N fb freq F, N exc | net +N | similar rule: ...`
    accept? [y/n/s/q]   y = accept (growth: then its best extension is offered), n = refuse (never proposed again),
                        s = skip for now, q = quit.   An optional one-line note is stored with the verdict.
"""
import argparse
import datetime
import sys
from dataclasses import replace
from typing import Callable

from src import affixes as A
from src import affixproposals as P
from src.affixbinding import PhonemeKeys, enumerateKeypresses
from src.affixdecisions import (APART, DECISIONS_PATH, AnchorDecision, Decisions, fileMd5, loadDecisions,
                                saveDecisions)
from src.keyboard import Starboard
from util import build_affix_rules
from util.build_affix_rules import KEYBOARD_JSON, STORE_PICKLE, Pending, loadStore

Proposer = Callable[[Pending, Decisions], P.Proposal | None]


def _numbersOf(p: P.Proposal) -> dict[str, object]:
    return {"net": round(p.net), "helpsWords": p.helpsWords, "helpsFreq": round(p.helpsFreq),
            "hurtsFallbacks": p.hurtsFallbacks, "hurtsExceptions": p.hurtsExceptions}


def _show(p: P.Proposal, say: Callable[[str], None]) -> None:
    say(f"\n{p.kind} {p.position} `{p.spellings}` /{p.phono}/: {p.label}")
    say("  " + p.line())
    if p.examples:
        say("  e.g. " + ", ".join(p.examples))
    for note in p.notes:
        say("  " + note)
    if p.rows:
        say("  per addition:" if p.kind == "growth" else "  per added spelling:")
        for row in p.rows:
            say("    " + row.line())
    if p.alternatives:
        say("  next best: " + "; ".join(f"{label} ({net:+.0f})" for label, net in p.alternatives))


def _ask(prompt: str, ask: Callable[[str], str], choices: str = "ynsq") -> str:
    while True:
        a = ask(prompt).strip().lower()[:1]
        if a and a in choices:
            return a


def reviewItem(
    item: Pending, decisions: Decisions, proposer: Proposer, path: str, today: str,
    ask: Callable[[str], str] = input, say: Callable[[str], None] = print,
) -> tuple[Decisions, bool]:
    """Review one pending item; returns (decisions, quit). The decisions file is saved after every answer."""
    while True:
        proposal = proposer(item, decisions)
        if proposal is None:
            return _nothingToPropose(item, decisions, path, today, ask, say), False
        _show(proposal, say)
        if proposal.kind == "fusion" and proposal.groups and proposal.evaluateSubset is not None:
            decisions, outcome = _reviewSpellings(item, proposal, decisions, path, today, ask, say)
            return decisions, outcome == "quit"
        if proposal.kind == "growth" and proposal.groups:
            decisions, outcome = _reviewGroups(item, proposal, decisions, path, today, ask, say)
            if outcome == "quit":
                return decisions, True
            if outcome == "skip":
                return decisions, False
            continue                       # offer the next proposal (an extension, or the next best form)
        a = _ask("  accept? [y/n/s/q] ", ask)
        if a == "q":
            return decisions, True
        if a == "s":
            return decisions, False
        note = ask("  note (optional): ").strip()
        entry = proposal.entry
        entry.note, entry.date, entry.numbers = note, today, _numbersOf(proposal)
        if a == "y":
            decisions = decisions.withEntry(entry)
            saveDecisions(decisions, path)
            if proposal.kind == "fusion":
                return decisions, False
            continue                       # growth: offer the best extension of what was just accepted
        if proposal.kind == "fusion":
            refusal = AnchorDecision(item.position, item.spellings, item.phono, APART, [], [proposal.label], note, today,
                                     _numbersOf(proposal))
            decisions = decisions.withEntry(refusal)
            saveDecisions(decisions, path)
            return decisions, False
        existing = decisions.get(item.position, item.spellings, item.phono) or AnchorDecision(
            item.position, item.spellings, item.phono, "fused" if "|" in item.spellings else "-", None)
        decisions = decisions.withEntry(replace(
            existing, refused=sorted(set(existing.refused) | {proposal.label}), note=note or existing.note, date=today))
        saveDecisions(decisions, path)


def _reviewGroups(
    item: Pending, proposal: P.Proposal, decisions: Decisions, path: str, today: str,
    ask: Callable[[str], str], say: Callable[[str], None],
) -> tuple[Decisions, str]:
    """One accept line per grown (anchor spelling + neighbour syllable) group; the accepted groups become the
    growth form(s), the refused ones are never proposed again. Returns (decisions, "done" | "skip" | "quit")."""
    accepted: list[tuple[str, str]] = []
    refused: list[str] = []
    net = 0.0
    for row in proposal.rows:
        group = proposal.groups.get(row.label)
        if group is None:
            continue
        a = _ask(f"  {row.label} (net {row.net:+.0f}): accept? [y/n/s/q] ", ask)
        if a == "q":
            return decisions, "quit"
        if a == "s":
            return decisions, "skip"
        if a == "y":
            accepted.append(group)
            net += row.net
        else:
            refused.append(row.label)
    note = ask("  note (optional): ").strip()
    existing = decisions.get(item.position, item.spellings, item.phono) or AnchorDecision(
        item.position, item.spellings, item.phono, "fused" if "|" in item.spellings else "-", None)
    growth = existing.growth
    numbers = dict(existing.numbers)
    if accepted:
        growth = (growth or []) + P.formsForGroups(root_of(proposal), accepted)
        numbers = {"acceptedGroups": [f"{sp} + /{ph}/" for sp, ph in accepted], "groupNet": round(net)}
    decisions = decisions.withEntry(replace(
        existing, growth=growth, refused=sorted(set(existing.refused) | set(refused)),
        note=note or existing.note, date=today, numbers=numbers))
    saveDecisions(decisions, path)
    say(f"  saved: {len(accepted)} group(s) accepted, {len(refused)} refused")
    return decisions, "done"


def _reviewSpellings(
    item: Pending, proposal: P.Proposal, decisions: Decisions, path: str, today: str,
    ask: Callable[[str], str], say: Callable[[str], None],
) -> tuple[Decisions, str]:
    """One accept line per ADDED spelling of a fusion. The accepted ones are merged with the rules' own spellings
    (a sub-merge: evaluated and confirmed before it is saved); the refused ones stay out. Returns (decisions, outcome)."""
    accepted: list[str] = []
    refused: list[str] = []
    for row in proposal.rows:
        a = _ask(f"  {row.label} (net {row.net:+.0f}): accept? [y/n/s/q] ", ask)
        if a == "q":
            return decisions, "quit"
        if a == "s":
            return decisions, "skip"
        (accepted if a == "y" else refused).append(row.label)
    note = ask("  note (optional): ").strip()
    assert proposal.evaluateSubset is not None
    full = proposal.spellings
    if not accepted:
        decisions = decisions.withEntry(AnchorDecision(item.position, full, item.phono, APART, [], refused, note, today,
                                                       _numbersOf(proposal)))
        saveDecisions(decisions, path)
        say(f"  saved: `{full}` stays apart (no spelling accepted)")
        return decisions, "done"
    sub = proposal.evaluateSubset(accepted)
    if sub is not proposal:
        _show(sub, say)
        if _ask(f"  save the merge `{sub.spellings}` (net {sub.net:+.0f})? [y/n] ", ask, "yn") == "n":
            return decisions, "skip"
    sub.entry.note, sub.entry.date, sub.entry.numbers = note, today, _numbersOf(sub)
    sub.entry.refused = sorted(refused)
    decisions = decisions.withEntry(sub.entry)
    if sub.spellings != full:       # the greedy full merge is settled too: apart
        decisions = decisions.withEntry(AnchorDecision(item.position, full, item.phono, APART, [], sorted(refused), note,
                                                       today, _numbersOf(proposal)))
    saveDecisions(decisions, path)
    say(f"  saved: merge `{sub.spellings}` fused" + (f"; refused spellings: {', '.join(refused)}" if refused else ""))
    return decisions, "done"


def root_of(proposal: P.Proposal) -> A.Candidate:
    """formsForGroups only reads `root.ortho` (merged or single): a stand-in carrying it."""
    return A.Candidate(proposal.position, 1, proposal.phono, proposal.spellings)


def _nothingToPropose(
    item: Pending, decisions: Decisions, path: str, today: str, ask: Callable[[str], str], say: Callable[[str], None],
) -> Decisions:
    entry = decisions.get(item.position, item.spellings, item.phono)
    if item.kind == "fusion":
        say(f"\nfusion {item.position} `{item.spellings}`: nothing to compare with; it stays apart (undecided).")
        return decisions
    if entry is not None and entry.growth is not None:
        say(f"\ngrowth `{item.spellings}`: no further proposal; growth stays as decided.")
        return decisions
    say(f"\ngrowth {item.position} `{item.spellings}` /{item.phono}/: no proposal with a positive net.")
    if _ask("  record 'no growth' for it? [y/n] ", ask, "yn") == "y":
        verdict = "fused" if "|" in item.spellings else "-"
        base = entry or AnchorDecision(item.position, item.spellings, item.phono, verdict, None)
        decisions = decisions.withEntry(replace(
            base, growth=[], date=today, note=base.note or "no growth: no proposal with a positive net (review)"))
        saveDecisions(decisions, path)
    return decisions


def review(
    items: list[Pending], decisions: Decisions, proposer: Proposer, path: str,
    ask: Callable[[str], str] = input, say: Callable[[str], None] = print, today: str | None = None,
    outcome: list[str] | None = None,
) -> Decisions:
    """Reviews the items in order. `outcome` (if given) receives "quit" when the user quit, or "fusion" when a fusion
    verdict was saved and the pass stopped there: the later items may be stale, the caller reselects first."""
    today = today or datetime.date.today().isoformat()
    for n, item in enumerate(items, 1):
        say(f"\n=== {n}/{len(items)}: {item.line()}")
        before = decisions
        decisions, quit_ = reviewItem(item, decisions, proposer, path, today, ask, say)
        if quit_:
            if outcome is not None:
                outcome.append("quit")
            break
        if item.kind == "fusion" and decisions is not before and outcome is not None:
            outcome.append("fusion")
            break
    return decisions


def _realProposer(decisionsPath: str, rules: list[dict]) -> Proposer:  # type: ignore[type-arg]
    """Loads the theory once (~30 s) and returns the proposer over the engine."""
    from util._theoryio import loadPhoneticAndDisambiguatedTheory
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; run from the repo root.")
    print("loading the stable theory ...", flush=True)
    phonetic, disambiguated, _w, _l = loadPhoneticAndDisambiguatedTheory(starboard)
    records, _skipped = A.extractRecords(phonetic, disambiguated)
    seedPairs, _fams = A.loadSeeds()
    pool = A.buildCandidates(records, seedPairs, decisions=loadDecisions(decisionsPath))
    ctx = A.SimContext(starboard, records)
    pk = PhonemeKeys(starboard)
    keypresses = enumerateKeypresses(starboard, ctx)
    keysOf = {(r["position"], r["ortho"], r["phono"]): tuple(r["keys"]) for r in rules}
    selected = frozenset((r["position"], r["ortho"], r["phono"]) for r in rules)
    byKey = {(c.position, c.ortho, c.phono): c for c in pool.values() if c.k == 1}

    def propose(item: Pending, decisions: Decisions) -> P.Proposal | None:
        root = byKey.get((item.position, item.spellings, item.phono))
        if root is None:
            print(f"  `{item.spellings}` is no longer in the pool; skipped")
            return None
        if item.kind == "fusion":
            return P.proposeFusion(root, pool, decisions, pk, ctx, keypresses, selected, lambda m: print(m, flush=True))
        keys = keysOf.get((item.position, item.spellings, item.phono))
        if keys is None:
            return None
        return P.proposeGrowth(root, decisions, keys, ctx)

    return propose


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--decisions", default=DECISIONS_PATH)
    ap.add_argument("--pickle", default=STORE_PICKLE)
    ap.add_argument("--only", choices=["growth", "fusion"])
    ap.add_argument("--limit", type=int)
    args = ap.parse_args(argv)
    store = loadStore(args.pickle)
    if store is None:
        print(f"{args.pickle} not found: run `python -m util.build_affix_rules` first.")
        return 1
    # loops by itself: review, save, reselect (cached evaluations: about a minute), continue with what is newly
    # pending, until nothing is pending, the user quits, or a pass changed no verdict
    while True:
        items = [Pending(**d) for d in store["selection"]["pending"] if not args.only or d["kind"] == args.only]
        if args.limit:
            items = items[:args.limit]
        if not items:
            print("nothing pending: the affix decisions cover the selected rules.")
            return 0
        md5Before = fileMd5(args.decisions)
        decisions = loadDecisions(args.decisions)
        proposer = _realProposer(args.decisions, store["selection"]["rules"])
        outcome: list[str] = []
        review(items, decisions, proposer, args.decisions, outcome=outcome)
        if "quit" in outcome:
            print("\nquit: rerun `python -m util.build_affix_rules` to reselect with your verdicts.")
            return 0
        if fileMd5(args.decisions) == md5Before:
            print("\nno verdict was saved in this pass (everything skipped): stopping.")
            return 0
        print("\nreselecting with your verdicts ...", flush=True)
        build_affix_rules.main(["--decisions", args.decisions, "--pickle", args.pickle])
        store = loadStore(args.pickle)
        if store is None:
            return 1


if __name__ == "__main__":
    sys.exit(main())
