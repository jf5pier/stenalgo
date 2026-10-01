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
from src.affixdecisions import APART, DECISIONS_PATH, AnchorDecision, Decisions, loadDecisions, saveDecisions
from src.keyboard import Starboard
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
) -> Decisions:
    today = today or datetime.date.today().isoformat()
    for n, item in enumerate(items, 1):
        say(f"\n=== {n}/{len(items)}: {item.line()}")
        decisions, quit_ = reviewItem(item, decisions, proposer, path, today, ask, say)
        if quit_:
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
    items = [Pending(**d) for d in store["selection"]["pending"] if not args.only or d["kind"] == args.only]
    if args.limit:
        items = items[:args.limit]
    if not items:
        print("nothing pending: the affix decisions cover the 30 selected rules.")
        return 0
    decisions = loadDecisions(args.decisions)
    proposer = _realProposer(args.decisions, store["selection"]["rules"])
    review(items, decisions, proposer, args.decisions)
    print("\nrerun `python -m util.build_affix_rules` (cached evaluations are reused) to see what is still pending.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
