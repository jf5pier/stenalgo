# Resume: Pluvier-style TAO prefix/suffix shortcut scan (2026-09-26)

TODO.md task "Pluvier-style TAO prefix/suffix shortcut scan" — measurement only, nothing wired into the theory.
Status: DONE, uncommitted (no commit requested yet).

## Files
- `scratch/pluvier_affix_scan.py` — the scan (run from repo root: `PYTHONPATH=. env/bin/python scratch/pluvier_affix_scan.py`, ~50 s). Holds the RULES table (transcribed from https://github.com/Vermoot/Pluvier/blob/main/TAO_rules.md, prefix/suffix rules only) and the FAMILIES map.
- `scratch/pluvier-affix-shortcuts.tsv` — 151 (chord, affix) rows, sorted by strict freq.
- `scratch/pluvier-affix-families.tsv` — 19 families, words deduplicated across a family's affixes.
- `Tao.md` (rough OCR of the book) was NOT scanned.

## Model
- Strokes: first stroke sequence of each Word in the disambiguated theory (Plover dictionary). Stroke i = orthographic syllable i (`orthosyllCV`); strokes beyond the syllable count are trailing marks (plural/conjugation), never touched. 56 of 171,448 words skipped (ortho/syllable letters mismatch).
- A shortcut replaces the syllable strokes the affix spans with ONE conflict-free stroke.
  - strict gain = (syllables fully inside the affix letter span) - 1, only if >= 2 such syllables.
  - loose gain = (syllables overlapping the affix span) - 1 — an upper bound (assumes the chord also absorbs a partly covered neighbour syllable).
- Suffix rules also match when a plural "s" follows. Frequency = film-subtitle frequency (Word.frequency), summed per Word entry (one per grammatical category).
- "strict freq" = summed frequency of the words that get >= 1 stroke shorter under the strict model.

## Findings
Only 6 families save strokes on the strict model:

| Family | Strict words | Strict freq | Freq x strokes saved | Loose freq |
|---|---|---|---|---|
| suffix -ité (ité rité ilité bilité bité vité cité sité) | 855 | 901.4 | 1015.2 | 1549.6 |
| suffix -tion (tion ration cation lation ciation ction ntion ition ption rtion...) | 537 | 589.1 | 589.1 | 2181.5 |
| prefix Latin (inter super multi trans re) | 897 | 367.5 | 367.5 | 477.3 |
| prefix ex- (ex exce exci) | 80 | 151.3 | 151.3 | 1568.5 |
| suffix -ment (ment vement) | 106 | 127.8 | 127.8 | 127.8 |
| suffix -logie (logie logique logiste logue) | 334 | 101.1 | 101.1 | 101.5 |

(Verb suffix family -ise/-iger: 37 words, 11.4 — marginal.)

Top single rows (strict freq): -RT rité 447.8 (129 words), INTS inter 308.8 (651), -RGS ration 237.8 (181), -BGS cation 169.7 (199), -LGS lation 159.5 (132), -LT ilité 140.5 (298), -FT vité 132.2 (118), -FPLT vement 127.8 (106), -BLT bilité 113.8 (244; saves 2 strokes each, 227.6 stroke-freq).

- -ité is the strongest suffix family; its members chain (…/bi/li/té → one stroke).
- -ment scores 0 on its own ("ment" is one syllable `m_ent`); the family's 127.8 is all -vement.
- Zero on strict (single-syllable affixes; a replacement stroke saves nothing): prefix families con-/com-, dé-, nasal+consonant (ent end int ind in ins ens), consonant+en (fin fen ten ven), vowel+m+b/p; suffix families -ier/-ien, -al/-el/-ble, -eur, -ance/-ande/-cte, -if/-ive, consonant clusters, vowel/glide endings. Their loose numbers (e.g. con-/com- 4720, nasal+consonant 4239) only materialise if the chord fuses with the neighbouring stroke, which this model does not measure.

## Open / next
- Human evaluation of the TSVs; family memberships were chosen by Claude (ex/exce/exci grouped; fin/ten/ven kept apart from nasal+consonant) — adjust FAMILIES if wanted.
- Prefix chords that fuse with the following stroke would need a different model (not built).
- Commit decision pending: the script, the two TSVs and this file are untracked.
