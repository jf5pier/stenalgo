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
    syll_cv : [str]
        Syllables in phonemes as provided by the lexicInfra and 
        groupped by cv_cv field
    orthosyll_cv : [str] 
        Orthograph of the syllables as provided by the lexicInfra
        and groupped by cv_cv field
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
    #syll_cv : [str]
    #orthosyll_cv : [str]

    def __post_init__(self) :
        self.fixX_KS()

    def fixLexiqueInfraGraphPhon(graphem_phonem) :
        # Apply correction to LexiqueInfra Graphem-Phonem correspondance
        # that are represented by a differente CV-CV in Lexique
        graphem_phonem = Word.fixAssociation(graphem_phonem, "cc-ks", "c-k.c-s")
        graphem_phonem = Word.fixAssociation(graphem_phonem, "rr-RR", "r-R.r-R")
        graphem_phonem = Word.fixAssociation(graphem_phonem, "oy-waj", "o-wa.y-j")
        # accastillage a-a.cc-k.a-a.s-s.t-t.ill-ij.a-a.ge-Z
        graphem_phonem = Word.fixAssociation(graphem_phonem, "ill-ij", "i-i.ll-j")
        # acuité a-a.c-k.ui-8i.t-t.é-e
        graphem_phonem = Word.fixAssociation(graphem_phonem, "ui-8i", "u-u.i-i")
        # aiguille ai-e.gu-g8.i-i.ll-j.e-#
        graphem_phonem = Word.fixAssociation(graphem_phonem, "gu-g8", "g-g.u-8")
        return graphem_phonem

    def fixAssociation(graphem_phoneme, badAsso, goodAsso) :
        if badAsso in graphem_phoneme :
            pos = graphem_phoneme.index(badAsso)
            return graphem_phoneme[0:pos] + goodAsso + \
                    graphem_phoneme[pos+len(badAsso):]
        return graphem_phoneme


    def breakdownSyllables(self, graphem_phoneme : str):
        # Uses the CV-CV breakdown of phonemes from Lexique with the grapheme-phoneme decomposition of 
        #  LexiqueInfra to find the graphemes parts of each syllable
        self.syll_cv = []
        self.orthosyll_cv = []
        syll_phon = []
        syll_graph = []
        semi_vowel_liaison = False
        skip_next_Y = False
        try :   
            graphem_phoneme = Word.fixLexiqueInfraGraphPhon(graphem_phoneme)
            graph_phon_pairs = [(gp.split("-")[0], gp.split("-")[1]) for gp in graphem_phoneme.split(".")]
            cv_split = self.cv_cv.split("-")
            for syllNb, cv_syll in enumerate(cv_split):
                last_syllable = syllNb == len(cv_syll) -1
                syll_phon = []
                syll_graph = []
                for cvNb, cv_phoneme in enumerate(cv_syll) :
                    #if cv_phoneme == "Y" and graph_phon_pairs[0][1] in ["wa"]:
                    #    if len(cv_split) < syllNb - 1 and cv_split[syllNb+1][0] == "Y":
                    #        semi_vowel_liaison = True
                    #    continue 
                    #if cv_phoneme == "Y" and semi_vowel_liaison :
                    #    semi_vowel_liaison = False
                    #    continue
                    if cv_phoneme == "C" :
                        #if graph_phon_pairs[0][0] in ["x"] :
                            
                    if cv_phoneme == "Y" :
                        while graph_phon_pairs[0][1] == "#" :
                            #admixtion a-a.d-d.m-m.i-i.x-ks.t-#.i-j.on-§
                            graph_phon = graph_phon_pairs.pop(0)
                            syll_phon.append( ("#", graph_phon[0]) )
                            syll_graph.append( graph_phon[1] )
                        if graph_phon_pairs[0][0] not in ["i", "ll", "o", "y", "u", "ill", \
                                "il", "ou"]:
                            continue
                        if skip_next_Y  :
                            # Rare english words and other exceptions
                            skip_next_Y = False
                            continue
                        #Some semi-vowel Y in Lexique are superflous because their vowel is already
                        #assigned to a V matched to a graphem-phonem in LexiqueInfra
                        if graph_phon_pairs[0][0] in ["oi", "o", "oin", "oî"] :
                            # le Y /j/ dans a-ba-ttoir , a-bo-ya, a-ccoin-tance
                            continue
                        if graph_phon_pairs[0][0] in ["ez", "ons"]:
                            # le Y /j/ dans ab-sou-dri-ez, a-cca-bli-ons
                            continue 


                    #if cv_phoneme == "Y" and graph_phon_pairs[0][1] not in ["j","8"]:
                    #    continue 
                    graph_phon = graph_phon_pairs.pop(0)
                    if graph_phon[1] == "Ej" :
                        #ace a-Ej.c-s.e-# Ejs VYC englis word
                        skip_next_Y = True
                    #silent phonemes are not matched by a cv_phoneme
                    while graph_phon[1] == "#" :
                        syll_phon.append( ("#", graph_phon[0]) )
                        syll_graph.append( graph_phon[1] )
                        graph_phon = graph_phon_pairs.pop(0)
                    syll_graph.append( (cv_phoneme, graph_phon[0]) )
                    syll_phon.append( graph_phon[1] )
                self.syll_cv.append(syll_phon)
                self.orthosyll_cv.append(syll_graph)
                #Append silent phonemes to end of previous syllable
                while len(graph_phon_pairs) > 0 and graph_phon_pairs[0][1] == "#" :
                    graph_phon = graph_phon_pairs.pop(0)
                    self.syll_cv[-1].append( ("#", graph_phon[0]) )
                    self.orthosyll_cv[-1].append( graph_phon[1] )

            if len(graph_phon_pairs) > 0 :
                print("Left-over graphem-phoneme not assigned")
                print(self.word, graphem_phoneme, self.syll, self.cv_cv)
                print(self.syll_cv)
                print(self.orthosyll_cv, "extra:", graph_phon_pairs)
                sys.exit(1)
        except Exception as e :
            print(e)
            print(self.word, graphem_phoneme, self.syll, self.cv_cv)
            print(self.syll_cv)
            print(self.orthosyll_cv)
            print(syll_phon, syll_graph, "extra:", graph_phon_pairs)
            sys.exit(1)
        return

    def fixX_KS(self) :
        #X sound should not be broken into 2 consonnants (k-s) in 2 syllables
        if self.isWellFormedCVSyll() and "x" in self.word and "k-s" in self.syll :
            pos = self.syll.index("k-s")
            self.syll = self.syll[0:pos] + "-ks" + self.syll[pos+3:]
            self.cv_cv= self.cv_cv[0:pos] + self.cv_cv[pos+1:]  # "*C-C*" becomes "*-C*"
            self.fixX_KS() #recurse if there is more than one X

    def isWellFormedCVSyll(self):
        # Verify cv_cv and syll have the same form
        a = self.cv_cv.split("-")
        b = self.syll.split("-")
        return len(a) == len(b) and list(map(len, a)) == list(map(len,b))

    def isWellFormedCVOrthosyll(self):
        # Verify cv_cv and orthosyll have generally the same form
        a = self.cv_cv.split("-")
        b = self.orthosyll.split("-")
        return len(a) == len(b) 

    def isSyllConsensus(self) :
        # Verify if the phonologic syll and syll_cv match once silent phonemes are removed
        if self.isWellFormedCVSyll() :
            for syll, syll_cv in zip(self.syll.split("-"), self.syll_cv):
                if syll != "".join(syll_cv).replace("#","") :
                    return False
            return True
        return False

    def isOrthoSyllConsensus(self) :
        # Verify if the orthograph of orthosyll and orthosyll_cv match 
        if self.isWellFormedCVOrthosyll() :
            for orthosyll, orthosyll_cv in zip(self.orthosyll.split("-"), self.orthosyll_cv):
                if orthosyll != "".join(orthosyll_cv) :
                    return False
            return True
        return False

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
        print("Top phonemes:",self.phonemes[:nb])


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
                ",".join([str(spel)+":%.1f"%freq for (spel,freq) in self.sortedSpellings()[:2]]) \
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
            print("Syllable:",str(syl))

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

        Syllable.printTopPhonemes(1)
        self.sylCol.printTopSyllables(1)
        print(len(self.mismatchSyllableSpelling))

Dictionary().analyseFrequencies()
