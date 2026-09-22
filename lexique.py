#!/usr/bin/python
# coding: utf-8
#
# This class provides functions to read Lexique version 383 [1,2] for its data
# concerning French word ortograph, frequency, grammatical info, phonology and
# phonetic syllable breakdow.  It then corrects the orthographic syllable
# breakdow using the phoneme to graphem association of LexiqueInfra [3].
# The output is a simplified French Lexique with corrected ortographic
# syllables.
#
# 1. New, B., Pallier, C., Brysbaert, M., Ferrand, L. (2004)
#  Lexique 2 : A New French Lexical Database.
#  Behavior Research Methods, Instruments, & Computers, 36 (3), 516-524.
# 2. New, B., Brysbaert, M., Veronis, J., & Pallier, C. (2007).
#  The use of film subtitles to estimate word frequencies.
#  Applied Psycholinguistics, 28(4), 661-677.
# 3. Gimenes, M., Perret, C., & New, B. (2020).
#  Lexique-Infra: grapheme-phoneme, phoneme-grapheme regularity, consistency,
#  and other sublexical statistics for 137,717 polysyllabic French words.
#  Behavior Research Methods. doi.org/10.3758/s13428-020-01396-2
#
import sys
import csv
import re
import xml.etree.ElementTree as ET
from copy import deepcopy
from dataclasses import dataclass
from src.grammar import Syllable, SyllableCollection
# from src.word import GramCat
from typing import Any

verboseList: list[str] = ['game', 'balaye', 'soleil', 'effraye','essaye','égaye']

def printVerbose(word: str, msg: list[Any]) -> None:
    if word in verboseList:  # ["soleil"] :
        print(word, " :\n", " ".join(map(str, msg)))

def loadLexiconExclusions(tsvPath: str = "resources/lexiconExclusions.tsv") -> dict[str, str]:
    """
    Parse resources/lexiconExclusions.tsv into a {word: reason} dict -- corpus
    `ortho` strings to drop entirely from the generated lexicon (see that file's
    header for the reason vocabulary). Replaces the old hardcoded
    `problemList`/`foreignList` Python literals.
    """
    with open(tsvPath, encoding="utf-8") as tsvFile:
        rawRows = [line.rstrip("\n") for line in tsvFile if not line.startswith("#")]
    exclusions: dict[str, str] = {}
    for row in rawRows[1:]:  # skip header
        if not row.strip():
            continue
        word, reason, _note = row.split("\t", 2)
        exclusions[word] = reason
    return exclusions


ignoredList = frozenset(loadLexiconExclusions())

# Spelling variants of the same lexeme that Lexique383 lists under distinct `lemme`
# strings, collapsed to one canonical lemme so they don't compete for a separate
# steno discriminator symbol.
#
# 2026-09-17: superseded the kasher-family entries this table used to carry
# (kascher/cascher/cachère/casher all -> "kasher", per Larousse). "casher" is now
# the canonical spelling with its own full 1990-reform inflection (casher/cashers/
# cashère/cashères, resources/Lexique383.tsv), rather than a variant folded under
# "kasher" -- kasher/cachère (and kascher/cascher, already inert) are now dropped
# entirely via resources/lexiconExclusions.tsv instead of lemme-normalized, since
# they were causing an unresolvable spelling-ambiguity in the discriminator
# selection (see SHARED_DISCRIMINATOR_REWIRE_PLAN.md-adjacent session notes / RESUME_2026-09-17.md).
# île/ile is the 1990 orthographic-reform circumflex-dropping variant of "île".
spellingVariantLemme: dict[str, str] = {
    "ile": "île",
}

# Closed-class pronoun paradigms that Lexique383 gives a distinct `lemme` string per
# number/gender form (unlike nouns/verbs, whose inflected forms share one lemme).
# Normalized here -- keyed by (lemme, cgram) since e.g. "celle" is also a rare,
# unrelated NOM sense (freq 0.02) that should NOT be folded in -- so number/gender
# is handled by the same-lemma/suffix discrimination track instead of costing a
# separate */# symbol slot.
pronounParadigmLemme: dict[tuple[str, str], str] = {
    ("ils", "PRO:per"): "il",
    ("elles", "PRO:per"): "elle",
    ("celle", "PRO:dem"): "celui",
    ("celles", "PRO:dem"): "celui",
    ("ceux", "PRO:dem"): "celui",
}

# Off by default: merging the full 1990-reform word list changes `lemme` values for
# anyone who runs `python lexique.py`, so it's opt-in rather than baked into the
# committed spellingVariantLemme table. Flip to True locally to regenerate
# LexiqueMixte.tsv with the reform applied; see resources/reform1990.tsv and
# scratch/reform1990/STATUS.md for scope (diacritic categories only, so far) and
# sourcing.
APPLY_1990_REFORM_LEMMES: bool = True


def _readReform1990Rows(tsvPath: str) -> list[list[str]]:
    """
    Read resources/reform1990.tsv (comment lines starting with '#', a header row, then
    tab-separated oldSpelling/newSpelling/category/appliesToLemmeNormalization/
    appliesToOrthoRewrite/appliesToPluralRewrite/isException/note rows), padded to the
    fixed 8-column width.
    """
    with open(tsvPath, encoding="utf-8") as tsvFile:
        rawRows = [line.rstrip("\n") for line in tsvFile if not line.startswith("#")]
    rows = []
    for row in rawRows[1:]:  # skip header
        if not row.strip():
            continue
        fields = row.split("\t")
        fields += [""] * (8 - len(fields))
        rows.append(fields[:8])
    return rows


def loadReform1990Lemmes(tsvPath: str) -> dict[str, str]:
    """
    Parse resources/reform1990.tsv into an {oldSpelling: newSpelling} dict, keeping
    only rows where appliesToLemmeNormalization is true and isException is false.
    """
    reformLemmes: dict[str, str] = {}
    for oldSpelling, newSpelling, _category, appliesToLemmeNormalization, \
            _appliesToOrthoRewrite, _appliesToPluralRewrite, isException, _note \
            in _readReform1990Rows(tsvPath):
        if appliesToLemmeNormalization == "True" and isException == "False":
            reformLemmes[oldSpelling] = newSpelling
    return reformLemmes


if APPLY_1990_REFORM_LEMMES:
    spellingVariantLemme.update(loadReform1990Lemmes("resources/reform1990.tsv"))


# Off by default, and independent of APPLY_1990_REFORM_LEMMES: this rewrites the actual
# `ortho`/`orthosyll_cv` output columns to the new-norm spelling for every corpus row in
# a reform-affected word's family (not just rows that already collide with an existing
# new-spelling row, unlike the lemme-merge above) -- this is what makes LexiqueMixte.tsv
# generative under the new norm rather than merely collision-free. See
# resources/reform1990.tsv and scratch/reform1990/STATUS.md / the 2026-09-16 plan for
# scope (diacritic categories only, so far) and the architectural reasoning (the rewrite
# happens at output time in outputMixedLexique(), not on word.ortho itself, since
# word.ortho must stay the original spelling for the LexiqueInfraCorrespondance
# grapheme-phoneme lookup in breakdownSyllables() to keep working).
APPLY_1990_REFORM_ORTHO: bool = True


@dataclass(frozen=True)
class OrthoRewriteRule:
    position: int
    oldPrefix: str
    oldChar: str
    newChar: str


