# Spec: grouped lexicon decisions

Scope: Lexicon Building (S1) and Synthetic Lexicon Building (S2). How a disagreement between our rows (`LexiqueMixte.tsv`,
`LexiqueSynthetic.tsv`) and the reference pronunciations (fr.wiktionary, GLÀFF; `util/_verbreferences.py`) becomes a
**decision group**, how the user rules on it, and how the ruling is replayed at build time so that both lexicons stay a pure
function of their committed inputs. Plan: `docs/SYNTHETIC_LEXICON_STATUS.md`.

## 1. Principles

- `LexiqueMixte.tsv` sets the phonetic and syllabic conventions; Synthetic rows are spliced from Mixte-derived rules, never
  transcribed from IPA. The references check and choose; they never override a lexicon convention (section 3) or an explicit
  user ruling (`spellingVariants.tsv`, the vowel rulings of 2026-10-08).
- One ruling covers every row that shares a **signature** (section 4). Groups are reviewed by descending slot count.
- An undecided (`pending`) group always gets the safe default: no change to Mixte, no new Synthetic row.

## 2. The decisions file: `resources/lexiconDecisions.tsv`

Committed, tab-separated, `#` comment lines allowed, sorted by `group_id`. Columns:

| Column | Content |
|---|---|
| `group_id` | first 10 hex digits of `sha1(kind + "\t" + level + "\t" + signature)`: stable across runs |
| `kind` | `mixte_rule`, `mixte_typo`, `synth_rule`, `ref_conflict`, `template` |
| `level` | `L1`..`L4` (section 4.3); `-` for kinds that are not difference groups (`template`, `synth_rule` mechanisms) |
| `signature` | human-readable, e.g. `j→l @ ll | osciller-family` (section 4.4) |
| `verdict` | `accept`, `reject`, `pending` |
| `param` | the chosen value when the decision has one: a template (`aim:er`), a preferred variant, a bar (`0.9`); else empty |
| `slots` | rows/slots the group covers when it was last mined (information, refreshed by the miner) |
| `counter` | counter-examples at that level (section 4.3; information) |
| `examples` | up to 3 `ortho:ours>ref` items, `;`-separated (information) |
| `note` | free text; the miner writes a one-line recommendation prefixed `rec:` |
| `date` | ISO date of the verdict, empty while pending |

Module `src/lexicondecisions.py`, modelled on `src/affixdecisions.py`: frozen `Decision` dataclass (the columns), immutable
`Decisions` with `get(groupId)`, `withEntry(decision)`, `accepted(kind) -> list[Decision]`, `pending()`; `loadDecisions(path)` /
`saveDecisions(decisions, path)` (deterministic order); `mergeMined(decisions, mined) -> Decisions`: adds new groups as `pending`,
refreshes `slots`/`counter`/`examples` of existing ones, **never** touches `verdict`, `param`, `note` (except a `rec:` prefix on a
pending row), `date`; a decided group the miner no longer finds is kept and flagged `note += " [stale]"`.

## 3. Lexicon conventions (never a difference)

Applied before computing edits; a row whose only edits are conventions is not a candidate:

| Convention | Edit ignored |
|---|---|
| closed `o` for written `o`/`au`/`eau` (the lexicon writes `o` where Wiktionary has `ɔ`) | ours `o`, ref `O` |
| optional schwa | insertion or deletion of `°` |
| notation (dots, stress, `ɡ`) | handled by `ipaToLexicon` already |

The `e`/`E` and doubled-glide differences are **not** conventions: they are real questions (status 6.4, 6.5) and must surface as
groups. Keep the list in one constant (`CONVENTION_EDITS` in `src/diffsignature.py`) so a later ruling can extend it.

## 4. Signatures: `src/diffsignature.py`

### 4.1 Edit script

For a row (`phon`, `syll_cv`, `orthosyll_cv`) and its `RefSet`: take the reference variant nearest to `phon` (edit distance; ties
broken by lexicographic order of the variant, for determinism). Compute a Levenshtein alignment with a deterministic backtrace
(on ties prefer match/substitution, then deletion, then insertion). Each non-match step is an `Edit(op, ours, ref, phonIndex)`:
`sub` (`j→l`), `del` (`j→∅`), `ins` (`∅→j`). Drop the edits listed as conventions (section 3). Merge adjacent edits on the same unit
into one (`ij→i` rather than two edits).

### 4.2 Anchoring an edit on a unit

