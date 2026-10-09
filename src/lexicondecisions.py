"""The user's grouped lexicon decisions, read from the committed `resources/lexiconDecisions.tsv` (spec
docs/specs/lexicon-decisions.md section 2), and the sidecar of examples the review shows (section 5.1).

One row per decision group (`Decision`); a group id is the first 10 hex digits of sha1(kind TAB level TAB signature),
so it is stable across runs. `Decisions` is immutable (every change returns a new one); `saveDecisions` is atomic and
deterministic (sorted by group id, fixed comment header). The miner calls `mergeMined`, which never overwrites a
verdict, a param, a date or a user note.
"""
import hashlib
import json
import os
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Any, Iterable, Mapping

DECISIONS_PATH = "resources/lexiconDecisions.tsv"
EXAMPLES_PATH = "lexicon_decision_examples.json"
EXAMPLES_FORMAT = 1

KINDS = ("mixte_rule", "mixte_typo", "synth_rule", "ref_conflict", "template")
LEVELS = ("L1", "L2", "L3", "L4", "-")
ACCEPT, REJECT, PENDING = "accept", "reject", "pending"
VERDICTS = (ACCEPT, REJECT, PENDING)
REC_PREFIX = "rec:"
STALE_FLAG = " [stale]"

COLUMNS = ("group_id", "kind", "level", "signature", "verdict", "param", "slots", "counter", "examples", "note", "date")
HEADER_COMMENT = (
    "# Grouped lexicon decisions (spec docs/specs/lexicon-decisions.md). Tab-separated, sorted by group_id.\n"
    "# group_id: first 10 hex digits of sha1(kind TAB level TAB signature) | kind: mixte_rule, mixte_typo, synth_rule,\n"
    "#   ref_conflict, template | level: L1..L4, or - | signature: human-readable | verdict: accept, reject, pending\n"
    "# param: chosen value (a template, a variant, a bar) or empty | slots, counter: size and counter-examples when last\n"
    "#   mined | examples: up to 3 ortho:ours>ref items, ';'-separated | note: free text ('rec:' = the miner's\n"
    "#   recommendation) | date: ISO date of the verdict, empty while pending\n"
)


class DecisionsError(ValueError):
    """The decisions file is malformed (bad column, duplicate group id, unknown verdict...)."""


def groupIdFor(kind: str, level: str, signature: str) -> str:
    return hashlib.sha1(f"{kind}\t{level}\t{signature}".encode("utf-8")).hexdigest()[:10]


def _clean(s: str) -> str:
    return " ".join(s.replace("\t", " ").splitlines())


@dataclass(frozen=True)
class Decision:
    groupId: str
    kind: str
    level: str
    signature: str
    verdict: str = PENDING
    param: str = ""
    slots: int = 0
    counter: int = 0
    examples: tuple[str, ...] = ()
    note: str = ""
    date: str = ""

    def validate(self) -> None:
        if self.kind not in KINDS:
            raise DecisionsError(f"{self.groupId}: unknown kind {self.kind!r}")
        if self.level not in LEVELS:
            raise DecisionsError(f"{self.groupId}: unknown level {self.level!r}")
        if self.verdict not in VERDICTS:
            raise DecisionsError(f"{self.groupId}: unknown verdict {self.verdict!r}")
        if self.groupId != groupIdFor(self.kind, self.level, self.signature):
            raise DecisionsError(f"{self.groupId}: does not match kind/level/signature "
                                 f"({groupIdFor(self.kind, self.level, self.signature)})")

    def row(self) -> list[str]:
        return [self.groupId, self.kind, self.level, _clean(self.signature), self.verdict, _clean(self.param),
                str(self.slots), str(self.counter), ";".join(_clean(e) for e in self.examples), _clean(self.note),
                self.date]


def minedDecision(kind: str, level: str, signature: str, slots: int, counter: int = 0,
                  examples: Iterable[str] = (), note: str = "") -> Decision:
    """A `pending` decision as the miner proposes it (the group id is computed)."""
    return Decision(groupIdFor(kind, level, signature), kind, level, signature, PENDING, "", slots, counter,
                    tuple(examples)[:3], note, "")


