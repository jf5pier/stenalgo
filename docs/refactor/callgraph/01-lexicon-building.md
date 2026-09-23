# Lexicon Building (S1)

## Overview

```
S1.1  Load lexicon exclusions            — loadLexiconExclusions (lexique.py:38), bound at :56
S1.2  Load 1990-reform lemma table       — loadReform1990Lemmes (lexique.py:117), applied at :131-132
S1.3  Load 1990-reform ortho rules       — loadReform1990OrthoRewrites (lexique.py:196), bound at :312
S1.4  Load 1990-reform plural rewrites   — loadReform1990PluralRewrites (lexique.py:329), bound at :374
S1.5  Load -eler/-eter qualifying verbs  — loadElerEterQualifyingVerbs (lexique.py:423), bound at :481
S1.6  Build one-off reform rules         — computeSingleEditRule (lexique.py:156), at :507, :536-537
S1.7  Read and filter Lexique383         — Lexique.__init__ (lexique.py:963) → read_corpus (:966)
  S1.7.1  Normalize lemma                — normalizeLemme (lexique.py:540)
  S1.7.2  Repair affricate/cluster syllabification — lexique.Word.__post_init__ (lexique.py:598)
  S1.7.3  Attach grapheme-phoneme breakdowns — Lexique.breakdownSyllables (lexique.py:1007)
    S1.7.3.1  Correct LexiqueInfra associations — Word.fixLexiqueInfraGraphPhon (lexique.py:652)
    S1.7.3.2  Align associations onto syllables — lexique.Word.breakdownSyllables (lexique.py:750)
S1.8  Syllabification stats (and row reorder) — printSyllabificationStats (lexique.py:1097)
S1.9  Write the mixed lexicon            — outputMixedLexique (lexique.py:1174)
  S1.9.1  Drop breakdown orphans         — inline (lexique.py:1184)
  S1.9.2  Strip subjonctif imparfait     — stripSubjonctifImparfait (lexique.py:1155)
  S1.9.3  Apply reform ortho rewrite     — orthoRewriteOccurrence (:229) / applyOrthoRewrite (:259), at :1197-1203
  S1.9.4  Regularize -eler/-eter         — regularizeElerEterOrtho (:454) / regularizeElerEterOrthosyll (:469), at :1208-1215
  S1.9.5  Regularize loanword plurals    — rewriteOrthosyllSuffix (lexique.py:343), at :1220-1224
  S1.9.6  interpeller → interpeler       — inline (lexique.py:1229-1234)
  S1.9.7  absous/dissous → absout/dissout — inline (lexique.py:1238-1244)

Synthetic Paradigm Completion (S1b)  (separate, manual, --apply scripts)
S1b.1 Verb paradigm completion           — util/completeVerbParadigms.py main (:350)
  S1b.1.1 Load theory 1                  — loadTheoryAndKeyboard (completeVerbParadigms.py:91)
  S1b.1.2 Derive conjugation ending tables — deriveConjugationEndingTables (src/verbparadigm.py:493)
  S1b.1.3 Find structural candidates     — findStructuralCandidates (completeVerbParadigms.py:165)
    S1b.1.3.1 Detect undersampled lemmas — detectUndersampledLemmas (src/verbparadigm.py:681)
    S1b.1.3.2 Generate missing participles — generateMissingParticiple (src/verbparadigm.py:367)
    S1b.1.3.3 Generate missing finite forms — generateMissingConjugatedForm (src/verbparadigm.py:577)
  S1b.1.4 Confirm by legacy discriminator collision — confirmCandidates (completeVerbParadigms.py:266)
  S1b.1.5 Append synthetic rows          — writeSynthetic (completeVerbParadigms.py:324), call at :402
S1b.2 NOM/ADJ gap generation             — util/generateMissingNomAdjForms.py main (:99)
  S1b.2.1 Derive NOM/ADJ ending tables   — deriveNomAdjEndingTables (src/nomAdjParadigm.py:250)
  S1b.2.2 Enumerate missing slots        — missingSlots (src/nomAdjParadigm.py:132) + isSuspectedInvariableForm (:166)
  S1b.2.3 Exception-table override       — overrideCandidate (generateMissingNomAdjForms.py:77)
  S1b.2.4 Morphalou-authoritative form   — generateAuthoritativeForm (src/nomAdjParadigm.py:522) → generateMissingForm (:309)
S1b.3 Dual-form gap fillers              — fixPayerDualFormGaps.py main (:113), fixAsseoirDualFormGaps.py main (:103), fixAsseoirDualFormGapsManual.py main (:204)
S1b.4 In-place synthetic repair          — util/fixEvaserWordFinalZSyllabification.py main (:109)
S1b.5 Consumption                        — Dictionary.readCorpus (dictionary.py:92) over wordSources (:66-69)
```

Lexicon Building (S1) turns the **source lexicons** into the **mixed lexicon**. It reads
`resources/Lexique383.tsv` (142,669 rows) and drops 145 excluded rows plus 17 `#`-prefixed
rows. It fixes lemmas at read time and attaches a syllable breakdown to each row from
`resources/LexiqueInfraCorrespondance.tsv` (137,822 rows). At write time it drops the
4,852 rows that got no breakdown and the 1,199 rows whose only reading was subjonctif
imparfait. It also rewrites spellings to the 1990 reform. The result is
`resources/LexiqueMixte.tsv`: 136,456 data rows, 12 columns. The stage exists because
Stenalgo needs every word's phonemes grouped into syllables, split into
onset/nucleus/coda, with the letters of each syllable attached. Lexique383 alone gives
unreliable orthographic syllables; LexiqueInfra gives the grapheme-phoneme alignment.
A separate manual side branch, Synthetic Paradigm Completion (S1b), appends generated
forms to `resources/LexiqueSynthetic.tsv` (42,225 rows). Phonetic Theory Building (S2)
reads that file after the mixed lexicon.

**Verification done for this document.** The module body minus its last three lines
(lexique.py:1-1260) was executed in memory, and `outputMixedLexique` wrote to the
scratchpad instead of `resources/`. The regenerated file is **byte-identical** to the
committed `resources/LexiqueMixte.tsv`. Every row count on this page comes from that run
or from read-only reads of the TSVs.

## Calls

### Load lexicon exclusions — loadLexiconExclusions (S1.1)   lexique.py:38
Called by: module import (lexique.py:56, `ignoredList = frozenset(...)`)
Input state: `resources/lexiconExclusions.tsv`: `#` comments, a header row, then
`word<TAB>reason<TAB>note` rows. 134 entries: 99 `foreign_word`, 19 `unpopular_spelling`,
14 `data_defect`, 2 `unsupported_phoneme`.
Transformation: parses the file into `{word: reason}`. Only the keys are kept, as the
frozenset `ignoredList`. The reason is documentation only.
Result: `ignoredList` (134 exact-match `ortho` strings). In Read and Filter Lexique383
(S1.7) it drops 145 Lexique383 rows; in Attach Grapheme-Phoneme Breakdowns (S1.7.3) it
skips 144 LexiqueInfra rows.
Artifacts: reads `resources/lexiconExclusions.tsv`.
Notes: one entry (`schampooiner`) matches no Lexique383 row, so it is stale. This list is
separate from `excluded_words.txt` (applied in Phonetic Theory Building (S2),
dictionary.py:102) and from `resources/ambiguityIgnoreList.tsv` (collision metric only).

