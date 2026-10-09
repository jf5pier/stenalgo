"""Builds `resources/mixteCorrections.tsv` from the accepted Mixte decisions (T2.3, spec docs/specs/lexicon-decisions.md
section 6): for every `accept`ed decision of kind `mixte_rule` or `mixte_typo`, each member row of its sidecar entry
(`lexicon_decision_examples.json`) becomes a correction row that `lexique.py` replays on the output rows.

Per member (`ortho`, `ours`, `ref`, `syllCV`, `orthosyllCV`, `rowKey` = `ortho lemme infover`, `cgram` (VER when absent), `genre`, `nombre`; the key of the
OUTPUT row is (ortho, lemme, cgram, infover, genre, nombre)):

- target phonology: the decision's `param` when set (the variant to adopt when the references offer several), else the member's
  `ref`. The real edits (src/diffsignature `realEdits`: the lexicon conventions of spec section 3 stay out, so a closed `o`
  or an optional schwa of ours is kept) from `ours` to the target are applied to the phonology and, unit by unit, to `syll_cv`:
  a substitution replaces the phoneme inside its unit; an insertion fills the silent `#` unit it is anchored on, else
  extends the anchoring unit (right after the preceding phoneme); a deletion removes the phoneme from its unit, which becomes
  `#` when nothing is left. `orthosyll_cv` is unchanged.
- validation (a member that fails is reported on stderr, left out of the file, and fails `--check` / the exit status): the
  sounded join of the new `syll_cv` (units without `#`) must equal the new phonology, no unit may be empty, and the new
  phonology must be at no real edit from the target.

Output: sorted, deterministic. A key claimed by two different accepted groups with different results is a failure too.

Run: python -m util.build_mixte_corrections [--decisions PATH] [--examples PATH] [--out PATH] [--check]
  --check writes nothing and fails when a member fails or when the committed file differs from what would be written.
"""
import argparse
import os
import re
import sys
from dataclasses import dataclass
from typing import Any

from src.diffsignature import AlignmentError, Edit, OP_INS, anchorEdits, realEdits, unitsOf
from src.lexicondecisions import (ACCEPT, DECISIONS_PATH, EXAMPLES_PATH, Decision, Decisions, loadDecisions,
                                  loadExamplesSidecar)
from src.mixtecorrections import CORRECTIONS_PATH, Correction, formatMixteCorrections

CORRECTED_KINDS = ("mixte_rule", "mixte_typo")
DEFAULT_CGRAM = "VER"


@dataclass(frozen=True)
class Failure:
    groupId: str
    ortho: str
    reason: str

    def __str__(self) -> str:
        return f"{self.groupId} {self.ortho}: {self.reason}"


def _applyEdits(phon: str, syllCV: str, orthosyllCV: str, edits: list[Edit]) -> tuple[str, str]:
    """(new phon, new syll_cv): the edits applied to the phonology and, unit by unit, to the breakdown."""
    units = unitsOf(syllCV)
    starts: list[int] = []
    at = 0
    for u in units:
        starts.append(at)
        at += 0 if u == "#" else len(u)
    cells: list[list[str]] = [[] if u == "#" else list(u) for u in units]
    # string order reversed: an edit never shifts the offset of an earlier one
    for e in reversed(edits):
        k = anchorEdits([e], phon, syllCV, orthosyllCV)[0].unitIndex
        offset = e.phonIndex - starts[k] if units[k] != "#" else 0
        if e.op == OP_INS:
            cells[k][offset:offset] = list(e.ref)
        else:
            cells[k][offset:offset + len(e.ours)] = list(e.ref)
    newUnits = ["".join(c) or "#" for c in cells]
    newPhon = phon
    for e in reversed(edits):
        newPhon = newPhon[:e.phonIndex] + e.ref + newPhon[e.phonIndex + len(e.ours):]
    separators = re.findall(r"[|_]", syllCV)
    out = newUnits[0]
    for sep, u in zip(separators, newUnits[1:]):
        out += sep + u
    return newPhon, out


