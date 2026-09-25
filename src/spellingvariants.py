# Spelling-variant drop lists, loaded from resources/spellingVariants.tsv
# (built by util/build_spelling_variants.py, arbitrated by Google Books Ngram
# frequencies in resources/LexiqueGoogleNgram.tsv).
#
# One canonical spelling is kept per variant set of the same word; the other
# spellings are dropped from the whole pipeline:
#   - lexique.py Lexique.read_corpus runs every corpus lemme through
#     reconcileLemme against the 1990-reform lemme normalization (the
#     non-canonical paradigm never reaches LexiqueMixte.tsv; a canonical on
#     the old side of a reform pair suppresses the normalization instead),
#     and Lexique.outputMixedLexique runs every output spelling through
#     reconcileOutputOrtho against the 1990-reform rewrite chain (the
#     canonical spelling may be either side of a reform pair, so the rewrite
#     must be overridable in BOTH directions, from one place);
#   - dictionary.py Dictionary.readCorpus (the single load choke point for
#     LexiqueMixte.tsv AND LexiqueSynthetic.tsv, through which the S2
#     appenders also read) skips rows with a dropped lemme or ortho, so stale
#     synthetic rows are invisible and dropped forms cannot be regenerated.
#
# Rows with status "review" (numbers could not settle the canonical choice)
# and "veto" (a human decided the spellings are genuinely distinct words)
# are recorded but never enforced. A missing file enforces nothing.
import csv
from dataclasses import dataclass, field, replace

SPELLING_VARIANTS_TSV = "resources/spellingVariants.tsv"


@dataclass(frozen=True)
class SpellingVariantDrops:
    """Lemmes and orthos to drop: the non-canonical spellings of every
    ACTIVE variant set of resources/spellingVariants.tsv, plus the kept
    canonical spellings themselves (needed to reconcile lemme normalization
    against the 1990-reform rewrite: a canonical on the OLD side of a pair
    must suppress the normalization, not be dropped by it)."""
    dropLemmes: frozenset[str]
    dropOrthos: frozenset[str]
    canonicals: frozenset[str]
    # dropOrtho -> canonicals of the active sets dropping it (per-set info
    # the flattened sets above lose).
    dropOrthoCanonicals: dict[str, frozenset[str]] = field(default_factory=dict)
    # canonical -> lemmes of corpus rows spelled with it, filled at runtime
    # by withCanonicalCarriers() (the corpus, not the TSV, knows that
    # "absous" is a form of lemme "absoudre" while "boîte" is its own lemme).
    canonicalCarriers: dict[str, frozenset[str]] = field(default_factory=dict)

    def withCanonicalCarriers(
            self, carriers: dict[str, frozenset[str]]) -> "SpellingVariantDrops":
        return replace(self, canonicalCarriers=carriers)

    def isDroppedLemme(self, lemme: str) -> bool:
        return lemme in self.dropLemmes

    def isDroppedOrtho(self, ortho: str) -> bool:
        return ortho in self.dropOrthos

    def isDroppedOrthoRow(self, ortho: str, lemme: str, gramCat: str,
                          rewritten: bool = False) -> bool:
        """Whether a corpus ROW spelled `ortho` (lemme `lemme`, category
        `gramCat`) is a dropped spelling-variant row.

        `rewritten` says whether this spelling is the product of the
        1990-reform rewrite chain (pre != post in reconcileOutputOrtho); rows
        read back from LexiqueMixte/LexiqueSynthetic are final, so callers
        there pass the default (False = native spelling).

        A dropped variant spelling can coincide with a conjugated form of a
        DIFFERENT, kept verb (e.g. "boite", dropped as the noun variant of
        "boîte", is also the subjonctif of "boiter"; "fritte" of "fritter").
        Such a native VER row is exempt UNLESS its lemme carries the set's
        own canonical -- "absout" under lemme "absoudre" (which carries
        "absous") is the same verb's variant spelling and still drops. A
        spelling the rewrite chain PRODUCED belongs to the pair's own family
        and drops unconditionally (driving the restore to the canonical); so
        does every non-VER row (plural/carrying-lemma cases like
        "barmans"/"barman" rely on it)."""
        if ortho not in self.dropOrthos:
            return False
        if lemme in self.dropLemmes:
            return True
        if rewritten:
            return True
        if gramCat == "VER":
            for canonical in self.dropOrthoCanonicals.get(ortho, ()):
                if lemme == canonical or lemme in self.canonicalCarriers.get(
                        canonical, ()):
                    return True
            return False
        return True

    def reconcileLemme(self, raw: str, normalized: str) -> str | None:
        """Reconciles a word's lemme after 1990-reform normalization
        (lexique.py read_corpus) against the drop lists.

        `raw` is the lemme before normalization, `normalized` after it.
        Returns the lemme to keep, or None to drop the row entirely:
          normalized kept            -> normalized
          normalized dropped, raw is
          a canonical spelling       -> raw        # suppress the normalization
          otherwise                  -> None       # non-canonical paradigm
        """
        if not self.isDroppedLemme(normalized):
            return normalized
        if raw in self.canonicals:
            return raw
        return None


EMPTY_DROPS = SpellingVariantDrops(frozenset(), frozenset(), frozenset())


def loadSpellingVariantDrops(
        tsvPath: str = SPELLING_VARIANTS_TSV) -> SpellingVariantDrops:
    """Active rows only; 'review' and 'veto' rows stay on record but enforce
    nothing. A missing or empty file is not an error (EMPTY_DROPS)."""
    dropLemmes: set[str] = set()
    dropOrthos: set[str] = set()
    canonicals: set[str] = set()
    dropOrthoCanonicals: dict[str, set[str]] = {}
    try:
        with open(tsvPath, newline="", encoding="utf-8") as f:
            rows = [line.rstrip("\n") for line in f
                    if not line.startswith("#")]
    except FileNotFoundError:
        return EMPTY_DROPS
    for row in csv.DictReader(rows, delimiter="\t"):
        if row.get("status") != "active":
            continue
        dropLemmes.update(row["dropLemmes"].split())
        canonical = row.get("canonical", "")
        for ortho in row["dropOrthos"].split():
            dropOrthoCanonicals.setdefault(ortho, set()).add(canonical)
            dropOrthos.add(ortho)
        if canonical:
            canonicals.add(canonical)
    return SpellingVariantDrops(
        frozenset(dropLemmes), frozenset(dropOrthos), frozenset(canonicals),
        {ortho: frozenset(cs) for ortho, cs in dropOrthoCanonicals.items()})


def reconcileOutputOrtho(pre: str, post: str,
                         drops: SpellingVariantDrops,
                         lemme: str = "", gramCat: str = "") -> tuple[str, bool] | None:
    """Reconciles a word's output spelling after the 1990-reform rewrite
    chain (lexique.py outputMixedLexique) against the drop lists.

    `pre` is the spelling before the chain, `post` the spelling after it;
    `lemme`/`gramCat` identify the row for isDroppedOrthoRow's kept-verb
    exemption (`rewritten` there = pre != post). Returns (spelling,
    rewritten?) or None to drop the row:
      post kept               -> (post, True)
      post dropped, pre kept  -> (pre, False)   # suppress the rewrite
      both dropped            -> None           # drop the row
    """
    postDropped = drops.isDroppedOrthoRow(post, lemme, gramCat,
                                          rewritten=(pre != post))
    preDropped = drops.isDroppedOrthoRow(pre, lemme, gramCat)
    if postDropped and preDropped:
        return None
    if postDropped:
        return (pre, False)
    return (post, True)
