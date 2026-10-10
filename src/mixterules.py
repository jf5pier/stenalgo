"""Systematic Mixte rules (spec docs/specs/lexicon-decisions.md section 6, second row): the registry of the rules that
fix, at the source, a defect of the Lexicon Building (S1) itself.

Two ways to replay an accepted `mixte_rule` / `mixte_typo` decision, and when to choose which:

- **Correction rows** (`resources/mixteCorrections.tsv`, `util/build_mixte_corrections.py`): the default. The decision's member
  rows are corrected one by one; nothing else changes. Right when the cause is the DATA (a wrong Lexique/Infra phonology or
  syllabification of those words), when the group is heterogeneous (the ruling is true of its members only), and for every
  `mixte_typo`. A correction row that stops matching fails the build, so none goes stale silently.
- **A systematic rule** (this module): only when the cause is a defect of the BUILD, e.g. a bad Infra graphem-phonem
  association pattern (`Word.fixLexiqueInfraGraphPhon`) or a reform rewrite that breaks the unit alignment, so that the same
  mistake would reappear in rows added by a lexicon refresh, and the group is homogeneous (precision >= 0.95: no counter-example
  is damaged). The rule fixes every present and future row of the pattern; its group id must be `accept`ed to run.

A rule is a pure function on an output row (`dict` with the Mixte column names `ortho phon lemme cgram ... syll_cv
orthosyll_cv`) returning the (possibly corrected) row; it must be idempotent and must not touch a row it does not recognise.
Rules run in `group_id` order, before the correction rows, from `lexique.py` `outputMixedLexique`, right after the loop that
builds the output rows (the same stage as the reform rewrites, a few lines from `Word.fixLexiqueInfraGraphPhon`, whose
string-level patterns remain the place for an Infra association fix that needs no row context).

Register a rule with `MIXTE_RULES["<group_id>"] = ruleFunction` once its decision exists; `GLIDE_RULE_ID` below is the first.
"""
import re
from typing import Any, Callable, Mapping

from src.lexicondecisions import ACCEPT, Decisions, groupIdFor
from src.orthounits import REPEAT, SILENT

MixteRule = Callable[[dict[str, Any]], dict[str, Any]]


def _parseUnits(breakdown: str) -> tuple[list[str], set[int]]:
    """(units, breaks): `breaks` holds the index of every unit that a syllable break follows."""
    syllables = breakdown.split("|")
    units: list[str] = []
    breaks: set[int] = set()
    for at, syllable in enumerate(syllables):
        units.extend(syllable.split("_"))
        if at < len(syllables) - 1:
            breaks.add(len(units) - 1)
    return units, breaks


def _renderUnits(units: list[str], breaks: set[int]) -> str:
    out: list[str] = []
    for at, unit in enumerate(units):
        out.append(unit)
        if at < len(units) - 1:
            out.append("|" if at in breaks else "_")
    return "".join(out)


def _glideRow(row: dict[str, Any], sounds: list[str], letters: list[str], breaks: set[int]) -> dict[str, Any]:
    new = dict(row)
    new["phon"] = "".join(unit for unit in sounds if unit != SILENT)
    new["syll_cv"] = _renderUnits(sounds, breaks)
    new["orthosyll_cv"] = _renderUnits(letters, breaks)
    return new


def splitGlides(row: dict[str, Any]) -> dict[str, Any]:
    """The glide rule (cases A-G of `_splitVerbGlides`, then the cgram-agnostic case H of `_splitFusedEj`)."""
    return _splitFusedEj(_splitVerbGlides(row))


def _splitFusedEj(row: dict[str, Any]) -> dict[str, Any]:
    """
    Case H (group e3e2ed7746, any grammatical category): the fused sound unit `Ej` on the letters `ay` (`crayon` `k_R_Ej|@`
    `c_r_ay|on`, `balaya` `b_a|l_Ej|a`, `ayant`, `attrayant`) is two units, `phon` unchanged:
    - the next unit is sounded after a syllable break: `E`, `j` on the letters `a`, `y`, the break moved between them
      (`k_R_E|j_@` `c_r_a|y_on`);
    - the next unit is silent with no break, or the word ends (`balaye` `b_a|l_Ej_#`, `spray` `s_p_R_Ej`): `E_j` on `a_y`, no break.
    Any other shape and any row whose breakdowns do not pair unit for unit are left alone. The `ay` rows whose sound is a lone
    `E` (about 18) are not touched.
    """
    sounds, soundBreaks = _parseUnits(row["syll_cv"])
    letters, letterBreaks = _parseUnits(row["orthosyll_cv"])
    if len(sounds) != len(letters) or soundBreaks != letterBreaks:
        return row
    for k in range(len(sounds)):
        if sounds[k] != "Ej" or letters[k] != "ay":
            continue
        following = sounds[k + 1] if k + 1 < len(sounds) else None
        if following is None or (following == SILENT and k not in soundBreaks):
            breaks2 = {b if b < k else b + 1 for b in soundBreaks}
        elif following != SILENT and k in soundBreaks:
            breaks2 = {b if b <= k else b + 1 for b in soundBreaks}
        else:
            continue
        sounds2 = sounds[:k] + ["E", "j"] + sounds[k + 1:]
        letters2 = letters[:k] + ["a", "y"] + letters[k + 1:]
        return _splitFusedEj(_glideRow(row, sounds2, letters2, breaks2))
    return row


