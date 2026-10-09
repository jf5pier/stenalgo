"""Signatures of the differences between our pronunciations and the reference ones (spec docs/specs/lexicon-decisions.md,
sections 3 and 4). Pure functions on strings; standard library only (src must not import util).

Pipeline for one row (`buildRowDiff`):

1. `nearestReference`: the reference variant with the fewest non-convention edits, then the smallest raw edit
   distance, then the lexicographically smallest variant (determinism). The spec says "edit distance"; counting the
   conventions out first is the only refinement (a variant that differs by a convention only must win over a variant
   that differs for real).
2. `editScript`: Levenshtein alignment over single phonemes. The backtrace runs from the end and, on a tie, prefers
   match/substitution, then deletion (a phoneme of ours missing from the reference), then insertion. Each non-match
   step is an `Edit(op, ours, ref, phonIndex)`; `phonIndex` is the index in OUR string of the substituted or deleted
   phoneme, or the index BEFORE which the missing phoneme should be inserted (len(ours) for an insertion at the end).
3. `dropConventions`: removes the edits of `CONVENTION_EDITS` (section 3); one constant, so a later ruling can extend it.
4. `anchorEdits`: attaches each edit to a unit of `syll_cv` / `orthosyll_cv` (they align unit for unit).
   Units are the `|`/`_` separated items; `#` consumes no phoneme, any other unit consumes `len(unit)` phonemes.
   A sub/del anchors on the unit consuming `phonIndex`. An insertion anchors on the silent `#` unit that
   immediately follows the unit of the preceding phoneme (`phonIndex - 1`), else on the unit of the preceding
   phoneme (the first unit at index 0). Consecutive edits that land on the same unit are merged into one
   (`ours` and `ref` concatenated in order). The unit position is `initial` (no sounded unit before it), else `final`
   (no sounded unit after it), else `medial`; a `#` unit takes the position its neighbours give it.
   Worked example, `kRij§` / `kRijj§`, `k_R_ij_#|§`, `c_r_i_i|ons`: the alignment inserts `j` before `ours[3]`; the
   preceding phoneme (`i`, index 2) sits in unit `ij`, the next unit is `#`, so the edit anchors on the 4th unit,
   grapheme `i`, medial: `∅→j @ i [medial]`.
5. `signatureAt(row, level)`: the signature string of section 4.4.

`CounterIndex` holds the units of the rows that MATCHED their reference (exact or convention-only), and answers the
counter-example counts of section 4.3 (four levels L1 grapheme, L2 + family, L3 + slot, L4 + lemma). `proposeGroups`
assigns each difference row to exactly one group: greedily, homogeneous candidates first (precision >= 0.95, >= 3 slots),
then heterogeneous ones (>= 3 slots), largest first; what is left is an L4 singleton (a typo).
"""
import heapq
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from src.orthounits import REPEAT

L1, L2, L3, L4 = "L1", "L2", "L3", "L4"
LEVELS = (L1, L2, L3, L4)
ClassKey = tuple[str, str]        # (family, slot): the template key or ending class, and the slot
MIN_PRECISION = 0.95
MIN_SLOTS = 3
EMPTY = "∅"

OP_SUB, OP_DEL, OP_INS = "sub", "del", "ins"


class AlignmentError(ValueError):
    """`syll_cv` / `orthosyll_cv` do not line up with the phonology (unit count, or an index outside the units)."""


@dataclass(frozen=True)
class Edit:
    op: str                    # "sub" | "del" | "ins" (a merged edit with both sides non-empty is a "sub")
    ours: str                  # our phonemes ("" for an insertion)
    ref: str                   # the reference phonemes ("" for a deletion)
    phonIndex: int             # index in our phonology (see the module docstring)

    @property
    def text(self) -> str:
        return f"{self.ours or EMPTY}→{self.ref or EMPTY}"


# (op, ours, ref): the lexicon conventions of section 3, never a difference.
CONVENTION_EDITS: frozenset[tuple[str, str, str]] = frozenset({
    (OP_SUB, "o", "O"),       # closed o for written o/au/eau
    (OP_DEL, "°", ""),        # optional schwa
    (OP_INS, "", "°"),
})