Walk `syll_cv` units (split on `|` and `_`) in step with `phon`: a unit `#` consumes no phoneme, any other unit consumes
`len(unit)` phonemes (`ij` consumes two). The edit's unit is the one consuming `phonIndex`; an insertion anchors on the silent
`#` unit that immediately follows the preceding phoneme's unit when there is one (that is where a sound went missing:
`criions` `k_R_ij_#|§`), else on the unit of the preceding phoneme (the first unit when at index 0). The **grapheme** is the `orthosyll_cv` unit at the same index (the two
breakdowns align unit for unit). The **unit position** is `initial`, `medial` or `final` (last sounded unit).

### 4.3 Levels and homogeneity

| Level | Key |
|---|---|
| `L1` | the tuple of (edit, grapheme, unit position) over the row's edits |
| `L2` | `L1` + morphological family: the verb template key (`endingTemplateKey`, src/verbparadigm.py:871), or the NOM/ADJ 2-letter ortho ending class (`orthoClassKeys`, src/nomAdjParadigm.py:227); **no slot** |
| `L3` | `L2` + slot |
| `L4` | `L3` + lemma |

(Revision 2026-10-09: the first audit put the slot into L2, which split one family such as `essayer` over ~25 groups, and 81% of
the edited Mixte rows fell to singletons. The family level without the slot sits between the grapheme level and the slot level.
The class key is passed as `(family, slot)`.)

**Counter-examples** of a group: rows of the audited lexicon that have the same grapheme at the same unit position with the
same *our* phoneme (the left side of the edit), restricted to the group's level key minus the edit, whose comparison to their own
references is `exact` or convention-only. Example: `j→l @ ll` at `L1` has the `fille`/`bille` rows as counter-examples (`ll`=/j/
matches the reference), so `L1` is not homogeneous; at `L2`/`L3` the `osciller` family has none.

