# Phonemes in Stenalgo and Pluvier: differences and missing-phoneme treatment

Résumé of how the two theories turn French phonemes into keys, and what each does with the phonemes it cannot place
on a key of its own. Sources: `starboard3h.json` (Stenalgo layout), `resources/pluvierPhonemeKeys.tsv` (Pluvier table,
copied from the Pluvier clone), `src/steno_encoding.py` of the clone (`VOWELS`, `CHUNKS`, `MANDATORY_CHUNKS`), the
theory comparison (`docs/THEORY_COMPARISON.md`). Phonemes are X-SAMPA, one ASCII character each
(`@` ã, `§` õ, `5` ẽ, `1` œ̃, `°` schwa, `8` ɥ, `N` ɲ, `G` ŋ, `Z` ʒ, `S` ʃ).

## 1. Two designs

| | Stenalgo | Pluvier |
|---|---|---|
| Model | Compositional: 20 consonants + 16 nucleus phonemes; a syllable is the union of the keys of its phonemes in three banks (onset, nucleus, coda). | A hand-made table plus per-syllable exceptions (`CHUNKS`) plus per-word dictionary entries. |
| Where chords may reach | Every key belongs to one bank; no chord crosses the onset / nucleus / coda split. | Chords cross it: nasal vowels use coda keys (`APB`, `OPB`), diphthongs and clusters have dedicated chords. |
| Coverage of the phoneme set | Every phoneme has keys. Writable-by-the-theory words: 100% of the frequency. | Phonemes the table cannot write at all: 0.69% of the frequency. |
| How the layout was made | CP-SAT against the lexicon's measured ambiguity, stroke cost and phoneme order (S4). | Ireland English layout, adapted by hand. |
| Ambiguity | Accepted where the lexicon says it is cheap (shared keypresses), the rest resolved later by marks and feature keys (S6/S7). | Resolved by the chunk rules and by choosing among dictionary outlines. |
| Phoneme-order violations (words, frequency-weighted) | 0.81% | 1.87% |

The plain Pluvier table encoding equals one of the real Pluvier outlines for only 2.77% of the words (34.4% of the
frequency): the table is a seed, most of the real theory lives in the chunk rules and the dictionary.

### What `CHUNKS` are
`CHUNKS` is the exception dictionary of the Pluvier generator (`Steno_Encoding.CHUNKS`, `src/steno_encoding.py` of the Pluvier
clone): a map from a **phoneme string** (a syllable or a piece of one, X-SAMPA, e.g. `v°n`, `Egze`, `wa`, `gR`, `N`) to the **chord
it is written with**, replacing what the per-phoneme tables (`VOWELS`, `CONSONANTS_LHS`, `CONSONANTS_RHS`) would produce. When the
encoder cuts a word into syllables it looks the pieces up in the chunk table (`find_matching`) and uses the tables for what no
chunk covers (I read the lookup, not every branch of the encoder). The value uses a small notation:

| notation | meaning | example |
|---|---|---|
| `A\|B` | two alternative chords, one for each hand. The clone's comment says "right_hand\|left_hand", but entries differ (`'N': '-PG\|PG'` lists the right-hand form first, `'v°n': 'WH\|FPB'` the left-hand one), so the order is not reliable | `'N': '-PG\|PG'`, `'v°n': 'WH\|FPB'` |
| leading `/` | already a finished chord, to be used as is (it does not combine with the neighbouring syllables) | `'Egze': '/KP'` |
| leading `-` | a right-hand chord | `'ij': '-/LZ'` |

So a chunk is what makes the theory non-compositional: it can cross the onset / nucleus / coda split (`'@': '/APB'` writes a nasal
vowel with coda keys), swallow a schwa (`'s°': 'S'`), merge a diphthong or a cluster into one chord (`'wa': 'OEU'`, `'ks': '-/BGS'`),
or even fix a whole syllable (`'vin': 'VH'`). `MANDATORY_CHUNKS` is a smaller dictionary of the same kind; the generator encodes
each word once with `CHUNKS` and once with `MANDATORY_CHUNKS` (`src/steno.py`), which is one source of the several outlines Pluvier
keeps for a word. Chunks are why the plain table encoding matches a real Pluvier outline for only 2.77% of the words.

