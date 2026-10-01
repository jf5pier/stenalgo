"""The user's decisions on the affix rules, read from the committed `affix_decisions.json`.

Two kinds of decision, both per ANCHOR (a k=1 syllable-affix candidate, or a merge of spelling variants
that share one sound):

- **fusion verdict** of a merged anchor (`a|b|c`, the exact spelling set the engine's greedy merge made):
  "fused" (the merge is one rule on one key), "apart" (the parts stay separate rules). A merge with no entry
  is undecided and behaves as "apart" (the safe default); the review tool lists it as pending.
- **growth**: the forms that fuse the anchor syllable with the NEIGHBOUR syllable on the same stroke (k=2). A
  list of `ScopeForm`; an empty list means "no growth" (anchor alone). An anchor with no entry has no growth
  either, but is pending in the review.

A scope form fuses the anchor with the neighbour syllable (the one before a suffix anchor, the one after a
prefix anchor) when the carrier matches:

- `anchors`: the anchor syllable's spelling is one of these (None: any spelling of the merged anchor);
- `sound`: the neighbour's phonology (X-SAMPA syllable, e.g. `ZuR`, `tR°`) fully matches this regex;
- `spelling`: the neighbour's spelling fully matches this regex.

All given conditions must hold. A carrier that a form names but that gains nothing under the rule's keys falls
back to the anchor alone (`affixrules.resolveFallbacks`), priced `EXCLUSION_COST` each.

Anchors are keyed by (position, spellings, phono): spellings is the `|`-joined spelling set exactly as the pool's
`Candidate.ortho` prints it. Forms are stored as strings (label, anchors, sound regex, spelling regex).
"""
import hashlib
import json
import os
import re
from dataclasses import dataclass, field

PREFIX, SUFFIX = "prefix", "suffix"
FUSED, APART, SINGLE = "fused", "apart", "-"
VERDICTS = (FUSED, APART, SINGLE)
DECISIONS_PATH = "affix_decisions.json"
FORMAT_VERSION = 1

AnchorKey = tuple[str, str, str]      # (position, spellings, phono)


class DecisionsError(ValueError):
    """The decisions file is malformed (bad regex, duplicate key, wrong verdict...)."""


@dataclass(frozen=True)
class ScopeForm:
    label: str                                 # human-readable scope, shown in the rule's form name
    anchors: frozenset[str] | None = None
    sound: re.Pattern[str] | None = None
    spelling: re.Pattern[str] | None = None

    def matches(self, anchorOrtho: str, neighbourOrtho: str, neighbourPhono: str) -> bool:
        if self.anchors is not None and anchorOrtho not in self.anchors:
            return False
        if self.sound is not None and not self.sound.fullmatch(neighbourPhono):
            return False
        return self.spelling is None or bool(self.spelling.fullmatch(neighbourOrtho))

    def toJson(self) -> dict[str, object]:
        return {"label": self.label, "anchors": sorted(self.anchors) if self.anchors is not None else None,
                "sound": self.sound.pattern if self.sound else None,
                "spelling": self.spelling.pattern if self.spelling else None}

    @staticmethod
    def fromJson(d: dict[str, object]) -> "ScopeForm":
        try:
            anchors = d.get("anchors")
            sound, spelling = d.get("sound"), d.get("spelling")
            return ScopeForm(
                str(d["label"]),
                frozenset(str(a) for a in anchors) if anchors is not None else None,  # type: ignore[attr-defined]
                re.compile(str(sound)) if sound is not None else None,
                re.compile(str(spelling)) if spelling is not None else None)
        except (KeyError, re.error, TypeError) as e:
            raise DecisionsError(f"bad scope form {d!r}: {e}") from e


