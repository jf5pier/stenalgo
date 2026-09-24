#!/usr/bin/python
# coding: utf-8
#
import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import override
from itertools import combinations

GramCat = Enum(
    "GramCat",
    [
        "ADJ", "ADJ:dem", "ADJ:ind", "ADJ:int", "ADJ:num",
        "ADJ:pos", "ADV", "ART:def", "ART:ind", "AUX",
        "CON", "LIA", "NOM", "ONO", "PRE",
        "PRO:dem", "PRO:ind", "PRO:int", "PRO:per", "PRO:pos",
        "PRO:rel", "VER",
    ],
)

type WordFeature = str
type Lemme = str
type LemmeGramCat = str  #format : "lemme_GramCat"
type WordOrtho = str
type WordPhono = str

@dataclass
class Word:
    """
    Representation of a Word defined by an orthograph and a pronunciation

    ortho : str
        The word's orthograph
    phonology : str
        Collection of phonemes representing the pronunciation
    lemme : str
        Root of the word
    gramCat : GramCat
        Grammatical category
    cgramortho : [GramCat]
        All grammatical categories of the words sharing this orthograph
    gender : str | None
        Gender of the noun or adjectiv
    number : str | None
        Number (singular or plural) of the noun or adjectiv
    infoVerb : list[list[str]] | None
        Conjugaiton of the verb
    rawSyllCV : str
        Phonemes in syllables after analysis of Lexique383 and LexiqueInfra
    rawOrthosyllCV : str
        Orthograph of the syllables after analysis of Lexique383
        and LexiqueInfra
    frequencyBook : float
        Frequency of the word in the written corpus
    frequencyFilm : float
        Frequency of the word in the film corpus
    syllCV : [[str]]
        Parsed rawSyllCV
    orthosyllCV : list[list[str]]
        Parsed rawOrthosyllCV
    frequency : float
        Chosen mix of the film and book frequencies
    """

    ortho: WordOrtho
    phonology: WordPhono
    lemme: Lemme
    gramCat: GramCat
    orthoGramCat: list[GramCat]
    gender: str | None
    number: str | None
    infoVerb: str | None
    rawSyllCV: str
    rawOrthosyllCV: str
    frequencyBook: float
    frequencyFilm: float
    orthosyllCV: list[list[str]] = field(init=False)
    syllCV: list[list[str]] = field(init=False)
    frequency: float = field(init=False)
    lemmeGramCat: LemmeGramCat = field(init=False)
    _hash: int = field(init=False)
    _infoVerb: list[list[str]] | None = field(init=False)

    def __post_init__(self) -> None:
        self.fix_e_n_en()
        self.fix_rdre_coda_syllable_break()
        self.fix_ayer_conditionnel_onset_glide()
        self.fix_glide_low_vowel_syllable_break()
        self.orthosyllCV = self.parseOrthoSyll()
        self.syllCV = self.parsePhonoSyll()
        # Formula to be optimized following the need of the typist
        # self.frequency = 0.9*self.frequencyFilm + 0.1* self.frequencyBook
        self.frequency = self.frequencyFilm
        # Stable across processes (unlike the salted builtin hash()), so a pickled Word and a
        # freshly built one agree, and set[Word] iteration order no longer follows
        # PYTHONHASHSEED (B43, B27).
        self._hash = int.from_bytes(
            hashlib.blake2b("\x1f".join(map(str, self.identity())).encode(),
                            digest_size=8).digest(),
            "big", signed=True)
        self._infoVerb = [self.splitInfoVerb(infoVerb)
                            for infoVerb in filter(lambda iv: iv != '', self.infoVerb.split(";"))
                            ] if self.infoVerb is not None else None
        # this is more precice than the lemme alone in identifying the family of a word
        # ex.: rucher_NOM vs rucher_VER
        self.lemmeGramCat = f"{self.lemme}_{self.gramCat.name}"

    def splitInfoVerb(self, infoVerb: str) -> list[str]:
        """ Split string of the kind : "ind:pre:1p" into a list of features
            ["indicatif", "présent", "pers_1", "nbr_p"]
        """
        iv = infoVerb.split(":")
        ret: list[str] = []
        if iv[0] == "inf":
            return ["infinitif"]
        else:
            # Append verbe mode first
            ret.append("indicatif") if iv[0] == "ind" else None
            ret.append("impératif") if iv[0] == "imp" else None
            ret.append("subjonctif") if iv[0] == "sub" else None
            ret.append("participe") if iv[0] == "par" else None
            ret.append("conditionnel") if iv[0] == "cnd" else None
            # Append verbe tense second
            ret.append("présent") if iv[1] == "pre" else None
            ret.append("passé") if iv[1] == "pas" else None
            # Participe are done parsing here
            if "participe" != ret[0]:
                ret.append("imparfait") if iv[1] == "imp" else None
                ret.append("future") if iv[1] == "fut" else None
                # All tenses except participe and infinitif also have person and number
                ret.append("pers_%s"%iv[2][0])  #ex.: 1ier personne du pluriel = pers_1 nbr_p
                ret.append("nbr_%s"%iv[2][1])
        return ret

    def mergeInfoVerb(self, infoVerb: str) -> None:
        """
        Fold in another ";"-separated infoVerb tag for this same homograph (same ortho,
        phonology, lemme, gramCat, gender and number -- i.e. same Word identity, see
        __post_init__'s _hash), exactly as if Lexique383 had listed it natively in the
        same row to begin with (that's how it already represents a common verb's several
        readings, e.g. "parle" carries "imp:pre:2s;ind:pre:1s;ind:pre:3s;sub:pre:1s;
        sub:pre:3s;" as one row). Used when a second source row for the same orthography
        (e.g. a LexiqueSynthetic paradigm-completion row) supplies a reading the first
        source's row was missing, so it doesn't become a second, separate Word instance
        that downstream code would have to reconcile as a same-spelling homograph.
        """
        # Both this Word's own infoVerb and the incoming tag may already carry Lexique383's
        # trailing ";" (its own row-ending convention) -- strip before rejoining so a merge
        # never produces a stray "";"" in the middle, keeping the native multi-tag format.
        newTag = infoVerb.strip(";")
        if newTag == "":
            return
        existingTags = [iv for iv in (self.infoVerb or "").split(";") if iv != ""]
        if newTag in existingTags:
            return
        self.infoVerb = ";".join(existingTags + [newTag]) + ";"
        self._infoVerb = [self.splitInfoVerb(iv)
                            for iv in filter(lambda iv: iv != '', self.infoVerb.split(";"))]

    def identity(self) -> tuple[str, str, str, str, str | None, str | None]:
        """ The fields that make two Words the same homograph (see mergeInfoVerb). """
        return (self.ortho, self.phonology, self.lemme, self.gramCat.name,
                self.gender, self.number)

    @override
    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other):
        if not isinstance(other, Word):
            return NotImplemented
        # _hash is a 64-bit digest of identity(); comparing it alone is the cheapest check and
        # was verified collision-free on the 169,695-Word corpus (2026-09-24).
        return self._hash == other._hash

    def getFeatures(self) -> list[WordFeature]:
        """
        Extract features from the word to help discriminate it from other words that are homophones.
        Also adds some combined features that could be useful like "not-masculin-singular"
        """
        features: list[WordFeature] = []
        features += [self.gramCat.name]
        features += [self.gender] if self.gender != None else []
        features += [self.number] if self.number != None else []
        # Adding gender_number feature combo. Gender and number are independent atomic
        # features, so they're ':'-joined (like every other compound feature) rather than
        # '_'-joined -- atomicFeatures() must split this back into {"m"/"f", "s"/"p"}, not
        # treat "m_s" as one indivisible token. "not_m_s" is its own indivisible flag
        # ("not the canonical masculine-singular form"), not a gender+number compound, so
        # it keeps its '_' -- there's no "not_m"/"not_s" to decompose it into.
        if self.gender != None and self.number != None:
            features += [f"{self.gender}:{self.number}"]
            if features[-1] != "m:s":
                features += ["not_m_s"]
        # Adding a VER:masculine/feminin:singular/plural combo for participe passé --
        # gramCat, gender and number are 3 independent atoms, so they're ':'-joined.
        if self.gramCat == GramCat.VER :
            if self.gender != None and self.number != None:
                features += [f"{self.gramCat.name}:{self.gender}:{self.number}"]
        try:
            if self._infoVerb is not None:
                for singleInfoVerb in self._infoVerb:
                    combos: list[tuple[WordFeature, ...]] = []
                    for comboSize in range(1, len(singleInfoVerb)+1):
                        combos += list(combinations(singleInfoVerb, comboSize))
                    for combination in combos:
                        combinationStr: WordFeature = ":".join(combination)
                        features += [combinationStr]
            return features
        except TypeError as e:
            print(self.ortho, self.infoVerb, self._infoVerb)
            raise e


    def fix_e_n_en(self) -> None:
        # enivre @nivR @|n_i_v_R_# e|n_i_v_r_e --> @|i_v_R_# en|i_v_r_e
        if "@|n_" in self.rawSyllCV and "e|n_" in self.rawOrthosyllCV:
            pos = self.rawSyllCV.index("@|n_")
            self.rawSyllCV = (
                self.rawSyllCV[:pos] + "@|" + self.rawSyllCV[pos + 4 :]
            )
            pos = self.rawOrthosyllCV.index("e|n_")
            self.rawOrthosyllCV = (
                self.rawOrthosyllCV[:pos] + "en|" + self.rawOrthosyllCV[pos + 4 :]
            )
            self.fix_e_n_en()

    def fix_rdre_coda_syllable_break(self) -> None:
        """
        Steno-encoding exception, not a claim about spoken syllable count: -rdre verbs
        (perdre, mordre, tordre, ...) encode their infinitive's "-dre" tail as a single
        syllable whose coda repeats /R/ (e.g. perdre = p_E_R_d_R_#, the second /R/
        standing in for the syllabic "-re"). Starboard maps coda /R/ here to one
        dedicated key, so the repeated /R/ collapses to a single keypress under
        `canonicalizeStrokes` and the infinitive becomes physically indistinguishable
        from perdent/perde/perdes (single /R/). Restricted to conjugated verb forms
        (infoVerb is not None) -- NOM homographs of this shape (ordre, désordre,
        contrordre) have no competing paradigm form to collide with, so splitting them
        would only cost a keystroke for no disambiguation benefit.

        Splits the coda at the same point perdez/perdons already split at
        (p_E_R|d_e, p_E_R|d_§), giving the infinitive its own extra stroke instead of
        silently losing the second /R/.
        """
        if self.infoVerb is None:
            return
        segments = self.rawSyllCV.split("|")
        last = segments[-1]
        if last.endswith("_R_d_R_#"):
            segments[-1] = last[: -len("_d_R_#")]
            segments.append("d_R_#")
            self.rawSyllCV = "|".join(segments)

        orthoSegments = self.rawOrthosyllCV.split("|")
        orthoLast = orthoSegments[-1]
        if orthoLast.endswith("_r_d_r_e"):
            orthoSegments[-1] = orthoLast[: -len("_d_r_e")]
            orthoSegments.append("d_r_e")
            self.rawOrthosyllCV = "|".join(orthoSegments)

    def fix_ayer_conditionnel_onset_glide(self) -> None:
        """
        Steno-encoding exception, not a claim about spoken syllable count: -ayer
        verbs' conditionnel 1p/2p forms (paieriez, paierions, essaieriez,
        balaierions, ...) append the future/conditional /R/ directly onto the
        radical's bare /E/, then the "-iez"/"-ions" ending's onset /j/ glide, all
        within one syllable (paieriez = p_E_#|R_j_e). Starboard's onset /R/ (one key)
        is a subset of onset /j/'s 2-key digraph, so /R/+/j/ collapses to the same
        chord as /j/ alone -- paieriez collapses onto payer/payez/payé/... (no /R/,
        e.g. payez = p_E_#|j_e), which is wrong: per Wiktionnaire's IPA, paieriez
        [pɛʁje] genuinely has the /ʁ/ that payez [pɛje] lacks (verified 2026-09-21,
        see ROADMAP.md).

        A first attempt re-keyed the ending's /j/ as nucleus /i/+/e/ instead of onset
        /j/ (nucleus /i/ has its own dedicated key, unlike onset /R/'s subset
        relationship to onset /j/) -- but Starboard's nucleus /i/+/e/ 2-key chord
        turned out to be the SAME chord already dedicated to the single phoneme /E/,
        so paieriez collapsed onto paierais/paierait/paieraient instead (same
        subsumption bug, new pair). No available phoneme substitution is collision-free
        here, so this uses the same syllable-break approach as
        fix_rdre_coda_syllable_break/fix_glide_low_vowel_syllable_break instead:
        split /R/ into its own bare-onset syllable, so it's never in the same stroke
        as /j/ at all. p_E_#|R_j_e -> p_E_#|R|j_e: onset /R/ alone can't be swallowed
        by a /j/ that's now a different stroke.

        Restricted to the exact -ayer conditionnel shape (a segment ending "_E_#"
        immediately followed by one starting "R_j_") -- the same "R_j" substring
        appears constantly elsewhere in French (rien, hier, pierre, marier, riez...)
        with no competing form to collide with, so a blanket split would cost those
        words a keystroke for no benefit.
        """
        if self.infoVerb is None:
            return
        segments = self.rawSyllCV.split("|")
        for i in range(len(segments) - 1):
            if segments[i].endswith("_E_#") and segments[i + 1].startswith("R_j_"):
                rest = segments[i + 1][len("R_j_"):]
                segments[i + 1 : i + 2] = ["R", "j_" + rest]
                self.rawSyllCV = "|".join(segments)

                orthoSegments = self.rawOrthosyllCV.split("|")
                for j in range(len(orthoSegments)):
                    m = re.match(r"^r_i_(ez|ons)$", orthoSegments[j])
                    if m:
                        orthoSegments[j : j + 1] = ["r", "i_" + m.group(1)]
                        self.rawOrthosyllCV = "|".join(orthoSegments)
                        break
                return

    def fix_glide_low_vowel_syllable_break(self) -> None:
        """
        Steno-encoding exception, not a claim about spoken syllable count: -uer verbs'
        passé-simple/participe-présent/subjonctif-imparfait forms (tua, tuant, continua,
        continuant, ...) end their final syllable with the /8/ (\\u0265, "u"-glide)
        immediately followed by bare /a/ or nasal /@/ (tua = t_8_a, tuant = t_8_@).
        Starboard's /8/ key is a 2-key digraph whose keys are a superset of /a/'s and
        /@/'s own dedicated single keys, so /8/+/a/ or /8/+/@/ collapses to the same
        chord as /8/ alone under `canonicalizeStrokes` -- tua and tuant collapse
        together, and both onto any other lemma sharing the bare /8/ ending. Restricted
        to the word's OWN final syllable (a mid-word "_8_a"/"_8_@" like situation's
        "si-tua-tion" or persuader's "per-sua-der" is not this ambiguity -- nothing else
        in the word collapses along with it, so splitting it would only cost a
        keystroke for no benefit).

        Splits the vowel into its own syllable -- t_8|a, t_8|@ -- mirroring
        fix_rdre_coda_syllable_break's approach. Restricted to conjugated verb forms
        (infoVerb is not None), same reasoning as fix_rdre_coda_syllable_break: this
        also catches -uas forms (tuas, remuas, ...), since their phonology is
        identical to the -ua form (tua) they share a stroke with. Deliberately NOT
        applied to ADJ/NOM homographs of a verb's participe présent (tuant the
        adjective, gargantua, diluant the solvent, ...) -- those never had a
        competing paradigm form to collide with in the first place (a homograph of an
        unsplit VER reading just means two valid strokes for the same text, which is
        harmless), and most of them (unlike the participles) aren't tied to any verb
        at all, so splitting them would only cost a keystroke for no benefit.
        """
        if self.infoVerb is None:
            return
        segments = self.rawSyllCV.split("|")
        last = segments[-1]
        if last.endswith("_8_a") or last.endswith("_8_@"):
            segments[-1], vowel = last[:-2], last[-1]
            segments.append(vowel)
            self.rawSyllCV = "|".join(segments)

        orthoSegments = self.rawOrthosyllCV.split("|")
        orthoLast = orthoSegments[-1]
        orthoMatch = re.search(r"^(.*_u)_(ant|as|ât|a)$", orthoLast)
        if orthoMatch:
            orthoSegments[-1] = orthoMatch.group(1)
            orthoSegments.append(orthoMatch.group(2))
            self.rawOrthosyllCV = "|".join(orthoSegments)

    def phonemesToSyllableNames(self, withSilent: bool=True, symbol: str="") -> list[str]:
        # Format is [[syll1letter1, syll1letter2], [syll2letter1, ...]]
        # Output is ["syll1letter1syll1letter2", "syll2letter1..."]
        if withSilent:
            return [symbol.join(syll) for syll in self.syllCV]
        else:
            return [symbol.join(syll).replace("#", "") for syll in self.syllCV]

    def graphemsToSyllables(self, withSilent: bool=True, symbol: str="") -> list[str]:
        if withSilent:
            return [symbol.join(syll) for syll in self.orthosyllCV]
        else:
            return [symbol.join(syll).replace("#", "") for syll in self.orthosyllCV]

    def syllablesToWord(self) -> str:
        return "".join(self.phonemesToSyllableNames())

    def parseOrthoSyll(self) ->list[list[str]]:
        # Format is "syll1letter1_syll1letter2|syll2letter1_..."
        # Output is [[syll1letter1, syll1letter2], [syll2letter1, ...]]
        return list(map(
            lambda syll: syll.split("_"), self.rawOrthosyllCV.split("|")
        ))

    def parsePhonoSyll(self) -> list[list[str]]:
        # Format is "syll1phonem1_syll1phonem2|syll2phonem1_..."
        return list(map(lambda syll: syll.split("_"), self.rawSyllCV.split("|")))

    def replaceSyllables(self, syll_orig: str, syll_final: str) -> str:
        """
        Replace all occurrences of syll_orig by syll_final in the phonology of the word
        """
        phono = self.phonology
        if syll_orig == syll_final :
            return phono
        i = 0
        while (pos := phono[i:].find(syll_orig)) != -1:
            pos += i
            phono = phono[0:pos] + syll_final + phono[len(syll_orig) + pos :]
            i = pos + len(syll_final)
        return phono

    @override
    def __str__(self) -> str:
        return f"Word(ortho={self.ortho}, phonology={self.phonology}, lemme={self.lemme}," + \
            f" gramCat={self.gramCat}, gender={self.gender}, number={self.number}," + \
            f" infoVerb={self.infoVerb}" #, rawSyllCV={self.rawSyllCV}," + \
            # f" rawOrthosyllCV={self.rawOrthosyllCV}, frequencyBook={self.frequencyBook}," + \
            # f" frequencyFilm={self.frequencyFilm}, syllCV={self.syllCV}," + \
            # f" orthosyllCV={self.orthosyllCV}, frequency={self.frequency})"