## 2. Phoneme to keys, side by side

Stenalgo key names: `R-` left hand, `-s` right hand, `a-`/`@-` left thumb, `-i`/`-e` right thumb. A `+` presses keys together.
A phoneme in **bold** shares its keypress with another phoneme of the same bank.

### Onset
| phoneme | Stenalgo | Pluvier |
|---|---|---|
| R t s p k m v | `R-` `t-` `s-` `p-` `k-` `m-` `v-` | `R` `T` `S` `P` `K` `PH` (m) `W` (v) |
| l d n f b Z z S g | `m-+t-` `p-+v-` `m-+R-` `k-+p-` `s-+v-` `v-+t-` `t-+w-` `p-+m-` `k-+s-` | `HR` `TK` `TPH` `TP` `PW` `SKWR` `SWR` `SH` `TKPW` |
| j | `R-+w-` | `KWR` |
| **w N G** | all three on `w-` | `w` = `W` (added; same key as v and 8), `N` only through `CHUNKS` (`PG`), **no `G`** |
| 8 | nucleus phoneme | `W` (same as v) |
| pairs | not needed (keys of both phonemes pressed together) | `KP` (gz), `KW` (kw), `SK` (tS), `S` (ps), `TPH` (pn) |

### Coda
| phoneme | Stenalgo | Pluvier |
|---|---|---|
| R t s l k m d n | `-R` `-t` `-s` `-l` `-k` `-m` `-d` `-n` | `R` `T` `S` `FL` `BG` `PL` `D` `PB` |
| p v f z S g N | `-j+-k` `-j+-s` `-s+-d` `-n+-l` `-Z+-m` `-k+-d` `-t+-n` | `P` `F` `F` (v and f share) `Z` `FP` `G` `PG` |
| **j b w** | all three on `-j` | b = `B`; **no `j`, no `w`** as single phonemes |
| **Z G** | both on `-Z` | Z = `G` (same key as g); **no `G` (ŋ) entry** (real outlines write *-ing* with the `g` key) |
| pairs | not needed | `TS` (tR), `*S` (st), `BGS` (ks), `PBLG` (bZ, dZ), `FLP` (sm), `RBG` (kR), `FR` (vR, fR) |

### Nucleus
| phoneme | Stenalgo | Pluvier |
|---|---|---|
| a i | `a-` `-i` | `A` `EU` |
| **e O** | both on `-e` | `E`, `O` (distinct) |
| **@ 9** | both on `@-` | `@` = `APB` (cross-part), `9` = `AO` |
| **° 8** | both on `@-+a-` | `°` = no key; `8` only inside a diphthong |
| E o § u y | `-i+-e` `a-+-e` `a-+-i` `@-+-e` `@-+-i` | `AEU` `OE` `OPB` (cross-part) `OU` `U` |
| 5 2 1 | `a-+-i+-e` `@-+-i+-e` all four keys | `EUFR` (cross-part), `AO` (same as 9), `U` (same as y) |
| diphthongs | not needed (semi-vowel consonant + vowel) | `AU` (8i), `AEU` (j2), `AE` (je), `OEU` (wa), `AOU` (wi), `AEPB` (j5), `-LZ` (ij) ... |

Stenalgo's shared keypresses are the pairs the lexicon rarely contrasts; their residual ambiguity is paid by the marks.
Pluvier's collisions (`2`/`9` on `AO`, `y`/`1` on `U`, `v`/`8` on `W`, `v`/`f` on `F`, `g`/`Z` on `G`) are settled by the
dictionary, not on the keys.

## 3. Treatment of the phonemes each theory cannot place

### The schwa `°`
- **Pluvier**: `VOWELS["°"] = ""`: no key. A syllable carrying a schwa is written by its consonants alone, and chunk rules
  absorb the common cases (`s°` -> `S`, `m°n` -> `/KH`, `v°n` -> `WH|FPB`).
  *fenêtre* /f°.nEtR/: the table encoding gives `TP/TPHAEUTS` (the syllable f° is the bare onset `TP`, then n-E-tR =
  `TPH` `AEU` `TS`); the shipped dictionary has the single stroke `WHAEUTS`. *petit* /p°.ti/ = `P/TEU` (table) or `P-T/EU`.