def _table(a: str, b: str) -> list[list[int]]:
    d = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        d[i][0] = i
    for j in range(len(b) + 1):
        d[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            d[i][j] = min(d[i - 1][j - 1] + (a[i - 1] != b[j - 1]), d[i - 1][j] + 1, d[i][j - 1] + 1)
    return d


def editScript(ours: str, ref: str) -> list[Edit]:
    """The non-match steps of the deterministic Levenshtein alignment of `ours` to `ref` (single-phoneme edits,
    in string order, conventions NOT yet dropped)."""
    d = _table(ours, ref)
    i, j = len(ours), len(ref)
    out: list[Edit] = []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and d[i][j] == d[i - 1][j - 1] + (ours[i - 1] != ref[j - 1]):
            if ours[i - 1] != ref[j - 1]:
                out.append(Edit(OP_SUB, ours[i - 1], ref[j - 1], i - 1))
            i, j = i - 1, j - 1
        elif i > 0 and d[i][j] == d[i - 1][j] + 1:
            out.append(Edit(OP_DEL, ours[i - 1], "", i - 1))
            i -= 1
        else:
            out.append(Edit(OP_INS, "", ref[j - 1], i))
            j -= 1
    out.reverse()
    return out


def dropConventions(edits: Iterable[Edit]) -> list[Edit]:
    return [e for e in edits if (e.op, e.ours, e.ref) not in CONVENTION_EDITS]


def realEdits(ours: str, ref: str) -> list[Edit]:
    """`dropConventions(editScript(ours, ref))`."""
    return dropConventions(editScript(ours, ref))


def nearestReference(ours: str, refs: Iterable[str]) -> str:
    """The reference variant nearest to `ours` (see the module docstring); ValueError when there is none."""
    best: tuple[int, int, str] | None = None
    for r in refs:
        key = (len(realEdits(ours, r)), _table(ours, r)[len(ours)][len(r)], r)
        if best is None or key < best:
            best = key
    if best is None:
        raise ValueError("no reference variant")
    return best[2]


@dataclass(frozen=True)
class AnchoredEdit:
    edit: Edit
    unitIndex: int
    grapheme: str
    position: str              # "initial" | "medial" | "final"
    unitPhon: str              # the phonemes of the unit the edit sits on ("" for a silent unit)

    @property
    def key(self) -> tuple[str, str, str]:
        """The (grapheme, position, our phonemes) triple a counter-example must share: the edit's own phonemes for a
        sub/del, the unit's phonemes for an insertion."""
        return (self.grapheme, self.position, self.edit.ours or self.unitPhon)


def unitsOf(syllCV: str) -> list[str]:
    return syllCV.replace("|", "_").split("_")


def graphemesOf(orthosyllCV: str) -> list[str]:
    """The grapheme of every unit; a repeat unit (`=`, src/orthounits.py) takes the grapheme of the unit before it."""
    out: list[str] = []
    for unit in unitsOf(orthosyllCV):
        out.append(out[-1] if unit == REPEAT and out else unit)
    return out


def _layout(phon: str, syllCV: str) -> tuple[list[str], list[int], list[str]]:
    """(units, start offset of each unit in `phon`, positions); AlignmentError when the units do not consume `phon`."""
    units = unitsOf(syllCV)
    starts: list[int] = []
    at = 0
    for u in units:
        starts.append(at)
        at += 0 if u == "#" else len(u)
    if at != len(phon):
        raise AlignmentError(f"{syllCV!r} consumes {at} phonemes, {phon!r} has {len(phon)}")
    sounded = [k for k, u in enumerate(units) if u != "#"]
    first, last = (sounded[0], sounded[-1]) if sounded else (-1, -1)
    positions = ["initial" if k <= first else "final" if k >= last else "medial" for k in range(len(units))]
    return units, starts, positions


def unitTriples(phon: str, syllCV: str, orthosyllCV: str) -> list[tuple[str, str, str]]:
    """(grapheme, position, phonemes) of every unit of a row, for the counter index."""
    units, starts, positions = _layout(phon, syllCV)
    graphemes = graphemesOf(orthosyllCV)
    if len(graphemes) != len(units):
        raise AlignmentError(f"{syllCV!r} / {orthosyllCV!r}: unit counts differ")
    return [(graphemes[k], positions[k], "" if u == "#" else phon[starts[k]:starts[k] + len(u)])
            for k, u in enumerate(units)]


def anchorEdits(edits: Sequence[Edit], phon: str, syllCV: str, orthosyllCV: str) -> list[AnchoredEdit]:
    """Anchors `edits` (already without conventions) on the units of the row; see the module docstring."""
    units, starts, positions = _layout(phon, syllCV)
    graphemes = graphemesOf(orthosyllCV)
    if len(graphemes) != len(units):
        raise AlignmentError(f"{syllCV!r} / {orthosyllCV!r}: unit counts differ")

    def unitAt(index: int) -> int:
        for k, u in enumerate(units):
            if u != "#" and starts[k] <= index < starts[k] + len(u):
                return k
        raise AlignmentError(f"phoneme index {index} outside {syllCV!r}")

    placed: list[tuple[Edit, int]] = []
    for e in edits:
        if e.op == OP_INS:
            if not units:
                raise AlignmentError("no units")
            k = 0 if e.phonIndex == 0 else unitAt(e.phonIndex - 1)
            if e.phonIndex > 0 and k + 1 < len(units) and units[k + 1] == "#":
                k += 1
        else:
            k = unitAt(e.phonIndex)
        placed.append((e, k))
    merged: list[tuple[Edit, int]] = []
    for e, k in placed:
        if merged and merged[-1][1] == k:
            p = merged[-1][0]
            ours, ref = p.ours + e.ours, p.ref + e.ref
            merged[-1] = (Edit(OP_SUB if ours and ref else OP_DEL if ours else OP_INS, ours, ref, p.phonIndex), k)
        else:
            merged.append((e, k))
    return [AnchoredEdit(e, k, graphemes[k], positions[k], "" if units[k] == "#" else units[k]) for e, k in merged]


@dataclass(frozen=True)
class RowDiff:
    """One row that differs from its reference, with everything the review shows."""
    ortho: str
    lemma: str
    classKey: ClassKey         # supplied by the caller: (family, slot); family = template key or `untemplated`
    ours: str
    ref: str
    edits: tuple[AnchoredEdit, ...]
    refSource: str = ""
    syllCV: str = ""
    orthosyllCV: str = ""
    rowKey: str = ""
    cgram: str = ""
    genre: str = ""
    nombre: str = ""

    def example(self) -> str:
        return f"{self.ortho}:{self.ours}>{self.ref}"

    def toJson(self) -> dict[str, str]:
        out = {"ortho": self.ortho, "ours": self.ours, "ref": self.ref, "refSource": self.refSource,
               "syllCV": self.syllCV, "orthosyllCV": self.orthosyllCV}
        if self.rowKey:
            out["rowKey"] = self.rowKey     # `ortho lemme infover` as audit_mixte builds it: keys the Mixte correction row
        if self.cgram:
            out["cgram"] = self.cgram       # with genre and nombre: the rest of the key of the Mixte correction row
            out["genre"] = self.genre
            out["nombre"] = self.nombre
        return out


def buildRowDiff(
    ortho: str, ours: str, refs: Iterable[str], syllCV: str, orthosyllCV: str, classKey: ClassKey | str, lemma: str,
    refSource: str = "", rowKey: str = "", cgram: str = "", genre: str = "", nombre: str = "",
) -> RowDiff | None:
    """The difference of a row with its nearest reference, or None when there is none besides conventions.
    Raises ValueError when there is no reference and AlignmentError when the units do not align."""
    ref = nearestReference(ours, refs)
    edits = realEdits(ours, ref)
    if not edits:
        return None
    key: ClassKey = classKey if isinstance(classKey, tuple) else (classKey, "")
    return RowDiff(ortho, lemma, key, ours, ref, tuple(anchorEdits(edits, ours, syllCV, orthosyllCV)),
                   refSource, syllCV, orthosyllCV, rowKey or ortho, cgram, genre, nombre)


def signatureAt(row: RowDiff, level: str) -> str:
    """`<edits> @ <graphemes> [<positions>]`, then ` | <family>` (L2), ` | <family> <slot>` (L3, L4), then ` | <lemma>`
    (L4); section 4.4. A row whose class key has no slot (family only) prints the family alone at L3 and L4."""
    if level not in LEVELS:
        raise ValueError(f"unknown level {level!r}")
    s = (",".join(a.edit.text for a in row.edits) + " @ " + ",".join(a.grapheme for a in row.edits)
         + " [" + ",".join(a.position for a in row.edits) + "]")
    family, slot = row.classKey
    if level == L2:
        s += " | " + family
    elif level in (L3, L4):
        s += " | " + (f"{family} {slot}" if slot else family)
    if level == L4:
        s += " | " + row.lemma
    return s


class CounterIndex:
    """The units of the rows whose comparison to their reference is exact or convention-only.

    A counter-example of an edit is a matched row with the same grapheme at the same unit position with the same our
    phonemes (`AnchoredEdit.key`), restricted by the level: any such row at L1, the same family at L2, the same family
    and slot at L3, the same family, slot and lemma at L4. For a multi-edit group the row must carry every edit's triple. A unit with several phonemes is
    indexed under its whole phoneme string and under each of its phonemes, so a sub/del of one phoneme of `ij`
    finds it. Counts are O(1) for a single edit; a multi-edit group scans the postings of its rarest triple."""

    def __init__(self) -> None:
        self._postings: dict[tuple[str, str, str], list[int]] = defaultdict(list)
        self._byFamily: Counter[tuple[tuple[str, str, str], str]] = Counter()
        self._bySlot: Counter[tuple[tuple[str, str, str], ClassKey]] = Counter()
        self._byLemma: Counter[tuple[tuple[str, str, str], ClassKey, str]] = Counter()
        self._rows: list[tuple[frozenset[tuple[str, str, str]], ClassKey, str, tuple[str, str, str, str]]] = []

    def __len__(self) -> int:
        return len(self._rows)

    def addRow(
        self, triples: Iterable[tuple[str, str, str]], classKey: ClassKey, lemma: str,
        shown: tuple[str, str, str, str] = ("", "", "", ""),
    ) -> None:
        """`triples`: (grapheme, position, phonemes) of the row's units; `shown`: (ortho, ours, syllCV, orthosyllCV)."""
        keys: set[tuple[str, str, str]] = set()
        for g, pos, ph in triples:
            keys.add((g, pos, ph))
            if len(ph) > 1:
                keys.update((g, pos, c) for c in ph)
        rowId = len(self._rows)
        self._rows.append((frozenset(keys), classKey, lemma, shown))
        for k in keys:
            self._postings[k].append(rowId)
            self._byFamily[(k, classKey[0])] += 1
            self._bySlot[(k, classKey)] += 1
            self._byLemma[(k, classKey, lemma)] += 1

    def add(self, grapheme: str, position: str, ourPhoneme: str, classKey: ClassKey, lemma: str) -> None:
        """One unit of one matched row (a row of several units: `addRow`)."""
        self.addRow([(grapheme, position, ourPhoneme)], classKey, lemma)

    def addMatchedRow(self, phon: str, syllCV: str, orthosyllCV: str, classKey: ClassKey, lemma: str,
                      ortho: str = "") -> None:
        """Indexes every unit of a row that matched its reference. A row whose units do not align is skipped."""
        try:
            triples = unitTriples(phon, syllCV, orthosyllCV)
        except AlignmentError:
            return
        self.addRow(triples, classKey, lemma, (ortho, phon, syllCV, orthosyllCV))

    def _match(self, keys: Sequence[tuple[str, str, str]], classKey: ClassKey, lemma: str, level: str) -> list[int]:
        if not keys:
            return []
        rarest = min(keys, key=lambda k: len(self._postings.get(k, ())))
        out: list[int] = []
        for rowId in self._postings.get(rarest, ()):
            triples, cls, lem, _shown = self._rows[rowId]
            if ((level == L2 and cls[0] != classKey[0]) or (level in (L3, L4) and cls != classKey)
                    or (level == L4 and lem != lemma)):
                continue
            if all(k in triples for k in keys):
                out.append(rowId)
        return out

    def count(self, keys: Sequence[tuple[str, str, str]], classKey: ClassKey, lemma: str, level: str) -> int:
        if len(set(keys)) == 1:
            k = keys[0]
            if level == L1:
                return len(self._postings.get(k, ()))
            if level == L2:
                return self._byFamily.get((k, classKey[0]), 0)
            if level == L3:
                return self._bySlot.get((k, classKey), 0)
            return self._byLemma.get((k, classKey, lemma), 0)
        return len(self._match(sorted(set(keys)), classKey, lemma, level))

    def examples(self, keys: Sequence[tuple[str, str, str]], classKey: ClassKey, lemma: str, level: str,
                 limit: int = 3) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        for rowId in self._match(sorted(set(keys)), classKey, lemma, level)[:limit]:
            ortho, ours, syll, orthosyll = self._rows[rowId][3]
            out.append({"ortho": ortho, "ours": ours, "ref": ours, "syllCV": syll, "orthosyllCV": orthosyll})
        return out


@dataclass
class ProposedGroup:
    level: str
    signature: str
    members: list[RowDiff]
    counter: int
    typo: bool = False                       # an L4 group of a single row
    heterogeneous: bool = False              # >= 3 slots but precision below MIN_PRECISION (section 4.3, rule 2)
    children: list[dict[str, Any]] = field(default_factory=list)       # next-finer-level subgroups (for the `d` split)
    counters: list[dict[str, str]] = field(default_factory=list)       # up to 3 counter-example rows

    @property
    def slots(self) -> int:
        return len(self.members)

    @property
    def precision(self) -> float:
        return self.slots / (self.slots + self.counter)

    @property
    def examples(self) -> tuple[str, ...]:
        return tuple(m.example() for m in self.members[:3])

    @property
    def rec(self) -> str:
        """The one-line recommendation the miner writes in `note` (prefix `rec:`)."""
        if self.typo:
            return "rec: typo (single row)"
        if self.heterogeneous:
            return f"rec: review (heterogeneous, precision {self.precision:.2f}; corrects its member rows only)"
        return f"rec: accept (precision {self.precision:.2f})"

    def sidecarEntry(self) -> dict[str, Any]:
        return {"members": [m.toJson() for m in self.members], "counters": self.counters, "children": self.children,
                "heterogeneous": self.heterogeneous}


def _keysOf(row: RowDiff) -> list[tuple[str, str, str]]:
    return [a.key for a in row.edits]


def _stats(rows: Sequence[RowDiff], level: str, counters: CounterIndex) -> tuple[int, int]:
    first = rows[0]
    return len(rows), counters.count(_keysOf(first), first.classKey, first.lemma, level)


def isHomogeneous(slots: int, counter: int) -> bool:
    return slots >= MIN_SLOTS and slots / (slots + counter) >= MIN_PRECISION


def _children(members: Sequence[RowDiff], level: str, counterIndex: CounterIndex) -> list[dict[str, Any]]:
    """The next-finer-level subgroups of a group (recursively down to L4), for the review's `d` split."""
    nxt = {L1: L2, L2: L3, L3: L4}.get(level)
    if nxt is None:
        return []
    sub: dict[str, list[RowDiff]] = defaultdict(list)
    for m in members:
        sub[signatureAt(m, nxt)].append(m)
    out: list[dict[str, Any]] = []
    for csig in sorted(sub, key=lambda s: (-len(sub[s]), s)):
        cm = sub[csig]
        _slots, ccount = _stats(cm, nxt, counterIndex)
        out.append({
            "level": nxt, "signature": csig, "slots": len(cm), "counter": ccount,
            "heterogeneous": len(cm) >= MIN_SLOTS and not isHomogeneous(len(cm), ccount),
            "examples": [m.example() for m in cm[:3]], "members": [m.toJson() for m in cm],
            "counters": counterIndex.examples(_keysOf(cm[0]), cm[0].classKey, cm[0].lemma, nxt),
            "children": _children(cm, nxt, counterIndex),
        })
    return out


def proposeGroups(diffRows: Sequence[RowDiff], counterIndex: CounterIndex) -> list[ProposedGroup]:
    """Section 4.3. Candidates: every (level, signature) group of L1..L4 with >= 3 rows. Greedy: repeatedly take the best
    candidate on the rows still unassigned, ordered by (homogeneous first, most rows, coarsest level, signature), and
    give it those rows; a candidate that lost rows is re-evaluated (its rows, hence its precision, only decrease). The
    rows no candidate takes become single-row L4 groups (`typo`; an L4 pair of identical rows stays a plain L4 group).
    Groups are returned sorted by (-slots, level, signature)."""
    bySig: dict[tuple[str, str], list[int]] = defaultdict(list)
    for i, r in enumerate(diffRows):
        for lv in LEVELS:
            bySig[(lv, signatureAt(r, lv))].append(i)
    counterOf: dict[tuple[str, str], int] = {}

    def counterFor(lv: str, sig: str, idx: Sequence[int]) -> int:
        if (lv, sig) not in counterOf:
            counterOf[(lv, sig)] = _stats([diffRows[idx[0]]], lv, counterIndex)[1]
        return counterOf[(lv, sig)]

    def sortKey(lv: str, sig: str, n: int) -> tuple[int, int, int, str]:
        return (0 if isHomogeneous(n, counterFor(lv, sig, bySig[(lv, sig)])) else 1, -n, LEVELS.index(lv), sig)

    heap: list[tuple[tuple[int, int, int, str], str, str, int]] = []
    for (lv, sig), idx in bySig.items():
        if len(idx) >= MIN_SLOTS:
            heapq.heappush(heap, (sortKey(lv, sig, len(idx)), lv, sig, len(idx)))
    taken = [False] * len(diffRows)
    assigned: list[tuple[str, str, list[int]]] = []
    while heap:
        _key, lv, sig, n = heapq.heappop(heap)
        free = [i for i in bySig[(lv, sig)] if not taken[i]]
        if len(free) < MIN_SLOTS:
            continue
        if len(free) != n:
            heapq.heappush(heap, (sortKey(lv, sig, len(free)), lv, sig, len(free)))
            continue
        for i in free:
            taken[i] = True
        assigned.append((lv, sig, free))
    for i, r in enumerate(diffRows):
        if not taken[i]:
            assigned.append((L4, signatureAt(r, L4), [i]))
    # the leftover L4 singletons of one signature (identical rows) are one group
    merged: dict[tuple[str, str], list[int]] = {}
    for lv, sig, idx in assigned:
        merged.setdefault((lv, sig), []).extend(idx)
    groups: list[ProposedGroup] = []
    for (lv, sig), idx in merged.items():
        members = [diffRows[i] for i in sorted(idx)]
        first = members[0]
        counter = counterFor(lv, sig, bySig[(lv, sig)])
        g = ProposedGroup(lv, sig, members, counter, typo=(lv == L4 and len(members) == 1),
                          heterogeneous=(len(members) >= MIN_SLOTS and not isHomogeneous(len(members), counter)))
        g.counters = counterIndex.examples(_keysOf(first), first.classKey, first.lemma, lv)
        g.children = _children(members, lv, counterIndex)
        groups.append(g)
    groups.sort(key=lambda g: (-g.slots, g.level, g.signature))
    return groups