def _splitVerbGlides(row: dict[str, Any]) -> dict[str, Any]:
    """
    The verb glide rule (rulings of 2026-10-09, TODO.md "Glide encodings"): a verb's glide opens the next syllable, as its own unit.

    Sounds (`syll_cv`) and letters (`orthosyll_cv`) are cut into the same units; the first matching case wins:
    - A  `-Ciions`/`-Ciiez` (letters `i` + `i`): `s_ij_#|§` -> `s_i|j_§` (`phon` unchanged);
    - B  `-yions`/`-yiez` (letters `y` + `i`): `8_ij_#|§` -> `8_ij|j_§` (`phon` gains a `j`: the doubled glide);
    - C  `-illions`/`-illiez`, `-oyiez` (letters `ill`/`ll`/`y` + `i`): `i|j_#_§` -> `i_j|j_§` (`phon` gains a `j`);
    - F  the letters `lli` (`appareillions`, `surveillions`): one `j` or the fused `jj` -> `j|j`, the second `j` on a repeat unit;
    - G  the fused `Ej` unit on the letters `ay` before a first- or second-person plural ending (`abstrayons` `Ej|§`, `abstrayions`
         `Ej_#|§`): `-ayons`/`-ayez` `E|j_§` (letters `a|y_ons`, `phon` unchanged), `-ayions`/`-ayiez` `E_j|j_§` (letters
         `a_y|i_ons`, `phon` gains a `j`), the shapes `payons` and `payions` already have;
    - E  one letter carrying a vowel and a glide (`cria` `k_R_ij|a`, `accablions` `b_l_ij|§`, `devrions` `v_R_ij|§`): the fused
         `ij` unit -> `i|j`, the glide on a repeat unit (`c_r_i|=_a`, src/orthounits.py); `phon` unchanged.
    Only a verb row whose two breakdowns pair unit for unit and break at the same places is touched; the result is left alone
    by a second call (idempotent).
    """
    if row.get("cgram") != "VER":
        return row
    sounds, soundBreaks = _parseUnits(row["syll_cv"])
    letters, letterBreaks = _parseUnits(row["orthosyll_cv"])
    if len(sounds) != len(letters) or soundBreaks != letterBreaks:
        return row
    ending = re.search(r"(ions|iez)$", row["ortho"]) is not None
    if re.search(r"(ions|iez|ons|ez)$", row["ortho"]):
        for k in range(len(sounds) - 1):
            if sounds[k] != "Ej" or letters[k] != "ay":
                continue
            if sounds[k + 1] in ("§", "e") and k in soundBreaks:
                sounds2 = sounds[:k] + ["E", "j"] + sounds[k + 1:]
                letters2 = letters[:k] + ["a", "y"] + letters[k + 1:]
                breaks2 = {b if b <= k else b + 1 for b in soundBreaks}
                return _glideRow(row, sounds2, letters2, breaks2)
            if sounds[k + 1] == SILENT and letters[k + 1] == "i" and k + 2 < len(sounds) and sounds[k + 2] in ("§", "e") \
                    and k + 1 in soundBreaks:
                sounds2 = sounds[:k] + ["E", "j", "j"] + sounds[k + 2:]
                letters2 = letters[:k] + ["a", "y", "i"] + letters[k + 2:]
                breaks2 = {b if b <= k else b + 1 for b in soundBreaks}
                breaks2.discard(k + 1)
                breaks2.discard(k + 2)
                breaks2.add(k + 1)
                return _glideRow(row, sounds2, letters2, breaks2)
    for k in range(len(sounds) - 1):
        following = sounds[k + 2] if k + 2 < len(sounds) else ""
        if sounds[k] == "ij" and sounds[k + 1] == SILENT and letters[k + 1] == "i" and following in ("§", "e") \
                and k + 1 in soundBreaks:
            sounds2, breaks2 = sounds[:], set(soundBreaks)
            breaks2.discard(k + 1)
            breaks2.add(k)
            if letters[k] == "i":
                sounds2[k], sounds2[k + 1] = "i", "j"
            elif letters[k] == "y":
                sounds2[k + 1] = "j"
            else:
                return row
            return _glideRow(row, sounds2, letters, breaks2)
        if sounds[k] == "j" and sounds[k + 1] == SILENT and letters[k + 1] == "i" and letters[k] in ("ill", "ll", "y") \
                and following in ("§", "e"):
            sounds2, breaks2 = sounds[:], set(soundBreaks)
            sounds2[k + 1] = "j"
            breaks2.discard(k - 1)
            breaks2.discard(k + 1)
            breaks2.add(k)
            return _glideRow(row, sounds2, letters, breaks2)
    for k in range(len(sounds)):
        if letters[k] == "lli" and sounds[k] in ("j", "jj") and ending and (k + 1 >= len(letters) or letters[k + 1] != REPEAT):
            sounds2 = sounds[:k] + ["j", "j"] + sounds[k + 1:]
            letters2 = letters[:k + 1] + [REPEAT] + letters[k + 1:]
            breaks2 = {b if b < k else b + 1 for b in soundBreaks}
            breaks2.discard(k + 1)
            if sounds[k] == "j":
                breaks2.discard(k - 1)
            breaks2.add(k)
            return _glideRow(row, sounds2, letters2, breaks2)
    for k in range(len(sounds) - 1):
        if sounds[k] == "ij" and sounds[k + 1] not in (SILENT, "j") and letters[k] in ("i", "y"):
            sounds2 = sounds[:k] + ["i", "j"] + sounds[k + 1:]
            letters2 = letters[:k + 1] + [REPEAT] + letters[k + 1:]
            breaks2 = {b if b < k else b + 1 for b in soundBreaks}
            breaks2.discard(k + 1)
            breaks2.add(k)
            return _glideRow(row, sounds2, letters2, breaks2)
    return row


