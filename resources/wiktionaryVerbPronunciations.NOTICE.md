# wiktionaryVerbPronunciations.tsv: attribution

`wiktionaryVerbPronunciations.tsv` holds the **IPA pronunciations of the conjugated forms that `LexiqueMixte.tsv` lacks** (the forms the
Synthetic lexicon generates), as printed on the French Wiktionary conjugation pages (`https://fr.wiktionary.org/wiki/Conjugaison:français/<verbe>`) for the verbs of
`LexiqueMixte.tsv`. It was fetched once, on 2026-10-08, by `python -m util.fetch_wiktionary_conjugations` (REST HTML endpoint,
one request every 0.25 s, user agent naming this project) so that checks against it need no network. Columns: lemma, spelling,
the lexicon's `infover` tags (`;`-separated: `ind:pre:1s`, `cnd:pre:3p`, `imp:pre:2s`, `inf`, `par:pre`, `par:pas:ms` ...), IPA with
syllable dots. Lemmas without a usable page are listed in `wiktionaryVerbPronunciations.missing.txt`.

The text of **Wiktionnaire** (fr.wiktionary.org) is published under the **Creative Commons Attribution-ShareAlike 4.0** licence
(https://creativecommons.org/licenses/by-sa/4.0/), by the Wiktionnaire contributors; the authors of a page are listed in its history.
This file is a derivative of that content and is shared under the same licence: if you redistribute it, keep this notice,
credit "Wiktionnaire contributors", link the licence, and share changes under CC BY-SA 4.0. Please check the licence terms
before relying on this summary.

Not used for anything the licence would make awkward: the file feeds `util/check_against_wiktionary.py` (a diagnostic) only;
nothing in the generated lexicon, theory or exports is copied from it.
