#!/usr/bin/python
# coding: utf-8
import sys
import json
import numpy as np
import csv
from enum import Enum
from dataclasses import dataclass

GramCat = Enum("GramCat",["ADJ", "ADJ:dem", "ADJ:ind", "ADJ:int", "ADJ:num", 
                          "ADJ:pos", "ADV", "ART:def", "ART:ind", "AUX", "CON", 
                          "LIA", "NOM", "ONO", "PRE", "PRO:dem", "PRO:ind", 
                          "PRO:int", "PRO:per", "PRO:pos", "PRO:rel", "VER"])

@dataclass
class Word:
    """
    Representation of a Word defined by an orthograph and a pronunciation
    
    word : str
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
    syll : str
        Syllables in phonemes as provided by the lexic
    cv-cv : str
        Consonant-Vowel brokendown by syllable  
    orthosyll : str
        Orthograph of the syllables (some are mistaken)
    frequency : float
        Frequency of the word in the chosen corpus
    """
    word : str
    phonology : str
    lemme : str
    gram_cat : str
    ortho_gram_cat : [GramCat]
    gender : str
    number : str
    info_verb : str
    syll : str
    cv_cv : str
    orthosyll : str
    frequency : float

    def breakdownSyllables(self, graphem_phoneme : str):
        try :   
            graph_phon_pairs = [(gp.split("-")[0], gp[1].split("-")) for gp in graphem_phoneme.split(".")]
        except IndexError as e :
            print(graphem_phoneme)
            sys.exit(1)
        return

@dataclass
class Phoneme :
    """
    Representation of the parts of a Syllable
    
    name : str
        Single char IPA representation of the phoneme
    frequency : float
        Frequency of occurence in the underlying lexicon/corpus
    """
    name : str
    frequency : float = 0.0

    def increaseFrequency(self, frequency: float):
        self.frequency += frequency

    def __eq__(self, other) :
        self.name == other.name
    def __lt__(self, other) :
        return self.frequency < other.frequency
    def __str__(self) :
        return self.name
    def __repr__(self):
        return self.name + ":" + "%.1f"%self.frequency

class PhonemeCollection:
    """
    Collection of Phonemes representing the existing sounds of a lexicon/corpus
    
    phonemes_names: {str:phoneme}
    phonemes : [Phoneme]
    """
    phoneme_names ={} 
    phonemes = []

    def getPhonemes(self, phoneme_names:str):
        """ Get phonemes from collection, adding missing ones if needed """
        ret = []
        for phoneme_name in phoneme_names :
            if phoneme_name not in self.phoneme_names :
                p = Phoneme(phoneme_name)
                self.phoneme_names[phoneme_name] = p
                self.phonemes.append(p)

            ret.append( self.phoneme_names[phoneme_name] )
        return ret

    def printTopPhonemes(self, nb: int) :
        self.phonemes.sort(reverse=True)
        print(self.phonemes[:nb])


class Syllable :
    """
    Representation of a unique sound part of a word 
    
    phonemes : [Phoneme]
        List of Phonemes sounding the Syllable
    spellings : {str: float}
        Dict of orthographic spelling that sound the same Syllable and frequency
    frequency : float
        Frequency of occurence in the underlying lexicon/corpus
    phonemeCol : PhonemeCollection
        Collection of Phonemes found in the underlying lexicon/corpus
    """
    phonemeCol : PhonemeCollection = PhonemeCollection()

    def __init__(self, phoneme_names: str, spelling: str, frequency: float = 0.0): 
        self.phonemes = []
        self.spellings = {}
        for phoneme in Syllable.phonemeCol.getPhonemes(phoneme_names):
            phoneme.increaseFrequency(frequency)
            self.phonemes.append(phoneme)
        self.frequency = frequency
        self.spellings[spelling] = frequency

    def increaseFrequency(self, frequency: float):
        self.frequency += frequency
        for phoneme in self.phonemes :
            phoneme.increaseFrequency(frequency)

    def increaseSpellingFrequency(self, spelling: str, frequency: float):
        spelling_frequency = self.spellings.get(spelling, 0.0) + frequency
        self.spellings[spelling] = spelling_frequency

    def printTopPhonemes(nb : int):
        Syllable.phonemeCol.printTopPhonemes( nb )

    def sortedSpellings(self) :
        spel_freq = [(k,v) for k,v in self.spellings.items()]
        spel_freq.sort(key=lambda kv: kv[1], reverse=True)
        return spel_freq

    def __eq__(self, other) :
        self.phonemes == other.phonemes
    def __lt__(self, other) :
        return self.frequency < other.frequency
    def __str__(self) :
        return "".join([str(p) for p in self.phonemes]) + " > " + \
                ",".join([str(spel)+":%.1f"%freq for (spel,freq) in self.sortedSpellings()]) \
                + " > " + "%.1f"%self.frequency

