import gzip

from util.build_spelling_variants import (
    SEED_VARIANT_SETS,
    discoverVariantSets,
    isNearVariantSpelling,
    matchSingleEditPattern,
    resolveSets,
    singleEditVariants,
)


def row(ortho, phon, lemme, cgram="VER", freqlivres="0.0"):
    return {"ortho": ortho, "phon": phon, "lemme": lemme, "cgram": cgram,
            "freqlivres": freqlivres}


class TestMatchSingleEditPattern:
    def test_circumflex_drop(self):
        assert matchSingleEditPattern("dessoûler", "dessouler") == "û->u"

    def test_geminate_simplification(self):
        assert matchSingleEditPattern("trimballer", "trimbaler") is not None
        assert matchSingleEditPattern("trimbaler", "trimballer") is not None

    def test_accent_grave_one_way(self):
        assert matchSingleEditPattern("événement", "évènement") == "é->è"
        # è->é is NOT in the family (the one-way rule).
        assert matchSingleEditPattern("évènement", "événement") is None

    def test_vowel_cluster(self):
        assert matchSingleEditPattern("saouler", "soûler") == "aou->oû"

    def test_y_to_i(self):
        assert matchSingleEditPattern("zyeuter", "zieuter") == "y->i"

    def test_sch(self):
        assert matchSingleEditPattern("schlinguer", "chlinguer") is not None

    def test_qu_to_c(self):
        assert matchSingleEditPattern("toquade", "tocade") == "qu->c"
        # c->qu is one-way: refused.
        assert matchSingleEditPattern("tocade", "toquade") is None

    def test_dessaouler_family_never_joins_saouler_family(self):
        # One single pattern application cannot bridge the two families.
        assert matchSingleEditPattern("dessaouler", "saouler") is None
        assert matchSingleEditPattern("dessouler", "soûler") is None

    def test_unrelated_words(self):
        assert matchSingleEditPattern("ver", "vert") is None
        assert matchSingleEditPattern("saint", "sain") is None
        assert matchSingleEditPattern("boîte", "boite") == "î->i"

    def test_too_far_apart(self):
        assert matchSingleEditPattern("a", "abcdefgh") is None


class TestSingleEditVariants:
    def test_geminate_both_directions(self):
        variants = singleEditVariants("trimbaler")
        assert "trimballer" in variants

    def test_near_variant_of_lexicon(self):
        lexicon = {"trimballer", "événementiel"}
        assert isNearVariantSpelling("trimbaler", lexicon)
        assert isNearVariantSpelling("évènementiel", lexicon)
        assert not isNearVariantSpelling("chien", lexicon)


class TestDiscoverVariantSets:
    EMPTY_REFORM = [dict(oldSpelling="", newSpelling="", isException="False")]

    def test_same_phon_cgram_pair_discovered(self):
        rows = [
            row("trimballer", "tR5bale", "trimballer"),
            row("trimbaler", "tR5bale", "trimbaler"),
            # Same edit pattern but different phonology: NOT a variant.
            row("vallader", "valad", "vallader"),
            row("valader", "valadE", "valader"),
        ]
        sets, rejected = discoverVariantSets(
            rows, excludedWords=set(), exceptionSpellings=set(),
            reformRows=self.EMPTY_REFORM)
        assert rejected == []
        assert frozenset({"trimballer", "trimbaler"}) in sets
        assert not any("vallader" in s for s in sets)

    def test_different_cgram_not_paired(self):
        rows = [
            row("cassade", "kasad", "cassade", cgram="NOM"),
            row("casade", "kasad", "casade", cgram="VER"),
        ]
        sets, _ = discoverVariantSets(
            rows, excludedWords=set(), exceptionSpellings=set(),
            reformRows=self.EMPTY_REFORM)
        # The seeds are always present; the fixture pair must not be.
        assert not any("cassade" in s for s in sets)

    def test_excluded_and_exception_words_never_paired(self):
        rows = [
            row("cassade", "kasad", "cassade", cgram="NOM"),
            row("casade", "kasad", "casade", cgram="NOM"),
        ]
        sets, _ = discoverVariantSets(
            rows, excludedWords={"casade"}, exceptionSpellings=set(),
            reformRows=self.EMPTY_REFORM)
        assert not any("casade" in s for s in sets)
        sets, _ = discoverVariantSets(
            rows, excludedWords=set(), exceptionSpellings={"casade"},
            reformRows=self.EMPTY_REFORM)
        assert not any("casade" in s for s in sets)

    def test_reform_rows_union(self):
        reform = [dict(oldSpelling="boîte", newSpelling="boite",
                       isException="False")]
        sets, _ = discoverVariantSets(
            [], excludedWords=set(), exceptionSpellings=set(),
            reformRows=reform)
        assert frozenset({"boîte", "boite"}) in sets

    def test_seed_sets_always_present(self):
        sets, rejected = discoverVariantSets(
            [], excludedWords=set(), exceptionSpellings=set(),
            reformRows=self.EMPTY_REFORM)
        for seed in SEED_VARIANT_SETS:
            assert seed in sets
        assert rejected == []

    def test_seed_blocked_by_guards_reported_not_dropped(self):
        # trimbaler excluded -> the empirical guard refuses the pair, but the
        # seed is known truth: it must still come back in one set.
        rows = [row("trimballer", "tR5bale", "trimballer"),
                row("trimbaler", "tR5bale", "trimbaler")]
        sets, rejected = discoverVariantSets(
            rows, excludedWords={"trimbaler"}, exceptionSpellings=set(),
            reformRows=self.EMPTY_REFORM)
        assert frozenset({"trimballer", "trimbaler"}) in sets
        assert rejected == []


class TestResolveSets:
    def test_highest_ngram_mass_wins(self):
        # trimballer/trimbaler is a SEED set: curated truth, auto-activates.
        sets = [frozenset({"trimbaler", "trimballer"})]
        rows = [row("trimballer", "tR5bale", "trimballer"),
                row("trimballe", "tR5bal", "trimballer"),
                row("trimbaler", "tR5bale", "trimbaler")]
        counts = {"trimballer": 181, "trimbaler": 78, "trimballe": 40}
        decision = resolveSets(sets, rows, counts)[0]
        assert decision["canonical"] == "trimballer"
        assert decision["dropLemmes"] == "trimbaler"
        assert decision["status"] == "active"
        assert decision["source"] == "seed"
        # The canonical mass includes the inflected forms of its lemma.
        assert decision["ngramCanonical"] == "221"

    def test_discovered_sets_never_auto_activate(self):
        # tache/tâche: distinct words sharing phon + cgram with lopsided
        # counts -- the pattern family cannot tell them apart, so a
        # discovered set must always land in review, never 'active'.
        sets = [frozenset({"tache", "tâche"})]
        decision = resolveSets(sets, [], {"tâche": 4855964, "tache": 1451182})[0]
        assert decision["source"] == "discovered"
        assert decision["status"] == "review"

    def test_close_call_flagged_for_review(self):
        sets = [frozenset({"trimbaler", "trimballer"})]
        rows = [row("trimballer", "tR5bale", "trimballer")]
        decision = resolveSets(sets, rows,
                               {"trimballer": 100, "trimbaler": 60})[0]
        assert decision["status"] == "review"

    def test_sparse_data_flagged_for_review(self):
        sets = [frozenset({"zyeuter", "zieuter"})]
        decision = resolveSets(sets, [], {"zieuter": 40, "zyeuter": 2})[0]
        assert decision["status"] == "review"
