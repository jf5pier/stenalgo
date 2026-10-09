# Generating a complete Synthetic lexicon: situation, work done, challenges left

Status of 2026-10-08. Branch work on making `resources/LexiqueSynthetic.tsv` (stage S2) fully regenerable and as complete as
possible. Companion files: `TODO.md` (the working list, with the measurements), `COMMIT_NOTES_synthetic_regeneration.md` (what to
commit), `docs/PIPELINE.md` section "Synthetic Lexicon Building (S2)" (the reference).

## 1. Why this work

`LexiqueSynthetic.tsv` holds the forms Lexique383 does not list but that a typist needs: the missing verb tenses, the missing
plurals and feminines of nouns and adjectives. It was append-only and had been edited by hand-run `util/fix*.py` scripts, so it
was not a function of the committed inputs. Emptying it and running the appenders gave **46,867 rows against 50,345 committed**,
with 3,963 rows only in the committed file, 485 only in the regenerated one and about 290 differing in content.

The goal: the file is a **pure function of committed inputs**, rebuilt from an empty file on every `python dictionary.py` run, and
**as complete as the sources allow**: every verb with a trusted Verbiste template gets a full conjugation, whether or not a
discriminator needs the form (the phonetics must be in the theory for a form to be typable).

## 2. What was done

