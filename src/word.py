#!/usr/bin/python
# coding: utf-8
#
from dataclasses import dataclass
from copy import deepcopy
from enum import Enum
from typing import List

GramCat = Enum(
    "GramCat",
    [
        "ADJ",
        "ADJ:dem",
        "ADJ:ind",
        "ADJ:int",
        "ADJ:num",
        "ADJ:pos",
        "ADV",
        "ART:def",
        "ART:ind",
        "AUX",
        "CON",
        "LIA",
        "NOM",
        "ONO",
        "PRE",
        "PRO:dem",
        "PRO:ind",
        "PRO:int",
        "PRO:per",
        "PRO:pos",
        "PRO:rel",
        "VER",
    ],
)


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
    gram_cat : GramCat
        Grammatical category
    cgramortho : [GramCat]
        All grammatical categories of the words sharing this orthograph
    gender : str
        Gender of the noun or adjectiv
    number : str
        Number (singular or plural) of the noun or adjectiv
    info_verb : str
        Conjugaiton of the verb
    raw_syll_cv : str
        Phonemes in syllables after analysis of Lexique383 and LexiqueInfra
    raw_orthosyll_cv : str
        Orthograph of the syllables after analysis of Lexique383
        and LexiqueInfra
    frequencyBook : float
        Frequency of the word in the written corpus
    frequencyFilm : float
        Frequency of the word in the film corpus
    syll_cv : [[str]]
        Parsed raw_syll_cv
    orthosyll_cv : [[str]]
        Parsed raw_orthosyll_cv
    frequency : float
        Chosen mix of the film and book frequencies
    """

    ortho: str
    phonology: str
    lemme: str
    gram_cat: GramCat | None
    ortho_gram_cat: List[GramCat]
    gender: str
    number: str
    info_verb: str
    raw_syll_cv: str
    raw_orthosyll_cv: str
    frequencyBook: float
    frequencyFilm: float

    def __post_init__(self):
        self.fix_e_n_en()
        self.parseOrthoSyll()
        self.parsePhonoSyll()
        # Formula to be optimized following the need of the typist
        # self.frequency = 0.9*self.frequencyFilm + 0.1* self.frequencyBook
        self.frequency = self.frequencyFilm

    def fix_e_n_en(self):
        # enivre @nivR @|n_i_v_R_# e|n_i_v_r_e --> @|i_v_R_# en|i_v_r_e
        if "@|n_" in self.raw_syll_cv and "e|n_" in self.raw_orthosyll_cv:
            pos = self.raw_syll_cv.index("@|n_")
            self.raw_syll_cv = (
                self.raw_syll_cv[:pos] + "@|" + self.raw_syll_cv[pos + 2 :]
            )
            pos = self.raw_orthosyll_cv.index("e|n_")
            self.raw_orthosyll_cv = (
                self.raw_orthosyll_cv[:pos] + "en|" + self.raw_orthosyll_cv[pos + 3 :]
            )
            self.fix_e_n_en()

    def phonemesToSyllableNames(self, withSilent=True, symbol=""):
        if withSilent:
            return [symbol.join(syll) for syll in self.syll_cv]
        else:
            return [symbol.join(syll).replace("#", "") for syll in self.syll_cv]

    def graphemsToSyllables(self, withSilent=True, symbol=""):
        if withSilent:
            return [symbol.join(syll) for syll in self.orthosyll_cv]
        else:
            return [symbol.join(syll).replace("#", "") for syll in self.orthosyll_cv]

    def syllablesToWord(self):
        return "".join(self.phonemesToSyllableNames())

    def parseOrthoSyll(self):
        # Format is "syll1letter1_syll1letter2|syll2letter1_..."
        self.orthosyll_cv = map(
            lambda syll: syll.split("_"), self.raw_orthosyll_cv.split("|")
        )

    def parsePhonoSyll(self):
        # Format is "syll1phonem1_syll1phonem2|syll2phonem1_..."
        self.syll_cv = map(lambda syll: syll.split("_"), self.raw_syll_cv.split("|"))

    def replaceSyllables(self, syll_orig: str, syll_final: str) -> str:
        phono = deepcopy(self.phonology)
        if syll_orig == syll_final :
            return phono
        while (pos := phono.find(syll_orig)) != -1:
            phono = phono[0:pos] + syll_final + phono[len(syll_orig) + pos :]
            #print(phono, syll_orig, syll_final, pos)
        return phono


#    def writeOrthoSyll(self):
#        # Format is "syll1letter1_syll1letter2|syll2letter1_..."
#        return "|".join(self.lettersToSyllables(symbol="_"))
#
#    def writePhonoSyll(self):
#        # Format is "syll1phonem1_syll1phonem2|syll2phonem1_..."
#        return "|".join(self.phonemesToSyllableNames(symbol="_"))
