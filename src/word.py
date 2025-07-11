#!/usr/bin/python
# coding: utf-8
#
import sys
from dataclasses import dataclass
from copy import deepcopy
from enum import Enum

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
    gender : str
        Gender of the noun or adjectiv
    number : str
        Number (singular or plural) of the noun or adjectiv
    infoVerb : str
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
    orthosyllCV : [[str]]
        Parsed rawOrthosyllCV
    frequency : float
        Chosen mix of the film and book frequencies
    """

    ortho: str
    phonology: str
    lemme: str
    gramCat: GramCat | None
    orthoGramCat: list[GramCat]
    gender: str
    number: str
    infoVerb: str
    rawSyllCV: str
    rawOrthosyllCV: str
    frequencyBook: float
    frequencyFilm: float

    def __post_init__(self) -> None:
        self.fix_e_n_en()
        self.orthosyllCV = self.parseOrthoSyll()
        self.syllCV = self.parsePhonoSyll()
        # Formula to be optimized following the need of the typist
        # self.frequency = 0.9*self.frequencyFilm + 0.1* self.frequencyBook
        self.frequency = self.frequencyFilm

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
