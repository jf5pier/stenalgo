#!/usr/bin/env python
# coding: utf-8
"""
Writes the accepted `template` decisions (resources/lexiconDecisions.tsv, kind `template`) into resources/verbModelExceptions.tsv
(spec docs/specs/lexicon-decisions.md section 6, row `template`): one row per member lemma, status `family_template`, the
template, and the note `group <group_id>`.

A decision row does not list its member lemmas, and the proposal files are gitignored: the members are recomputed here,
deterministically, with util.propose_verb_templates (the exceptions the proposals see are the hand-curated rows only, never the
managed ones, so the groups do not shrink once their lemmas are templated). The template of a group is the decision's `param`
when set, else the template of the group.

The rows this tool manages are exactly those whose note is `group <10 hex digits>`; they sit at the end of the file under a
marker comment, sorted by lemma. Every other line (comments, header, hand-curated rows) is kept byte for byte. A lemma that
already has a hand row with a non-trusted status (needs_review, defective, skip_artifact, ...) is never overridden: it is listed
on stderr as needing an individual decision. A group that is rejected, pending, or no longer found loses its managed rows.

    python -m util.apply_template_decisions [--check] [--assume-accepted GROUP_ID,...|all --out PATH] [--exceptions PATH]

--check exits 1 when the file would change. --assume-accepted treats those pending groups as accepted, for measurement; it writes
only to the temp copy named by --out, never to the real file.
"""
import argparse
import os
import re
import sys
import tempfile
from collections.abc import Collection, Iterable
from dataclasses import dataclass
from pathlib import Path

from src.lexicondecisions import ACCEPT, DECISIONS_PATH, Decisions, loadDecisions
from src.verbparadigm import VERBISTE_TRUSTED_STATUSES, VerbModelException, loadVerbModelExceptions, parseConjugationTemplates
from src.word import Lemme
from util.lexicon_completeness import (
    MIXTE_PATH, SYNTHETIC_PATH, VERB_EXCEPTIONS_PATH, VERBISTE_CONJUGATIONS_PATH,
)
from util.propose_verb_templates import MIN_EVIDENCE, Proposal, buildGroups, run
from util._verbreferences import GLAFF_PATH, WIKTIONARY_PATH

STATUS = "family_template"
MANAGED_NOTE = re.compile(r"^group ([0-9a-f]{10})$")
MARKER = ("# --- rows below are managed by util.apply_template_decisions (accepted `template` decisions, note `group <id>`): "
          "do not edit by hand ---")
HEADER_FIELDS = ("lemme", "template", "model_sibling", "status", "note")


@dataclass(frozen=True)
class ManagedRow:
    lemme: Lemme
    template: str
    groupId: str

    def line(self) -> str:
        return "\t".join((self.lemme, self.template, "", STATUS, f"group {self.groupId}"))


def isManaged(line: str) -> bool:
    if not line or line.startswith("#"):
        return False
    fields = line.split("\t")
    return len(fields) >= 5 and fields[3] == STATUS and MANAGED_NOTE.match(fields[4]) is not None


def handLines(text: str) -> list[str]:
    """The lines of the file that this tool does not manage (managed rows and the marker dropped), trailing blanks trimmed."""
    lines = [line for line in text.split("\n") if line != MARKER and not isManaged(line)]
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def handExceptions(text: str, path: str | Path) -> dict[Lemme, VerbModelException]:
    """The hand-curated exceptions: the file as the loader reads it, minus the managed rows."""
    with tempfile.TemporaryDirectory() as tmp:
        tmpPath = os.path.join(tmp, Path(path).name)
        with open(tmpPath, "w", encoding="utf-8", newline="") as out:
            out.write("\n".join(handLines(text)) + "\n")
        return loadVerbModelExceptions(tmpPath)


def groupMembers(proposals: list[Proposal]) -> dict[str, tuple[str, list[Lemme]]]:
    """group id -> (template, sorted member lemmas) of the `proposed` groups."""
    groups, decisions = buildGroups(proposals, {})
    return {decision.groupId: (template, lemmas) for (_signature, template, lemmas, _slots), decision in zip(groups, decisions)}


def acceptedGroupIds(decisions: Decisions, assume: Collection[str] | str = ()) -> dict[str, str]:
    """group id -> template override ('' = the group's own) of the accepted `template` decisions, plus the assumed ones."""
    accepted = {d.groupId: d.param for d in decisions.accepted("template")}
    pending = [d for d in decisions.all() if d.kind == "template" and d.groupId not in accepted]
    for d in pending:
        if assume == "all" or d.groupId in assume:
            accepted[d.groupId] = d.param
    return accepted