### Load 1990-reform lemma table — loadReform1990Lemmes (S1.2)   lexique.py:117
Called by: module import, lexique.py:131-132 (gated by `APPLY_1990_REFORM_LEMMES = True`, :95)
Input state: `resources/reform1990.tsv` read by `_readReform1990Rows` (:98), padded to 8
columns: `oldSpelling newSpelling category appliesToLemmeNormalization
appliesToOrthoRewrite appliesToPluralRewrite isException note`. The file has 10
categories: 91 `autres_rectifications`, 65 `mots_empruntes_accent`, 40 `olle_otter`,
35 `mots_empruntes_pluriel`, 11 `circonflexe`, 11 `trema`, 9 `illier_illiere`, 6
`accent_grave`, 1 `numeraux_composes`, 1 `participe_passe_laisser`.
Transformation: keeps rows with `appliesToLemmeNormalization == "True"` and
`isException == "False"` as `{old: new}`. These are merged into `spellingVariantLemme`
(:71), which is seeded with `{"ile": "île"}`.
Result: `spellingVariantLemme` with 56 entries.
Artifacts: reads `resources/reform1990.tsv`.

### Load 1990-reform ortho rules — loadReform1990OrthoRewrites (S1.3)   lexique.py:196
Called by: module import, lexique.py:312-314 (gated by `APPLY_1990_REFORM_ORTHO = True`, :145)
Input state: the same reform rows.
Transformation: for each `appliesToOrthoRewrite == "True"` row that is not an exception,
`computeSingleEditRule` (:156) turns old/new into one `OrthoRewriteRule` (position,
old prefix, old char, new char). The rule is a substitution, a deletion or an insertion.
If the two spellings differ by more than one edit, the whole module import raises.
Every rule is keyed under `oldSpelling`. **Only substitution rules** are also keyed
under `newSpelling` (:224-225). The comment at :214-223 explains why: re-running a
deletion rule on an already-reformed word would delete again (`grole` → `groe`).
Result: `_reform1990OrthoRewrites`, 237 keys.
Artifacts: reads `resources/reform1990.tsv`.
Notes: the lemma lookup at Apply Reform Ortho Rewrite (S1.9.3) interacts badly with
Load 1990-Reform Lemma Table (S1.2) for deletion and insertion rules. See Suspected bugs #1.

### Load 1990-reform plural rewrites — loadReform1990PluralRewrites (S1.4)   lexique.py:329
Called by: module import, lexique.py:374-377 (`APPLY_1990_REFORM_EMPRUNT_PLURIEL = True`, :326)
Input state: reform rows.
Transformation: keeps `appliesToPluralRewrite == "True"` and non-exception rows as
`{oldPlural: newPlural}`. These are whole-word plural swaps, not lemmas.
Result: `_reform1990PluralRewrites`, 33 entries (for example `barmen→barmans`,
`curricula→curriculums`, `lieder→lieds`).
Artifacts: reads `resources/reform1990.tsv`.

### Load -eler/-eter qualifying verbs — loadElerEterQualifyingVerbs (S1.5)   lexique.py:423
Called by: module import, lexique.py:481-484 (`APPLY_1990_REFORM_ELER_ETER = True`, :420)
Input state: `resources/verbiste/verbs-fr.xml` (the `<v><i>infinitive</i><t>template</t>` entries).
Transformation: every verb with template `app:eler` becomes `{lemme: "l"}`, and every
verb with `j:eter` becomes `{lemme: "t"}`. The reform's named exceptions are left out:
`APPELER_EXCEPTIONS` (:397, appeler/rappeler) and `JETER_FAMILY_EXCEPTIONS` (:398, jeter
plus 7 `-jeter` compounds).
Result: `_elerEterQualifyingVerbs`, 124 verbs. The companion table
`ELER_ETER_DERIVED_NOUN_VERBS` (:408) maps 9 `-ellement`/`-ettement` nouns to their verb.
Artifacts: reads `resources/verbiste/verbs-fr.xml`. Several fix scripts also patch this
file (`fixMatirVerbTemplate`, `split*VerbisteTemplate`), but none of them touches the
`app:eler`/`j:eter` templates.

### Build one-off reform rules — computeSingleEditRule (S1.6)   lexique.py:156
Called by: module import at :507 (`_interpelerRule`, `interpeller→interpeler`) and
:536-537 (`_absousRule`, `_dissousRule`).
Input state: hard-coded spelling pairs.
Transformation: same single-edit rule derivation as in Load 1990-Reform Ortho Rules
(S1.3). `INTERPELER_FIXED_FORMS` (:512) lists the 13 attested forms that lose an `l`.
The stressed présent forms and the futur/conditionnel forms are left out of that list
on purpose (OQLF source cited at :498-504).
Result: three rules, used by the interpeller one-off (S1.9.6) and the absous/dissous
one-off (S1.9.7).

### Read and filter Lexique383 — read_corpus (S1.7)   lexique.py:966
Called by: `Lexique.__init__` (lexique.py:963), from the module body `lexique = Lexique()` (:1261)
Input state: **source lexicons**: `Lexique383.tsv` (142,669 rows, 35 columns).
Transformation: for each row, it skips the row if `ortho` starts with `#` (17 rows, such
as `#etc.` and `#p.m.`) or if `ortho` is in `ignoredList` (145 rows). Otherwise it builds
a `lexique.Word` with ortho, phon, the **normalized** lemma (S1.7.1), cgram, cgramortho,
genre, nombre, infover, syll, cv-cv, orthosyll, `freqlivres` and `freqfilms2`. It
appends the Word to `self.words` and to `words_by_ortho[ortho]`. Then it calls Attach
Grapheme-Phoneme Breakdowns (S1.7.3).
Result: **raw lexicon rows**: 142,507 `lexique.Word`. Of these, 137,655 carry a
`syll_cv`/`orthosyll_cv` breakdown and 4,852 are breakdown orphans.
Artifacts: reads `resources/Lexique383.tsv`.
Helpers not expanded: `printVerbose` (:34, debug print for the 6 words in `verboseList` :32).
Notes: `words` and `words_by_ortho` are **class-level** mutable attributes
(lexique.py:957-958), and `read_corpus` appends to them in place. See Suspected bugs #6.
Frequency columns are copied verbatim. No lemma frequency and no other Lexique383
column survives.

### Normalize lemma — normalizeLemme (S1.7.1)   lexique.py:540
Called by: Read and Filter Lexique383 (S1.7), lexique.py:977
Input state: a raw `(lemme, cgram)` pair.
Transformation: first it looks up `pronounParadigmLemme` (:81), keyed by (lemme, cgram):
`ils→il`, `elles→elle` (PRO:per), and `celle/celles/ceux→celui` (PRO:dem). This puts the
pronoun forms under one LemmeGramCat, so Same-Lemma Disambiguation (S3) handles them
instead of Lemma-Homophone Marking (S4). Otherwise it looks up `spellingVariantLemme`
(`ile→île` plus the 55 reform lemmas), keyed by lemma only.
Result: 5 rows get a pronoun lemma and 149 rows get a reform or variant lemma.
Notes: the lemma is changed **before** the output-time ortho rewrite looks rules up by
lemma. That ordering causes Suspected bugs #1.