def computeSingleEditRule(oldSpelling: str, newSpelling: str) -> "OrthoRewriteRule":
    """
    Compute the single-character edit (substitution, deletion, OR insertion) that turns
    oldSpelling into newSpelling: same length -> substitution at the one differing
    position (e.g. "événement"/"évènement", é->è); oldSpelling one character longer ->
    deletion (e.g. "quincaillier"/"quincailler", dropping the "i" before "er" -- newChar
    is "" for a deletion); newSpelling one character longer -> insertion (e.g.
    "chariot"/"charriot", inserting an "r" -- oldChar is "" for an insertion). Raises if
    the two strings don't differ by exactly one such edit.
    """
    if len(oldSpelling) == len(newSpelling):
        diffPositions = [i for i, (o, n) in enumerate(zip(oldSpelling, newSpelling)) if o != n]
        if len(diffPositions) != 1:
            raise ValueError(
                f"reform1990.tsv: {oldSpelling!r}/{newSpelling!r} differ at "
                f"{len(diffPositions)} positions, expected exactly 1")
        position = diffPositions[0]
        return OrthoRewriteRule(position, oldSpelling[:position],
                                 oldSpelling[position], newSpelling[position])
    if len(oldSpelling) == len(newSpelling) + 1:
        for position in range(len(oldSpelling)):
            if oldSpelling[:position] + oldSpelling[position + 1:] == newSpelling:
                return OrthoRewriteRule(position, oldSpelling[:position],
                                         oldSpelling[position], "")
        raise ValueError(
            f"reform1990.tsv: {oldSpelling!r} isn't newSpelling {newSpelling!r} plus one "
            "inserted character, can't derive a single-character deletion")
    if len(newSpelling) == len(oldSpelling) + 1:
        for position in range(len(newSpelling)):
            if newSpelling[:position] + newSpelling[position + 1:] == oldSpelling:
                return OrthoRewriteRule(position, oldSpelling[:position],
                                         "", newSpelling[position])
        raise ValueError(
            f"reform1990.tsv: {newSpelling!r} isn't oldSpelling {oldSpelling!r} plus one "
            "inserted character, can't derive a single-character insertion")
    raise ValueError(
        f"reform1990.tsv: {oldSpelling!r}/{newSpelling!r} differ in length by more than "
        "one character, can't derive a single-character ortho-rewrite rule")


def loadReform1990OrthoRewrites(tsvPath: str) -> dict[str, "OrthoRewriteRule"]:
    """
    Parse resources/reform1990.tsv into a rewrite-rule dict keyed by BOTH the old and
    new spelling of each appliesToOrthoRewrite=true row (so a word matches regardless of
    whether APPLY_1990_REFORM_LEMMES already normalized its lemme). Each rule records the
    single character position that distinguishes the old and new spelling --
    orthoRewriteOccurrence()/applyOrthoRewrite() use it to scope the rewrite to a word's
    own stem/prefix rather than a blind global character replace (e.g. "événement"'s
    word-initial é must stay put; only the second é, before the mute e syllable, changes).
    """
    rewrites: dict[str, OrthoRewriteRule] = {}
    for oldSpelling, newSpelling, _category, _appliesToLemmeNormalization, \
            appliesToOrthoRewrite, _appliesToPluralRewrite, isException, _note \
            in _readReform1990Rows(tsvPath):
        if appliesToOrthoRewrite != "True" or isException == "True":
            continue
        rule = computeSingleEditRule(oldSpelling, newSpelling)
        rewrites[oldSpelling] = rule
        # Only a same-length substitution is safe to also key under newSpelling: its
        # occurrence check (ortho[position] == oldChar) naturally fails once the text
        # already reads newChar there, so re-matching an already-reformed word is a
        # harmless no-op. An insertion/deletion rule has no such guard -- e.g. deleting
        # one letter of a double ("grolle"->"grole") leaves a single letter that still
        # matches the same anchor, and re-running the rule against the *already*
        # single-lettered "grole" deletes again, producing "groe". Keying those only
        # under oldSpelling is enough: the word.lemme fallback lookup in
        # outputMixedLexique still finds this rule whenever word.ortho itself is the
        # one that actually still needs rewriting.
        if rule.oldChar != "" and rule.newChar != "":
            rewrites[newSpelling] = rule
    return rewrites


def orthoRewriteOccurrence(ortho: str, rule: OrthoRewriteRule) -> int | None:
    """
    Return which occurrence (1-based) of the rule's anchor character in `ortho` is the
    one this rule targets, or None if `ortho` doesn't belong to this rule's word family.

    For a substitution/deletion, the anchor is rule.oldChar itself (the character being
    replaced/removed) -- occurrence is which instance of it in `ortho` sits at
    rule.position, checked via an exact prefix + character match (wrong stem, or the
    character at that position doesn't already match, both return None -- e.g. an
    unrelated word that merely shares a lemme string).

    For an insertion (rule.oldChar == ""), there's no character to match at `position`
    (nothing is there yet in the old spelling) -- instead anchor on the last character of
    rule.oldPrefix (stable across a word family's inflected forms) and count its
    occurrences up to and including `position`, so applyOrthoRewrite can find the same
    spot to insert after. A rule with an empty oldPrefix inserts at the very start
    (occurrence 0 is the sentinel for "before the first character").
    """
    if rule.oldChar == "":
        if ortho[:rule.position] != rule.oldPrefix:
            return None
        if not rule.oldPrefix:
            return 0
        return ortho[:rule.position].count(rule.oldPrefix[-1])
    if len(ortho) <= rule.position or ortho[:rule.position] != rule.oldPrefix \
            or ortho[rule.position] != rule.oldChar:
        return None
    return ortho[:rule.position + 1].count(rule.oldChar)


def applyOrthoRewrite(text: str, rule: OrthoRewriteRule, occurrence: int) -> str:
    """
    Apply rule's old->new edit to the `occurrence`-th targeted spot in `text`.
    `occurrence` is computed once from the word's own `ortho` (orthoRewriteOccurrence)
    and reused for both the flat ortho string and the syllable-separated orthosyll_cv
    string, since separators never reorder the underlying letters.

    For a deletion (rule.newChar == ""), also drops one adjacent syllable separator
    ("_"/"|") if present, so orthosyll_cv doesn't end up with a dangling empty
    letter-slot between two separators (e.g. "ll__er" instead of "ll_er"). `ortho` itself
    never contains a separator, so this is a no-op there beyond the plain deletion.

    For an insertion (rule.oldChar == ""), inserts rule.newChar directly adjacent to the
    occurrence-th instance of rule.oldPrefix's last character, with no separator in
    between -- this naturally produces a doubled-letter token like "rr" in orthosyll_cv
    (matching the same digraph convention a deletion collapses in reverse, e.g. category
    8's "ll"/"tt"), rather than a separately-separated letter-slot.
    """
    chars = list(text)
    if rule.oldChar == "":
        if not rule.oldPrefix:
            chars.insert(0, rule.newChar)
            return "".join(chars)
        anchor = rule.oldPrefix[-1]
        count = 0
        for i, c in enumerate(chars):
            if c == anchor:
                count += 1
                if count == occurrence:
                    chars.insert(i + 1, rule.newChar)
                    return "".join(chars)
        return text
    count = 0
    targetIndex = None
    for i, c in enumerate(chars):
        if c == rule.oldChar:
            count += 1
            if count == occurrence:
                targetIndex = i
                break
    if targetIndex is None:
        return text
    if rule.newChar:
        chars[targetIndex] = rule.newChar
        return "".join(chars)
    del chars[targetIndex]
    if targetIndex < len(chars) and chars[targetIndex] in "_|":
        del chars[targetIndex]
    elif targetIndex > 0 and chars[targetIndex - 1] in "_|":
        del chars[targetIndex - 1]
    return "".join(chars)


_reform1990OrthoRewrites: dict[str, OrthoRewriteRule] = (
    loadReform1990OrthoRewrites("resources/reform1990.tsv") if APPLY_1990_REFORM_ORTHO else {}
)


