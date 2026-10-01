"""Decided growth scopes of the affix rules (user decisions of 2026-09-30,
scratch/scope-decisions-2026-09-30.md).

An anchor listed in `SCOPES` does NOT grow through the generic lattice (`growAffixesLattice`): its rule
has exactly the forms listed here, in order. A scope form fuses the anchor syllable with the NEIGHBOUR
syllable (the one before a suffix anchor, the one after a prefix anchor, so k=2) when the carrier matches:

- `anchors`: the anchor syllable's spelling is one of these (None: any spelling of the merged anchor);
- `sound`: the neighbour's phonology (X-SAMPA syllable, e.g. `ZuR`, `tR°`) fully matches this regex;
- `spelling`: the neighbour's spelling fully matches this regex.

All given conditions must hold. An anchor with an empty form list is a "no growth" anchor. A carrier
that a form names but that gains nothing under the rule's keys falls back to the anchor alone
(`affixrules.resolveFallbacks`), priced `EXCLUSION_COST` each.

Anchors are keyed by (position, ortho, phono) of the pool's k=1 anchor, exactly as `Candidate` reports them.
"""
import re
from dataclasses import dataclass

C = "ptkbdgfsSvzZmnNlRjw"                      # consonant phonemes (X-SAMPA)
V = f"[^{C}]"                                  # any vowel phoneme
CL = "[^aeiouyàâäéèêëîïôöùûüœ]"                 # consonant letters
C12, C0 = f"[{C}]{{1,2}}", f"[{C}]*"
C12_NOT_BV = "[" + "".join(c for c in C if c not in "bv") + "]{1,2}"


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


def _form(label: str, anchors: str | None = None, sound: str | None = None, spelling: str | None = None) -> ScopeForm:
    return ScopeForm(label, frozenset(anchors.split("|")) if anchors else None,
                     re.compile(sound) if sound else None, re.compile(spelling) if spelling else None)


PREFIX, SUFFIX = "prefix", "suffix"
ScopeKey = tuple[str, str, str]

SCOPES: dict[ScopeKey, list[ScopeForm]] = {
    (SUFFIX, "ment", "m@"): [_form("C{1,2}[eui]+", spelling=f"{CL}{{1,2}}[eui]+")],
    (PREFIX, "re|reh", "R°"): [],
    (PREFIX, "en", "@"): [_form("C{1,2}@", sound=f"{C12}@")],
    (PREFIX, "de|des|dé|déh", "de"): [],
    (PREFIX, "de", "d°"): [_form("man|ve", spelling="man|ve")],
    (SUFFIX, "tion", "sj§"): [_form("C*[ai]", sound=f"{C0}[ai]")],
    (PREFIX, "ain|hin|im|in", "5"): [_form("in+té", anchors="in", spelling="té")],
    (PREFIX, "é", "e"): [],
    (SUFFIX, "ter", "te"): [],
    (SUFFIX, "té", "te"): [_form("C\\{bv}{1,2}i", sound=f"{C12_NOT_BV}i")],
    (PREFIX, "au", "o"): [_form("jour|to|tre|di", sound="ZuR|to|tR°|di")],
    (PREFIX, "pa", "pa"): [],
    (SUFFIX, "cer|cé|cée|cés|scer|se|ser|sser|ssez|ssée|sé", "se"): [_form("cé:m@", anchors="cé", sound="m@")],
    (PREFIX, "par", "paR"): [],
    (PREFIX, "ai|aî|e|ei|hai|he|hê|é", "E"): [_form("e:ksky|kspli|sE|n°", anchors="e", sound="ksky|kspli|sE|n°")],
    (SUFFIX, "der", "de"): [_form("dez|der|dé:gaR|m@", anchors="dez|der|dé", sound="gaR|m@")],
    (PREFIX, "ra|rai|raie|re|rhé|ré|réh", "Re"): [_form("ré:a|fle|vE|C{1,2}y", anchors="ré", sound=f"a|fle|vE|{C12}y")],
    (PREFIX, "sa|sah", "sa"): [],
    (SUFFIX, "ver", "ve"): [_form("vé:Ri", anchors="vé", sound="Ri")],
    (PREFIX, "pro|proh|prô", "pRo"): [],
    (PREFIX, "ce|sce|se", "s°"): [],
    (PREFIX, "pou|pu", "pu"): [],
    (SUFFIX, "ser|sée|zer|zé", "ze"): [_form("li", sound="li"), _form("sez:C*y", anchors="sez", sound=f"{C0}y")],
    (PREFIX, "de|dea|di|die|dis|dy|dî", "di"): [_form("di:C{1,2}i", anchors="di", sound=f"{C12}i")],
    (PREFIX, "e|hi|hy|i|y|î", "i"): [_form("i:[mn][aeiouy]", anchors="i", sound="[mn][aeiouy]")],
    (SUFFIX, "rae|rai|raie|re|rer|rez|rrer|rrhée|rrée|rée", "Re"): [
        _form("rer:p[aeiouy]|C*e|sy", anchors="rer", sound=f"p[aeiouy]|{C0}e|sy")],
    (PREFIX, "o", "o"): [_form("C{1,2}i|kV", sound=f"{C12}i|k{V}")],
    (SUFFIX, "ger", "Ze"): [],
    (SUFFIX, "ner", "ne"): [_form("né:C{1,2}[i°]", anchors="né", sound=f"{C12}[i°]")],
    (SUFFIX, "cher", "Se"): [],
}

# Fusions of spelling variants decided by the user (2026-10-01): the merged anchor carries the approved
# growth of its approved part only (the form's `anchors` keep it off the other spellings), the other
# spellings are anchor-only. `der` also gets its `gaR|m@` scope extended from `dez` to `der` and `dé`.
APPROVED_FUSIONS: dict[ScopeKey, list[ScopeForm]] = {
    (PREFIX, "am|an|ant|em|en|ench|enh|ham|han|hen", "@"): [_form("en:C{1,2}@", anchors="en", sound=f"{C12}@")],
    (SUFFIX, "ner|nez|nner|nnée|née|nées", "ne"): [_form("né:C{1,2}[i°]", anchors="né", sound=f"{C12}[i°]")],
    (SUFFIX, "der|dé|dée", "de"): [_form("dez|der|dé:gaR|m@", anchors="dez|der|dé", sound="gaR|m@")],
    (SUFFIX, "ccion|cion|cyon|sion|ssion|tion|tions", "sj§"): [_form("tion:C*[ai]", anchors="tion|tions", sound=f"{C0}[ai]")],
}


def scopeFormsOf(position: str, ortho: str, phono: str) -> list[ScopeForm] | None:
    """The decided forms of this anchor (empty: no growth), or None when it has no decided scope."""
    key = (position, ortho, phono)
    return SCOPES[key] if key in SCOPES else APPROVED_FUSIONS.get(key)


def fusionVerdict(merged: ScopeKey, parts: list[ScopeKey]) -> str | None:
    """What the user decided for a merged spelling-variant anchor: "fused" (an approved fusion, or a merged
    anchor that is itself one of the 30 decided anchors), "apart" (it contains a decided anchor but was
    not approved: its parts stay separate), or None (no decision: the engine's own rival test applies)."""
    if merged in APPROVED_FUSIONS or merged in SCOPES:
        return "fused"
    if any(p in SCOPES for p in parts):
        return "apart"
    return None