- **Stenalgo**: the schwa is always written, with the thumb chord `@-`+`a-` it shares with `8`. *fenêtre* = `kp@a/mRietR`
  (the `@a` in the first stroke), *petit* = `p@a/ti`.
- Consequence: Pluvier gains strokes and keys on the schwa (the main reason its outlines are short), at the price of
  outlines that no longer spell the phonology; Stenalgo keeps the phonology and pays the keys.

### Nasal vowels `@ § 5 1`
- Pluvier writes them with coda keys inside the vowel chord (`@` = `APB`, `§` = `OPB`, `5` = `EUFR` or `EUPB`, `1` = `U`), so a nasal
  vowel mixes onset-side vowel keys with the right hand and competes with the coda consonants.
- Stenalgo keeps the nasals in the nucleus bank: `@` a thumb key, `§` = `a-`+`-i`, `5` three keys, `1` four keys.

### Semi-vowels `j w 8` and diphthongs
- Stenalgo treats `j` and `w` as consonants (onset: `R-+w-`, shared `w-`; coda: shared `-j`) and `8` as a nucleus: *wa*, *ja*, *8i*
  are ordinary compositions.
- Pluvier writes them through diphthong chunks: `wa` = `OEU`, `wi` = `AOU`, `j5` = `AEPB`, `8i` = `AU`, `ij` / `aj` / `ej` = `-LZ`; it has
  no single-phoneme coda `j` or `w`, no table entry for `G`, and onset `N` only through `CHUNKS`.

### Palatal and velar nasals `N G`
- *gagner* /gaNe/: Pluvier moves the `N` to the right hand of the first syllable (`TKPWAPG/-R`), a syllabification shift; Stenalgo
  presses the shared onset key `w-` of the second syllable (`ksa/weR`).
- Coda `G` (the *-ing* words): Pluvier uses `G` (the `g` key, so *parking* = `PARBG/EUG`); Stenalgo shares `-Z` with `Z`.

### Clusters
Pluvier has pair chords for the frequent clusters (`KP` gz, `PBLG` bZ/dZ, `BGS` ks, `TS` tR). Stenalgo presses the keys of both phonemes and
the theory measures the order violations instead.

## 4. Words that depend on the gap (Stenalgo theory, 268,393 words)
Full list: `scratch/pluvier_unplaceable_words.tsv` (phoneme, part, word, phonology, film frequency). Share = frequency mass of these words
over the whole dictionary.

| phoneme (part) | words | frequency share | examples (Stenalgo -> Pluvier) |
|---|---|---|---|
| `N` onset | 3574 | 0.22% | *gagner* `ksa/weR` -> `TKPWAPG/-R`; *magnifique*; *seigneur*; *ignore* |
| `j` coda | 2801 | 0.52% | *fille* `kpij` -> `TP-LZ`; *famille* `kpa/mij`; *travail* `tRa/vaj` -> `TRAFL`; *soleil* |
| `G` coda | 147 | 0.013% | *parking* `paR/kiZ` -> `PARBG/EUG`; *camping*; *shopping* |
| `w` coda | 37 | 0.003% | *out* `ajt` -> `AE/OUT`; *house* `ajnl` -> `HAOUZ`; *country*; *ground* |
| `G` onset | 9 | 0.001% | *bingo* `svi/wae` -> `PWEUG/O`; *gringo* |

Coda `j` is the one that matters (0.5% of the frequency): Pluvier absorbs it into the `-LZ` / `FL` chunks, Stenalgo spends one key (`-j`).

## 5. Consequences for the comparison
- A per-phoneme score of the Pluvier layout (put its table on the Starboard keys and score it in the CP-SAT objective) would not be
  a fair measure: five phonemes are cross-part or keyless (`@ § 5 ° 8`), five pairs of phonemes share keys, and clusters, diphthongs and
  the schwa are handled by chunks the per-phoneme model cannot represent. The two theories are compared on outlines instead
  (`docs/THEORY_COMPARISON.md`).
- The cost gap seen in the comparison (Stenalgo 4.08 keys per word against 3.83) follows from the designs above: Stenalgo writes every phoneme
  and then adds disambiguation keys, Pluvier drops the schwa, merges phonemes into chunk chords and leaves homophones ambiguous
  (its collisions are costed in section 5b of the report).