def desiredRows(
    members: dict[str, tuple[str, list[Lemme]]], accepted: dict[str, str], hand: dict[Lemme, VerbModelException],
    templateNames: Collection[str] | None = None,
) -> tuple[list[ManagedRow], list[tuple[Lemme, str, str]]]:
    """The managed rows, sorted by lemma, and the (lemma, group id, hand status) of the members left to an individual decision."""
    rows: dict[Lemme, ManagedRow] = {}
    individual: list[tuple[Lemme, str, str]] = []
    for groupId in sorted(accepted):
        if groupId not in members:
            print(f"warning: accepted group {groupId} is not among the current proposals (stale): its rows are dropped",
                  file=sys.stderr)
            continue
        template = accepted[groupId] or members[groupId][0]
        if templateNames is not None and template not in templateNames:
            raise SystemExit(f"group {groupId}: unknown template {template!r}")
        for lemme in members[groupId][1]:
            exception = hand.get(lemme)
            if exception is not None:
                if exception.status not in VERBISTE_TRUSTED_STATUSES:
                    individual.append((lemme, groupId, exception.status or "none"))
                continue
            if lemme in rows:
                raise SystemExit(f"{lemme}: in two accepted groups ({rows[lemme].groupId}, {groupId})")
            rows[lemme] = ManagedRow(lemme, template, groupId)
    return [rows[lemme] for lemme in sorted(rows)], sorted(individual)


def render(text: str, rows: Iterable[ManagedRow]) -> str:
    lines = handLines(text)
    managed = [row.line() for row in rows]
    if managed:
        lines += [MARKER, *managed]
    return "\n".join(lines) + "\n"


def computeNewText(
    exceptionsPath: str, decisionsPath: str, assume: Collection[str] | str, sources: tuple[str, str, str, str], minEvidence: int,
) -> tuple[str, str, list[ManagedRow], list[tuple[Lemme, str, str]]]:
    with open(exceptionsPath, encoding="utf-8", newline="") as f:
        text = f.read()
    hand = handExceptions(text, exceptionsPath)
    proposals, _reasons, _unlocked = run(*sources, minEvidence, hand)
    decisions = loadDecisions(decisionsPath)
    accepted = acceptedGroupIds(decisions, assume)
    rows, individual = desiredRows(groupMembers(proposals), accepted, hand,
                                   set(parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)))
    return text, render(text, rows), rows, individual


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="exit 1 if the exceptions file would change; write nothing")
    parser.add_argument("--assume-accepted", default="", metavar="GROUP_ID,...|all",
                        help="measurement only: treat these pending groups as accepted (needs --out)")
    parser.add_argument("--out", help="write here instead of the exceptions file (required with --assume-accepted)")
    parser.add_argument("--exceptions", default=VERB_EXCEPTIONS_PATH)
    parser.add_argument("--decisions", default=DECISIONS_PATH)
    parser.add_argument("--mixte", default=MIXTE_PATH)
    parser.add_argument("--synthetic", default=SYNTHETIC_PATH)
    parser.add_argument("--wiktionary", default=WIKTIONARY_PATH)
    parser.add_argument("--glaff", default=GLAFF_PATH)
    parser.add_argument("--min-evidence", type=int, default=MIN_EVIDENCE)
    args = parser.parse_args()
    if args.assume_accepted and (not args.out or args.check):
        parser.error("--assume-accepted writes only to a temp copy: give --out PATH, without --check")
    assume: Collection[str] | str = "all" if args.assume_accepted == "all" else [g for g in args.assume_accepted.split(",") if g]
    old, new, rows, individual = computeNewText(
        args.exceptions, args.decisions, assume, (args.mixte, args.synthetic, args.wiktionary, args.glaff), args.min_evidence)
    print(f"{len(rows)} managed family_template rows from {len({r.groupId for r in rows})} accepted groups", file=sys.stderr)
    if individual:
        print(f"{len(individual)} member lemmas have a non-trusted hand row and need an individual decision:", file=sys.stderr)
        for lemme, groupId, status in individual:
            print(f"  {lemme}\tgroup {groupId}\t{status}", file=sys.stderr)
    if args.check:
        if new != old:
            print(f"{args.exceptions} would change (run python -m util.apply_template_decisions)", file=sys.stderr)
            raise SystemExit(1)
        return
    target = args.out or args.exceptions
    if new != old or args.out:
        with open(target, "w", encoding="utf-8", newline="") as f:
            f.write(new)
        print(f"wrote {target}", file=sys.stderr)
    else:
        print("unchanged", file=sys.stderr)


if __name__ == "__main__":
    main()