class Decisions:
    """The decisions keyed by group id. Immutable: every change returns a new `Decisions`."""

    def __init__(self, entries: Iterable[Decision] = ()) -> None:
        d: dict[str, Decision] = {}
        for e in entries:
            if e.groupId in d:
                raise DecisionsError(f"duplicate group id {e.groupId}")
            d[e.groupId] = e
        self._entries = d

    @property
    def entries(self) -> Mapping[str, Decision]:
        return MappingProxyType(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, groupId: object) -> bool:
        return groupId in self._entries

    def get(self, groupId: str) -> Decision | None:
        return self._entries.get(groupId)

    def all(self) -> list[Decision]:
        """Every decision in the saved order (by group id)."""
        return [self._entries[k] for k in sorted(self._entries)]

    def withEntry(self, decision: Decision) -> "Decisions":
        return Decisions([*(e for k, e in self._entries.items() if k != decision.groupId), decision])

    def accepted(self, kind: str | None = None) -> list[Decision]:
        return [e for e in self.all() if e.verdict == ACCEPT and (kind is None or e.kind == kind)]

    def pending(self, kind: str | None = None) -> list[Decision]:
        return [e for e in self.all() if e.verdict == PENDING and (kind is None or e.kind == kind)]


def mergeMined(decisions: Decisions, mined: Iterable[Decision]) -> Decisions:
    """Merges the groups the miner found into the decisions.

    - a new group is added as `pending` (verdict, param and date emptied, whatever `mined` carries);
    - an existing group gets its `slots`, `counter` and `examples` refreshed and nothing else, except `note` on a
      `pending` row: a `rec:` note of the miner replaces an empty or `rec:` note, and a `[stale]` flag is cleared;
    - a decided (accept/reject) group that the miner no longer finds is kept and its note gets ` [stale]`
      (once); a `pending` group not found is left as it is (it is only information, and a `d` split relies on it).
    """
    found: dict[str, Decision] = {}
    for item in mined:
        found[item.groupId] = item
    out: dict[str, Decision] = {}
    for e in decisions.all():
        m = found.get(e.groupId)
        if m is None:
            out[e.groupId] = (replace(e, note=e.note + STALE_FLAG)
                              if e.verdict != PENDING and not e.note.endswith(STALE_FLAG) else e)
            continue
        note = e.note
        if note.endswith(STALE_FLAG):
            note = note[:-len(STALE_FLAG)]
        if e.verdict == PENDING and m.note.startswith(REC_PREFIX) and (not note or note.startswith(REC_PREFIX)):
            note = m.note
        out[e.groupId] = replace(e, slots=m.slots, counter=m.counter, examples=m.examples, note=note)
    for gid, m in found.items():
        if gid not in out:
            out[gid] = replace(m, verdict=PENDING, param="", date="")
    return Decisions(out.values())


def loadDecisions(path: str = DECISIONS_PATH) -> Decisions:
    entries: list[Decision] = []
    header: list[str] | None = None
    with open(path, encoding="utf-8") as f:
        for lineNo, raw in enumerate(f, 1):
            line = raw.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            cells = line.split("\t")
            if header is None:
                if tuple(cells) != COLUMNS:
                    raise DecisionsError(f"{path}:{lineNo}: bad header {cells!r}")
                header = cells
                continue
            if len(cells) != len(COLUMNS):
                raise DecisionsError(f"{path}:{lineNo}: {len(cells)} columns, expected {len(COLUMNS)}")
            c = dict(zip(COLUMNS, cells))
            try:
                slots, counter = int(c["slots"] or 0), int(c["counter"] or 0)
            except ValueError as e:
                raise DecisionsError(f"{path}:{lineNo}: bad number: {e}") from e
            d = Decision(c["group_id"], c["kind"], c["level"], c["signature"], c["verdict"], c["param"], slots, counter,
                         tuple(x for x in c["examples"].split(";") if x), c["note"], c["date"])
            d.validate()
            entries.append(d)
    if header is None:
        raise DecisionsError(f"{path}: no header line")
    return Decisions(entries)


def saveDecisions(decisions: Decisions, path: str = DECISIONS_PATH) -> None:
    """Atomic, deterministic write: comment header, column line, rows sorted by group id."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(HEADER_COMMENT)
        f.write("\t".join(COLUMNS) + "\n")
        for e in decisions.all():
            f.write("\t".join(e.row()) + "\n")
    os.replace(tmp, path)


def writeExamplesSidecar(path: str, examples: Mapping[str, dict[str, Any]]) -> None:
    """Writes `lexicon_decision_examples.json` (format: spec section 5.1): group id -> {members, counters, children}."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"format": EXAMPLES_FORMAT, "groups": {k: examples[k] for k in sorted(examples)}}, f,
                  ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, path)


def loadExamplesSidecar(path: str = EXAMPLES_PATH) -> dict[str, dict[str, Any]]:
    """The sidecar's groups; an absent file is an empty sidecar (the review then shows no member rows)."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    if d.get("format") != EXAMPLES_FORMAT:
        raise DecisionsError(f"{path}: unsupported examples format {d.get('format')!r}")
    groups: dict[str, dict[str, Any]] = d.get("groups", {})
    return groups
