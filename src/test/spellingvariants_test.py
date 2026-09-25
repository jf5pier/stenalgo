import pytest

from src.spellingvariants import (
    EMPTY_DROPS,
    SpellingVariantDrops,
    loadSpellingVariantDrops,
    reconcileOutputOrtho,
)


class TestLoadSpellingVariantDrops:
    def test_active_rows_enforced(self, tmp_path):
        tsv = tmp_path / "spellingVariants.tsv"
        tsv.write_text(
            "# comment\n"
            "setId\tcanonical\tdropLemmes\tdropOrthos\tstatus\n"
            "trimballer\ttrimballer\ttrimbaler\ttrimbaler\tactive\n"
            "beluga\tbéluga\tbeluga\tbeluga belugas\tactive\n",
            encoding="utf-8")
        drops = loadSpellingVariantDrops(str(tsv))
        assert drops.dropLemmes == frozenset({"trimbaler", "beluga"})
        assert drops.dropOrthos == frozenset({"trimbaler", "beluga", "belugas"})
        assert drops.canonicals == frozenset({"trimballer", "béluga"})

    def test_review_and_veto_rows_not_enforced(self, tmp_path):
        tsv = tmp_path / "spellingVariants.tsv"
        tsv.write_text(
            "setId\tcanonical\tdropLemmes\tdropOrthos\tstatus\n"
            "a\ta\tb\tb\treview\n"
            "c\tc\td\td\tveto\n",
            encoding="utf-8")
        assert loadSpellingVariantDrops(str(tsv)) == EMPTY_DROPS

    def test_missing_file_is_empty(self, tmp_path):
        assert loadSpellingVariantDrops(
            str(tmp_path / "absent.tsv")) == EMPTY_DROPS

    def test_empty_drop_cells_are_fine(self, tmp_path):
        tsv = tmp_path / "spellingVariants.tsv"
        tsv.write_text(
            "setId\tcanonical\tdropLemmes\tdropOrthos\tstatus\n"
            "a\ta\t\t\tactive\n",
            encoding="utf-8")
        drops = loadSpellingVariantDrops(str(tsv))
        assert drops.dropLemmes == frozenset()
        assert drops.dropOrthos == frozenset()
        assert drops.canonicals == frozenset({"a"})


class TestReconcileOutputOrtho:
    drops = SpellingVariantDrops(frozenset({"évènement"}),
                                 frozenset({"évènement", "évènements"}),
                                 frozenset({"événement"}))

    def test_post_kept(self):
        # No dropped spelling involved: the rewrite stands.
        assert reconcileOutputOrtho(
            "événement", "évènement", EMPTY_DROPS) == ("évènement", True)

    def test_post_dropped_pre_kept_suppresses_rewrite(self):
        # Canonical is the OLD spelling: the 1990 rewrite that produced the
        # new one must be overridden, falling back to the pre-rewrite form.
        assert reconcileOutputOrtho(
            "événement", "évènement", self.drops) == ("événement", False)

    def test_post_kept_pre_dropped(self):
        assert reconcileOutputOrtho(
            "évènements", "événements", self.drops) == ("événements", True)

    def test_both_dropped_drops_the_row(self):
        assert reconcileOutputOrtho(
            "évènement", "évènements", self.drops) is None

    def test_identity_untouched(self):
        assert reconcileOutputOrtho(
            "chien", "chien", self.drops) == ("chien", True)


class TestKeptVerbOrthoExemption:
    """A dropped variant spelling may coincide with a conjugated form of a
    DIFFERENT, kept verb (boite: noun variant of boîte AND subjonctif of
    boiter) -- the ortho drop must not eat the verb's rows."""

    drops = SpellingVariantDrops(frozenset({"boite"}),
                                 frozenset({"boite", "boites"}),
                                 frozenset({"boîte"}))

    def test_kept_verb_form_survives(self):
        # (pre == post: no rewrite fired for the verb row in the first place)
        assert reconcileOutputOrtho(
            "boite", "boite", self.drops, "boiter", "VER") == ("boite", True)

    def test_variant_verb_row_still_dies(self):
        # A verb row of the variant paradigm itself carries the dropped lemme.
        assert reconcileOutputOrtho(
            "boites", "boites", self.drops, "boite", "VER") is None

    def test_noun_restore_unchanged(self):
        assert reconcileOutputOrtho(
            "boîte", "boite", self.drops, "boîte", "NOM") == ("boîte", False)

    def test_isDroppedOrthoRow(self):
        assert self.drops.isDroppedOrthoRow("boite", "boiter", "VER") is False
        assert self.drops.isDroppedOrthoRow("boite", "boite", "VER") is True
        assert self.drops.isDroppedOrthoRow("boite", "boîte", "NOM") is True
        assert self.drops.isDroppedOrthoRow("boite", "boiter", "NOM") is True
        assert self.drops.isDroppedOrthoRow("chien", "chien", "NOM") is False

    def test_rewritten_verb_form_still_drops(self):
        # absous -> absout under lemme absoudre: the rewrite produced the
        # dropped spelling, so the row belongs to the pair's family and the
        # drop applies (driving the restore to the canonical "absous").
        drops = SpellingVariantDrops(frozenset(),
                                     frozenset({"absout"}),
                                     frozenset({"absous"}))
        assert drops.isDroppedOrthoRow("absout", "absoudre", "VER",
                                       rewritten=True) is True
        assert reconcileOutputOrtho(
            "absous", "absout", drops, "absoudre", "VER") == ("absous", False)

    def test_native_kept_verb_form_survives_reconcile(self):
        # No rewrite fired (pre == post): native "boite" of boiter stays.
        assert reconcileOutputOrtho(
            "boite", "boite", self.drops, "boiter", "VER") == ("boite", True)

    def test_same_paradigm_native_variant_still_drops(self):
        # Native "absout" under lemme "absoudre": absoudre CARRIES the set's
        # canonical "absous", so this is the same verb's variant spelling --
        # the drop applies even though no rewrite fired for the native row.
        drops = SpellingVariantDrops(
            frozenset(), frozenset({"absout"}), frozenset({"absous"}),
            {"absout": frozenset({"absous"})}).withCanonicalCarriers(
                {"absous": frozenset({"absoudre"})})
        assert drops.isDroppedOrthoRow("absout", "absoudre", "VER") is True
        assert drops.isDroppedOrthoRow("absout", "absoudre", "VER",
                                       rewritten=True) is True
        # Without carrier data the exemption defaults to keeping -- callers
        # that can't know the carriers stay permissive.
        assert drops.isDroppedOrthoRow("boite", "boiter", "VER") is False


class TestReconcileLemme:
    drops = SpellingVariantDrops(frozenset({"ognon"}),
                                 frozenset({"ognon", "ognons"}),
                                 frozenset({"oignon"}))

    def test_normalized_kept(self):
        # No dropped lemme involved: the normalization stands.
        assert self.drops.reconcileLemme("chien", "chien") == "chien"

    def test_normalized_dropped_raw_canonical_suppresses_normalization(self):
        # Canonical is the OLD side of the reform pair (oignon/ognon): the
        # normalization to the dropped new spelling must be suppressed, not
        # take the whole paradigm down with it.
        assert self.drops.reconcileLemme("oignon", "ognon") == "oignon"

    def test_normalized_dropped_raw_also_dropped_drops_the_row(self):
        assert self.drops.reconcileLemme("ognon", "ognon") is None

    def test_normalized_dropped_raw_unkept_drops_the_row(self):
        # A raw lemme that is neither kept nor canonical has no business
        # surviving its own paradigm's drop.
        assert self.drops.reconcileLemme("ognonns", "ognon") is None