#    def writeOrthoSyll(self):
#        # Format is "syll1letter1_syll1letter2|syll2letter1_..."
#        return "|".join(self.lettersToSyllables(symbol="_"))
#
#    def writePhonoSyll(self):
#        # Format is "syll1phonem1_syll1phonem2|syll2phonem1_..."
#        return "|".join(self.phonemesToSyllableNames(symbol="_"))


# Atomic features that conflict with each other (plural↔singular, masculine↔feminine).
ATOMIC_FEATURE_CONFLICTS: dict[str, str] = {"p": "s", "s": "p", "m": "f", "f": "m"}


def atomicFeatures(f: WordFeature) -> frozenset[str]:
    """Split a (possibly compound) feature string into its atomic features, stripping any
    'not_' prefix. Splits only on ':' -- '_' is internal to a single atom's own name
    (e.g. "pers_3" is one atom, "person = 3", not two)."""
    base = f[4:] if f.startswith("not_") else f
    return frozenset(t for t in base.split(':') if t)


def groupWordsByLemme(words: list[Word]) -> dict[LemmeGramCat, list[Word]]:
    """
    Split a group of homophone Words (sharing the same strokes) by lemme+gramCat, preserving
    the order in which each lemmeGramCat's words first appear in words.
    """
    wordByLemme: dict[LemmeGramCat, list[Word]] = {word.lemmeGramCat: [] for word in words}
    for word in words:
        wordByLemme[word.lemmeGramCat].append(word)
    return wordByLemme


def groupWordsByBareLemme(words: list[Word]) -> dict[Lemme, list[Word]]:
    """
    Split a group of homophone Words (sharing the same strokes) by bare lemme (ignoring
    gramCat), preserving the order in which each lemme's words first appear in words. Unlike
    groupWordsByLemme, this collapses different grammatical uses of the same lemma (e.g.
    être_VER vs être_AUX) into one group, since they are not distinct lemmas competing for a
    discriminating symbol.
    """
    wordByLemme: dict[Lemme, list[Word]] = {word.lemme: [] for word in words}
    for word in words:
        wordByLemme[word.lemme].append(word)
    return wordByLemme
