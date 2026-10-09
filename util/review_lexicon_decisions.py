"""
Interactive review of the pending lexicon decision groups (spec docs/specs/lexicon-decisions.md section 5; hand-run).
It reads `resources/lexiconDecisions.tsv` (the groups the audit miner left `pending`) and the examples sidecar
`lexicon_decision_examples.json`, shows each group, and writes your verdict to the decisions file after EVERY answer.

    python -m util.review_lexicon_decisions [--kind KIND] [--min-slots N] [--file PATH] [--examples PATH] [--list]

Groups come by descending slot count (then group id). For each: kind, level, signature, slots, precision, the `rec:`
note, up to 8 member rows (ortho  ours  ref(source)  syll_cv  orthosyll_cv) and up to 3 counter-examples.
    [y/n/s/p/d/q]   y = accept, n = reject, s = skip for now, p = set a param, then accept,
                    d = split: the group becomes `reject` (note `split: L2`) and its next-finer-level subgroups
                        are added as pending and reviewed next, q = quit.
Anything typed after the letter is stored as the note (`y fine, same as fille`). `--list` prints the pending table.
"""
import argparse
import datetime
import sys
from dataclasses import replace
from typing import Any, Callable

from src.lexicondecisions import (ACCEPT, DECISIONS_PATH, EXAMPLES_PATH, PENDING, REJECT, Decision, Decisions,
                                  loadDecisions, loadExamplesSidecar, minedDecision, saveDecisions,
                                  writeExamplesSidecar)

MAX_MEMBERS, MAX_COUNTERS = 8, 3


def pendingGroups(decisions: Decisions, kind: str | None = None, minSlots: int = 0) -> list[Decision]:
    return sorted((d for d in decisions.pending(kind) if d.slots >= minSlots), key=lambda d: (-d.slots, d.groupId))


def _precision(d: Decision) -> str:
    return f"{d.slots / (d.slots + d.counter):.2f}" if d.slots + d.counter else "n/a"


def listTable(groups: list[Decision]) -> list[str]:
    lines = ["group_id\tkind\tlevel\tslots\tcounter\tprecision\tsignature\tnote"]  # note: `rec:` says heterogeneous
    lines += [f"{d.groupId}\t{d.kind}\t{d.level}\t{d.slots}\t{d.counter}\t{_precision(d)}\t{d.signature}\t{d.note}"
              for d in groups]
    return lines


def _rowLine(r: dict[str, Any]) -> str:
    ref = r.get("ref", "") + (f"({r['refSource']})" if r.get("refSource") else "")
    return "    " + "  ".join(str(x) for x in (r.get("ortho", ""), r.get("ours", ""), ref, r.get("syllCV", ""),
                                              r.get("orthosyllCV", "")))


def show(d: Decision, entry: dict[str, Any] | None, say: Callable[[str], None]) -> None:
    say(f"\n{d.groupId}  {d.kind}  {d.level}  {d.signature}")
    heterogeneous = bool((entry or {}).get("heterogeneous"))
    say(f"  slots {d.slots}  counter {d.counter}  precision {_precision(d)}" + ("  HETEROGENEOUS" if heterogeneous else "")
        + (f"  {d.note}" if d.note else ""))
    if heterogeneous:
        say("  (the group mixes rows that match their reference with rows that do not; accepting corrects its member rows only)")
    members = (entry or {}).get("members", [])
    if members:
        say(f"  members ({min(len(members), MAX_MEMBERS)} of {len(members)}):")
        for r in members[:MAX_MEMBERS]:
            say(_rowLine(r))
    elif d.examples:
        say("  e.g. " + "; ".join(d.examples))
    counters = (entry or {}).get("counters", [])
    if counters:
        say("  counter-examples (matched their reference):")
        for r in counters[:MAX_COUNTERS]:
            say(_rowLine(r))


def _ask(ask: Callable[[str], str], prompt: str, choices: str) -> tuple[str, str]:
    """(letter, rest of the line) for the first valid letter typed."""
    while True:
        line = ask(prompt).strip()
        if line and line[0].lower() in choices:
            return line[0].lower(), line[1:].strip()


def _childDecision(parent: Decision, child: dict[str, Any]) -> Decision:
    return minedDecision(parent.kind, child["level"], child["signature"], int(child["slots"]),
                         int(child.get("counter", 0)), child.get("examples", []),
                         "rec: review (heterogeneous)" if child.get("heterogeneous") else "rec: review")


def review(
    decisions: Decisions, path: str, examples: dict[str, dict[str, Any]], examplesPath: str | None = None,
    ask: Callable[[str], str] = input, say: Callable[[str], None] = print, today: str | None = None,
    kind: str | None = None, minSlots: int = 0,
) -> Decisions:
    """Reviews the pending groups in order, saving `path` after every answer (and the sidecar after a split)."""
    today = today or datetime.date.today().isoformat()
    queue = pendingGroups(decisions, kind, minSlots)
    total = len(queue)
    n = 0
    while queue:
        d = queue.pop(0)
        n += 1
        say(f"\n=== {n}/{total}")
        show(d, examples.get(d.groupId), say)
        while True:
            a, note = _ask(ask, "  accept? [y/n/s/p/d/q] ", "ynspdq")
            if a == "q":
                return decisions
            if a == "s":
                break
            if a == "d":
                children = (examples.get(d.groupId) or {}).get("children", [])
                if not children:
                    say("  no finer subgroups known for this group.")
                    continue
                added: list[Decision] = []
                for c in children:
                    cd = _childDecision(d, c)
                    existing = decisions.get(cd.groupId)
                    decisions = decisions.withEntry(existing if existing is not None else cd)
                    if existing is None or existing.verdict == PENDING:
                        added.append(existing or cd)
                    examples[cd.groupId] = {k: c[k] for k in ("members", "counters", "children") if k in c}
                decisions = decisions.withEntry(replace(d, verdict=REJECT, date=today, note=note or f"split: {children[0]['level']}"))
                saveDecisions(decisions, path)
                if examplesPath:
                    writeExamplesSidecar(examplesPath, examples)
                say(f"  split into {len(added)} pending subgroup(s) of level {children[0]['level']}")
                queue = sorted(added, key=lambda x: (-x.slots, x.groupId)) + queue
                total += len(added)
                break
            param = ""
            if a == "p":
                param = ask("  param: ").strip()
            decisions = decisions.withEntry(replace(
                d, verdict=ACCEPT if a in "yp" else REJECT, param=param, date=today, note=note or d.note))
            saveDecisions(decisions, path)
            break
    return decisions


def main(argv: list[str] | None = None, ask: Callable[[str], str] = input, say: Callable[[str], None] = print) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", default=DECISIONS_PATH)
    ap.add_argument("--examples", default=EXAMPLES_PATH)
    ap.add_argument("--kind")
    ap.add_argument("--min-slots", type=int, default=0)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)
    decisions = loadDecisions(args.file)
    groups = pendingGroups(decisions, args.kind, args.min_slots)
    if args.list:
        for line in listTable(groups):
            say(line)
        return 0
    if not groups:
        say("nothing pending: the lexicon decisions cover every mined group.")
        return 0
    review(decisions, args.file, loadExamplesSidecar(args.examples), args.examples, ask, say,
           kind=args.kind, minSlots=args.min_slots)
    return 0


if __name__ == "__main__":
    sys.exit(main())