# Off by default, and independent of the other three reform flags: category 3's
# "mots empruntés" plural-regularization (e.g. "des barmen" -> "des barmans"). Unlike
# the diacritic categories above, this is a literal whole-plural swap, not a single
# fixed-position character edit -- it never touches the singular row, and the reform1990.tsv
# oldSpelling/newSpelling here ARE the full irregular/regularized plural spellings (not a
# lemme). See resources/reform1990.tsv's "mots_empruntes_pluriel" rows and
# scratch/reform1990/STATUS.md for sourcing (only pairs where Lexique383 already attests
# BOTH the sourced regular plural and some other, differing plural spelling under the
# same lemme are included -- that differing spelling is the row this rewrites).
APPLY_1990_REFORM_EMPRUNT_PLURIEL: bool = True


def loadReform1990PluralRewrites(tsvPath: str) -> dict[str, str]:
    """
    Parse resources/reform1990.tsv into an {oldPlural: newPlural} dict, keeping only
    rows where appliesToPluralRewrite is true and isException is false.
    """
    pluralRewrites: dict[str, str] = {}
    for oldSpelling, newSpelling, _category, _appliesToLemmeNormalization, \
            _appliesToOrthoRewrite, appliesToPluralRewrite, isException, _note \
            in _readReform1990Rows(tsvPath):
        if appliesToPluralRewrite == "True" and isException == "False":
            pluralRewrites[oldSpelling] = newSpelling
    return pluralRewrites


def rewriteOrthosyllSuffix(orthosyllCv: str, oldOrtho: str, newOrtho: str) -> str:
    """
    Rewrite orthosyllCv's trailing letters to match newOrtho, given that oldOrtho and
    newOrtho share a common prefix (e.g. "barmen"/"barmans" share "barm") and differ only
    in their suffix. Finds the syllable-string index right after the shared prefix's last
    letter (counting only letters, so separators "_"/"|" and multi-letter graphemes like
    "ch" are handled transparently -- iterating characters one at a time naturally counts
    both letters of a digraph token), keeps everything up to there, and appends the new
    suffix's letters directly (no separator), the same trailing-digraph convention already
    used by applyOrthoRewrite's insertion case. Verified letter-by-letter against real
    corpus rows for barmen->barmans, brunches->brunchs, curricula->curriculums, and
    scénarii->scénarios (see scratch/reform1990/STATUS.md).
    """
    prefixLen = 0
    for o, n in zip(oldOrtho, newOrtho):
        if o != n:
            break
        prefixLen += 1
    newSuffix = newOrtho[prefixLen:]
    letterCount = 0
    cutIndex = len(orthosyllCv)
    for i, ch in enumerate(orthosyllCv):
        if ch in "_|":
            continue
        letterCount += 1
        if letterCount == prefixLen:
            cutIndex = i + 1
            break
    return orthosyllCv[:cutIndex] + newSuffix


_reform1990PluralRewrites: dict[str, str] = (
    loadReform1990PluralRewrites("resources/reform1990.tsv")
    if APPLY_1990_REFORM_EMPRUNT_PLURIEL else {}
)


# 1990-reform rule 5 (-eler/-eter verbs): regularizes the doubled-consonant conjugation
# convention (e.g. "amoncelle") to the single-consonant + grave-accent convention ("amoncèle").
# This is a pure spelling-convention change, NOT a phonology change -- both spellings encode the
# same open-e sound, confirmed by the official report's own wording ("L'emploi du e accent grave
# pour noter le son `e ouvert`... est étendu à tous les verbes de ce type") -- so only
# ortho/orthosyll_cv need rewriting, same as the other two reform mechanisms above.
#
# Exception list verified against the OFFICIAL Journal officiel report (fetched 2026-09-16 from
# academie-francaise.fr/sites/academie-francaise.fr/files/rectifications.pdf), not just the
# secondary Wiktionnaire annex used earlier this session -- this caught a real discrepancy: the
# annex's summary table lists "appeler, rappeler, interpeler" as exceptions, but the official
# report's own rule text says only "On ne fait exception que pour appeler (et rappeler) et jeter
# (et les verbes de sa famille)" -- interpeler is NOT named, so it regularizes like any other
# -eler verb (interpelle -> interpèle). "Jeter's family" isn't enumerated in the report either;
# taken here as jeter plus every Verbiste-j:eter-tagged verb whose infinitive literally ends in
# "-jeter" (déjeter, forjeter, interjeter, introjeter, projeter, rejeter, surjeter) -- the
# etymologically natural reading, all sharing the "jet-" radical via prefixation.
APPELER_EXCEPTIONS = frozenset({"appeler", "rappeler"})
JETER_FAMILY_EXCEPTIONS = frozenset({
    "jeter", "déjeter", "forjeter", "interjeter", "introjeter", "projeter", "rejeter", "surjeter",
})

# nounLemme -> verbLemme, for the "-ment" nouns/adverbs the reform's rule-5 text explicitly says
# follow their verb's regularization ("Les noms en -ement dérivés de ces verbes suivront la même
# orthographe: amoncèlement, bossèlement, ..."). The report names 18; only the 9 below are
# actually attested in Lexique383 under their doubled-consonant lemme -- the rest either aren't
# in the corpus at all, or (martèlement) the corpus already only has the reformed spelling as its
# lemme, so there's nothing to rewrite.
ELER_ETER_DERIVED_NOUN_VERBS: dict[str, str] = {
    "amoncellement": "amonceler",
    "bossellement": "bosseler",
    "cliquettement": "cliqueter",
    "ensorcellement": "ensorceler",
    "étincellement": "étinceler",
    "grommellement": "grommeler",
    "morcellement": "morceler",
    "nivellement": "niveler",
    "ruissellement": "ruisseler",
}

APPLY_1990_REFORM_ELER_ETER: bool = True


def loadElerEterQualifyingVerbs(verbisteXmlPath: str) -> dict[str, str]:
    """
    Return {lemme: targetConsonant} for every -eler/-eter verb Verbiste classifies under the
    doubled-consonant template (app:eler or j:eter), excluding the reform's named exceptions.
    """
    qualifying: dict[str, str] = {}
    root = ET.parse(verbisteXmlPath).getroot()
    for verbElement in root.findall("v"):
        infinitiveElement = verbElement.find("i")
        templateElement = verbElement.find("t")
        if infinitiveElement is None or templateElement is None:
            continue
        lemme, template = infinitiveElement.text, templateElement.text
        if not lemme or not template:
            continue
        if template == "app:eler" and lemme not in APPELER_EXCEPTIONS:
            qualifying[lemme] = "l"
        elif template == "j:eter" and lemme not in JETER_FAMILY_EXCEPTIONS:
            qualifying[lemme] = "t"
    return qualifying


def elerEterRadicalParts(verbLemme: str, consonant: str) -> tuple[str, str]:
    """Return (stem, doubledPrefix) for `verbLemme` -- stem is the radical with its own
    trailing consonant dropped (e.g. "amonceler" -> "amonce"), doubledPrefix is what the
    doubled-consonant conjugated forms start with (e.g. "amoncell")."""
    radical = verbLemme[:-2]  # strip infinitive "-er"
    stem = radical[:-1]       # drop the radical's own trailing consonant
    return stem, stem + consonant * 2


def regularizeElerEterOrtho(ortho: str, verbLemme: str, consonant: str) -> str | None:
    """
    Rewrite `ortho` from the doubled-consonant -eler/-eter convention to the grave-accent
    convention if it matches that pattern for `verbLemme`'s radical (e.g. "amoncelle" with
    verbLemme="amonceler", consonant="l" -> "amoncèle"); returns None if `ortho` doesn't carry
    the doubled form (infinitive, imparfait, participles, etc. are already unaffected -- the
    doubling only ever shows up in the "e ouvert" stressed slots).
    """
    stem, doubledPrefix = elerEterRadicalParts(verbLemme, consonant)
    if not ortho.startswith(doubledPrefix):
        return None
    newPrefix = stem[:-1] + "è" + consonant
    return newPrefix + ortho[len(doubledPrefix):]