def dropStrayGlide(row: dict[str, Any]) -> dict[str, Any]:
    """
    A verb's `ij` unit on the letter `i` followed by a silent unit on the letter `e...` (`dévierait` `d_e|v_ij_#|R_E`
    `d_é|v_i_e|r_ait`) is the vowel only: the mute `e` of the conditional and future endings makes no glide, and no source has one
    (`deviRE`). The unit becomes `i` and the `j` leaves `phon`. Exactly five Mixte rows have this shape (`dévierait`, `sciera`,
    `recopierait`, `mésallieras`, `mésallies`), all of them differing from Wiktionary/GLÀFF by that `j` (precision 1.00).
    """
    if row.get("cgram") != "VER":
        return row
    sounds, soundBreaks = _parseUnits(row["syll_cv"])
    letters, letterBreaks = _parseUnits(row["orthosyll_cv"])
    if len(sounds) != len(letters) or soundBreaks != letterBreaks:
        return row
    for k in range(len(sounds) - 1):
        if sounds[k] == "ij" and sounds[k + 1] == SILENT and letters[k] == "i" and letters[k + 1].startswith("e"):
            sounds2 = sounds[:]
            sounds2[k] = "i"
            return _glideRow(row, sounds2, letters, soundBreaks)
    return row


def schwaOfE(row: dict[str, Any]) -> dict[str, Any]:
    """
    A verb's stem schwa written `2` (Lexique383 spells the /ø/-like schwa of the letter `e` with the eu vowel: `corseter`
    `kORs2te`, `peser` `p2za`, `menuiser` `m2n8ize`) is the project's schwa `°` (ruling of 2026-10-10): every `2` unit whose
    letter unit is a plain `e` becomes `°`; the `2` of `eu`/`oeu`/`eû` letters is the real vowel and stays (`ameuter` `am2te`).
    `flageller` is the one exception (`flagellant` is `flaZEl@` in Wiktionary and GLAFF). 62 Mixte verb rows, 25 lemmas;
    against the references 41 agree exactly, 8 more up to the mid vowel `o`/`O`, 12 have no reference.
    """
    if row.get("cgram") != "VER" or row.get("lemme") in SCHWA_OF_E_EXCEPTIONS:
        return row
    sounds, soundBreaks = _parseUnits(row["syll_cv"])
    letters, letterBreaks = _parseUnits(row["orthosyll_cv"])
    if len(sounds) != len(letters) or soundBreaks != letterBreaks:
        return row
    if "".join(unit for unit in sounds if unit != SILENT) != row["phon"]:
        return row
    changed = [k for k, (sound, letter) in enumerate(zip(sounds, letters)) if sound == "2" and letter.lower() == "e"]
    if not changed:
        return row
    for k in changed:
        sounds[k] = "°"
    return _glideRow(row, sounds, letters, soundBreaks)