def correctedBreakdown(ours: str, target: str, syllCV: str, orthosyllCV: str) -> tuple[str, str, str]:
    """(phon, syll_cv, orthosyll_cv) of the corrected row; ValueError (AlignmentError included) when the edits cannot be
    applied or the result is not consistent (see the module docstring)."""
    edits = realEdits(ours, target)
    if not edits:
        raise ValueError(f"no real edit from {ours!r} to {target!r}")
    newPhon, newSyll = _applyEdits(ours, syllCV, orthosyllCV, edits)
    units = unitsOf(newSyll)
    if "" in units:
        raise ValueError(f"empty unit in {newSyll!r}")
    if len(units) != len(unitsOf(orthosyllCV)):
        raise ValueError(f"{newSyll!r} / {orthosyllCV!r}: unit counts differ")
    if "".join(u for u in units if u != "#") != newPhon:
        raise ValueError(f"sounded join of {newSyll!r} is not {newPhon!r}")
    if realEdits(newPhon, target):
        raise ValueError(f"corrected phonology {newPhon!r} is still not the target {target!r}")
    return newPhon, newSyll, orthosyllCV


def _keyOf(member: dict[str, Any]) -> tuple[str, str, str, str, str, str]:
    rowKey = str(member.get("rowKey", ""))
    parts = rowKey.split(" ", 2)
    if len(parts) != 3 or parts[0] != member["ortho"]:
        raise ValueError(f"member has no usable rowKey ({rowKey!r}): rerun `python -m util.audit_mixte` to refresh the sidecar")
    return (parts[0], parts[1], str(member.get("cgram", DEFAULT_CGRAM)), parts[2], str(member.get("genre", "")),
            str(member.get("nombre", "")))


def buildCorrections(decisions: Decisions, sidecar: dict[str, dict[str, Any]]) -> tuple[list[Correction], list[Failure]]:
    """The correction rows of the accepted Mixte decisions and the members that could not be corrected."""
    corrections: dict[tuple[str, str, str, str, str, str], Correction] = {}
    failures: list[Failure] = []
    accepted = sorted((d for kind in CORRECTED_KINDS for d in decisions.accepted(kind)), key=lambda d: d.groupId)
    for decision in accepted:
        entry = sidecar.get(decision.groupId)
        if entry is None or not entry.get("members"):
            failures.append(Failure(decision.groupId, "-", "accepted group without member rows in the sidecar"))
            continue
        for member in entry["members"]:
            try:
                failure = _correctMember(decision, member, corrections)
            except (ValueError, AlignmentError, KeyError) as e:
                failure = str(e)
            if failure:
                failures.append(Failure(decision.groupId, str(member.get("ortho", "?")), failure))
    return sorted(corrections.values(), key=lambda c: (c.key, c.groupId)), failures


def _correctMember(decision: Decision, member: dict[str, Any], corrections: dict[tuple[str, str, str, str, str, str], Correction]
                   ) -> str:
    """Adds the member's correction; returns the failure reason, '' when fine."""
    key = _keyOf(member)
    target = decision.param or member["ref"]
    phon, syll, orthosyll = correctedBreakdown(member["ours"], target, member["syllCV"], member["orthosyllCV"])
    c = Correction(key[0], key[1], key[2], key[3], key[4], key[5], phon, syll, orthosyll, decision.groupId)
    previous = corrections.get(key)
    if previous is not None and previous.fields()[6:9] != c.fields()[6:9]:
        return f"also corrected differently by group {previous.groupId}"
    if previous is None:
        corrections[key] = c
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--decisions", default=DECISIONS_PATH)
    parser.add_argument("--examples", default=EXAMPLES_PATH)
    parser.add_argument("--out", default=CORRECTIONS_PATH)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    decisions = loadDecisions(args.decisions) if os.path.exists(args.decisions) else Decisions()
    corrections, failures = buildCorrections(decisions, loadExamplesSidecar(args.examples))
    for failure in failures:
        print(f"FAILED {failure}", file=sys.stderr)
    text = formatMixteCorrections(corrections)
    ok = not failures
    if args.check:
        current = open(args.out, encoding="utf-8").read() if os.path.exists(args.out) else ""
        if current != text:
            print(f"{args.out} is out of date ({len(corrections)} correction rows expected)", file=sys.stderr)
            ok = False
    else:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"wrote {args.out}: {len(corrections)} rows, {len(failures)} failed")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