def regularizeElerEterOrthosyll(orthosyllCv: str, consonant: str) -> str:
    """
    Apply the same rewrite to the syllable-separated orthosyll_cv string. The doubled consonant
    is its own letter-unit there (e.g. "...c_e_ll_e...", one "ll" token, not two "l" letters),
    and can straddle a syllable boundary ("_" or "|" separator) depending on the conjugated
    form's syllabification (e.g. "...c_e|ll_e|r_aient..." for "amoncelleraient") -- match
    boundary-agnostically rather than assuming a fixed separator.
    """
    pattern = re.compile("e([_|])" + re.escape(consonant * 2))
    return pattern.sub(lambda m: "è" + m.group(1) + consonant, orthosyllCv, count=1)


_elerEterQualifyingVerbs: dict[str, str] = (
    loadElerEterQualifyingVerbs("resources/verbiste/verbs-fr.xml")
    if APPLY_1990_REFORM_ELER_ETER else {}
)


# interpeller/interpeler is a one-off, NOT covered by the general -eler mechanism above.
# Verbiste's own template tags reflect the traditional infinitive spelling ("interpeller",
# double-l) matching neither app:eler (single-l infinitive) nor any other verb this project's
# category-8 mechanism handles, so it never qualifies via loadElerEterQualifyingVerbs() at all.
# More importantly, Lexique383's actual "interpeller" rows show the double consonant in EVERY
# form -- infinitive, imparfait, participles, passé simple -- not just the "e ouvert" stressed
# slots the way every other -eler verb (regular or appeler/jeter-exception) does; a plain
# family-wide single-edit deletion (like categories 9/10/12 use) would incorrectly touch the
# stressed forms too, and the doubled-consonant->accent regularizer above would incorrectly
# also match the infinitive (which, unlike every regular -eler verb, literally starts with the
# doubled-consonant prefix). Resolved by consulting the OQLF's Banque de dépannage linguistique
# (authoritative, dedicated per-word note, fetched 2026-09-16):
# "Consonne simple après e prononcé [ə] : interpelons, interpelait (mais interpelle). Présent,
# imparfait, passé simple, subjonctif, impératif et participes aussi touchés" -- i.e. every form
# loses one 'l' EXCEPT the je/tu/il/ils présent-tense-family forms (interpelle/interpellent) and
# the futur/conditionnel forms built on that same stressed radical (interpellerai-style), which
# keep the double consonant unchanged, matching the traditional appeler/rappeler exception
# pattern rather than the regular -eler accent regularization.
APPLY_1990_REFORM_INTERPELER: bool = True

_interpelerRule = computeSingleEditRule("interpeller", "interpeler")

# The exact Lexique383 "interpeller"-lemme ortho spellings needing the single-l fix (every
# attested row except the présent/subjonctif/impératif stressed forms and futur/conditionnel
# forms, which correctly keep their double consonant and are deliberately absent from this set).
INTERPELER_FIXED_FORMS = frozenset({
    "interpeller", "interpella", "interpellai", "interpellaient", "interpellais",
    "interpellait", "interpellant", "interpellez", "interpellèrent", "interpellé",
    "interpellée", "interpellées", "interpellés",
})


# absous/absout, dissous/dissout: the masculine singular past participle of absoudre/dissoudre
# is spelled with an irregular final "s" (unlike the feminine "absoute"/"dissoute"); the reform
# corrects it to match the feminine's "t" -- confirmed minimal and unconditional by the OQLF's
# Banque de dépannage linguistique (fetched 2026-09-16): "absout, p. p. -- Du verbe absoudre" /
# "dissout, p. p. -- Du verbe dissoudre", no further note or caveat.
#
# Lexique383 also carries a SEPARATE ADJ-tagged row at the exact same spelling for each --
# "absous" ADJ (m, s, freq 0.02) alongside the VER row, and "dissous" ADJ (m, PLURAL, freq 0.27)
# alongside the VER row (singular). Gated on gram_cat=="VER" here since the generic
# lemme/ortho-keyed ortho-rewrite mechanism above can't otherwise distinguish rows sharing a
# lemme or ortho by gramCat -- and the ADJ rows are deliberately left untouched: OQLF's own
# entries only address the participle, with no plural form or ADJ-homograph caveat, so there's
# no sourced basis for guessing whether "dissous" ADJ (plural) should become "dissouts" or stay
# "dissous", or whether "absous" ADJ (the same spelling, singular) is really the same participial
# adjective as the VER row or a distinct headword -- left for future research, not guessed here.
APPLY_1990_REFORM_ABSOUS_DISSOUS: bool = True

_absousRule = computeSingleEditRule("absous", "absout")
_dissousRule = computeSingleEditRule("dissous", "dissout")


def normalizeLemme(lemme: str, gram_cat: str) -> str:
    canonical = pronounParadigmLemme.get((lemme, gram_cat))
    if canonical is not None:
        return canonical
    return spellingVariantLemme.get(lemme, lemme)

