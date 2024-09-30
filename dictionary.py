#!/usr/bin/python
# coding: utf-8
#
# This class provides reads a converted Lexique version 383 [1,2] that has its 
# syllabification redone using graphen-phonemes pairs from Lexique infra[3].
#
# The output is 
#
# 1. New, B., Pallier, C., Brysbaert, M., Ferrand, L. (2004) 
#  Lexique 2 : A New French Lexical Database.
#  Behavior Research Methods, Instruments, & Computers, 36 (3), 516-524.
# 2. New, B., Brysbaert, M., Veronis, J., & Pallier, C. (2007). 
#  The use of film subtitles to estimate word frequencies. 
#  Applied Psycholinguistics, 28(4), 661-677.
# 3. Gimenes, M., Perret, C., & New, B. (2020). 
#  Lexique-Infra: grapheme-phoneme, phoneme-grapheme regularity, consistency, 
#  and other sublexical statistics for 137,717 polysyllabic French words. 
#  Behavior Research Methods. doi.org/10.3758/s13428-020-01396-2
#
import sys
import json
import numpy as np
import csv
from copy import deepcopy
from enum import Enum
from dataclasses import dataclass
from src.grammar import *

def printVerbose(word : str,msg : list) :
    #return
    if word in []: #["soleil"] :
        print(word, " :\n", " ".join(map(str,msg)))

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
        Orthograph of the syllables after analysis of Lexique383 and LexiqueInfra
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
    phonology : str
    lemme : str
    gram_cat : str
    ortho_gram_cat : [GramCat]
    gender : str
    number : str
    info_verb : str
    raw_syll_cv : str
    raw_orthosyll_cv : str
    frequencyBook : str
    frequencyFilm : str

    def __post_init__(self) :
        self.fix_e_n_en()
        self.parseOrthoSyll() 
        self.parsePhonoSyll() 
        # Formula to be optimized following the need of the typist
        #self.frequency = 0.9*self.frequencyFilm + 0.1* self.frequencyBook
        self.frequency = self.frequencyFilm
    
    def fix_e_n_en(self) :
        # enivre @nivR @|n_i_v_R_# e|n_i_v_r_e --> @|i_v_R_# en|i_v_r_e
        if "@|n_" in self.raw_syll_cv and "e|n_" in self.raw_orthosyll_cv :
            pos = self.raw_syll_cv.index("@|n_")
            self.raw_syll_cv = self.raw_syll_cv[:pos] + "@|" +\
                    self.raw_syll_cv[pos+2:]
            pos = self.raw_orthosyll_cv.index("e|n_")
            self.raw_orthosyll_cv = self.raw_orthosyll_cv[:pos] + "en|" +\
                    self.raw_orthosyll_cv[pos+3:]
            self.fix_e_n_en()

    def phonemesToSyllables(self, withSilent=True, symbol="") : 
        if withSilent:
            return [symbol.join(syll) for syll in self.syll_cv]
        else :
            return [symbol.join(syll).replace("#","") for syll in self.syll_cv]

    def graphemsToSyllables(self, withSilent=True, symbol="") : 
        if withSilent:
            return [symbol.join(syll) for syll in self.orthosyll_cv]
        else : 
            return [symbol.join(syll).replace("#","") for syll in self.orthosyll_cv]
            

    def syllablesToWord(self) :
        return "".join(self.phonemesToSyllables())

    def parseOrthoSyll(self) :
        # Format is "syll1letter1_syll1letter2|syll2letter1_..."
        self.orthosyll_cv = map(lambda syll: syll.split("_"), self.raw_orthosyll_cv.split("|"))

    def parsePhonoSyll(self) :
        # Format is "syll1phonem1_syll1phonem2|syll2phonem1_..."
        self.syll_cv = map(lambda syll: syll.split("_"), self.raw_syll_cv.split("|"))

    def writeOrthoSyll(self) :
        # Format is "syll1letter1_syll1letter2|syll2letter1_..."
        return "|".join(self.lettersToSyllables(symbol="_"))

    def writePhonoSyll(self) :
        # Format is "syll1phonem1_syll1phonem2|syll2phonem1_..."
        return "|".join(self.phonemesToSyllables(symbol="_"))


