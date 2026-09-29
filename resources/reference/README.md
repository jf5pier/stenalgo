# External references for the affix work

Local copies (fetched 2026-09-29) so comparisons stay reproducible offline.

| file | source | what it is |
|---|---|---|
| `Pluvier_TAO_rules.md` | https://github.com/Vermoot/Pluvier/blob/main/TAO_rules.md (raw) | Pluvier's lesson-by-lesson extraction of the TAO (Québec court-reporter steno) rules. Only the *abbreviation* rules matter to us (affix/ending briefs: `-GS` tion, `-FT` vité/cité, `AER` ier, `KOEN` con-, `MULT` multi-, `INTS` inter-, ...), not the phonology/keys. Machine-readable subset: `resources/affixSeeds.tsv`. |
| `oqlf_prefixes_suffixes.html` | https://www.oqlf.gouv.qc.ca/prix-concours/creativite-lexicale/contenu-pedagogique/tableau-prefixes-suffixes.aspx | OQLF table of productive French prefixes (27) and suffixes (17). Needs a browser User-Agent to download (plain curl gets 403). |
| `oqlf_affixes.tsv` | extracted from the HTML above | position / affix / meaning. |

## Standing practice

Every affix-selection run is compared against both lists, and each affix that is *not* proposed
gets a stated reason (no anchor / grown-only node / conflicts or exception rate / pseudo-affix
attestedShare / frequency too low for the budget / already inside another rule's form).
Generator: `scratch/affix_reference_diff.py` -> `scratch/affix-reference-diff.md`
(reads `scratch/affix-candidates.tsv` and `scratch/affix-sweep/{L,M,H}/affix-rules.tsv`).
Note the TAO list is a reference for *which endings deserve a brief*, not for its key choices.