@dataclass
class Word:
    """
    Representation of a Word defined by an orthograph and a pronunciation

    ortho : str
        The word's orthograph
    phonology : str
        Collection of phonemes representing the pronunciation
    lemme : str
        Root of the word
    gram_cat : GramCat
        Grammatical category
    cgramortho : [GramCat]
        All grammatical categories of the words sharing this orthograph
    gender : str
        Gender of the noun or adjectiv
    number : str
        Number (singular or plural) of the noun or adjectiv
    info_verb : str
        Conjugaiton of the verb
    syll : str
        Syllables in phonemes as provided by the Lexique383
    cv-cv : str
        Consonant-Vowel brokendown by syllable
    orthosyll : str
        Orthograph of the syllables (some are mistaken)
    frequency : float
        Frequency of the word in the written chosen corpus
    frequencyFilm : float
        Frequency of the word in the film chosen corpus
    syll_cv : [[str]]
        Syllables in phonemes as provided by the LexicInfra and
        groupped by Lexique383 cv_cv field into list of phonems
    orthosyll_cv : [[(str, str)]
        Orthograph of the syllables as provided by the LexicInfra
        and groupped by Lexique383 cv_cv field into list of phonems' graphems
    """
    ortho: str
    phonology: str
    lemme: str
    gram_cat: str  # GramCat
    ortho_gram_cat: str  # List[GramCat]
    gender: str
    number: str
    info_verb: str
    syll: str
    cv_cv: str
    orthosyll: str
    frequency: float
    frequencyFilm: float

    def __post_init__(self) -> None:
        self.syll_cv: list[list[str]] = deepcopy([])
        self.orthosyll_cv: list[list[tuple[str, str]]] = deepcopy([])
        self.orig_syll: str = deepcopy(self.syll)
        self.orig_cv_cv: str = deepcopy(self.cv_cv)
        self.fix_x_k_s()
        self.fix_g_dZ()
        self.fix_j_dZ()
        self.fix_ch_tS()

    def fix_x_k_s(self) -> None:
        # X sound should not be broken into 2 consonnants (k-s) in 2 syllables
        if (self.isWellFormedCVSyll()
                and "x" in self.ortho and "k-s" in self.syll):
            printVerbose(self.ortho, ["fix_x_k_s"])
            pos = self.syll.index("k-s")
            self.syll = self.syll[0:pos] + "-ks" + self.syll[pos+3:]
            self.cv_cv = self.cv_cv[0:pos] + "-CC" + \
                self.cv_cv[pos+3:]  # "*C-C*" becomes "*-CC*"
            self.fix_x_k_s()  # recurse if there is more than one

    def fix_g_dZ(self) -> None:
        # adagio a-a.d-d.a-a.g-dZ.i-j.o-o a-dad-Zjo V-CVC-CYV
        if (self.isWellFormedCVSyll()
                and "g" in self.ortho and "d-Z" in self.syll):
            printVerbose(self.ortho, ["fix_g_dZ"])
            pos = self.syll.index("d-Z")
            self.syll = self.syll[0:pos] + "-dZ" + self.syll[pos+3:]
            self.cv_cv = self.cv_cv[0:pos] + "-CC" + \
                self.cv_cv[pos+3:]  # "*C-C*" becomes "*-CC*"
            self.fix_g_dZ()  # recurse if there is more than one

    def fix_j_dZ(self) -> None:
        # banjo b-b.an-@.j-dZ.o-o b@d-Zo CVC-CV
        if (self.isWellFormedCVSyll()
                and "j" in self.ortho and "d-Z" in self.syll):
            printVerbose(self.ortho, ["fix_j_dZ"])
            pos = self.syll.index("d-Z")
            self.syll = self.syll[0:pos] + "-dZ" + self.syll[pos+3:]
            self.cv_cv = self.cv_cv[0:pos] + "-CC" + \
                self.cv_cv[pos+3:]  # "*C-C*" becomes "*-CC*"
            self.fix_j_dZ()  # recurse if there is more than one

    def fix_ch_tS(self) -> None:
        # machos m-m.a-a.ch-tS.o-o.s-# mat-So mat-So CVC-CV CVC-C
        if self.isWellFormedCVSyll() and "t-S" in self.syll:
            printVerbose(self.ortho, ["fix_ch_tS"])
            pos = self.syll.index("t-S")
            self.syll = self.syll[0:pos] + "-tS" + self.syll[pos+3:]
            self.cv_cv = self.cv_cv[0:pos] + "-CC" + \
                self.cv_cv[pos+3:]  # "*C-C*" becomes "*-CC*"
            self.fix_ch_tS()  # recurse if there is more than one

    @staticmethod
    def fixLexiqueInfraGraphPhon(graphem_phonem: str) -> str:
        # Apply correction to LexiqueInfra Graphem-Phonem correspondance
        # that are represented by a differente CV-CV in Lexique
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "cc-ks", "c-k.c-s")
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "xc-ksk", "x-ks.c-k")  # exclame
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "rr-RR", "r-R.r-R")
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "oy-waj", "o-wa.y-j")
        # accastillage a-a.cc-k.a-a.s-s.t-t.ill-ij.a-a.ge-Z
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "ill-ij", "i-i.ll-j")
        # acuité a-a.c-k.ui-8i.t-t.é-e
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "ui-8i", "u-8.i-i")
        # aiguille ai-e.gu-g8.i-i.ll-j.e-#
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "gu-g8", "g-g.u-8")
        # asseye a-a.ss-s.ey-Ej.e-# a-sEj
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "ey-Ej", "e-E.y-j")
        # balayera b-b.a-a.l-l.ay-Ej.e-°.r-R.a-a (LexiqueInfraCorrespondance.tsv
        # inconsistency: the pa:yer-template family's "ay" grapheme is split into two
        # graphemes "a-E.y-j" for most conjugated forms -- e.g. this same lemma's own
        # "balayerait" already has "a-e.y-j" -- but stays merged as one "ay-Ej" pair for
        # some sibling forms of the identical futur/cnd paradigm slot (e.g.
        # "balayera"/"balayerai"/...). The merged form makes the following "e-°"
        # (schwa, the futur/cnd tense marker) collapse into the SAME syllable as the
        # vowel+glide instead of starting its own syllable the way every other word in
        # the lexicon with a glide-before-schwa environment does (confirmed: 0
        # exceptions among 164 other lemmas, e.g. accueillir "j_°" is always its own
        # syllable) -- splitting the grapheme here, matching the already-correct
        # sibling forms, lets the existing Y-slot logic below place the glide in its
        # own syllable naturally, no other code change needed.
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "ay-Ej.e-°", "a-E.y-j.e-°")
        # bienheureuse
        # b-b.i-j.en-5n.h-#.eu-2.r-R.eu-2.s-z.e-# bj5-n2-R2z CYV-CV-CVC
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "en-5n", "e-5.n-n")
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "enn-@n", "en-@.n-n")  # désennuie
        # This is not the perfect treatment, it creates ortho-syll
        # like e-nivre instead of en-ivre
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "en-@n", "e-@.n-n")  # enamourée
        # coordinateurs c-k.oo-oO.r-R.d-d.i-i.n-n.a-a.t-t.eu-9.r-R.s-#
        # ko-OR-di-na-t9R ko-OR-di-na-t9R CV-VC-CV-CV-CVC CV-VC-CV-CV-CVC
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "oo-oO", "o-o.o-O")
        # mezzos m-m.e-E.zz-dz.o-o.s-# mEd-zo mEd-zo CVC-CV CVC-C
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "zz-dz", "z-d.z-z")
        # suggère s-s.u-y.gg-gZ.è-E.r-R.e-# syg-ZER syg-ZER CVC-CVC CVC-CVC
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "gg-gZ", "g-g.g-Z")
        # ubiquiste u-y.b-b.i-i.qu-k8.i-i.s-s.t-t.e-#
        # y-bi-k8ist y-bi-k8ist V-CV-CYVCC V-CV-CYVCC
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "qu-k8", "q-k.u-8")
        # vieillie v-v.i-j.ei-e.lli-ji.e-# vje-ji vje-ji CYV-YV CYV-YV
        graphem_phonem = Word.fixAssociation(
            graphem_phonem, "lli-ji", "ll-j.i-i")
        return graphem_phonem

    @staticmethod
    def fixAssociation(graphem_phoneme: str, badAsso: str,
                       goodAsso: str) -> str:
        if badAsso in graphem_phoneme:
            pos = graphem_phoneme.index(badAsso)
            return graphem_phoneme[0:pos] + goodAsso + \
                graphem_phoneme[pos+len(badAsso):]
        return graphem_phoneme

    def phonemesToSyllables(self, withSilent:bool = True, symbol: str = "") -> list[str]:
        if withSilent:
            return [symbol.join(syll) for syll in self.syll_cv]
        else:
            return [symbol.join(syll).replace("#", "")
                    for syll in self.syll_cv]

    def lettersToSyllables(self, symbol: str = "") -> list[str]:
        return [symbol.join(map(lambda cv_lett: cv_lett[1], syll))
                for syll in self.orthosyll_cv]

    def syllablesToWord(self) ->str:
        return "".join(self.phonemesToSyllables())

    def writeOrthoSyll(self) ->str:
        # Format is "syll1letter1_syll1letter2|syll2letter1_..."
        return "|".join(self.lettersToSyllables(symbol="_"))

    def writePhonoSyll(self) ->str:
        # Format is "syll1phonem1_syll1phonem2|syll2phonem1_..."
        return "|".join(self.phonemesToSyllables(symbol="_"))

    def breakdownSyllables(self, graphem_phoneme: str) -> None:
        # Uses the CV-CV breakdown of phonemes from Lexique with the
        # grapheme-phoneme decomposition of LexiqueInfra to find
        # the graphemes parts of each syllable
        printVerbose(self.ortho, ["Breakdown"])
        if self.syll_cv != [] or self.orthosyll_cv != []:
            printVerbose(self.ortho, ["already:", self.syll_cv,
                                      self.orthosyll_cv])
            # print("Word ", self.ortho, "is already already broke down")
            # print(self.syllablesToWord())
            # print(self.syll_cv, self.orthosyll_cv)
            # print(graphem_phoneme)
            return
        syll_phon: list[str] = []
        syll_graph: list[tuple[str, str]] = []
        skip_next_Y = False
        skip_next_C = False
        # if True:
        graph_phon_pairs = []
        try:
            graphem_phoneme = Word.fixLexiqueInfraGraphPhon(graphem_phoneme)
            graph_phon_pairs = [(gp.split("-")[0], gp.split("-")[1])
                                for gp in graphem_phoneme.split(".")]
            cv_split = self.cv_cv.split("-")
            for syllNb, cv_syll in enumerate(cv_split):
                _ = syllNb == len(cv_syll) - 1
                syll_phon = []
                syll_graph = []
                for cvNb, cv_phoneme in enumerate(cv_syll):
                    printVerbose(self.ortho, [
                        syllNb, cv_syll, cvNb, cv_phoneme, "\n", "g/p:",
                        graph_phon_pairs[0][0], graph_phon_pairs[0][1],
                        "\n", "skip Y/C:", skip_next_Y, skip_next_C])
                    if cv_phoneme == "C":
                        if skip_next_C:
                            skip_next_C = False
                            continue

                        if (graph_phon_pairs[0][0] in ["ch"] and
                                graph_phon_pairs[0][1] in ["tS"]):
                            skip_next_C = True
                        elif (graph_phon_pairs[0][0] in ["x"] and
                                graph_phon_pairs[0][1] in ["ks", "gz"]):
                            # ajax  a.j.a.x a-a.j-Z.a-a.x-ks a-Zaks V-CVCC
                            skip_next_C = True
                            printVerbose(
                                self.ortho, ["x: skip_next_C ", skip_next_C])
                        elif (graph_phon_pairs[0][0] in ["g", "j"]
                              and graph_phon_pairs[0][1] == "dZ"):
                            # adagio a-a.d-d.a-a.g-dZ.i-j.o-o
                            # a-da-dZjo V-CV-CCYV after fix
                            skip_next_C = True
                        elif (graph_phon_pairs[0][0] in ["pp"]
                              and (cvNb == len(cv_syll) - 1 or
                              (cv_syll[cvNb+1] == "C"
                               and graph_phon_pairs[1][0] not in ["l", "r"]))):
                            # appropriation
                            # a-a.pp-p.r-R.o-o.p-p.r-R.i-ij.a-a.t-s.i-j.on-§
                            # a-pRo-pRi-ja-sj§ V-CCV-CCV-YV-CYV
                            skip_next_C = True

                    if cv_phoneme == "V":
                        while graph_phon_pairs[0][1] == "#":
                            printVerbose(self.ortho, ["Pop # in V"])
                            graph_phon = graph_phon_pairs.pop(0)
                            syll_phon.append(graph_phon[1])
                            syll_graph.append(("#", graph_phon[0]))
                            if len(graph_phon_pairs) == 0:
                                printVerbose(
                                    self.ortho, ["no more graph/phon"])
                                self.syll_cv.append(syll_phon)
                                self.orthosyll_cv.append(syll_graph)
                                return
                        # appropriation
                        # a-a.pp-p.r-R.o-o.p-p.r-R.i-ij.a-a.t-s.i-j.on-§
                        # a-pRo-pRi-ja-sj§ V-CCV-CCV-YV-CYV
                        # balaye b-b.a-a.l-l.ay-Ej.e-# ba-lEj CV-CVY
                        if graph_phon_pairs[0][1] in ["ij", "Ej"]:
                            skip_next_Y = True

                    if cv_phoneme == "Y":
                        while graph_phon_pairs[0][1] == "#":
                            printVerbose(self.ortho, ["Pop # in Y", graph_phon_pairs, syll_phon, syll_graph])
                            # admixtion a-a.d-d.m-m.i-i.x-ks.t-#.i-j.on-§
                            graph_phon = graph_phon_pairs.pop(0)
                            syll_phon.append(graph_phon[1])
                            syll_graph.append(("#", graph_phon[0]))
                            if len(graph_phon_pairs) == 0:
                                printVerbose(
                                    self.ortho, ["no more graph/phon"])
                                self.syll_cv.append(syll_phon)
                                self.orthosyll_cv.append(syll_graph)
                                return
                        if graph_phon_pairs[0][0] not in [
                                "i", "ll", "o", "y", "u", "ill",
                                "il", "ou", "l", "lli", "w", "ï"]:
                            printVerbose(
                                self.ortho, ["skip Y of", graph_phon_pairs[0]])
                            skip_next_Y = False
                            continue
                        if skip_next_Y:
                            skip_next_Y = False
                            # Rare english words and other exceptions
                            printVerbose(
                                self.ortho, ["skip next Y of",
                                             graph_phon_pairs[0]])
                            continue

                    if len(graph_phon_pairs) > 0:
                        graph_phon = graph_phon_pairs.pop(0)
                        if (graph_phon[1] == "Ej"
                                and cvNb <= len(cv_syll) - 2
                                and cv_syll[cvNb+1] == "C"):
                            # ace a-Ej.c-s.e-# Ejs VYC englis word
                            skip_next_Y = True
                        elif (graph_phon[1] == "ij"
                              and cvNb == len(cv_syll) - 1):
                            # atrium a-a.t-t.r-R.i-ij.u-O.m-m a-tRi-jOm
                            # V-CCV-YVC
                            skip_next_Y = True
                        # silent phonemes are not matched by a cv_phoneme
                        while graph_phon[1] == "#":
                            printVerbose(self.ortho, ["Pop # at end"])
                            syll_phon.append(graph_phon[1])
                            syll_graph.append(("#", graph_phon[0]))
                            if len(graph_phon_pairs) == 0:
                                printVerbose(
                                    self.ortho, ["no more graph/phon"])
                                self.syll_cv.append(syll_phon)
                                self.orthosyll_cv.append(syll_graph)
                                return
                            graph_phon = graph_phon_pairs.pop(0)
                        syll_graph.append((cv_phoneme, graph_phon[0]))
                        syll_phon.append(graph_phon[1])
                    printVerbose(
                        self.ortho, ["appended g/p ", syll_graph, syll_phon])
                    if len(graph_phon_pairs) == 0:
                        printVerbose(self.ortho, ["no more graph/phon"])
                        self.syll_cv.append(syll_phon)
                        self.orthosyll_cv.append(syll_graph)
                        return

                self.syll_cv.append(syll_phon)
                self.orthosyll_cv.append(syll_graph)
                # Append silent phonemes to end of previous syllable
                while (len(graph_phon_pairs) > 0
                       and graph_phon_pairs[0][1] == "#"):
                    graph_phon = graph_phon_pairs.pop(0)
                    self.syll_cv[-1].append(graph_phon[1])
                    self.orthosyll_cv[-1].append(("#", graph_phon[0]))
                if len(graph_phon_pairs) == 0:
                    printVerbose(self.ortho, ["no more graph/phon"])
                    return

            if len(graph_phon_pairs) > 0:
                print("Left-over graphem-phoneme not assigned")
                print(self.ortho, graphem_phoneme, self.syll, self.cv_cv)
                print(self.syll_cv)
                print(self.orthosyll_cv, "extra:", graph_phon_pairs)
                sys.exit(1)
        # if False:
        except Exception as e:
            print(e)
            print(self.ortho, graphem_phoneme, self.orig_syll,
                  self.syll, self.orig_cv_cv, self.cv_cv)
            print(self.syll_cv)
            print(self.orthosyll_cv)
            print(syll_phon, syll_graph, "extra:", graph_phon_pairs)
            sys.exit(1)
        return

    def isWellFormedCVSyll(self) -> bool:
        # Verify cv_cv and syll have the same form
        a = self.cv_cv.split("-")
        b = self.syll.split("-")
        return len(a) == len(b) and list(map(len, a)) == list(map(len, b))

    def isWellFormedCVOrthosyll(self) -> bool:
        # Verify cv_cv and orthosyll have generally the same form
        a = self.cv_cv.split("-")
        b = self.orthosyll.split("-")
        return len(a) == len(b)

    def isSyllConsensus(self) -> bool:
        # Verify if the phonologic syll and syll_cv match once silent phonemes
        # are removed
        if self.isWellFormedCVSyll():
            for syll, syll_cv in zip(self.syll.split("-"), self.syll_cv):
                if syll != "".join(syll_cv).replace("#", ""):
                    return False
            return True
        return False

    def isOrthoSyllConsensus(self) -> bool:
        # Verify if the orthograph of orthosyll and orthosyll_cv match
        if self.isWellFormedCVOrthosyll():
            for orthosyll, orthosyll_cv in zip(self.orthosyll.split("-"),
                                               self.orthosyll_cv):
                if orthosyll != "".join(map(lambda o: o[1], orthosyll_cv)):
                    return False
            return True
        return False


