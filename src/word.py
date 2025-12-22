#!/usr/bin/python
# coding: utf-8
#
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
        self.orthosyllCV = self.parseOrthoSyll()
        self.syllCV = self.parsePhonoSyll()
        # Formula to be optimized following the need of the typist
        # self.frequency = 0.9*self.frequencyFilm + 0.1* self.frequencyBook
        self.frequency = self.frequencyFilm
        self._hash = hash(f"{self.ortho}{self.phonology}{self.lemme}{self.gramCat.name}{self.gender}{self.number}")
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

    @override
    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other):
        if not isinstance(other, Word):
            return NotImplemented
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
        # Adding gender_number feature combo
        if self.gender != None and self.number != None:
            features += [f"{self.gender}_{self.number}"]
            if features[-1] != "m_s":
                features += ["not_m_s"]
        # Adding a VER_masculine/feminin_singular/plural combo for participe passé
        if self.gramCat == GramCat.VER :
            if self.gender != None and self.number != None:
                features += [f"{self.gramCat.name}_{self.gender}_{self.number}"]
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