### Repair affricate/cluster syllabification — lexique.Word.__post_init__ (S1.7.2)   lexique.py:598
Called by: `lexique.Word(...)` construction in Read and Filter Lexique383 (S1.7)
Input state: one row's Lexique383 `syll` (phonemic syllables joined by `-`) and `cv-cv`
(C/V/Y skeleton).
Transformation: it saves `orig_syll`/`orig_cv_cv`. Then, only while `syll` and `cv_cv`
have the same shape (`isWellFormedCVSyll` :921), it moves syllable boundaries so that one
grapheme's two-consonant sound stays in one onset:
`fix_x_k_s` (:608, `k-s`→`-ks` when the ortho has `x`), `fix_g_dZ` (:619, `d-Z`→`-dZ`
with `g`), `fix_j_dZ` (:630, with `j`) and `fix_ch_tS` (:641, `t-S`→`-tS`, with no
ortho condition). Each fix recurses until nothing is left to change.
Result: `cv_cv` is rewritten on 2,344 rows. `cv_cv` is what the breakdown (S1.7.3.2)
walks. `syll` itself is not written out.

### Attach grapheme-phoneme breakdowns — Lexique.breakdownSyllables (S1.7.3)   lexique.py:1007
Called by: Read and Filter Lexique383 (S1.7), lexique.py:998
Input state: raw lexicon rows, none broken down yet, plus `LexiqueInfraCorrespondance.tsv`
(`item phono cgram grapheme assoc regTo_GP`; `assoc` is `grapheme-phoneme` pairs joined
by `.`, with `#` for silent letters).
Transformation: for each Infra row that does not start with `#` and is not excluded, it
takes the Lexique383 Words with the same ortho (`words_by_ortho[item]`, which raises
`KeyError` if the ortho is missing). It breaks down every such Word whose `phonology`
equals the Infra `phono` column. **Second chance:** if none match, it rebuilds a
phonology from the `assoc` column (`associationToPhonology` :1002) and tries again. This
rescues 273 rows. If that fails too, it prints "Not found in Lexique383"; the current
data triggers this 0 times. A Word that already has a breakdown is skipped (:755),
so the first matching Infra row wins. 15,047 Infra orthos have several rows with the
same phono, one per cgram.
Result: 137,655 Words with `syll_cv: list[list[phoneme]]` and
`orthosyll_cv: list[list[(C|V|Y|#, grapheme)]]`. The rest are **breakdown orphans**:
4,852 rows, of which 4,795 contain a space, a hyphen or an apostrophe (multi-word
expressions and compounds, which LexiqueInfra does not cover). There are 3,491 NOM, 794
ADJ and 212 VER. One orphan is a real heterophone miss: `engraisser` VER `@gRese` has an
Infra item but no Infra row with that phonology.
Artifacts: reads `resources/LexiqueInfraCorrespondance.tsv`.
Notes: the match test uses Infra's `phono` column, but the breakdown is built from the
`assoc` column. Nothing checks that `assoc` agrees with Lexique383 `phon`. See
Suspected bugs #2.

### Correct LexiqueInfra associations — Word.fixLexiqueInfraGraphPhon (S1.7.3.1)   lexique.py:652
Called by: Align Associations onto Syllables (S1.7.3.2), lexique.py:770
Input state: one `assoc` string.
Transformation: 18 hard-coded first-occurrence substring substitutions (`fixAssociation`
:720). Each splits a merged grapheme-phoneme pair whose phonemes fall in different
syllables of the Lexique383 skeleton: `cc-ks`, `xc-ksk`, `rr-RR`, `oy-waj`, `ill-ij`,
`ui-8i`, `gu-g8`, `ey-Ej`, `ay-Ej.e-°` (the pa:yer futur/cnd split), `en-5n`, `enn-@n`,
`en-@n`, `oo-oO`, `zz-dz`, `gg-gZ`, `qu-k8` and `lli-ji`.
Result: an `assoc` string whose pairs line up one-to-one with the C/V/Y slots.
Notes: each rule fixes only the **first** occurrence. A word with two such clusters keeps
the second one unsplit.

### Align associations onto syllables — lexique.Word.breakdownSyllables (S1.7.3.2)   lexique.py:750
Called by: Attach Grapheme-Phoneme Breakdowns (S1.7.3), lexique.py:1023 / :1035
Input state: one Word's `cv_cv` skeleton (after S1.7.2) and its corrected `assoc`.
Transformation: it walks the skeleton syllable by syllable and slot by slot, taking
grapheme-phoneme pairs off the front of the list. Silent pairs (`#`) are attached to the
current syllable, or to the previous one at a syllable end. The rules are:
`skip_next_C` for `ch-tS`, `x-ks/gz`, `g|j-dZ` and word-final `pp`; `skip_next_Y` after
`ij`/`Ej` vowels and a few English `Ej` patterns; and Y slots are only consumed by
glide-capable graphemes (`i ll o y u ill il ou l lli w ï`). If pairs are left over, or
any exception occurs, it prints a diagnostic and calls **`sys.exit(1)`**, which aborts
the whole build (:904-918).
Result: `syll_cv`/`orthosyll_cv` for that Word. These are written out as
`syll1ph1_syll1ph2|syll2…` by `writePhonoSyll` (:746) and `writeOrthoSyll` (:742).
Helpers not expanded: `phonemesToSyllables` (:728), `lettersToSyllables` (:735).

### Syllabification stats (and row reorder) — printSyllabificationStats (S1.8)   lexique.py:1097
Called by: module body, lexique.py:1262
Input state: raw lexicon rows, broken down.
Transformation: it prints how many rows disagree between the Lexique383 `syll`/`orthosyll`
and the breakdown: 52,942 syll/orthosyll count mismatches, 306 syll/infrasyll mismatches
(compared after `moveDualPhonem` :1055) and 137,329 matches. It updates a
`SyllableCollection` and class-level `Syllable` stats that nothing reads. **Side effect:**
`self.words.sort(key=frequencyFilm, reverse=True)` (:1101).
Result: no data change. However, because `outputMixedLexique` uses a stable sort by
ortho, this sort decides the **order of rows that share an ortho** in the output: film
frequency, descending. Without it, the regenerated file has the same rows but not the
same bytes (checked).
Notes: a refactor that drops this "print-only" call changes the row order in
`LexiqueMixte.tsv`. That can change first-seen tie-breaks in Phonetic Theory Building
(S2) (`wordByIdentity`, `wordsByOrtho` order).

