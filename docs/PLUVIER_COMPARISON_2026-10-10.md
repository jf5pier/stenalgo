# Stenalgo vs Pluvier: findings of the comparison (2026-10-10)

Produced with `python -m util.compare_theories` (code and definitions: `docs/THEORY_COMPARISON.md`) and the two diagnostics in `scratch/`.

**Inputs.** `plover_stenalgo_dictionary.json` of the lexicon of commit `b643f87` (288,648 strokes); `starboard3h.json` (md5 `578d39899c077ce1be6c88876e0bdf1c`, unchanged);
Lexique383 `freqfilms2` summed per spelling (universe: 125,655 spellings); Pluvier clone commit `47ab823` (2024-04-06) as FOUR layers, lowest priority first, a later file taking an outline from an earlier one:
`dicofr.json` (167,796 entries, the generated dictionary) < `dicofr-plural.json` (29,314) < `verbs.json` (106,511, many `pronoun + verb` entries) < `tao_la_salle_simple.json` (3,686, the manual TAO/La Salle briefs).
8,476 outlines are taken by a higher layer; the generator's collision record `dup.json` (26,513 outlines) is added to the claimants. Pluvier's word = its cheapest outline (fewest strokes, ties by Starboard cost).

## Correction: the first run loaded only `dicofr.json`

The first run (and the numbers first reported in the conversation) used `dicofr.json` alone. That file is the GENERATED dictionary, and Pluvier's generator deliberately leaves the most frequent words out of it (`resources/alone.json`);
they are the briefs of `tao_la_salle(_simple).json` (`la` `-LG`, `vous` `-FS`, `ne` `H-`, `un` `UPB`, `les` `-LS`, `et` `E`, `à` `A`...), which the generator's `append_tao` step layers on top. Plural and verb forms are in two more files.
`dicofr.json` alone covered 71.8% of the Lexique frequency, the four layers cover 93.9%. The first-run figures understate Pluvier badly and are superseded:

| metric (words covered by both) | first run, `dicofr.json` only | four layers |
|---|---|---|
| Pluvier coverage (frequency share) | 71.78% | 93.85% |
| spellings covered by both | 81,558 | 108,150 |
| Pluvier words colliding (share of frequency) | 15,087 (61.7%) | 16,308 (39.0%) |
| strokes per word, Stenalgo / Pluvier | 1.511 / 1.334 | 1.479 / 1.220 |
| cost on Starboard, Stenalgo / Pluvier | 298.1 / 286.0 | 286.5 / 253.8 |
| Pluvier cost, `S` on the cheaper pinky key / on Ireland | 282.2 / 279.9 (first-run model) | 252.6 / 253.2 |
| keeper rule: strokes per word / cost on Starboard | 1.374 / 289.3 | 1.279 / 258.9 |
| all claimants marked: strokes per word / cost on Starboard | 1.952 / 338.1 | 1.609 / 286.6 |
| words with a phoneme-order violation, Stenalgo / Pluvier | 0.96% / 2.05% | 0.81% / 1.87% |
| table encoding equals a Pluvier outline (words / frequency) | 3.57% / 44.6% | 2.77% / 34.4% |

Whether a real Pluvier user loads all four files is not established (the README only says briefs are added on top of the generated dictionary); `verbs.json` overlaps `dicofr.json` on 71,794 outlines and conflicts with it on 7,644.

## Long form and short form of Stenalgo

The tables above price Stenalgo's **long form**: `plover_stenalgo_dictionary.json` alone, the theory without its abbreviation layers. Its **short form** adds the affix abbreviations (S9b, `affix_abbreviations.tsv`, 30 rules):
each word takes the cheapest of its long outline and its short outlines (fewest strokes, then cost). Run with `--stenalgo-abbreviations affix_abbreviations.tsv`. Same words (covered by both), films frequency:

| metric | Stenalgo long | Stenalgo short | Pluvier (four layers) |
|---|---|---|---|
| strokes per word | 1.479 | 1.340 | 1.220 |
| cost on Starboard | 286.5 | 277.3 | 253.8 |
| words abbreviated (share of frequency) | | 50,367 (12.26%) | |

Pluvier has the same two forms where a word owns several outlines (51.00% of the frequency, 51,101 words): its **short form** is the briefest outline (what the tables above use), its **long form** the longest (most strokes, then cheapest). They differ for 24,063 words (14.04% of frequency).

| metric | Stenalgo long | Stenalgo short | Pluvier long | Pluvier short |
|---|---|---|---|---|
| strokes per word | 1.479 | 1.340 | 1.373 | 1.220 |
| cost on Starboard | 286.5 | 277.3 | 276.8 | 253.8 |
| cost on Starboard, `S` on the cheaper pinky key | | | 275.8 | 252.6 |
| cost on Ireland | | | 276.0 | 253.2 |

Strokes per word with the extra stroke a colliding word needs for disambiguation (`withoutCollisions`; Pluvier's long form is re-checked against the claimants of its own long outlines):

| strokes per word | Stenalgo long | Stenalgo short | Pluvier long | Pluvier short |
|---|---|---|---|---|
| as listed | 1.479 | 1.340 | 1.373 | 1.220 |
| most frequent claimant keeps the outline | 1.479 | 1.340 | 1.431 | 1.279 |
| every claimant marked (upper bound) | 1.479 | 1.340 | 1.767 | 1.609 |

Stenalgo's rows do not change: no long outline and no affix outline is shared with another word (measured). With every claimant marked, Pluvier ends above Stenalgo's short form in both forms.

Fully spelled out, Pluvier is about level with Stenalgo's short form; the lead is in the briefs. Collisions are measured on the short form only.

The expression layer (phrase abbreviations, `plover_stenalgo_expressions.stenalgo`) is NOT in the short form: it maps word sequences, not a word, so it has no per-word outline to price. Pluvier's TAO briefs, by contrast, are inside its numbers.
Collision figures are unchanged (the abbreviation layer is collision-checked by its own build).

## Layers and claimants

**The four layers.** Pluvier ships its theory as several outline -> word files, not one. They are applied in priority order, lowest first, and a later file takes an outline from an earlier one:
`dicofr.json` (the generated base) < `dicofr-plural.json` (plurals) < `verbs.json` (verb forms) < `tao_la_salle_simple.json` (hand-made briefs of the most frequent words, which the generator deliberately leaves out of `dicofr.json`).
Loading `dicofr.json` alone is what understated Pluvier in the first run.

**Claimants.** An outline is *claimed* by every word that wants it. When a layer takes an outline from an earlier one, the word that loses it is still a claimant of that outline; so are all the words listed for it in `dup.json`,
the generator's record of the outlines it could not give to a single word. The *owner* is the word that finally has the outline. A word **collides** when its chosen outline has more than one claimant (reading `HRA` as `la` or `là` is the user's problem, not the dictionary's).
A claimant left with no outline at all is *lost* and counts as not covered. In the extra-stroke estimate, `winnerKeeps` lets the most frequent claimant keep the outline and marks the others, `everyClaimant` marks all of them (upper bound).
Stenalgo has no claimants by construction (measured: 0).

## Summary (four layers, films frequency)

- **Coverage.** Stenalgo 99.30% of frequency, Pluvier 93.85%; both 93.24% (108,150 spellings); Stenalgo only 6.05%, Pluvier only 0.60%. 3,467 Lexique spellings (4.5% of frequency) appear only in Pluvier's collision records or lost every outline to a higher layer
  and count as not covered.
- **Collisions** (words covered by both). Stenalgo 0 (measured). Pluvier 16,308 words (39.0% of frequency) have a chosen outline another word claims, in 16,053 groups; 13,568 sit in groups made up entirely of common words.
- **Strokes per word.** Stenalgo 1.479 long form, 1.340 short form (affix abbreviations, see above), Pluvier 1.220. If the colliding Pluvier words took one more cheap stroke (85): 1.279 when the most frequent claimant keeps the outline (7,046 words, 5.99% of frequency), 1.609 when every claimant is marked (upper bound).
- **Chord cost** (Starboard finger weights, frequency-weighted). Stenalgo 286.5. Pluvier 253.8 by the Gemini conversion to Starboard, 252.6 with the Ireland `S` on the cheaper pinky key, 253.2 on the Ireland model (`S` priced as two keys, see below).
  With the extra stroke: 258.9 (keeper rule), 286.6 (all marked: level with Stenalgo's 286.5).
- **Phoneme order.** 0.81% of Stenalgo words have a violation, 1.87% of Pluvier words. Approximate on the Pluvier side (the table encoding matches a shipped outline for 34.4% of frequency).
- **Sensitivity to the layer order.** Reversing `dicofr` and `verbs` (`verbs` < plural < `dicofr` < TAO): Pluvier coverage 92.67% (93.85%), strokes per word 1.21 (1.22), cost 251.2 (253.8), keeper rule strokes 1.271 (1.279). The conclusions do not depend on it.
- **Where the gap comes from.** Pluvier is shorter mostly on the frequent words, where its TAO briefs give one stroke (below); Stenalgo writes syllables, so a two-syllable word costs two strokes unless an expression or affix abbreviation applies.

## Why Pluvier costs more on the Starboard than on the Ireland model (revised)

**The finger assignment, validated** (`scratch/validate_ireland_fingers.py`). Each Ireland key is on the Starboard key of the same finger and row as in `Starboard._fingerAssignments` (`keyboard.py`) and in the Gemini conversion the Plover plugin uses (`GEMINI` in `export_plover_complements.py`):
T K -> keys 4 5 (left ring), P W -> 6 7 (middle), H R -> 8 9 (index), A O -> 11 12 (left thumb), E U -> 13 14 (right thumb), -F -R -> 16 17 (index), -P -B -> 18 19 (middle), -L -G -> 20 21 (ring), -T -S -D -Z -> 22 23 24 25 (right pinky, 4 keys, rows top/bottom/top/bottom).
Rows agree (even id = top row). The model and the conversion differ in two places only: the `S` (below) and the `*`, which the model puts on the left index (10), or the right index (15) when only that one is free, and the conversion always on 10.
The finger tables are the same objects, so a given key set costs the same on both boards, EXCEPT where the keyboards differ physically:
- Starboard left pinky has 4 keys (0 1 reserved, 2 3 usable); Ireland has the single tall `S`. 
- the Starboard refuses some right-pinky combinations (`-S+-D`, `-T+-Z` diagonals, any three of -T -S -D -Z); the Ireland model prices them as `pinky4keys` (325), the same as four keys.

**`S` as two keys** (the model now does what the tall-`S` variant of the report did). `S` is priced as the cheaper of the top (2) and bottom (3) left pinky key, shape terms included: with `T` it takes the top key, with `K` the bottom key (no zig-zag); `S`+`P`/`W` keeps a one-column gap (+100) on either row.
The earlier Ireland model exempted `S` from the shape terms altogether, which was too generous (the gap to P/W is charged to every other column skip). Result, same Pluvier outlines (four layers, words covered by both):

| Pricing | Mean cost |
|---|---|
| Gemini conversion on Starboard (`S` on the bottom pinky key) | 253.84 |
| Starboard, `S` on the cheaper pinky key (2 or 3) | 252.64 |
| Ireland model, `S` as two keys (revised; was 250.35 with `S` exempt from shape terms) | 253.19 |
| the 106,294 words priced on BOTH: Starboard cheaper-`S` / Ireland | 252.64 / 252.71 |

On the words both boards can price, the two prices agree within 0.07: the whole gap is the treatment of `S`, plus which chords can be priced (below).

**The unpressable share** (`scratch/analyze_unpressable.py`): 1.24% of Pluvier's frequency (1,959 words) has a chosen outline with a chord the Starboard cannot press, and 0.99% of it is unpriced on Ireland too, so it is not a Starboard limit at all:

| cause | frequency share | on Ireland |
|---|---|---|
| an EMPTY first stroke: `ai` is `/-S`, `aient` `/AEUPBT` in `dicofr.json` (a generator artifact: Plover would not accept an empty stroke; `ai` alone is 0.87%) | 0.869% | unpriced |
| chord text with keys out of steno order (`AEBLDS`, `EDS`, `ADS`, `PHS`: `-DS` for `-SD`) | 0.126% | unpriced |
| right pinky, `-S` + `-D` (diagonal; `laissez` is `HRAEUSD`) | 0.133% | priced 325 (`pinky4keys`) |
| right pinky, `-T` + `-S` + `-Z` (`poutres` is `POUTSZ`, `O*ETSZ`) | 0.103% | priced 325 |
| right pinky, `-T` + `-Z` (diagonal; `-TZ` in `-ATIZ` verbs) | 0.003% | priced 325 |
| `-T` + `-S` + `-D` | 0.000% | priced 325 |

So the real Starboard limit is 0.24% of frequency: three right-pinky shapes that Pluvier uses for `-SD` (`-ez` verbs), `-TSZ` and `-TZ`. These words are dropped from the Starboard mean (and the Ireland mean keeps them at 325 on the pinky), which is what the "pressable in both" rows remove.
Nothing was done about the 0.99% of artifacts; they lower Pluvier's coverage in both columns.

## Top 200 words by film frequency (`scratch/compare_top_words.py`)

43 of the 200 need fewer strokes in Pluvier (8.5% of the top-200 frequency mass), 134 the same number, 4 fewer in Stenalgo; 16 are covered by Stenalgo only and 3 by Pluvier only (not compared).
With `dicofr.json` alone the figures were 18 / 124 / 5 / 50 / 3. The 3 Pluvier-only words are the multi-word spellings `est-ce que`, `peut-être`, `parce que` (Stenalgo's dictionary holds single words; phrases are the expression layer's job).
The 16 Stenalgo-only words are mostly in Pluvier's collision record (`l'`, `t'`, `suis`, `veux`, `peu`, `viens`, `crois`, `dois`, `voilà`, `vois`, `nom`: every outline lost to another word) or have no entry (`tous`, `ces`, `autre`, `ans`, `faites`).
Several Pluvier outlines of the shorter words are in its collision record too (marked `[COLLIDES]`): there the gap closes if the words must be disambiguated.

```
{'pluvier fewer': 43, 'equal': 134, 'stenalgo fewer': 4, 'only stenalgo': 16, 'only pluvier': 3, 'neither': 0} total 200
rank word freq | stenalgo (strokes) | pluvier (strokes) [collides in Pluvier?]
 45 avec              3704.9 | a/viek (2) | W- (1)
 53 ils               3075.1 | il/-s (2) | KWR* (1)
 57 était             2707.6 | e/tie (2) | ETS (1)
 63 ici               2411.8 | i/si (2) | EURB (1)
 64 es                2388.4 | ie/-d (2) | AEU (1) [COLLIDES]
 71 pourquoi          2005.2 | p@eR/kwa (2) | PROEUBG (1)
 77 avez              1784.2 | a/ve (2) | WE (1)
 79 alors             1777.7 | a/mteR (2) | AORL (1)
 82 peux              1743.8 | p@ie/-d (2) | PAO* (1)
 83 comment           1649.3 | kae/m@ (2) | KPHA (1)
 90 allez             1414.8 | a/mte/-d (3) | HR/*EZ (2)
 91 aussi             1402.3 | ae/si (2) | ORB (1) [COLLIDES]
 93 fais              1390.9 | kpie/-d (2) | TPAEU (1) [COLLIDES]
 94 jamais            1360.2 | vta/mie (2) | SKWRAPL (1)
 98 merci             1314.5 | mieR/si (2) | PH-RB (1)
109 été               1127.7 | e/te (2) | ET (1)
110 maintenant        1124.5 | maie/t@a/mR@ (3) | PHEUT (1) [COLLIDES]
112 avoir             1081.2 | a/vwaR (2) | AFRS (1)
113 toujours          1072.4 | t@e/vt@eR (2) | TOUG (1)
115 dis               1025.8 | pvi/-d (2) | EUD (1) [COLLIDES]
117 vas               1009.2 | va/-s (2) | WA* (1)
122 vraiment           968.6 | vRie/m@ (2) | WRAEUPLT (1)
136 aux                835.6 | ae/-s (2) | O*EBGS (1) [COLLIDES]
138 aller              834.0 | a/mt*e (2) | HR-R (1)
142 après              787.6 | a/pRie (2) | APG (1)
144 avant              785.6 | a/v@ (2) | AFG (1) [COLLIDES]
145 avais              785.4 | a/vie/-d (3) | AF/AEUS (2)
147 personne           768.6 | pieR/sen (2) | P-RB (1)
148 accord             761.8 | a/keR (2) | A*BG (1)
149 besoin             758.0 | sv@a/twaie (2) | PWOEUPB (1)
156 petit              717.7 | p@a/ti (2) | TEU (1)
160 déjà               692.7 | pve/vta (2) | TKEG (1)
168 sera               637.4 | s@a/Ra (2) | SRA (1)
171 depuis             631.1 | pv@a/p@ai (2) | TKEP (1)
172 quelqu'un          629.0 | kiel/k@aie (2) | KWU (1)
174 beaucoup           626.0 | svae/k@e (2) | PWOEBG (1)
178 monsieur           583.5 | m@a/sRw@ie (2) | -RPL (1)
180 maison             570.3 | mie/twai (2) | PH-Z (1)
181 bonjour            569.9 | svai/vt@eR (2) | PW-G (1)
186 voulez             553.4 | v@e/mte (2) | WOULD (1)
191 maman              537.4 | ma/m@ (2) | PHAPLT (1)
194 avons              529.5 | a/vai (2) | WO* (1)
196 arrive             525.1 | a/Rijs (2) | AFRB (1) [COLLIDES]
frequency mass of the pluvier-fewer words / top200: 0.085
--- only Pluvier:
106 est-ce que 1159.4 -BG ['-BG', 'AEUS/K']
127 peut-être 907.7 -PT ['-PT', '-PTS', 'PAOT/AEUTS']
189 parce que 548.6 PARS/K ['PARS/K']
--- only Stenalgo (first 50):
15 l' 11393.3 mt- in dup record
35 t' 4344.2 t- in dup record
43 suis 3760.6 s@ai in dup record
61 veux 2486.9 v@ie/-d in dup record
99 tous 1287.0 t@es 
103 ces 1222.5 sie 
107 autre 1148.1 aetR 
108 peu 1145.8 p*@ie in dup record
125 viens 944.8 vRwaie/-d in dup record
128 crois 904.5 kRwa/-d in dup record
131 dois 894.7 pvwa/-d in dup record
154 voilà 726.4 vwa/mta in dup record
155 ans 718.2 *@/-s 
162 vois 689.8 vwa/-d in dup record
190 faites 542.0 kpiet/-s 
195 nom 528.2 mR*ai in dup record
```

## Full report of the run (`theory_comparison.md`, films frequency, four layers)


Frequency: films; Pluvier commit 47ab823; Pluvier layers (lowest priority first): dicofr.json, dicofr-plural.json, verbs.json, tao_la_salle_simple.json.

### Coverage (Lexique383 spellings)

| set | spellings | with frequency | frequency share |
|---|---|---|---|
| universe | 125655 | 95092 | 100.00% |
| stenalgo | 119232 | 91518 | 99.30% |
| pluvier | 113707 | 86794 | 93.85% |
| both | 108150 | 83722 | 93.24% |
| stenalgoOnly | 11082 | 7796 | 6.05% |
| pluvierOnly | 5557 | 3072 | 0.60% |
| neither | 866 | 502 | 0.10% |

### Collisions on the words covered by both

| | stenalgo | pluvier |
|---|---|---|
| words colliding | 0 | 16308 |
| frequency share | 0.00% | 38.97% |
| groups | 0 | 16053 |
| words in groups fully common | 0 | 13568 |

### Strokes, complexity and phoneme order on the words covered by both

| metric | stenalgo | pluvier |
|---|---|---|
| strokes per word | 1.479 | 1.220 |
| cost on Starboard | 286.521 | 253.837 |
| unpressable on Starboard (freq share) | 0.02% | 1.24% |
| cost on Starboard, pressable in both (105782 words) | 286.665 | 253.766 |
| cost on Starboard, Ireland `S` on the cheaper pinky key | | 252.641 |
| cost on Ireland | | 253.186 |

### If every colliding word took one more stroke (cheapest single key: 85 on Starboard, 85 on Ireland)

| metric | stenalgo | pluvier |
|---|---|---|
| *most frequent claimant keeps the outline* | | |
| words given a stroke | 0 | 7046 (5.99% of frequency) |
| strokes per word | 1.479 | 1.279 |
| cost on Starboard | 286.521 | 258.939 |
| cost on Starboard, Ireland `S` on the cheaper pinky key | | 257.743 |
| cost on Ireland | | 258.332 |
| *every claimant marked* | | |
| words given a stroke | 0 | 16308 (38.97% of frequency) |
| strokes per word | 1.479 | 1.609 |
| cost on Starboard | 286.521 | 286.559 |
| cost on Starboard, Ireland `S` on the cheaper pinky key | | 285.364 |
| cost on Ireland | | 285.897 |

### Phoneme order

| metric | stenalgo | pluvier |
|---|---|---|
| words with a phoneme order violation | 0.81% | 1.87% |
| mean violations per word | 0.008 | 0.019 |
| unencodable words (freq share) | 0.00% | 0.69% |

Pluvier table encoding equals one of the word's Pluvier outlines for 2.77% of its words (34.38% of frequency).


## Caveats

- Layer priority and the set of files are assumptions (see above); the layer order matters little, the choice of files a lot.
- `verbs.json` has 21,189 values with a space (`tu es`): they are outside the Lexique universe and count as `outsideUniverse`, not as coverage.
- The Ireland finger assignment (left pinky S; ring T K; middle P W; index H R *; thumbs A O / E U; right index -F -R *; middle -P -B; ring -L -G; pinky -T -S -D -Z) is the standard one, not validated.
- Costs are Starboard's finger weights applied to both layouts; they are not an ergonomic measurement of Ireland.
- Pluvier outlines are the cheapest by Starboard cost, a user's actual choice may differ; outlines containing chords that are not valid Ireland chords (188 in `dicofr.json` alone) are unpriced.
- Stenalgo's order violations are those of the ideal layout encoding of the phonology, not of the shipped outlines.
- The long form is Stenalgo WITHOUT its abbreviation layers, while Pluvier includes its briefs; the short form adds the affix abbreviations but not the expression layer (phrases), so the gap is still overstated a little.
- Not done: the CP-SAT score of each theory+layout; a `*`-mark resolution of collisions; the words that lost every Pluvier outline given an extra stroke.

## Reproduce

```bash
P=/home/jfsp/Steno/Pluvier/resources
python -m util.compare_theories --pluvier-dict $P/dicofr.json --pluvier-dict $P/dicofr-plural.json \
    --pluvier-dict $P/verbs.json --pluvier-dict $P/tao_la_salle_simple.json --pluvier-dup $P/dup.json --out /some/dir
python scratch/compare_top_words.py
python scratch/compare_s_key_gap.py
```