def syllFromPhon(row: dict[str, Any]) -> dict[str, Any]:
    """
    Ruling of 2026-10-10 "phon wins": when `phon` differs from the sounded join of `syll_cv` (every unit but `#`) ONLY by
    `E`/`e` swaps at equal length, the swapped units of `syll_cv` take the `phon` vowel. The 108 rows of `em-`/`en-` +
    `ê`/`ei` (`embêter` `@|b_e|t_e` -> `@|b_E|t_e`, `emmêler`, `embouteiller`) keep their open `E` in `phon`, as the rest of
    their paradigm does (`embêtez` `@|b_E|t_e`); the other disagreeing rows (loanwords: `capharnaüm`, `samoan`, `spoiler`)
    differ by more than the swap and are untouched.
    """
    sounds, breaks = _parseUnits(row["syll_cv"])
    joined = "".join(unit for unit in sounds if unit != SILENT)
    phon = row["phon"]
    if joined == phon or len(joined) != len(phon):
        return row
    if any(a != b and {a, b} != {"E", "e"} for a, b in zip(joined, phon)):
        return row
    fixed: list[str] = []
    at = 0
    for unit in sounds:
        if unit == SILENT:
            fixed.append(unit)
            continue
        fixed.append(phon[at:at + len(unit)] if len(unit) == 1 and unit in "Ee" else unit)
        at += len(unit)
    if "".join(unit for unit in fixed if unit != SILENT) != phon:
        return row
    new = dict(row)
    new["syll_cv"] = _renderUnits(fixed, breaks)
    return new


SCHWA_OF_E_EXCEPTIONS = frozenset({"flageller"})

STRAY_GLIDE_SIGNATURE = "verb ij before a silent e unit (dévierait, sciera): the glide j is stray, ij -> i"
STRAY_GLIDE_RULE_ID = groupIdFor("mixte_rule", "-", STRAY_GLIDE_SIGNATURE)

GLIDE_RULE_SIGNATURE = "verb glides opening the next syllable: ij -> i|j, doubled j|j after y and ill, repeat unit ="
GLIDE_RULE_ID = groupIdFor("mixte_rule", "-", GLIDE_RULE_SIGNATURE)

SCHWA_OF_E_SIGNATURE = "verb 2 on the plain letter e is the stem schwa: 2 -> ° (corseter, peser, menuiser; not eu)"
SCHWA_OF_E_RULE_ID = groupIdFor("mixte_rule", "-", SCHWA_OF_E_SIGNATURE)

SYLL_FROM_PHON_SIGNATURE = "phon differs from the sounded join of syll_cv only by E/e swaps (embêter, emmêler): syll_cv takes the phon vowel"
SYLL_FROM_PHON_RULE_ID = groupIdFor("mixte_rule", "-", SYLL_FROM_PHON_SIGNATURE)

MIXTE_RULES: dict[str, MixteRule] = {
    GLIDE_RULE_ID: splitGlides, STRAY_GLIDE_RULE_ID: dropStrayGlide, SCHWA_OF_E_RULE_ID: schwaOfE,
    SYLL_FROM_PHON_RULE_ID: syllFromPhon}


def activeRules(decisions: Decisions, registry: Mapping[str, MixteRule] | None = None) -> list[tuple[str, MixteRule]]:
    """The (group_id, rule) pairs to run: the registered rules whose group is accepted, sorted by group id.
    `registry` defaults to `MIXTE_RULES` (a parameter for tests)."""
    rules = MIXTE_RULES if registry is None else registry
    out: list[tuple[str, MixteRule]] = []
    for groupId in sorted(rules):
        d = decisions.get(groupId)
        if d is not None and d.verdict == ACCEPT:
            out.append((groupId, rules[groupId]))
    return out


def applyRules(rows: list[dict[str, Any]], rules: list[tuple[str, MixteRule]]) -> list[dict[str, Any]]:
    """`rows` through each active rule in turn; the same list when there is no rule."""
    if not rules:
        return rows
    for _groupId, rule in rules:
        rows = [rule(row) for row in rows]
    return rows