| Area | Change |
|---|---|
| Determinism | The output depended on set/dict iteration order (the string hash seed): two runs gave the same rows in a different order. `util/build_synthetic_lexicon.py` sorts the file after every appender (`canonicalizeSynthetic`) and prunes the dropped spelling variants after every appender (`util.prune_spelling_variants`; the generators ignore `spellingVariants.tsv`, so `dissous`, dropped for `dissout`, was regenerated every round and the loop never converged). |
| From scratch | `build_synthetic_lexicon` empties the file to its header first (`resetToHeader`); `--incremental` keeps the old rows. Converges in **2 rounds** (was 5), about 2 minutes. |
| Verbs, filter | `confirmCandidates` kept only candidates whose lemma newly collided in discriminator-feature space (introduced in `e060dd2` for the `rechampir`/`regarnir` problem). It hid whole paradigms (`confédérer`: 3 forms in Mixte, its 28 generated ones dropped). Now every candidate is kept; the filter is behind `--only-colliding`. |
| Verbs, detection | The detector flagged only lemmas whose discriminator features were a strict subset of their siblings'. `allTemplatedVerbLemmas` now completes every verb with a trusted template (`--undersampled-only` keeps the old detection). |
| Verbs, participles | `spliceParticiplePhon` stripped every `#` and re-added them at the end: it lost the leading `#_` of silent-h participles (`hanchées`) and moved internal silent units (`ahurie`). Now only trailing `_#` is stripped (Mixte's own convention). `generateMissingParticiple` refuses a participle whose breakdown does not spell its word (Lexique's `persifflé`, `croître` `crus`, the dropped `dissous`). |
| Hand rows | The 21 `asseoir`/`rasseoir` rows of `util/fixAsseoirDualFormGapsManual.py` are data now: `resources/syntheticManualRows.tsv`, appended by S2.4 (`util/appendSyntheticManualRows.py`). |
| NOM/ADJ, Morphalou | The committed NOM/ADJ rows had been validated against Morphalou 3.1, an external download. `util/build_morphalou_forms.py` distils it into `resources/morphalouNomAdjForms.tsv` (22,147 rows, 646 KB: the spellings of the slots Mixte lacks); attribution in `morphalouNomAdjForms.NOTICE.md` (LGPL-LR). |
| NOM/ADJ, agreement bars | The donor tables demanded 100% agreement, so one noisy donor sank a regular plural. Now 0.9 when Morphalou confirms the spelling (`morphalou_relaxed`), 0.95 for slots Morphalou has no entry for (`donor_table_relaxed`). Measured against the committed rows: 681 of 686 overlapping rows reproduce field for field at 0.9. |
| NOM/ADJ, cascade | A generated row served as donor for the next round (about 190 rows over rounds 2-4). The ending tables are now learned from Mixte alone, and the appender iterates to its own fixed point (a generated row can be the source slot of another missing slot). |
| NOM/ADJ, self-blocking | `existingOrthoByLemme` was keyed by lemma, so a spelling generated for one slot blocked the same spelling for another slot or category (`allèles` m.p./f.p., `audiovisuels` NOM/ADJ): 43 committed rows recovered, field for field, plus about 800 homographic rows. |
| Diagnostics | `util/check_synthetic_regeneration.py` (regenerates twice in a temp copy, checks byte-identity, reports the differences against the committed file). `util/check_against_wiktionary.py` (section 5). |
| References | `util/fetch_wiktionary_conjugations.py` + `util/_wiktionaryconj.py` (fr.wiktionary conjugation tables), `util/_pronunciation.py` (IPA to lexicon alphabet, tolerant comparison). GLÀFF downloaded locally (section 4). |
| Tests and docs | About 60 new tests (1,302 pass; the one failure, `plover_plugin_test`'s stale expressions file, predates this work); `CLAUDE.md`, `docs/PIPELINE.md`, README credit updated. |

## 3. Where it stands

Regeneration from scratch, two runs byte-identical (md5 `7812d625fc7e8177744858daee5c397f`):

| | Original | Now |
|---|---|---|
| rows | 46,867 (committed: 50,345) | **61,981** |
| only in committed | 3,963 | **412** (355 VER, 29 NOM, 28 ADJ) |
| only in regenerated | 485 | 11,505 (new full paradigms, plurals, homographic slots) |
| rounds to converge | 5 (and did not converge once the verbs were completed) | 2 |

`LexiqueSynthetic.tsv` itself is **unchanged**: the regenerated file only lived in temp copies. Adopting it is the one-time
refresh of TODO step 5 and needs approval, a full `python dictionary.py` and the md5 comparison of the pipeline outputs
(they change wherever Synthetic rows change).

Decisions already taken (user, 2026-10-08):
- the regenerated vowel value is adopted in all six classes of the 218 differing rows (doubled `-eler` `°`->`E`, `-ayer` `e`->`E`, `-ier`
  subjunctives without the final glide, `baie` `e`, and, against `util/harmonyVowelTargets.tsv`, `autographie` `O`->`o` and `clone`
  `o`->`O`; `décaties` follows Mixte's `dekasi`). Do not hand-run `fixHarmonyVowels` / `fixMixedHarmonyVowels` on the Synthetic file;
- the donor-only agreement bar is 0.95.

## 4. The reference sources

| Source | What | Size | Status |
|---|---|---|---|
| **Morphalou 3.1** (ATILF/CNRTL, LGPL-LR) | NOM/ADJ spellings | CSV 106 MB (zip 38 MB) | Downloaded to `morphalou/` (gitignored); only its distillate is committed. |
| **fr.wiktionary conjugation tables**, fetched 2026-10-08 | IPA of every simple form, current content | `resources/wiktionaryVerbPronunciations.tsv`: 121,356 rows, 6.2 MB, 5,499 lemmas | Untracked, ready to commit (CC BY-SA 4.0, NOTICE written). Only the forms Mixte lacks are kept. 74 lemmas have no usable page (`.missing.txt`). |
| **GLÀFF 1.2.2** (Sajous, Hathout, Calderone; Wiktionnaire snapshot around 2013, CC BY-SA 3.0) | IPA of 1.04 million verb forms | 158 MB | Local only, `glaff/` (gitignored). An older snapshot of the same Wiktionnaire, not an independent annotation. |

Coverage of the 174,199 verb slots missing from `LexiqueMixte.tsv` (6,289 verb lemmas; 716 have no trusted template, 2 are
complete): Wiktionary 93.9%, GLÀFF 98.7%, union **98.8%**. Finite tenses 98.0% (Wiktionary) and 99.7% (GLÀFF); past participles
only 12.8% (Wiktionary: most pages omit the feminine and plural participle table) and 78% (GLÀFF).

## 5. Checking our rows: `util/check_against_wiktionary.py`

Compares every Synthetic VER row with the Wiktionary pronunciation of the same lemma and tag, GLÀFF as fallback, in the lexicon
alphabet. Labels: exact, equivalent (schwas, open/close mid vowels and a doubled glide ignored; the detail names the relaxation and
the direction: "ours o, ref O"), differs, no reference. Run on the committed file: 41,480 rows with a reference, **82.0% exact, 97.6% exact
or equivalent**, 979 differ. On an older regeneration: 82.0% / 98.0%, 904 differ.

What the "equivalent" bucket contains: `o` where Wiktionary has `ɔ` (4,342 rows: the closed-`o` convention of the lexicon, a design
choice), `E`/`e` in both directions (767 and 739 rows: the `-ayer` question, see 6.4), schwas (438), glides (74).

## 6. Challenges left

### 6.1 About 128,000 verb slots are still missing

After synthesis, **128,416 of the 174,199 missing slots remain** (5,564 lemmas; the committed file leaves 131,802): the generator
fills about a quarter. They are spread evenly over all tenses. Reasons seen: the 100% agreement bar of the finite ending tables
(`MIN_FINITE_MATCH_RATE = 1.0`), ending-table entries that no donor of the template attests (passé simple 2s/2p and conditionnel 1p/2p
of `-éer`, `-ier`, `-iller`: `créerions`, `clouas`, `déshabillâtes`), `en-`/`em-`+vowel verbs whose infinitive loses its `n` unit in
`Word` (`enivrer`, `enorgueillir`), and homograph tag rows (`regrées` as `sub:pre:2s`).

**99.3% of these slots exist in Wiktionary or GLÀFF** (Wiktionary 96.4%, GLÀFF 99.1%; 917 in neither), so the forms and their
pronunciations are known. The references give a pronunciation, not our syllable breakdowns (`syll_cv`, `orthosyll_cv`), so they
guide and validate the generator rather than replace it.

Options to measure with `check_against_wiktionary.py` (a candidate file, scored for rows filled and agreement):
(1) lower the finite agreement bar (0.95, 0.9); (2) derive a missing slot from the same lemma's other forms by a slot-to-slot suffix map
learned across templates (conditionnel 3s `créerait` -> 1p `créerions`), keeping `isWellFormedSplice` as the guard; (3) copy the
phonology of an attested homograph for the tag rows (76 rows); (4) reinsert the `n` unit before splicing (20 rows); (5) steer the
choice among donors by the reference pronunciation.

### 6.2 Reconciling Wiktionary and GLÀFF where they differ

Both are Wiktionnaire, 13 years apart, so agreement is not independent proof and disagreement is partly a matter of time. On the
**163,326 slots both have**:

| Class | Slots | Share |
|---|---|---|
| identical after notation normalization (dots, optional schwa, `ɡ`/`g`) | 159,897 | 97.9% |
| equivalent: mid vowel `e`/`ɛ` | 1,839 | 1.1% |
| equivalent: doubled glide (`kʁij.jɔ̃` / `kʁi.jɔ̃`) | 933 | 0.6% |
| equivalent: schwa, schwa + mid vowel, mid vowel + glide | 307 | 0.2% |
| genuinely different | **350** | 0.2% |

The doubled glide is a systematic difference of epoch: the current pages write `-iions` as `ij.jɔ̃` (also our `-oyer` encoding, `assoyions`
`aswajj§`), GLÀFF as `i.jɔ̃`. The 350 real differences (spread evenly over the tenses) are of four kinds:
- **an error in one source**: Wiktionary `défleurir` imparfait carries a stray accented letter, `vouloir` impératif has garbled IPA (`vul§ouv9j§`);
- **a change of the page since 2013**: `arguer` (`aRgj§` now, `aRgyj§` in GLÀFF), `réargenter` (`5` against `@`), `rentraire`;
- **variants listed by one source only**: `débecqueter` (GLÀFF lists three), `assener` (`asnat`/`as°nat` against `asenat`), `abasourdir` (`s`/`z`);
- **a loanword**: `driver` (`dRiv` against `dRajv`).

Proposed policy, to confirm: (1) treat identical and equivalent as agreement, equivalences logged; (2) a pronunciation is a *set* of
variants, a generated row passes if it is in the union; (3) on a real difference prefer the current Wiktionary unless it fails a
sanity check (characters outside the IPA inventory, unbalanced symbols, implausible length), then GLÀFF; (4) when both are plausible,
use our own attested forms of the lemma as the tiebreaker (the generated candidate from the donor table is a third opinion: majority
of three); (5) write the unresolved remainder (about 350 slots) to a review file for a human, which is small enough to settle by hand;
(6) never let a reference override an explicit user ruling in the lexicon (`spellingVariants.tsv`, the vowel decisions of section 3).

### 6.3 Real differences in our own rows

From the checker (committed file), for example: `osciller` and relatives (ours `osijat`, Wiktionary `ɔsilat`: the `ll` is /l/; 24 rows),
`obstruer` (`OpstRy§` against `ObstR8§`), `empuantir` (`@p8@t` against `@py@t`), `tiller`/`grappiller` (`tilj§` against `tijj§`),
`discourir` (`diskuRE` against `diskuRRE`), the doubled-consonant `-eler` futures (about 130 rows with a schwa where the references have
`E`; the regenerated file fixes them). These are lexicon (S1) questions as much as synthetic ones.

### 6.4 Vowel conventions

`o` against `ɔ` (4,342 rows) is the closed-`o` convention of the lexicon. `-ayer`: Wiktionary writes open `ɛ` for word-final or silent `y`
(`délaye`, `délaient`) and closed `e` before a pronounced vowel (`délayé`, `délayâmes`), so the rule "`ay` is never closed /e/ plus glide"
is right for the first kind only; the 81 rows adopted from the regeneration split by form. `cloner` (closed `o` per Wiktionary) and
`autographier` (closed `o`, against the validated `O` of Mixte) show that `util/harmonyVowelTargets.tsv` is itself disputable.

### 6.5 Glide encoding of the `-ier` verbs (S1, TODO "INVESTIGATE LATER")

The glide fix of `lexique.py` only fires for the biphoneme `wa`; `criions` stays `kRij§` (`k_R_ij_#|§`, glide fused into the vowel
unit). Current Wiktionary has `kʁij.jɔ̃`. **Decided and implemented 2026-10-09** (`docs/LEXICON_COMPLETION_CONTINUATION.md` §2): the
glide opens the next syllable as its own unit (`criions` `k_R_i|j_§`), doubled `j|j` after `y` and `ill` (`essuyions` `8_ij|j_§`, `brillions`
`i_j|j_§`), and a letter carrying a vowel and a glide gets a repeat unit `=` (`cria` `k_R_i|j_a` / `c_r_i|=_a`); rule `splitGlides` in
`src/mixterules.py`, 481 verb rows. Still open: the effect on strokes, homophones and the elicitation (not measured), and the Synthetic
regeneration on the new donors.

### 6.6 Leftover rows against the committed file

412 only in the committed file: 355 VER (tenses the strict tables skip for `bitter`, `corseter`, `stripper`, `valeter`, `agréer`, `créer`,
`enivrer`, `clouer`, `déshabiller`; `enorgueillir`), 29 NOM and 28 ADJ (the `-ène` adjectives `autogènes`, `endogènes`; `bodys`/`caddys`/
`catchs`; 13 tag gaps by design; 6 corrupt committed spellings such as `autolog`, `hambourgeoi`: good riddance). About 10 orthographic-
syllable rows are wrong on one side (`épagomène` `è_n_es` committed; `benoîtes`, `cashmeres` regenerated).

### 6.7 Participles

Few sources list the feminine and plural participle forms of intransitive verbs; 1,808 participle slots are in neither source. The
participle phonology is copied from the attested one, so those forms stay a generation question.

### 6.8 Adoption

To do before the refresh: the remaining generator work above, the orthographic-syllable rows, the stale counts in `docs/PIPELINE.md`
and `CLAUDE.md` (test count 1240), the install instructions for Morphalou and GLÀFF (TODO), then the approved replacement of
`LexiqueSynthetic.tsv`, a full `python dictionary.py` from a clean state and the md5 comparison of `phonetic_theory.tsv`,
`disambiguated_theory.tsv`, `resolved_press_sets.json`, `keypress_groups.json`, `realization_report.json`,
`plover_stenalgo_dictionary.json` and the trainer JSONs (they will change; the user judges), then a second run with identical md5s.
Licensing: the Wiktionary file and any GLÀFF-derived data are CC BY-SA; commit them knowingly (NOTICE files written).

## 7. Reproducing

```bash
python -m util.build_synthetic_lexicon                    # S2 from scratch (2 rounds); --incremental keeps the rows
python -m util.check_synthetic_regeneration               # two from-scratch runs in a temp copy, byte-identity, diff report (~12 min)
python -m util.check_against_wiktionary [--synthetic PATH] # our rows against the references (~25 s)
python -m util.build_morphalou_forms                      # rare: needs morphalou/Morphalou3.1_CSV.csv
python -m util.fetch_wiktionary_conjugations              # rare: refreshes the Wiktionary file (~50 min, 4 requests/s)
```

Files added: `util/check_synthetic_regeneration.py`, `util/check_against_wiktionary.py`, `util/_pronunciation.py`,
`util/fetch_wiktionary_conjugations.py`, `util/_wiktionaryconj.py`, `util/build_morphalou_forms.py`, `util/appendSyntheticManualRows.py`,
`resources/morphalouNomAdjForms.tsv` (+ `.NOTICE.md`), `resources/syntheticManualRows.tsv`,
`resources/wiktionaryVerbPronunciations.tsv` (+ `.missing.txt`, `.NOTICE.md`). Modified: `util/build_synthetic_lexicon.py`,
`util/completeVerbParadigms.py`, `util/generateMissingNomAdjForms.py`, `src/nomAdjParadigm.py`, `src/verbparadigm.py`, `dictionary.py`,
`CLAUDE.md`, `docs/PIPELINE.md`, `README.md`, `TODO.md`, `.gitignore`.