### Write the mixed lexicon — outputMixedLexique (S1.9)   lexique.py:1174
Called by: module body, lexique.py:1263 (`"resources/LexiqueMixte.tsv"`)
Input state: raw lexicon rows, broken down and reordered by S1.8.
Transformation: it goes through the rows sorted by **original** `ortho` (:1183). For each
row, it runs S1.9.1 to S1.9.7 in order, then writes the 12 columns: `ortho` (rewritten),
`phon` (Lexique383, unchanged), `lemme` (normalized), `cgram`, `cgramortho`, `genre`,
`nombre`, `infover` (stripped), `syll_cv`, `orthosyll_cv` (rewritten), `freqlivres` and
`freqfilms2`. The Lexique383 `syll`, `cv-cv`, `orthosyll`, lemma frequencies and
neighbourhood measures are dropped.
Result: **mixed lexicon**: 136,456 rows (142,507 − 4,852 orphans − 1,199 subjonctif
imparfait rows). Byte-identical to the committed file.
Artifacts: writes `resources/LexiqueMixte.tsv`.
Notes: `cgramortho` is not recomputed after an ortho rewrite. The file is sorted by
pre-rewrite ortho, so rewritten rows are slightly out of order (for example `acuponcture`
sits where `acupuncture` would). Rewriting can create identity duplicates with the
already-reformed spelling (24 identities, see Suspected bugs #5). One row (`borough`)
has an `orthosyll_cv` whose letters do not spell its `ortho`: an Infra `assoc` defect.

#### Drop breakdown orphans (S1.9.1)   lexique.py:1184
Called by: Write the Mixed Lexicon (S1.9)
Input state / Transformation: rows with `orthosyll_cv == []` are skipped with no message.
Result: 4,852 rows dropped, mostly multi-word expressions (`a priori`, `a fortiori`,
`abaisse-langue`, …).

#### Strip subjonctif imparfait — stripSubjonctifImparfait (S1.9.2)   lexique.py:1155
Called by: Write the Mixed Lexicon (S1.9), lexique.py:1185
Input state: one row's `infover` (for example `sub:imp:1s;sub:pre:3s;`).
Transformation: it removes every `sub:imp*` tag. It returns `None` when nothing is left,
and the caller then drops the row. An empty `infover` (non-verbs) is returned unchanged.
Result: 1,199 rows dropped (for example `suffît`), and 237 rows lose the tag but are kept.
Rationale: the tense was declared out of scope on 2026-09-21 (ROADMAP.md); before that,
these forms collided silently.

#### Apply reform ortho rewrite — orthoRewriteOccurrence / applyOrthoRewrite (S1.9.3)   lexique.py:1197-1203
Called by: Write the Mixed Lexicon (S1.9)
Input state: the row's original `ortho`, its (normalized) `lemme` and its `orthosyll_cv` string.
Transformation: `rule = rewrites.get(word.lemme) or rewrites.get(word.ortho)`.
`orthoRewriteOccurrence` (:229) checks the rule's prefix and anchor character against
the ortho and returns which occurrence of the anchor to edit, or `None`, for words that
are not in the family. `applyOrthoRewrite` (:259) applies the same occurrence edit to
`ortho` and to `orthosyll_cv`. A deletion also removes one adjacent `_`/`|` separator;
an insertion creates a digraph token (for example `rr`).
Result: 243 rows rewritten (for example `allégement→allègement`, `allô→allo`,
`asseoir→assoir`, `acupuncture→acuponcture`). 77 rows find a rule but have no occurrence;
these are harmless no-ops (for example `assied` under lemma `asseoir`).
Notes: see Suspected bugs #1. Inflected forms of 24 `-otter`/`-olle`/`-illier` lemmas
are missed (67 rows).

#### Regularize -eler/-eter — regularizeElerEterOrtho / regularizeElerEterOrthosyll (S1.9.4)   lexique.py:1208-1215
Called by: Write the Mixed Lexicon (S1.9)
Input state: `orthoOut` after S1.9.3; `word.lemme` is either a qualifying verb or one of
the 9 derived nouns.
Transformation: if `orthoOut` starts with the doubled-consonant prefix (`amoncell`), the
prefix becomes `stem[:-1] + "è" + consonant` (`amoncèl`). The orthosyll string gets the
first `e[_|]ll`→`è[_|]l` substitution. Forms without doubling (infinitive, imparfait,
participles) do not match and are left unchanged.
Result: 130 rows rewritten (for example `amoncelle→amoncèle`, `attellera→attèlera`,
`becquette→becquète`, `nivellement→nivèlement`).

#### Regularize loanword plurals — rewriteOrthosyllSuffix (S1.9.5)   lexique.py:1220-1224
Called by: Write the Mixed Lexicon (S1.9)
Input state: rows with `nombre == "p"` whose **original** ortho is a key in
`_reform1990PluralRewrites`.
Transformation: `ortho` becomes the new plural. `rewriteOrthosyllSuffix` (:343) keeps the
orthosyll string up to the letters shared by the two plurals and adds the new suffix
without a separator.
Result: 33 rows (`barmen→barmans`, `ferries→ferrys`, `errata→erratums`, …).

#### interpeller → interpeler (S1.9.6)   lexique.py:1229-1234
Called by: Write the Mixed Lexicon (S1.9)
Transformation: for lemma `interpeller`/`interpeler` and ortho in
`INTERPELER_FIXED_FORMS`, it applies `_interpelerRule` (one `l` deleted).
Result: 13 rows.

#### absous/dissous → absout/dissout (S1.9.7)   lexique.py:1238-1244
Called by: Write the Mixed Lexicon (S1.9)
Transformation: only for `gram_cat == "VER"`. The ADJ homographs are deliberately left alone (:525-533).
Result: 2 rows.

---

## Synthetic Paradigm Completion (S1b)

None of these scripts runs in a rebuild. Each is a dry-run by default and appends to
`resources/LexiqueSynthetic.tsv` only with `--apply`. `lexique.py` never reads or writes
that file. The file has 42,225 rows: 35,928 VER, 3,896 NOM and 2,401 ADJ. It uses the
mixed-lexicon columns plus `source` (always `synthetic`), and all frequencies are 0.0.
It contains no exact duplicate rows and no `sub:imp` rows. The `sub:imp` rows were
removed in commit fd7e242 by an edit that no script records. 6,759 synthetic rows have
the same identity as a mixed-lexicon row, so Consumption (S1b.5) only merges their
`infover` into that Word. 31,252 rows become new Words.

### Verb paradigm completion — completeVerbParadigms.main (S1b.1)   util/completeVerbParadigms.py:350
Called by: a person, `python -m util.completeVerbParadigms [--apply]`
Input state: theory 1 (so the mixed lexicon **plus the current synthetic rows**), the
Verbiste XML files and `resources/verbModelExceptions.tsv`.
Transformation: it caps its own address space at 4 GiB (`_capMemory` :343). It loads the
templates (`loadVerbisteTemplates` verbparadigm.py:48, `loadVerbModelExceptions` :67,
`parseConjugationTemplates` :190). It runs the **legacy** feature extractor
`extractDiscriminatingFeatures` (src/featureextractor.py:31), then S1b.1.2 to S1b.1.5.
Result: VER synthetic rows (participle gender/number forms and finite forms).
Artifacts: reads `FirstTheory.pickle`, `starboard3h.json`, `resources/verbiste/*.xml`,
`resources/verbModelExceptions.tsv`; appends to `resources/LexiqueSynthetic.tsv`.
Notes: the whole script's gating relies on the superseded discriminator design
(Legacy path, CLAUDE.md item 7). Its docstring (:27-31, :405) says the file is "not yet
wired"; it is wired (S1b.5).

#### Load theory 1 — loadTheoryAndKeyboard (S1b.1.1)   util/completeVerbParadigms.py:91
Transformation: unpickles `FirstTheory.pickle` if it exists. Otherwise it builds a
`Dictionary` and runs `analyseSyllabification`, `optimizeBiphonemeOrder` and
`buildTheory`, but writes nothing.
Result: theory 1. A stale pickle means that rows appended since the last rebuild do not
count as attested. See Suspected bugs #7.

#### Derive conjugation ending tables — deriveConjugationEndingTables (S1b.1.2)   src/verbparadigm.py:493
Called by: Verb Paradigm Completion (S1b.1), :373
Input state: every VER Word of theory 1 that has a trusted template (`getTrustedTemplate`
:88: Verbiste, or an exception row with status `regular`/`family_template`) and an
attested infinitive (`attestedInfinitiveWordByLemme` :433 requires `ortho == lemme`).
Transformation: for each template and each field (`phonology`, `rawSyllCV`,
`rawOrthosyllCV`), the infinitive suffix is the longest common suffix of all donor
infinitives. For every attested finite tag (3-part `mood:tense:pn`), the candidate ending
is the slot value minus a radical as long as the infinitive radical (:561). The table
keeps the most common ending per slot and records its match rate and donor count.
Words that carry an `inf` tag are skipped.
Result: `ConjugationEndingTables` (:467).
Notes: the radical is cut by **character count on the raw `|`/`_` string**, so the
infinitive's syllable boundary before the stem-final consonant is carried into every
generated form. See Suspected bugs #4.

#### Find structural candidates — findStructuralCandidates (S1b.1.3)   util/completeVerbParadigms.py:165
Called by: Verb Paradigm Completion (S1b.1), :375
Input state: legacy `strokeLemmeDiscriminators`, theory 1, templates and ending tables.
Transformation: for each undersampled lemma (S1b.1.3.1) it fills every missing
participle gender/number slot (S1b.1.3.2), using one attested participle as the
phonology donor. It then fills every missing finite slot of `allFiniteSlots` (:407,
which leaves out `inf`, `par:pre`, `par:pas` and `sub:imp`, `FINITE_SLOT_EXCLUDED_CODES`
:397) with S1b.1.3.3, gated by `MIN_FINITE_MATCH_RATE = 1.0` (:73). Attested slots come
from `attestedParticipleFormsByLemme` (:112) and `attestedFiniteFormsByLemme` (:130,
which ignores rows tagged `inf`).
Result: `(lemmeGramCat, info, generated Word, reference Word)` candidates plus skip reasons.

##### Detect undersampled lemmas — detectUndersampledLemmas (S1b.1.3.1)   src/verbparadigm.py:681
Transformation: groups VER LemmeGramCats by trusted template. A lemma is flagged when its
own legacy feature space (`fullFeatureSpace` :119, the union of discriminating features
over its homophone groups) is a strict subset of the union of its siblings' spaces.
Lemmas with no siblings are skipped.
Result: `dict[LemmeGramCat, UndersampledLemma]`.

##### Generate missing participles — generateMissingParticiple (S1b.1.3.2)   src/verbparadigm.py:367
Transformation: ortho comes from the Verbiste `par:pas` ending (`infinitiveRadical` :239,
`generateOrthoForm` :252). Phon and `syll_cv` are copied from the donor participle
(`spliceParticiplePhon` :296). `orthosyll_cv` is the donor radical plus `""/s/e/es`
(`generateParticipeOrthosyll` :344). `infover = "par:pas;"`, frequency 0.
Result: one VER Word.

##### Generate missing finite forms — generateMissingConjugatedForm (S1b.1.3.3)   src/verbparadigm.py:577
Transformation: ortho is the Verbiste radical plus the ending. Each phonological field is
the infinitive value truncated by the template's infinitive-suffix length, plus the
table's ending (:611). It returns `None` below the minimum match rate or when the slot
is missing.
Result: one VER Word with `infover = "code:pn;"`, or `None`.

#### Confirm by legacy discriminator collision — confirmCandidates (S1b.1.4)   util/completeVerbParadigms.py:266
Transformation: temporarily appends every candidate to its reference word's theory-1
group (`temporarilyAugmented` :238). It reruns `extractDiscriminatingFeatures` and
`buildDiscriminatorSelection` (featureextractor.py:284), and keeps only candidates whose
LemmeGramCat is in `newlyCollidingLemmas` (verbparadigm.py:646), meaning it takes part
in a new cross-lemma **feature-set** collision.
Result: the confirmed candidates. All others are skipped as "irrelevant to disambiguation today".

#### Append synthetic rows — writeSynthetic (S1b.1.5)   util/completeVerbParadigms.py:324
Transformation: appends one TSV line per confirmed candidate (writing the header if the
file is new). It does not deduplicate against the file.
Artifacts: appends to `resources/LexiqueSynthetic.tsv`.

### NOM/ADJ gap generation — generateMissingNomAdjForms.main (S1b.2)   util/generateMissingNomAdjForms.py:99
Called by: a person, `python -m util.generateMissingNomAdjForms [--apply] [--morphalou PATH | --no-morphalou]`
Input state: mixed lexicon plus synthetic lexicon rows, read by `loadWords`
(nomAdjParadigm.py:415), which drops `excluded_words.txt` entries. Also
`resources/nomAdjModelExceptions.tsv` (`loadNomAdjModelExceptions` :76) and, optionally,
`morphalou/Morphalou3.1_CSV.csv` (`loadMorphalouIndex` :477). That file is **untracked**:
on a fresh clone the script warns and uses only the donor table.
Transformation: for each NOM/ADJ LemmeGramCat (`attestedSlots` :100) and each missing
slot, it picks a source slot (`chooseSourceSlot` :566). It skips the slot for an
`invariable` exception or a suspected invariable form (S1b.2.2). Otherwise it uses the
exception override (S1b.2.3) or the authoritative form (S1b.2.4). A candidate is skipped
when its ortho already exists for that lemma in either TSV, excluded rows included
(`loadAllOrthosByLemme` :392).
Result: about 6.3k NOM/ADJ synthetic rows today (all NOM+ADJ rows in the file).
Artifacts: appends to `resources/LexiqueSynthetic.tsv` (:191).
Notes: the nomAdjParadigm.py module docstring (:28-30) says the cross-lemma collision
check is reused here. `generateMissingNomAdjForms.py` runs no collision check at all.

#### Derive NOM/ADJ ending tables — deriveNomAdjEndingTables (S1b.2.1)   src/nomAdjParadigm.py:250
Transformation: for every lemma with at least 2 attested slots and every ordered slot
pair, it derives the per-field (fromSuffix, toSuffix) after the common prefix. Results
are grouped by gramCat and by the 3-, 2- and 1-letter ortho ending class
(`orthoClassKeys` :227). It keeps the most common entry per key, with its match rate and
donor count.
Result: `NomAdjEndingTables` (:236).

#### Enumerate missing slots — missingSlots / isSuspectedInvariableForm (S1b.2.2)   src/nomAdjParadigm.py:132 / :166
Transformation: a NOM is expected to have `s`/`p` for each attested gender, and an ADJ
all four slots. A slot is treated as invariable (so no row is generated) when the number
changes and the ortho ends in `s`/`z`, when a NOM singular ends in `x`, when an ADJ ends
in `x`, or when the gender changes and the ADJ ends in one of
`ADJ_INVARIANT_GENDER_SUFFIXES` (:159).

#### Exception-table override — overrideCandidate (S1b.2.3)   util/generateMissingNomAdjForms.py:77
Transformation: for an `irregular` exception row, ortho comes from `override_ortho`
(`;`-joined per slot) and phon from `override_phonology`. If `override_phonology` is
blank, the source word's phon is used as a placeholder (:88). **`syll_cv` and
`orthosyll_cv` are always copied from the source word** (:94).
Result: one Word, or `None`. See Suspected bugs #3.

#### Morphalou-authoritative form — generateAuthoritativeForm (S1b.2.4)   src/nomAdjParadigm.py:522
Transformation: `generateMissingForm` (:309) tries the class keys from most to least
specific. It needs a match rate of 1.0 and at least `MIN_DONOR_COUNT_BY_CLASS_KEY_LENGTH`
(:306) donors ({3:1, 2:2, 1:4}), and a cross-axis ADJ goes through a same-gender detour.
Morphalou then confirms the ortho (`morphalou`), replaces it (`morphalou_override`,
:562, keeping the donor's phon, `syll_cv` and `orthosyll_cv`), or leaves it unverified
(`donor_table`).
Result: `(Word | None, source)`.

### Dual-form gap fillers (S1b.3)
- `util/fixPayerDualFormGaps.py` main :113: adds the missing `i`/`y` counterpart forms for
  the pa:yer family (`balaie`/`balaye`). It uses a per-(slot, form type) ending table
  learned from donors (match rate 1.0). Reads the mixed lexicon, the synthetic lexicon and
  Verbiste; appends synthetic rows.
- `util/fixAsseoirDualFormGaps.py` main :103: the same method, generalized to the 2- and
  3-way alternations of ass:eoir (`ié`/`eye`/`oi`). Appends synthetic rows.
- `util/fixAsseoirDualFormGapsManual.py` main :204: 26 hand-derived rows
  (`NEW_SYNTHETIC_ROWS`, appended; `(ortho, lemme)` dedup at :173), plus
  `TAG_ONLY_FIXES` written into **`Lexique383.tsv`** (:142-163). The header (:34-43) records
  that an earlier version patched `LexiqueMixte.tsv` directly and the fix was lost on the
  next `python lexique.py`.

### In-place synthetic repair — fixEvaserWordFinalZSyllabification.main (S1b.4)   util/fixEvaserWordFinalZSyllabification.py:109
Transformation: rewrites `syll_cv`/`orthosyll_cv` of the `évaser` rows with phon `evaz`
so that the word-final `z` becomes a coda (`|z_#` → `_z_#`). This is the only script
that edits synthetic rows in place.
Notes: the defect it fixes is systemic, not specific to `évaser`. See Suspected bugs #4.

### Consumption — Dictionary.readCorpus (S1b.5)   dictionary.py:92
Called by: `Dictionary.__init__` (dictionary.py:76), in Phonetic Theory Building (S2)
Input state: `wordSources = [LexiqueMixte.tsv, LexiqueSynthetic.tsv]` (dictionary.py:66-69), read in that order.
Transformation: the `source` column is ignored. A synthetic row whose identity
(`ortho, phon, lemme, cgram, gender, number`, :130) is already loaded only adds its
`infover` through `Word.mergeInfoVerb` (word.py:129). Its `syll_cv`, `orthosyll_cv` and
frequencies are discarded (:132-137). Any other row becomes a new Word, and its strokes
come from `syll_cv` (`parsePhonoSyll` word.py:365).
Result: the Word list. This is the **only pipeline consumer**. Other readers are
generators and validators: `fix*DualFormGaps`, `generateMissingNomAdjForms`,
`validateLexiconAgainstNomAdjParadigms`, `crossCheckNomAdjWithMorphalou`.

---

## One-shot lexicon fix scripts

These are historical patches, run by hand with `--apply`. The Mixte column says whether
the script writes `resources/LexiqueMixte.tsv` directly. "Source too" says whether the
same correction was also made where `lexique.py` would regenerate it: Lexique383, Infra,
Verbiste, or code in lexique.py.

**Finding:** regenerating the mixed lexicon from the current sources and the current
`lexique.py` gives a file **byte-identical** to the committed one. So **no fix is
currently held only in LexiqueMixte.tsv**, and a `python lexique.py` rerun today loses
nothing. Three Mixte patches were order-dependent: their source half was completed by a
later companion script (marked †). Before those companions ran, a rerun would have lost
them.

| Script | Files patched | Mixte? | Source too? | Purpose |
|---|---|---|---|---|
| fixAbregerFutureAccent | conjugations-fr.xml | no | n/a | abr:éger futur/cnd `è`→`é` endings |
| fixAdvenirRenaitreGaps | conjugations-fr.xml | no | n/a | adv:enir 3p présent; ren:aître participles |
| fixAsseoirDualFormGaps | Synthetic (append) | no | n/a | ass:eoir alternant rows (S1b.3) |
| fixAsseoirDualFormGapsManual | Lexique383 (tags), Synthetic (append) | no | yes | 26 hand rows + missing tags |
| fixAyGraphemeEjQuality | Lexique383, Mixte (`phon`,`syll_cv`) | yes | yes† (Infra via fixAyGraphemeInfraPhono) | `ay` is always open `Ej` |
| fixAyGraphemeInfraPhono | Infra (`phono`,`assoc`) | no | yes | same rule in Infra, so a regen keeps it |
| fixCeSchwa | Lexique383, Infra, Mixte | yes | yes | `ce` /s2/ → /s°/ |
| fixCroitreMouvoirAccents | conjugations-fr.xml, Lexique383, Mixte | yes | yes | croître/mouvoir circumflex forms |
| fixDeleteWeatherVerbErrors | Lexique383, Mixte (row delete) | yes | yes | drop impossible 1st/2nd-person weather-verb rows |
| fixDuplicateInfTag | Lexique383, Mixte | yes | yes | `inf;;inf;;` → `inf;` |
| fixEstOuverteVoyelle | Lexique383, Infra, Mixte | yes | yes | `est` (être) /e/ → /E/ |
| fixEvaserWordFinalZSyllabification | Synthetic (in place) | no | n/a | évaser word-final z coda (S1b.4) |
| fixFoutreDefectiveTenses | conjugations-fr.xml | no | n/a | foutre passé simple / sub:imp slots |
| fixGniezInfraPhono | Infra (`phono`) | no | yes | completes fixGniezPronunciation (17 orphaned rows) |
| fixGniezPronunciation | Lexique383, Infra (`assoc`), Mixte | yes | yes† (Infra `phono` via fixGniezInfraPhono) | `-gniez` keeps its /j/ |
| fixGrelerFigurativePlural | conjugations-fr.xml | no | n/a | grêl:er 3p slots |
| fixInfPlusOtherTag | Lexique383, Mixte | yes | yes | strip spurious tag next to `inf` |
| fixLeguerEquerHarcelerAccent | conjugations-fr.xml | no | n/a | l:éguer/diss:équer/harc:eler futur/cnd endings |
| fixMarinDateCorruption | Infra | no | yes | `Mar-05` → `maR5` (Excel) |
| fixMatirVerbTemplate | verbs-fr.xml | no | n/a | matir → fin:ir template |
| fixMultiTagPartialMismatch | Lexique383, Mixte | yes | yes | drop tags that do not match the ortho |
| fixOuirConditionnelOrder | conjugations-fr.xml | no | n/a | reorder o:uïr cnd alternatives |
| fixParticipeAdjNomVowelQuality | Lexique383, Mixte | yes | yes | ADJ/NOM homograph takes the VER row's E/e |
| fixParticipeMissingNombre | Lexique383, Mixte | yes | yes | blank `nombre` → `s` on m participles |
| fixParticipePlusOtherTag | Lexique383, Mixte | yes | yes | strip spurious tag next to `par:pas` |
| fixPayerAyGrapheme | Infra (`assoc`), Mixte | yes | yes | split `ay-Ej` in 3 pa:yer infinitives |
| fixPayerDualFormGaps | Synthetic (append) | no | n/a | pa:yer i/y counterparts (S1b.3) |
| fixPayerNonfuturVowelQuality | Lexique383, Mixte | yes | yes† (Infra via fixAyGraphemeInfraPhono) | pa:yer présent vowel = E |
| fixResidualConjugationTemplates | conjugations-fr.xml | no | n/a | dép:ecer etc. primary alternative |
| fixResidualRowErrors | Lexique383, Mixte | yes | yes | 4 row fixes (for example `lamer` → `inf;`) |
| fixSourdreDefectiveGaps | conjugations-fr.xml, Lexique383, Mixte | yes | yes | sourdre slots; delete `sourds` VER |
| fixSpuriousDuplicateVerbRows | Lexique383, Mixte (row delete) | yes | yes | drop duplicate VER/AUX rows under the wrong lemma |
| fixXlfnSingleCorruption | Infra | no | yes | `_xlfn.SINGLE(...)` phono (Excel) |
| completeVerbParadigms | Synthetic (append) | no | n/a | S1b.1 |
| generateMissingNomAdjForms | Synthetic (append) | no | n/a | S1b.2 |
| splitEtudierVerbisteTemplate / splitAnglicismErVerbisteTemplate | verbs-fr.xml, conjugations-fr.xml | no | n/a | split aim:er into étudi:er / squatt:er for the ending tables |
| change_ai-E_to_ai-e_endings.sh / change_eCe_to_ECe_words.sh | write `*_modified`/`*_racine` copies of Lexique383/Infra | no | (manual copy-back) | early bulk phonology edits |
| copyLineFromTo.py | `<file>.out` | no | n/a | generic key/value column substitution helper |

A Mixte patch that a later `python lexique.py` would lose is still possible in two ways.
First, any future script that patches Mixte without its source. Second, a script that
patches Mixte by matching the **pre-reform** ortho, which differs from the ortho in Mixte
after S1.9.3 to S1.9.5. LEXICON_RECOMPUTE_PIPELINE.md:56-58 still advises patching Mixte
directly "rather than re-running lexique.py wholesale, to avoid unrelated full-file
regen diffs". There are none today, so a full rerun is now the safer check.

## New glossary terms
- **Breakdown (syllable breakdown)** — The pair `syll_cv` (phonemes) / `orthosyll_cv`
  (graphemes), syllables joined by `|` and slots by `_`, with `#` for silent phonemes.
  Built by aligning a LexiqueInfra association onto the Lexique383 C/V/Y skeleton.
  *`lexique.Word.breakdownSyllables` lexique.py:750.* Phonetic Theory Building (S2) reads
  strokes from `syll_cv` alone.
- **Association (grapheme-phoneme association, `assoc`)** — The LexiqueInfra column of
  `grapheme-phoneme` pairs, joined by `.`. *LexiqueInfraCorrespondance.tsv; `fixLexiqueInfraGraphPhon` lexique.py:652.*
- **Breakdown orphan** — A Lexique383 row with no LexiqueInfra association whose phonology
  matches. It is silently dropped from the mixed lexicon. *lexique.py:1184.* 4,852 today.
- **Lexicon exclusion** — An ortho dropped in Lexicon Building (S1)
  (`resources/lexiconExclusions.tsv`). Distinct from `excluded_words.txt`, which drops a
  word in Phonetic Theory Building (S2), and from `ambiguityIgnoreList.tsv`, which only
  affects the collision metric. Avoid calling all three "the exclusion list".
- **Reform rewrite** — Any output-time change to the 1990-reform spelling: reform ortho
  rewrite (single-edit rule, S1.9.3), -eler/-eter regularization (S1.9.4), loanword
  plural rewrite (S1.9.5) and the two one-offs. It changes only `ortho`/`orthosyll_cv`,
  never `phon`. Distinct from **reform lemma normalization** (S1.7.1), which changes `lemme`.
- **Pronoun paradigm lemma** — The `pronounParadigmLemme` fold (`ils→il`, `ceux→celui`, …). *lexique.py:81.*
- **Synthetic row** — A generated lexicon row in `LexiqueSynthetic.tsv` (`source=synthetic`,
  frequency 0). *completeVerbParadigms.py:324; generateMissingNomAdjForms.py:62.*
- **Donor / ending table** — The attested words of a template (verbs) or an ortho ending
  class (NOM/ADJ). Their shared suffix transformation is learned by mode, together with a
  match rate and donor count, and spliced onto a gap. *`deriveConjugationEndingTables`
  verbparadigm.py:493; `deriveNomAdjEndingTables` nomAdjParadigm.py:250.*
- **Undersampled lemma** — A VER LemmeGramCat whose legacy discriminating-feature space
  is a strict subset of its template siblings'. *`detectUndersampledLemmas` verbparadigm.py:681.*
- **Fix script** — A one-shot `util/fix*.py` patch (dry run by default, `--apply` writes).
  Preferred over "fixer".

## Suspected bugs
1. lexique.py:224-225 with :1197-1198 — reform deletion/insertion rules are keyed only
   under `oldSpelling`, but when the same `reform1990.tsv` row also sets
   `appliesToLemmeNormalization`, `word.lemme` has already become `newSpelling`
   (normalizeLemme :540). The lemma lookup misses, and only the row whose ortho equals
   the old lemma spelling is rewritten. Scenario: lemma `ballotter→balloter`. The mixed
   lexicon has `balloter` (rewritten infinitive) next to `ballottait`, `ballottés`,
   `ballotte`, and `dégoter` next to `dégottera`. That is 67 rows over 24 lemmas
   (balloter, cachotier, corole, fumerole, greloter, joailler, quincailler, ognon, …).
   The comment at :220-223 says this case is covered. Confidence: high (in-memory regen).
2. lexique.py:1021/:1033 with :770-883 — a breakdown is attached when Infra's `phono`
   column matches the Lexique383 `phon`, but `syll_cv` is built from the `assoc` column,
   which can disagree. Scenario: `embêter` `phon=@bEte`, Infra `assoc` `ê-e` →
   `syll_cv=@|b_e|t_e`. Theory 1 then types a closed `e`, and `capharnaüm` loses its
   final `Om` (`ü-#.m-#`). 132 mixed-lexicon rows have `syll_cv` phonemes ≠ `phon`, and
   175 VER synthetic rows inherit the same mismatch through the ending tables. Confidence:
   high (data), impact medium.
3. util/generateMissingNomAdjForms.py:88/:94 — `overrideCandidate` takes ortho and phon
   from the exception table but copies `syll_cv`/`orthosyll_cv` from the source word.
   Scenario: `molle`/`molles` (lemma `mou`, ADJ f) get `phon=mOl`, `syll_cv=m_u`, so theory 1
   types them like `mou`. `vieux` (lemma `vieil`, m/p) keeps `vieil`'s placeholder `vjEj`.
   Of the 12 NOM/ADJ synthetic rows with `syll_cv` ≠ `phon`, `molle(s)` come from this
   bug; the rest inherit Suspected bugs #2 from their source row. A related case,
   `morphalou_override` (nomAdjParadigm.py:562), keeps the donor `orthosyll_cv` after
   replacing the ortho: 52 rows whose `orthosyll_cv` does not spell the ortho (`bijoux`
   `b_i|j_ou`, `touareg` `t_a_r|gu_i`). Low impact, because strokes come from `syll_cv`.
   Confidence: high.
4. src/verbparadigm.py:561/:611 — radicals are cut by character count on the raw
   breakdown string, so the infinitive's syllable boundary before the stem-final consonant
   survives into word-final forms. The result is a vowel-less trailing syllable: the
   bug fixEvaserWordFinalZSyllabification patched for `évaser` alone. Scenario: synthetic
   `cannes` (canner, sub:pre:2s) `k_a|n_#` → theory 1 `((2,12),(6,8))`, 2 strokes, while
   NOM `cannes` is `((2,12,22),)`. Same for `vitamines`, `discrimines`, `fritte`, … That
   is 10,539 synthetic rows over 3,628 lemmas; **3,843 of them become new Words** (the
   rest merge into mixed-lexicon identities, which drops their bad `syll_cv`). They get an
   extra stroke and miss real homophones. Confidence: high (checked in `FirstTheory.pickle`).
5. lexique.py:1197-1244 with dictionary.py:132-137 — a reform rewrite can turn an
   old-spelling row into the identity of an already-attested new-spelling row (24
   identities: `gélinotte`, `allègement`, `acuponcture`, `dessouler`, `brunchs`, …).
   `readCorpus` keeps the first row's frequencies and discards the second's instead of
   adding them, so the merged word's frequency is undercounted. That feeds frequency
   ranking downstream (the Lemma-Homophone Marking (S4) ratio exemption, the Plover
   most-frequent pick). Confidence: medium.
6. lexique.py:957-958 — `Lexique.words`/`words_by_ortho` are class attributes mutated in
   place by `read_corpus`. A second `Lexique()` in the same process would double every
   row and break breakdown matching. Not triggered: one instance per run and no
   importers. Confidence: high, likelihood low.
7. util/completeVerbParadigms.py:95-97 with :324-340 — idempotency relies on
   `FirstTheory.pickle` including earlier synthetic rows, and `writeSynthetic` does not
   deduplicate against the file. Scenario: `--apply` twice without deleting the pickles →
   the same candidates are appended again. The duplicates then merge by identity in
   Phonetic Theory Building (S2), so the only damage is a larger file. Confidence: medium.

## Dead-code observations
- `Lexique.printTopWordsFilm`/`printTopWordsBooks` (lexique.py:1087-1095),
  `lexique.Word.isSyllConsensus`/`isOrthoSyllConsensus` (:933-951): defined, never called.
- lexique.py:775 `_ = syllNb == len(cv_syll) - 1`: a no-op expression.
- `printSyllabificationStats` (:1097) statistics (`sylCol`, `Syllable` class state,
  `moveDualPhonem` :1055) are never read. Only its sort side effect matters (S1.8), so it
  is not removable as-is.
- `verboseList`/`printVerbose` (:32-36): debug tracing for 6 hard-coded words.
- `lexiconExclusions.tsv` entry `schampooiner`: matches no Lexique383 row.
- The completeVerbParadigms.py gating (`confirmCandidates`, `detectUndersampledLemmas`,
  `newlyCollidingLemmas`) depends on the legacy `extractDiscriminatingFeatures`/
  `buildDiscriminatorSelection` path. If that path is retired, this generator has to be
  re-gated or retired too.

## Doc drift
- lexique.py:89-94, :135-145, :317 say the reform flags are "Off by default" / "opt-in"
  ("Flip to True locally"). All five `APPLY_1990_REFORM_*` flags are `True` (:95, :145,
  :326, :420, :505, :534).
- lexique.py:220-223 says the lemma fallback lookup finds deletion rules "whenever
  word.ortho itself … still needs rewriting". It does not once the lemma is normalized
  (Suspected bugs #1).
- LEXICON_RECOMPUTE_PIPELINE.md:22 lists only Lexique383 and Infra as `lexique.py`
  inputs. It also reads `lexiconExclusions.tsv`, `reform1990.tsv` and `verbs-fr.xml`.
  :23 says paradigm completion reads `Lexique383.tsv`. It reads `FirstTheory.pickle`
  (mixed lexicon plus synthetic lexicon rows), Verbiste and `verbModelExceptions.tsv`;
  `generateMissingNomAdjForms` also reads Morphalou and `nomAdjModelExceptions.tsv`.
- LEXICON_RECOMPUTE_PIPELINE.md:56-58 advises patching `LexiqueMixte.tsv` directly to
  avoid "unrelated full-file regen diffs". A regen is byte-identical today.
- util/completeVerbParadigms.py:27-31, :405; util/fixPayerDualFormGaps.py:38-41;
  util/fixAsseoirDualFormGaps.py:34: "LexiqueSynthetic.tsv is not yet wired". It is
  read by dictionary.py:66-69.
- src/nomAdjParadigm.py:28-30 says `newlyCollidingLemmas` is reused as the NOM/ADJ
  collision safety check. `generateMissingNomAdjForms.py` runs no collision check.
- 00-skeleton.md §1 step 0 and the stage brief mention `resources/reform1990*.tsv`. Only
  `resources/reform1990.tsv` exists.
- README.md:72 and CLAUDE.md say LexiqueInfra "provides associations for 137k of the 142k
  words" and the lexicon has "136k French words". Both are right as row counts (137,822
  Infra rows; 136,456 output rows). Note that the mixed lexicon is *rows*, not distinct
  words.
