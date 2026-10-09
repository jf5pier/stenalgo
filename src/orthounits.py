"""
The marker units of `orthosyll_cv` that are not letters of the spelling.

`syll_cv` and `orthosyll_cv` pair unit for unit (util/check_lexicon_features.py, check `units`). Two kinds of unit have no
letters of their own:

- `#` is a silent *sound*: the sounded side of a pair whose letters make no sound (`syll_cv` side only).
- `=` is a *repeated letter*: one letter carrying two sounds across a syllable break (`cria` `k_R_i|j_a` is spelled
  `c_r_i|=_a`: the `i` is the vowel, and `=` stands for the same `i` as the glide that opens the next syllable). It sits on the
  `orthosyll_cv` side only and adds nothing to the spelling.

`=` was chosen because it is inert in sed/awk replacement strings, regexes, TSV, JSON and HTML, and occurs nowhere in
Lexique383, the Infra correspondence, Mixte or Synthetic before the glide rule (src/mixterules.py).
"""

REPEAT = "="
SILENT = "#"


def spellingOf(orthosyllCV: str) -> str:
    """The spelling an `orthosyll_cv` string spells: the separators, the silent marks and the repeat marks removed."""
    return orthosyllCV.replace("|", "").replace("_", "").replace(SILENT, "").replace(REPEAT, "")


def stripMarks(unitsText: str) -> str:
    """`unitsText` (letters joined from units, as the syllable spellings of Word) without the silent and repeat marks."""
    return unitsText.replace(SILENT, "").replace(REPEAT, "")