`precision = slots / (slots + counter)`. The miner proposes, for each row:
1. the **coarsest level with precision ≥ 0.95 and slots ≥ 3** (a *homogeneous* group);
2. else the **coarsest level with slots ≥ 3**, flagged *heterogeneous* (precision shown; the review's `d` splits it);
3. else `L4`: a single-row `L4` group is `mixte_typo` (or a per-slot `synth_rule` residue).

Rows are assigned greedily, homogeneous candidates first, then by descending slots, so a row belongs to exactly one group and
the slot counts add up. Rationale: an accepted Mixte group corrects **its member rows only** (section 6), so a heterogeneous
group is safe to accept; precision tells the user how systematic the question is, not what the ruling would touch. The goal
is the fewest decisions for the most slots.

### 4.4 Signature string

`<edits> @ <graphemes> [<positions>] | <family> <slot> | <lemma>`, the parts after `@` present according to the level, edits
joined by `,`. Examples: `j→l @ ll [medial]` (L1), `E→e @ ay [final] | p:ayer` (L2), `E→e @ ay [final] | p:ayer ind:pre:1s`
(L3), `j→∅ @ i [medial] | cr:ier ind:imp:1p | crier` (L4). The class key is the pair (family, slot).

## 5. The review CLI: `util/review_lexicon_decisions.py`

`python -m util.review_lexicon_decisions [--kind KIND] [--min-slots N] [--file PATH]`. Interactive loop on the `pending` groups,
sorted by `slots` descending then `group_id`. For each group print: kind, level, signature, slots, precision, the `rec:` note,
up to 8 member rows (`ortho  ours  ref(source)  syll_cv  orthosyll_cv`) and up to 3 counter-examples. Answers:
`y` accept, `n` reject, `s` skip, `p` set `param` then accept, `d` split (replace the group by its next-finer-level subgroups,
added as `pending`, and review those next), `q` quit; an optional note after the answer. Save after every answer
(`saveDecisions`), like `util/review_affix_rules.py` (`reviewItem` :60, `_reviewGroups` :107). Non-interactive `--list` prints the
pending table.

### 5.1 The examples sidecar: `lexicon_decision_examples.json`

Gitignored, written by the miner (`writeExamplesSidecar`), read by the review (`loadExamplesSidecar`, absent file = empty).
`{"format": 1, "groups": {group_id: entry}}`, keys sorted. An `entry`:

- `heterogeneous`: true when the group was proposed by rule 2 of section 4.3 (the review shows it; `rec:` says so too);
- `members`: every row of the group, `{ortho, ours, ref, refSource, syllCV, orthosyllCV}` (`RowDiff.toJson`);
- `counters`: up to 3 matched rows that share the group's counter key, same fields (`ref` = `ours`: they matched);
- `children`: the next-finer-level subgroups (L1 -> L2 -> L3 -> L4; none for L4), each
  `{level, signature, slots, counter, heterogeneous, examples, members, counters, children}` (`ProposedGroup.children`).

The `d` answer sets the parent `reject` with note `split: <child level>` (or the typed note), adds the children as
`pending` (an existing child keeps its verdict), and copies each child's `members`/`counters`/`children` into the sidecar
under its own group id. The miner must treat a `split:` parent as "descend": its rows go to the child groups.
`mergeMined` leaves a `pending` group the miner does not re-find untouched, for that reason.

## 6. Replay at build time

| Kind | Applied by | How |
|---|---|---|
| `mixte_typo`, `mixte_rule` (data) | `lexique.py` `outputMixedLexique` | `util/build_mixte_corrections.py` turns every accepted group's member rows (from the sidecar) into rows of the committed `resources/mixteCorrections.tsv` (key `ortho lemme cgram infover`; corrected `phon syll_cv orthosyll_cv`; `group_id`). The corrected breakdown applies the anchored edits to the units (substitution inside the unit; an insertion fills the anchoring `#` unit or extends the unit; a deletion leaves `#`). `param` may name the variant to adopt when the references offer several. Each key must match exactly one row, else the build fails |
| `mixte_rule` (systematic) | `lexique.py`, next to `fixLexiqueInfraGraphPhon` | when the cause is a defect of the build itself (a bad Infra association pattern, a reform rewrite that breaks the unit alignment), a function in `src/mixterules.py` (registry `{group_id: rule}`, pure function on a row) fixes it at the source; run only when its group is `accept` |
| `synth_rule` | `util/completeVerbParadigms.py`, `util/generateMissingNomAdjForms.py` | a mechanism runs for a (class, slot) only when its group is `accept` |
| `template` | `getTrustedTemplate` | accepted groups are written into `resources/verbModelExceptions.tsv` with status `family_template` |
| `ref_conflict` | `util/_verbreferences.py` | `param` names the preferred variant; overrides the automatic preference |

Registered systematic Mixte rules (2026-10-09, both `accept`ed in `resources/lexiconDecisions.tsv`, kind `mixte_rule`, level `-`):
`splitGlides` (`e3e2ed7746`: the verb glides opening the next syllable, doubled after `y`/`ill`, with the repeat unit `=`) and
`dropStrayGlide` (`e1cded21a8`: `ij` before a silent `e` unit -> `i`). The repeat unit `=` (`src/orthounits.py`) sits on the
`orthosyll_cv` side only: the previous grapheme repeated in the onset of the next unit, adding nothing to the spelling; it lets one
letter carry two sounds across a syllable break while the two breakdowns still pair unit for unit. A deletion rule of `reform1990.tsv`
also carries a `followingChar` guard (`lexique.py`), so that `asseoir -> assoir` leaves the `assey-` forms alone.

Reference variants: neither Wiktionary nor GLÀFF supplies a regional label to the pipeline. A reference is a set of variants and only
vetoes: a candidate passes if it is exact or equivalent to any variant (`compare`, `util/_pronunciation.py`); when the two sources disagree
only the plausible Wiktionary variants count (`RefSet.preferred`). The stored pronunciation is a project convention.

Determinism: rules and corrections are applied in `group_id` order; the outputs are sorted as today. Two runs from the same inputs
must give byte-identical `LexiqueMixte.tsv` and `LexiqueSynthetic.tsv`.

## 7. Tests (table for `src/test/diffsignature_test.py`)

| phon / ref | syll_cv | orthosyll_cv | expected L1 signature |
|---|---|---|---|
| `osija` / `osila` | `o\|s_i\|j_a` | `o\|sc_i\|ll_a` | `j→l @ ll [medial]` |
| `kRij§` / `kRijj§` | `k_R_ij_#\|§` | `c_r_i_i\|ons` | `∅→j @ i [medial]` (ins anchored on the silent 4th unit, grapheme `i`) |
| `kloni` / `klOni` | `k_l_o\|n_i` | `c_l_o\|n_i` | none: ours `o`, ref `O` is the convention |
| `kloni` / `kl2ni` (constructed) | `k_l_o\|n_i` | `c_l_o\|n_i` | `o→2 @ o [medial]` |
| `delEE` / `deleE` | `d_e\|l_E_#\|E` | `d_é\|l_ai_e\|nt`-style | `E→e @ ai [medial]` (one edit; build the fixture so units align) |
| `kRe°Rj§` / `kReRj§` | — | — | no difference (schwa convention) |

Adjust the `criions` expectation to whatever 4.1/4.2 actually produce, but the rule must be documented in the docstring.