class Lexique:

    #picked = []
    words: list[Word] = []
    words_by_ortho: dict[str, list[Word]] = {}
    word_source: str = "resources/Lexique383.tsv"
    graphem_phoneme_source: str = "resources/LexiqueInfraCorrespondance.tsv"
    sylCol: SyllableCollection = SyllableCollection()

    def __init__(self) -> None:
        self.words = self.read_corpus()

    def read_corpus(self) -> list[Word]:
        with open(self.word_source) as f:
            corpus = csv.DictReader(f, delimiter='\t')

            for corpus_word in corpus:
                if (corpus_word["ortho"] is not None
                    and corpus_word["ortho"][0] != "#"
                        and corpus_word["ortho"] not in ignoredList):
                    printVerbose(corpus_word["ortho"], ["Creating word"])
                    word = Word(ortho=corpus_word["ortho"],                   # mangeait
                                phonology=corpus_word["phon"],                      # m@ZE
                                lemme=normalizeLemme(corpus_word["lemme"],
                                                      corpus_word["cgram"]),        # manger
                                # gram_cat = GramCat[corpus_word["cgram"]] if \
                                #        corpus_word["cgram"] != '' else None,
                                # ortho_gram_cat = [GramCat[gc] for gc in \
                                #        corpus_word["cgramortho"].split(",")],
                                gram_cat=corpus_word["cgram"],                      # VER
                                ortho_gram_cat=corpus_word["cgramortho"],           # VER
                                gender=corpus_word["genre"],                        # 
                                number=corpus_word["nombre"],                       # 
                                info_verb=corpus_word["infover"],                   # ind:imp:3s;
                                syll=corpus_word["syll"],                           # m@-ZE
                                cv_cv=corpus_word["cv-cv"],                         # CV-CV
                                orthosyll=corpus_word["orthosyll"],                 # man-geait
                                frequency=float(corpus_word["freqlivres"]),         # 20.14
                                frequencyFilm=float(corpus_word["freqfilms2"])      # 4.93
                                )
                    self.words.append(word)
                    same_ortho = self.words_by_ortho.get(corpus_word["ortho"],
                                                         deepcopy([])) + [word]
                    self.words_by_ortho[corpus_word["ortho"]] = same_ortho
        self.breakdownSyllables()
        return self.words

    @staticmethod
    def associationToPhonology(asso: str) -> str:
        asso_split = map(lambda s:  s.split("-"), asso.split("."))
        phono = list(map(lambda s: s[1], asso_split))
        return "".join(phono).replace("#", "")

    def breakdownSyllables(self) -> None:
        with open(self.graphem_phoneme_source) as f:
            graph_phon_asso = csv.DictReader(f, delimiter='\t')
            for asso_word in graph_phon_asso:
                printVerbose(asso_word["item"], ["BreakdownSyllables"])
                if (asso_word["item"][0] != "#"
                        and asso_word["item"] not in ignoredList):
                    corpus_words = self.words_by_ortho[asso_word["item"]]
                    foundInLexicon = False
                    for word in corpus_words:
                        printVerbose(
                            word.ortho,
                            ["corpus_words found, phono:", word.phonology,
                             asso_word["phono"], "CV", word.cv_cv])
                        if word.phonology == asso_word["phono"]:
                            foundInLexicon = True
                            word.breakdownSyllables(asso_word["assoc"])

                    if not foundInLexicon:
                        # Some words in LexiqueInfra have the wrong phology,
                        # but the association seems right. We get the phonology
                        # from the association and try a second time to find a
                        # matching word.
                        asso_word["phono"] = Lexique.associationToPhonology(
                            asso_word["assoc"])
                        for word in corpus_words:
                            if word.phonology == asso_word["phono"]:
                                foundInLexicon = True
                                word.breakdownSyllables(asso_word["assoc"])

                    if not foundInLexicon:
                        # Problem.
                        lexicalPhono = list(
                            map(lambda w: w.phonology,
                                filter(lambda w: w.ortho ==
                                       asso_word["item"], corpus_words)))
                        print("Not found in Lexique383",
                              asso_word["item"], asso_word["phono"],
                              Lexique.associationToPhonology(
                                  asso_word["assoc"]),
                              lexicalPhono)
        return

    @staticmethod
    def isVowel(char: str) -> bool:
        return char in "aeiouy2589OE§@°"

    @staticmethod
    def moveDualPhonem(syllables: list[str]) -> list[str]:
        # Move dual-phonems representation ij and gz to better compare
        # to Lexique383
        # This function is only used to compare the analysis to Lexique383.
        # Its result is currently not kept

        if (len(syllables) <= 1):
            return syllables
        ret: list[str] = []
        semivowelToMove = ""
        for i, syllOrig in enumerate(syllables):
            s = deepcopy(syllOrig)
            if semivowelToMove != "":
                s = semivowelToMove + s
                semivowelToMove = ""
            if i+1 < len(syllables):
                if s[-1] == "j":  # ['prié', ['pRi', 'je'], ['pRij', 'e']]
                    if Lexique.isVowel(syllables[i+1][0]):  # not bouilloire
                        ret.append(s[:-1])
                        semivowelToMove = "j"
                    else:
                        ret.append(s)
                elif len(s) > 2 and s[-2:] == "gz":
                    # ['exigé', ['Eg', 'zi', 'Ze'], ['Egz', 'i', 'Ze']]
                    ret.append(s[:-1])
                    semivowelToMove = "z"
                else:
                    ret.append(s)
            else:
                ret.append(s)
        return ret

    def printTopWordsFilm(self, nb=500) -> None:
        print("Somme\t%f" % sum(map(lambda w: w.frequencyFilm, self.words)))
        for w in self.words[:nb]:
            print("%s\t%f" % (w.ortho, w.frequencyFilm))

    def printTopWordsBooks(self, nb=500) -> None:
        print("Somme\t%f" % sum(map(lambda w: w.frequency, self.words)))
        for w in self.words[:nb]:
            print("%s\t%f" % (w.ortho, w.frequency))

    def printSyllabificationStats(self) -> None:
        self.mismatchSyllableSpelling: list[Word] = []
        self.mismatchSyllableAssociation = []
        self.matchSyllableAssociation = []
        self.words.sort(key=lambda x: x.frequencyFilm, reverse=True)
        for word in self.words:
            syllable_names = word.syll.split("-")
            spellings = word.orthosyll.split("-")
            if len(syllable_names) != len(spellings):
                self.mismatchSyllableSpelling.append(word)
            if len(syllable_names) == len(word.phonemesToSyllables()):
                # if syllable_names != word.phonemesToSyllables(False) :
                if syllable_names != Lexique.moveDualPhonem(
                        word.phonemesToSyllables(False)):
                    self.mismatchSyllableAssociation.append(
                        [word, syllable_names, Lexique.moveDualPhonem(
                            word.phonemesToSyllables(False)),
                         word.lettersToSyllables()])
                else:
                    self.matchSyllableAssociation.append(
                        [word, syllable_names,
                         word.phonemesToSyllables()])

            else:
                for (syllable_name, spelling) in zip(syllable_names,
                                                     spellings):
                    _ = self.sylCol.updateSyllable(
                        syllable_name, spelling, word.frequency)

        Syllable.printTopPhonemes(5)
        self.sylCol.printTopSyllables(5)
        print("Nb Mismatched syll/orthosyll",
              len(self.mismatchSyllableSpelling))
        for m in self.mismatchSyllableSpelling:
            printVerbose(m.ortho, ["syll/orthosyll not matching", m])

        print("Nb Mismatched syll/infrasyll",
              len(self.mismatchSyllableAssociation))
        for m in self.mismatchSyllableAssociation:
            printVerbose(m[0].ortho, ["syll/infrasyll not matching"])

        print("Nb Matched syll/infrasyll", len(self.matchSyllableAssociation))
        for m in self.matchSyllableAssociation:
            printVerbose(m[0].ortho, ["syll/infrasyll matching"])

        brokenDown = list(filter(lambda w: w.orthosyll_cv != [], self.words))
        print("Nb broken down", len(brokenDown))
        for m in brokenDown:
            printVerbose(m.ortho, ["broken down", m])

        missing = [w.ortho for w in filter(
            lambda w: w.orthosyll_cv == [], self.words)]
        for m in missing:
            printVerbose(m, ["orthosyll_cv is missing"])
        print("Nb missing", len(missing))
        print("\n".join(map(str, self.mismatchSyllableAssociation)))

    @staticmethod
    def stripSubjonctifImparfait(infoVerb: str) -> str | None:
        """
        Strip any "sub:imp:*" (subjonctif imparfait) tags from an infover string,
        returning None if that was the word's ONLY reading -- the caller should then
        drop the row entirely. Declared out of scope for the theory 2026-09-21 (see
        ROADMAP.md): src/elicitation.py already excluded this combination from ever
        getting a discriminator (2026-09-19, archaic/literary tense, not worth a
        keypress), which just left it silently colliding with whatever else shared
        its stroke (e.g. "suffît" onto "suffi") instead of actually being unreachable.
        Removing it from the corpus makes that explicit: the tense is no longer part
        of the typable theory at all, rather than present-but-permanently-colliding.
        A verb's other, in-scope readings sharing the same row (e.g. "sub:imp:1s;
        sub:pre:3s;") are kept -- only the sub:imp tag itself is dropped.
        """
        if not infoVerb:
            return infoVerb
        kept = [tag for tag in infoVerb.split(";") if tag and not tag.startswith("sub:imp")]
        return ";".join(kept) + ";" if kept else None

    def outputMixedLexique(self, filename: str) -> None:
        with open(filename, "w") as f:
            fieldnames = ["ortho", "phon", "lemme", "cgram", "cgramortho",
                          "genre", "nombre", "infover", "syll_cv",
                          "orthosyll_cv", "freqlivres", "freqfilms2"]

            corpus = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
            corpus.writeheader()

            for word in sorted(self.words, key=lambda w: w.ortho):
                if word.orthosyll_cv != []:
                    infoVerbOut = self.stripSubjonctifImparfait(word.info_verb)
                    if infoVerbOut is None:
                        continue
                    printVerbose(word.ortho, ["Writing to", filename])
                    orthoOut = word.ortho
                    orthosyllOut = word.writeOrthoSyll()
                    # Lookup by lemme covers regular words (nouns/verbs whose inflected
                    # forms all share the affected spelling as their lemme, e.g.
                    # "dessoûler"). It misses irregular participles like "mû", whose sole
                    # corpus row has lemme="mouvoir" -- fall back to an exact ortho match
                    # (safe: dict-key equality, not a prefix/substring test, so it can't
                    # over-match an unrelated word like "mûr" that merely shares a prefix).
                    rule = _reform1990OrthoRewrites.get(word.lemme) \
                        or _reform1990OrthoRewrites.get(word.ortho)
                    if rule is not None:
                        occurrence = orthoRewriteOccurrence(word.ortho, rule)
                        if occurrence is not None:
                            orthoOut = applyOrthoRewrite(word.ortho, rule, occurrence)
                            orthosyllOut = applyOrthoRewrite(orthosyllOut, rule, occurrence)
                    # -eler/-eter verbs and their -ment-derived nouns (word.lemme may be either,
                    # see ELER_ETER_DERIVED_NOUN_VERBS) -- independent of the rule above, since
                    # it's a different sub-mechanism (a doubled-consonant->accent transform, not
                    # a fixed-position character swap).
                    verbLemme = word.lemme if word.lemme in _elerEterQualifyingVerbs \
                        else ELER_ETER_DERIVED_NOUN_VERBS.get(word.lemme)
                    if verbLemme is not None and verbLemme in _elerEterQualifyingVerbs:
                        consonant = _elerEterQualifyingVerbs[verbLemme]
                        rewrittenOrtho = regularizeElerEterOrtho(orthoOut, verbLemme, consonant)
                        if rewrittenOrtho is not None:
                            orthoOut = rewrittenOrtho
                            orthosyllOut = regularizeElerEterOrthosyll(orthosyllOut, consonant)
                    # Category 3 loanword plural regularization (e.g. barmen -> barmans) --
                    # a literal whole-plural swap, restricted to number=="p" rows, keyed by
                    # the word's own original ortho (never its lemme, since that's the
                    # singular).
                    if word.number == "p":
                        newPlural = _reform1990PluralRewrites.get(word.ortho)
                        if newPlural is not None:
                            orthosyllOut = rewriteOrthosyllSuffix(orthosyllOut, word.ortho, newPlural)
                            orthoOut = newPlural
                    # interpeller/interpeler: one-off per-form fix, see INTERPELER_FIXED_FORMS.
                    # Checked against both spellings since APPLY_1990_REFORM_LEMMES (if also on)
                    # already normalizes word.lemme from "interpeller" to "interpeler" at
                    # word-construction time, before this output step ever runs.
                    if APPLY_1990_REFORM_INTERPELER and word.lemme in ("interpeller", "interpeler") \
                            and word.ortho in INTERPELER_FIXED_FORMS:
                        occurrence = orthoRewriteOccurrence(word.ortho, _interpelerRule)
                        if occurrence is not None:
                            orthoOut = applyOrthoRewrite(orthoOut, _interpelerRule, occurrence)
                            orthosyllOut = applyOrthoRewrite(orthosyllOut, _interpelerRule, occurrence)
                    # absous/absout, dissous/dissout: gated on gram_cat=="VER" so the separate
                    # ADJ-tagged homograph rows (see comment above APPLY_1990_REFORM_ABSOUS_DISSOUS)
                    # are deliberately left untouched.
                    if APPLY_1990_REFORM_ABSOUS_DISSOUS and word.gram_cat == "VER" \
                            and word.ortho in ("absous", "dissous"):
                        rule = _absousRule if word.ortho == "absous" else _dissousRule
                        occurrence = orthoRewriteOccurrence(word.ortho, rule)
                        if occurrence is not None:
                            orthoOut = applyOrthoRewrite(orthoOut, rule, occurrence)
                            orthosyllOut = applyOrthoRewrite(orthosyllOut, rule, occurrence)
                    corpus.writerow({
                        "ortho": orthoOut,
                        "phon": word.phonology,
                        "lemme": word.lemme,
                        "cgram": word.gram_cat,
                        "cgramortho": word.ortho_gram_cat,
                        "genre": word.gender,
                        "nombre": word.number,
                        "infover": infoVerbOut,
                        "syll_cv": word.writePhonoSyll(),
                        "orthosyll_cv": orthosyllOut,
                        "freqlivres": word.frequency,
                        "freqfilms2": word.frequencyFilm
                    })


lexique = Lexique()
lexique.printSyllabificationStats()
lexique.outputMixedLexique("resources/LexiqueMixte.tsv")