@dataclass
class AnchorDecision:
    position: str
    spellings: str                              # the exact `|`-joined spelling set
    phono: str
    verdict: str                                # FUSED / APART for a merge, SINGLE ("-") for one spelling
    growth: list[ScopeForm] | None = field(default_factory=list)   # [] = no growth, None = growth undecided (pending)
    refused: list[str] = field(default_factory=list)        # proposal labels the user said no to
    note: str = ""
    date: str = ""
    numbers: dict[str, object] = field(default_factory=dict)   # help/hurt numbers at decision time

    @property
    def key(self) -> AnchorKey:
        return (self.position, self.spellings, self.phono)

    def toJson(self) -> dict[str, object]:
        return {"position": self.position, "spellings": self.spellings, "phono": self.phono,
                "verdict": self.verdict, "growth": None if self.growth is None else [f.toJson() for f in self.growth],
                "refused": self.refused,
                "note": self.note, "date": self.date, "numbers": self.numbers}

    @staticmethod
    def fromJson(d: dict[str, object]) -> "AnchorDecision":
        try:
            dec = AnchorDecision(
                str(d["position"]), str(d["spellings"]), str(d["phono"]), str(d["verdict"]),
                None if d.get("growth", []) is None else [ScopeForm.fromJson(f) for f in d.get("growth", [])],  # type: ignore[attr-defined]
                [str(r) for r in d.get("refused", [])],  # type: ignore[attr-defined]
                str(d.get("note", "")), str(d.get("date", "")), dict(d.get("numbers", {})))  # type: ignore[call-overload]
        except (KeyError, TypeError) as e:
            raise DecisionsError(f"bad anchor entry {d!r}: {e}") from e
        dec.validate()
        return dec

    def validate(self) -> None:
        if self.position not in (PREFIX, SUFFIX):
            raise DecisionsError(f"{self.key}: position must be prefix or suffix")
        if self.verdict not in VERDICTS:
            raise DecisionsError(f"{self.key}: unknown verdict {self.verdict!r}")
        if ("|" in self.spellings) != (self.verdict != SINGLE):
            raise DecisionsError(f"{self.key}: a merged anchor (a|b) needs verdict fused/apart, a single spelling '-'")
        if self.verdict == APART and self.growth:
            raise DecisionsError(f"{self.key}: an apart merge is not a rule and cannot have growth forms")


class Decisions:
    """The decisions, keyed by anchor. Immutable by convention: the review builds a new one per answer."""

    def __init__(self, entries: list[AnchorDecision] | None = None) -> None:
        self.entries: dict[AnchorKey, AnchorDecision] = {}
        for e in entries or []:
            if e.key in self.entries:
                raise DecisionsError(f"duplicate anchor {e.key}")
            self.entries[e.key] = e

    def get(self, position: str, ortho: str, phono: str) -> AnchorDecision | None:
        return self.entries.get((position, ortho, phono))

    def growthForms(self, position: str, ortho: str, phono: str) -> list[ScopeForm] | None:
        """The decided growth forms of this anchor (empty: no growth), or None when it has no decided growth
        (no entry, `growth: null` = undecided, or an apart merge that is not a rule)."""
        e = self.entries.get((position, ortho, phono))
        return None if e is None or e.verdict == APART else e.growth

    def fusionVerdict(self, position: str, ortho: str, phono: str) -> str:
        """FUSED or APART for a merged anchor; undecided is APART (the safe default)."""
        e = self.entries.get((position, ortho, phono))
        return e.verdict if e is not None and e.verdict in (FUSED, APART) else APART

    def isDecidedMerge(self, position: str, ortho: str, phono: str) -> bool:
        return (position, ortho, phono) in self.entries

    def toJson(self) -> dict[str, object]:
        ordered = sorted(self.entries.values(), key=lambda e: (e.position, e.phono, e.spellings))
        return {"format": FORMAT_VERSION, "anchors": [e.toJson() for e in ordered]}

    @staticmethod
    def fromJson(d: dict[str, object]) -> "Decisions":
        if d.get("format") != FORMAT_VERSION:
            raise DecisionsError(f"unsupported decisions format {d.get('format')!r}")
        return Decisions([AnchorDecision.fromJson(e) for e in d.get("anchors", [])])  # type: ignore[attr-defined]

    def withEntry(self, entry: AnchorDecision) -> "Decisions":
        entries = dict(self.entries)
        entries[entry.key] = entry
        return Decisions(list(entries.values()))


def loadDecisions(path: str = DECISIONS_PATH) -> Decisions:
    with open(path, encoding="utf-8") as f:
        return Decisions.fromJson(json.load(f))


def saveDecisions(decisions: Decisions, path: str = DECISIONS_PATH) -> None:
    """Atomic write (a crash or Ctrl-C never leaves a half-written file)."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(decisions.toJson(), f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, path)


def fileMd5(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def decisionsMd5(path: str = DECISIONS_PATH) -> str:
    return fileMd5(path)


def inputFingerprint(
    paths: tuple[str, ...] = ("resources/LexiqueMixte.tsv", "resources/LexiqueSynthetic.tsv", "starboard3h.json"),
) -> dict[str, str]:
    """md5 of the lexicons and the layout the affix selection depends on (theory pickles are not checked)."""
    return {p: fileMd5(p) for p in paths if os.path.exists(p)}