class Dictionary:

    picked = []
    words = []
    words_by_ortho= {}
    frequent_word = []
    nb_frequent_words = 200
    totalFrequencies = 0.0
    frequent_word_frequencies = 0.0
    word_source = "resources/LexiqueMixte.tsv"
    frequent_word_file = "resources/top500_film.txt"
    sylCol = SyllableCollection()

    def __init__(self):
        self.words = self.read_corpus()
        

    def read_corpus(self):
        with open(self.frequent_word_file) as fw :
            self.totalFrequencies = float( fw.readline().strip().split("\t")[-1] )
            for line in fw.readlines()[:self.nb_frequent_words] :
                ls = line.strip().split("\t")
                self.frequent_word.append( ls[0] )
                self.frequent_word_frequencies += float( ls[1] )

        with open(self.word_source) as f:
            corpus = csv.DictReader(f, delimiter='\t')
            
            for corpus_word in corpus:
                if corpus_word["ortho"] != None and corpus_word["ortho"][0] != "#" :
                    word = Word(ortho= corpus_word["ortho"],
                            phonology = corpus_word["phon"],
                            lemme = corpus_word["lemme"],
                            gram_cat = GramCat[corpus_word["cgram"]] if \
                                    corpus_word["cgram"] != '' else None,
                            ortho_gram_cat = [GramCat[gc] for gc in \
                                    corpus_word["cgramortho"].split(",")],
                            #gram_cat = corpus_word["cgram"],
                            #ortho_gram_cat = corpus_word["cgramortho"],
                            gender = corpus_word["genre"],
                            number = corpus_word["nombre"],
                            info_verb = corpus_word["infover"],
                            raw_syll_cv = corpus_word["syll_cv"],
                            raw_orthosyll_cv = corpus_word["orthosyll_cv"],
                            frequencyBook = float(corpus_word["freqlivres"]),
                            frequencyFilm = float(corpus_word["freqfilms2"])
                            )
                    self.words.append(word)
                    same_ortho = self.words_by_ortho.get(corpus_word["ortho"], 
                                                         deepcopy([])) + [word]
                    self.words_by_ortho[corpus_word["ortho"]] = same_ortho
        return self.words


    def isVowel(char : str) :
        return char in "aeiouy2589OE§@°"

    def moveDualPhonem(syllables: [str] ) :
        #Move dual-phonemes representation ij and gz to better compare to Lexique383
        #This function is only used to compare the analysis to Lexique383.
        #Its result is currently not kept

        if (len(syllables) <= 1):
            return syllables
        ret = []
        semivowelToMove = ""
        for i,syllOrig in enumerate(syllables) :
            s = deepcopy(syllOrig)
            if semivowelToMove != "":
                s = semivowelToMove + s
                semivowelToMove = ""
            if i+1 < len(syllables) :
                if s[-1] == "j":  #['prié', ['pRi', 'je'], ['pRij', 'e']]
                    if Lexique.isVowel( syllables[i+1][0] ) : # not bouilloire
                        ret.append(s[:-1])
                        semivowelToMove = "j"
                    else :
                        ret.append(s)
                elif len(s) > 2 and s[-2:] == "gz": 
                    #['exigé', ['Eg', 'zi', 'Ze'], ['Egz', 'i', 'Ze']]
                    ret.append(s[:-1])
                    semivowelToMove = "z"
                else :
                    ret.append(s)
            else :
                ret.append(s)
        return ret

    def printSyllabificationStats(self) :
        self.words.sort(key=lambda x: x.frequency, reverse=True)
        for word in self.words :
            # Remove the frequent words from syllable frequency statistics
            frequency = word.frequency if word.ortho not in self.frequent_word else 0.0
            syllable_names = word.phonemesToSyllables(withSilent=False)
            spellings = word.graphemsToSyllables(withSilent=False)
            for (syllable_name, spelling) in zip(syllable_names, spellings): 
                syllable = self.sylCol.updateSyllable(syllable_name, spelling, frequency)

        #Syllable.printTopPhonemes()
        #self.sylCol.printTopSyllables()
        #print(self.sylCol.syllable_names.keys())
        #Syllable.printTopPhonemesPerPosition()
        #Syllable.printTopPhonemesPerInvPosition()
        #Syllable.printTopBiphonemes(50)
        for i in range(10):
            Syllable.optimizeBiphonemeOrder()

dictionary = Dictionary() 
dictionary.printSyllabificationStats()
