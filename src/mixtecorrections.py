"""The committed Mixte corrections (spec docs/specs/lexicon-decisions.md section 6, first row): `resources/mixteCorrections.tsv`,
written by `util/build_mixte_corrections.py` from the accepted `mixte_rule` / `mixte_typo` decisions, replayed by
`lexique.py` `outputMixedLexique` on the OUTPUT rows, after every reform rewrite.

A correction row is keyed by the output row's (ortho, lemme, cgram, infover as written, trailing `;` included) and carries
the corrected `phon`, `syll_cv`, `orthosyll_cv` plus the `group_id` of the decision that produced it. Every key must match
exactly one output row: a key that matches none (the row moved, was renamed or dropped) or several fails the build with the
whole list, so a correction never goes stale silently.

Standard library only; kept apart from `lexique.py` (a script that builds the lexicon on import) so it can be tested alone.
"""
import os
from dataclasses import dataclass
from typing import Any, Sequence

CORRECTIONS_PATH = "resources/mixteCorrections.tsv"
MANUAL_CORRECTIONS_PATH = "resources/mixteManualCorrections.tsv"
COLUMNS = ("ortho", "lemme", "cgram", "infover", "genre", "nombre", "phon", "syll_cv", "orthosyll_cv", "group_id")
HEADER_COMMENT = (
    "# Corrections of LexiqueMixte.tsv rows (spec docs/specs/lexicon-decisions.md section 6), written by\n"
    "# `python -m util.build_mixte_corrections` from the accepted mixte_rule / mixte_typo decisions. Do not edit by hand.\n"
    "# ortho, lemme, cgram, infover, genre, nombre: the key of the OUTPUT row (infover as written, trailing ';' included;\n"
    "#   genre and nombre tell the NOM/ADJ slots of one spelling apart); it must match\n"
    "#   exactly one row of the build, else the build fails | phon, syll_cv, orthosyll_cv: the corrected fields\n"
    "# group_id: the decision that produced the row. Sorted by key.\n"
)


class MixteCorrectionError(ValueError):
    """The corrections file is malformed, or a correction does not match exactly one output row."""


@dataclass(frozen=True)
class Correction:
    ortho: str
    lemme: str
    cgram: str
    infover: str
    genre: str
    nombre: str
    phon: str
    syllCV: str
    orthosyllCV: str
    groupId: str

    @property
    def key(self) -> tuple[str, str, str, str, str, str]:
        return (self.ortho, self.lemme, self.cgram, self.infover, self.genre, self.nombre)

    def fields(self) -> tuple[str, ...]:
        return (self.ortho, self.lemme, self.cgram, self.infover, self.genre, self.nombre, self.phon, self.syllCV, self.orthosyllCV, self.groupId)


def rowKeyOf(row: dict[str, Any]) -> tuple[str, str, str, str, str, str]:
    return (row["ortho"], row["lemme"], row["cgram"], row["infover"], row.get("genre", ""), row.get("nombre", ""))


def formatMixteCorrections(corrections: Sequence[Correction]) -> str:
    """The file text: comment header, column line, rows sorted by (key, group_id). Deterministic."""
    lines = [HEADER_COMMENT.rstrip("\n"), "\t".join(COLUMNS)]
    lines += ["\t".join(c.fields()) for c in sorted(corrections, key=lambda c: (c.key, c.groupId))]
    return "\n".join(lines) + "\n"


def loadMixteCorrections(path: str = CORRECTIONS_PATH) -> list[Correction]:
    """The corrections of `path`; an absent or header-only file gives []. MixteCorrectionError on a malformed row or a
    duplicated key."""
    if not os.path.exists(path):
        return []
    out: list[Correction] = []
    seen: dict[tuple[str, str, str, str, str, str], str] = {}
    headerSeen = False
    with open(path, encoding="utf-8") as f:
        for number, line in enumerate(f, 1):
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            cells = line.split("\t")
            if not headerSeen:
                if tuple(cells) != COLUMNS:
                    raise MixteCorrectionError(f"{path}:{number}: header {cells!r}, expected {list(COLUMNS)!r}")
                headerSeen = True
                continue
            if len(cells) != len(COLUMNS):
                raise MixteCorrectionError(f"{path}:{number}: {len(cells)} columns, expected {len(COLUMNS)}")
            c = Correction(*cells)
            if c.key in seen:
                raise MixteCorrectionError(f"{path}:{number}: duplicate key {c.key!r} (groups {seen[c.key]}, {c.groupId})")
            seen[c.key] = c.groupId
            out.append(c)
    return out


def loadAllMixteCorrections(paths: Sequence[str] = (CORRECTIONS_PATH, MANUAL_CORRECTIONS_PATH)) -> list[Correction]:
    """The corrections of every file of `paths` (the generated file, then the hand-maintained one). MixteCorrectionError when a
    key occurs in two files."""
    out: list[Correction] = []
    owner: dict[tuple[str, str, str, str, str, str], str] = {}
    for path in paths:
        for c in loadMixteCorrections(path):
            if c.key in owner:
                raise MixteCorrectionError(f"duplicate key {c.key!r} in {owner[c.key]} and {path}")
            owner[c.key] = path
            out.append(c)
    return out


def applyMixteCorrections(rows: list[dict[str, Any]], corrections: Sequence[Correction]) -> list[dict[str, Any]]:
    """`rows` with every correction applied (phon, syll_cv, orthosyll_cv replaced); a new list, the input rows are not
    modified. Without corrections the rows come back as they are. Raises MixteCorrectionError listing every key that matches
    no row and every key that matches several."""
    if not corrections:
        return rows
    wanted = {c.key: c for c in corrections}
    positions: dict[tuple[str, str, str, str, str, str], list[int]] = {}
    for i, row in enumerate(rows):
        k = rowKeyOf(row)
        if k in wanted:
            positions.setdefault(k, []).append(i)
    unmatched = sorted(k for k in wanted if k not in positions)
    ambiguous = sorted(k for k, at in positions.items() if len(at) > 1)
    if unmatched or ambiguous:
        parts = [f"no output row for {k!r} (group {wanted[k].groupId})" for k in unmatched]
        parts += [f"{len(positions[k])} output rows for {k!r} (group {wanted[k].groupId})" for k in ambiguous]
        raise MixteCorrectionError("Mixte corrections do not match exactly one row each:\n  " + "\n  ".join(parts))
    out = list(rows)
    for k, at in positions.items():
        c = wanted[k]
        out[at[0]] = {**rows[at[0]], "phon": c.phon, "syll_cv": c.syllCV, "orthosyll_cv": c.orthosyllCV}
    return out