class SyllableCollection :
    """
    Collection of all Syllables found in a lexicon/corpus
    
    syllable_names: {str:phoneme}
    syllables : [Syllables]
    """
    syllable_names = {} 
    syllables = []

    def updateSyllable(self, syllable_name:str, spelling: str, addedfrequency: float):
        """ Updates syllable from collection, adding missing ones if needed """
        if syllable_name not in self.syllable_names:
            s = Syllable(syllable_name, spelling, addedfrequency)
            self.syllable_names[syllable_name] = s
            self.syllables.append(s)
        # Adds the spelling if it is missing
        self.syllable_names[syllable_name].increaseSpellingFrequency(spelling, addedfrequency) 

    def getSyllable(self, syllable_name:str, spelling: str, frequency = 0.0):
        """ Get syllable from collection, adding missing ones if needed """
        self.updatSyllable(syllable_name, spelling, frequency)
        return self.syllable_names[syllable_name] 
    
    def printTopSyllables(self, nb: int) :
        self.syllables.sort(reverse=True)
        for syl in self.syllables[:nb] :
            print(str(syl))

class Dictionary:

    picked = []
    words = []
    words_by_ortho= {}
    word_source = "resources/Lexique383.tsv"
    graphem_phoneme_source= "resources/LexiqueInfraCorrespondance.tsv"
    sylCol = SyllableCollection()


    def read_corpus(self):
        with open(self.word_source) as f:
            corpus = csv.DictReader(f, delimiter='\t')
            
            for corpus_word in corpus:
                if corpus_word["ortho"] != None and corpus_word["ortho"][0] != "#":
                    word = Word(word = corpus_word["ortho"],
                            phonology = corpus_word["phon"],
                            lemme = corpus_word["lemme"],
                            gram_cat = GramCat[corpus_word["cgram"]] if corpus_word["cgram"] != '' else None,
                            ortho_gram_cat = [GramCat[gc] for gc in corpus_word["cgramortho"].split(",")],
                            gender = corpus_word["genre"],
                            number = corpus_word["nombre"],
                            info_verb = corpus_word["infover"],
                            syll = corpus_word["syll"],
                            cv_cv= corpus_word["cv-cv"],
                            orthosyll = corpus_word["orthosyll"],
                            frequency = float(corpus_word["freqlivres"])
                            )
                    self.words.append(word)
                    same_ortho = self.words_by_ortho.get(corpus_word["ortho"], []) + [word]
                    self.words_by_ortho[corpus_word["ortho"]] = same_ortho
        self.breakdownSyllables()
        return self.words

    def breakdownSyllables(self):
        with open(self.graphem_phoneme_source) as f:
            graph_phon_asso = csv.DictReader(f, delimiter='\t')
            for asso_word in graph_phon_asso :
                if asso_word["item"][0] != "#":
                    corpus_words = self.words_by_ortho[asso_word["item"]]
                    for word in corpus_words : 
                        if word.phonology == asso_word["phono"]:
                            word.breakdownSyllables(asso_word["assoc"])


        return

    def analyseFrequencies(self) :
        self.mismatchSyllableSpelling = []
        self.words = self.read_corpus()
        self.words.sort(key=lambda x: x.frequency, reverse=True)
        for word in self.words :
            syllable_names = word.syll.split("-")
            spellings = word.orthosyll.split("-")
            if len(syllable_names) != len(spellings):
                self.mismatchSyllableSpelling.append(word)
            else : 
                for (syllable_name, spelling) in zip(syllable_names, spellings): 
                    syllable = self.sylCol.updateSyllable(syllable_name, spelling, word.frequency)

        self.sylCol.printTopSyllables(20)
        Syllable.printTopPhonemes(20)
        print(len(self.mismatchSyllableSpelling))

Dictionary().analyseFrequencies()
