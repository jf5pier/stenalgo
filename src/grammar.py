#!/usr/bin/python
# coding: utf-8
#
from dataclasses import dataclass
from enum import Enum
from itertools import permutations,chain
from multiprocessing import Pool
from copy import deepcopy
import numpy as np


GramCat = Enum("GramCat",["ADJ", "ADJ:dem", "ADJ:ind", "ADJ:int", "ADJ:num", 
                          "ADJ:pos", "ADV", "ART:def", "ART:ind", "AUX", "CON", 
                          "LIA", "NOM", "ONO", "PRE", "PRO:dem", "PRO:ind", 
                          "PRO:int", "PRO:per", "PRO:pos", "PRO:rel", "VER"])

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

    #There's an argument to have "w" and "j" as part of the vowels
    vowel_phonemes = "aeiE@o°§uy5O9821"
    consonant_phonemes = "RtsplkmdvjnfbZwzSgNG"

    def __post_init__(self) :
        # 7 phonemes is the max per syll
        self.posFrequency = [0.0,0.0,0.0,0.0,0.0,0.0,0.0] 
        self.invPosFrequency = [0.0,0.0,0.0,0.0,0.0,0.0,0.0] 

    def increaseFrequency(self, frequency: float, pos : int = 0, invPos : int = 0):
        self.frequency += frequency
        self.posFrequency[pos] += frequency
        self.invPosFrequency[invPos] += frequency

    def isVowel(self) :
        return self.name in self.vowel_phonemes
    def isConsonant(self) :
        return self.name in self.consonant_phonemes

    def __eq__(self, other) :
        self.name == other.name
    def __lt__(self, other) :
        return self.frequency < other.frequency
    def __str__(self) :
        return self.name
    def __repr__(self):
        return self.name + ":" + "%.1f"%self.frequency

@dataclass
class Biphoneme :
    """
    Coocurence of two phonemes in a group of phonemes (syllable or other)

    pair : (str, str)
        Pair of phonemes
    frequency : 
        Occurence frequency of the pair of phoenemes
    """
    pair : (str, str)
    frequency : float = 0.0

    def increaseFrequency(self, frequency: float) :
        self.frequency += frequency

    def __eq__(self, other) :
        self.pair == other.pair
    def __lt__(self, other) :
        return self.frequency < other.frequency
    def __str__(self) :
        return self.pair
    def __repr__(self):
        return self.pair[0]+ self.pair[1] + ":" + "%.1f"%self.frequency


class PhonemeCollection:
    """
    Collection of Phonemes representing the existing sounds of a lexicon/corpus
    
    phonemes_names: {str:Phoneme}
    phonemes : [Phoneme]
    """

    def __init__(self) :
        self.phoneme_names ={} 
        self.phonemes = []

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
    
    def getPhoneme(self, phoneme_name:str) :
        return self.getPhonemes(phoneme_name)[0]

    def printTopPhonemes(self, nb: int=-1) :
        self.phonemes.sort(reverse=True)
        print("Top phonemes:", self.phonemes[:nb])

    def printTopPhonemesPerPosition(self, nb: int = -1) :
        for i in range(7) :
            self.phonemes.sort(key=lambda p : p.posFrequency[i], reverse=True)
            print("Phonemes in pos %i"%i, list(map(lambda p : (\
                    p.name, "%.1f"%p.posFrequency[i]), self.phonemes[:nb])), "\n")

    def printTopPhonemesPerInvPosition(self, nb: int = -1) :
        for i in range(7) :
            self.phonemes.sort(key=lambda p : p.invPosFrequency[i], reverse=True)
            print("Phonemes in inverted pos -%i"%(i+1), list(map(lambda p : (\
                    p.name, "%.1f"%p.invPosFrequency[i]), self.phonemes[:nb])), "\n")

    def printBarchart(self,phoneme_order : str, vsize : int = 10):
        maxFreq = 0.0
        for phoneme_name in phoneme_order :
           maxFreq = max(maxFreq, self.phoneme_names[phoneme_name].frequency)
        for i in range(vsize,0,-1) :
            toPrint = "> "
            for phoneme_name in phoneme_order :
                phoneme = self.phoneme_names[phoneme_name]
                toPrint += phoneme.name if phoneme.frequency >= i*maxFreq/vsize else " "
            toPrint += " <"
            print(toPrint)
        print("> " + phoneme_order + " <")
        print("^"*(len(phoneme_order)+4), "\n")



class BiphonemeCollection:
    """
    Collection of pairs of phonemes found in syllables
    
    biphonemes_names: {(str,str):Biphoneme}
    biphonemes : [Biphoneme]
    """
    
    def __init__(self) :
        self.biphoneme_names ={} 
        self.biphonemes = []

    def getBiphonemes(self, biphoneme_names:[(str,str)]):
        """ Get biphonemes from collection, adding missing ones if needed """
        ret = []
        for biphoneme_name in biphoneme_names :
            if biphoneme_name not in self.biphoneme_names :
                bp = Biphoneme(biphoneme_name)
                self.biphoneme_names[biphoneme_name] = bp
                self.biphonemes.append(bp)

            ret.append( self.biphoneme_names[biphoneme_name] )
        return ret

    def getBiphoneme(self, biphoneme_name : (str,str) ):
        return self.getBiphonemes([biphoneme_name])[0]

    def printTopBiphonemes(self, nb: int = -1) :
        self.biphonemes.sort(reverse=True)
        print("Biphonemes:", list(map(lambda bp : (\
                bp.pair, "%.1f"%bp.frequency), self.biphonemes[:nb])), "\n")

    def getPhonemesNames(self) :
        """ Extract single phonemes names from pairs of phonemes"""
        left = set(map(lambda p : p.pair[0], self.biphonemes))
        right = set(map(lambda p : p.pair[1], self.biphonemes))
        return "".join(set(list(left) + list(right)))

        
    def optimizeOrder(self) :
        """ Optimize the order of the phonemes found in the biphonemes
            to reduce the frequency where two phonemes would be types in
            the wrong order to produce a syllable. """
        score=0
        phonemes = list(self.getPhonemesNames())
        np.random.shuffle(phonemes)
        bestPermutation = "".join(phonemes)
        bestScore,bestNegScore, bestBadOrder = self.scorePermutation(phonemes)
        #print("Starting order (%0.1f):"%bestScore, bestPermutation)
        #print("Biphonemes in wrong order:", bestBadOrder)

        #The algorithm moves a window over the phonem string and tests permutations
        # in that window exclusively.  A window scan goes over every phonem substring
        # left to right, then right to left.
        windowSize = 4
        windowScans = 400
        maxShuffleSize = 7
        randOrder = np.array(range(len(phonemes)))
        for scan in range(windowScans) :
            np.random.shuffle(randOrder)
            shuffleSize=np.random.randint(2,maxShuffleSize)
            mutatedPermutation = list(deepcopy(bestPermutation))
            tmp = bestPermutation[randOrder[0]]
            for i in range(1, shuffleSize) :
                mutatedPermutation[randOrder[i-1]] = bestPermutation[randOrder[i]]
            mutatedPermutation[randOrder[shuffleSize-1]] = tmp
            mutatedPermutation = "".join(mutatedPermutation)
            
            #print("Test perm:", mutatedPermutation, scan)
            for pos in chain(range(len(phonemes) - windowSize), 
                             range(len(phonemes) - windowSize, 0, -1)):
                subPhonemes = mutatedPermutation[pos:pos+windowSize]
                for permutation in permutations(subPhonemes):
                    subp = "".join(permutation)
                    p = mutatedPermutation[:pos] + subp + mutatedPermutation[pos+windowSize:]
                    score, negScore, badOrder = self.scorePermutation(p)
                    if score > bestScore :
                        #if score > (bestScore * 1.03) :
                            #print("New order (%0.1f > %0.1f):"%(score,bestScore), p)
                            #print("Biphonemes in wrong order:", badOrder)
                        bestScore = score
                        bestNegScore = negScore
                        bestPermutation = p
                        bestBadOrder = badOrder
        print("Best order (%0.1f %0.1f):"%(bestScore,bestNegScore), bestPermutation)
        print("Disordered:", bestBadOrder)
        return bestPermutation
        #print("Biphonemes in wrong order:", bestBadOrder)

    def scorePermutation(self, permutation : str) :
        score = 0.0
        negScore = 0.0
        badOrder = []
        for biphoneme in self.biphonemes :
            left,right = biphoneme.pair
            if permutation.index(left) < permutation.index(right) :
                score += biphoneme.frequency
            else :
                score -= biphoneme.frequency
                negScore -= biphoneme.frequency
                badOrder.append(biphoneme)
        return score, negScore, badOrder

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
    preVowelPhonemeCol : PhonemeCollection
        Collection of phonemes found before the vowels of a syllable
    postVowelPhonemeCol : PhonemeCollection
        Collection of phonemes found after the vowels of a syllable
    vowelPhonemeCol : PhonemeCollection
        Collection phonemes found in the vowels part syllable
    preVowelBiphonemeCol : BiphonemeCollection
        Collection of pair of phonemes found before the vowels of a syllable
    postVowelBiphonemeCol : BiphonemeCollection
        Collection of pair of phonemes found after the vowels of a syllable
    multiVowelBiphonemeCol : BiphonemeCollection
        Collection of pair of phonemes found in multi-vowels syllable
    """
    phonemeCol : PhonemeCollection = PhonemeCollection()
    preVowelPhonemeCol : PhonemeCollection = PhonemeCollection()
    postVowelPhonemeCol : PhonemeCollection = PhonemeCollection()
    vowelPhonemeCol : PhonemeCollection = PhonemeCollection()
    preVowelBiphonemeCol : BiphonemeCollection = BiphonemeCollection()
    postVowelBiphonemeCol : BiphonemeCollection = BiphonemeCollection()
    multiVowelBiphonemeCol : BiphonemeCollection = BiphonemeCollection()

    def __init__(self, phoneme_names: str, spelling: str, frequency: float = 0.0): 
        self.phonemes = []
        self.phonemes_pre = []
        self.phonemes_post = []
        self.phonemes_vowel = []
        self.biphonemes_pre = []
        self.biphonemes_post = []
        self.biphonemes_vowel = []
        self.spellings = {}
        phonemes = Syllable.phonemeCol.getPhonemes(phoneme_names)
        firstVowelPos = -1
        lastVowelPos = -1
        for pos,phoneme in enumerate(phonemes):
            phoneme.increaseFrequency(frequency, pos=pos, invPos=len(phonemes)-pos-1 )
            self.phonemes.append(phoneme)
            if firstVowelPos == -1 and not phoneme.isVowel() :
                phoneme_pre = Syllable.preVowelPhonemeCol.getPhoneme(phoneme.name)
                phoneme_pre.increaseFrequency(frequency)
                self.phonemes_pre.append(phoneme_pre)
            elif firstVowelPos != -1 and not phoneme.isVowel() :
                phoneme_post = Syllable.postVowelPhonemeCol.getPhoneme(phoneme.name)
                phoneme_post.increaseFrequency(frequency)
                self.phonemes_post.append(phoneme_post)
            #Break down the syllable into consonants-vowels-consonants
            if phoneme.isVowel() :
                phoneme_vowel = Syllable.vowelPhonemeCol.getPhoneme(phoneme.name)
                phoneme_vowel.increaseFrequency(frequency)
                self.phonemes_vowel.append(phoneme_vowel)
                
                if firstVowelPos == -1:
                    firstVowelPos = pos
                lastVowelPos = pos

        #Track the cooccurences of phonemes pairs in the first consonnants group
        if firstVowelPos >= 2 :
            for pos1,phoneme1 in enumerate(phonemes[:firstVowelPos-1]) :
                for phoneme2 in phonemes[pos1+1:firstVowelPos]:
                    biphoneme  = Syllable.preVowelBiphonemeCol.getBiphoneme( \
                                    (phoneme1.name, phoneme2.name) )
                    biphoneme.increaseFrequency(frequency) 
                    self.biphonemes_pre.append(biphoneme)

        #Track the cooccurences of phonemes pairs in the last consonnants group
        if lastVowelPos <= len(phonemes) - 3 :
            for pos1,phoneme1 in enumerate(phonemes[lastVowelPos+1:-1]) :
                for phoneme2 in phonemes[lastVowelPos+pos1+2:]:
                    biphoneme  = Syllable.postVowelBiphonemeCol.getBiphoneme( \
                                    (phoneme1.name, phoneme2.name) )
                    biphoneme.increaseFrequency(frequency) 
                    self.biphonemes_post.append(biphoneme)
        
        #Track the cases where multiple vowels are part of the middle (inclue semivowels??)
        if firstVowelPos < lastVowelPos :
            for pos1,phoneme1 in enumerate(phonemes[firstVowelPos:lastVowelPos]) :
                for phoneme2 in phonemes[firstVowelPos+pos1+1:lastVowelPos+1]:
                    biphoneme  = Syllable.multiVowelBiphonemeCol.getBiphoneme( \
                                    (phoneme1.name, phoneme2.name) )
                    biphoneme.increaseFrequency(frequency) 
                    self.biphonemes_vowel.append(biphoneme)
        
        self.frequency = frequency
        self.spellings[spelling] = frequency

    def increaseFrequency(self, frequency: float):
        self.frequency += frequency
        for pos,phoneme in enumerate(self.phonemes) :
            phoneme.increaseFrequency(frequency, pos=pos, invPos=len(self.phonemes)-pos-1)
        for phoneme in self.phonemes_pre :
            phoneme.increaseFrequency(frequency)
        for phoneme in self.phonemes_post :
            phoneme.increaseFrequency(frequency)
        for phoneme in self.phonemes_vowel :
            phoneme.increaseFrequency(frequency)
        for biphoneme in self.biphonemes_pre:
            biphoneme.increaseFrequency(frequency)
        for biphoneme in self.biphonemes_post:
            biphoneme.increaseFrequency(frequency)
        for biphoneme in self.biphonemes_vowel:
            biphoneme.increaseFrequency(frequency)

    def increaseSpellingFrequency(self, spelling: str, frequency: float):
        spelling_frequency = self.spellings.get(spelling, 0.0) + frequency
        self.spellings[spelling] = spelling_frequency
        self.increaseFrequency(frequency)

    def printTopPhonemesPerPosition(nb: int =-1 ):
        Syllable.phonemeCol.printTopPhonemesPerPosition( nb )

    def printTopPhonemesPerInvPosition(nb: int =-1 ):
        Syllable.phonemeCol.printTopPhonemesPerInvPosition( nb )

    def printTopPhonemes(nb: int =-1 ):
        print("Whole words phonemes:")
        Syllable.phonemeCol.printTopPhonemes( nb )
        print("Pre-vowel phonemes :")
        Syllable.preVowelPhonemeCol.printTopPhonemes( nb )
        print("Vowel phonemes :")
        Syllable.vowelPhonemeCol.printTopPhonemes( nb )
        print("Post-vowel phonemes :")
        Syllable.postVowelPhonemeCol.printTopPhonemes( nb )

    def printTopBiphonemes(nb: int =-1 ):
        print("Pre-vowels biphonemes")
        Syllable.preVowelBiphonemeCol.printTopBiphonemes( nb )
        print("Vowel biphonemes")
        Syllable.multiVowelBiphonemeCol.printTopBiphonemes( nb )
        print("Post-vowels biphonemes")
        Syllable.postVowelBiphonemeCol.printTopBiphonemes( nb )

    def optimizeBiphonemeOrder() :
        print("Left hand optimization :")
        #for i in range(10):
        order = Syllable.preVowelBiphonemeCol.optimizeOrder()
        Syllable.preVowelPhonemeCol.printBarchart(order)

        print("Right hand optimization :")
        #for i in range(10):
        order = Syllable.postVowelBiphonemeCol.optimizeOrder()
        Syllable.postVowelPhonemeCol.printBarchart(order)

        print("Vowel optimization :")
        #for i in range(10):
        order = Syllable.multiVowelBiphonemeCol.optimizeOrder()
        Syllable.vowelPhonemeCol.printBarchart(order)
        print("")

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
                ", ".join([str(spel)+": %.1f"%freq for (spel,freq) in \
                    self.sortedSpellings()[:4]]) \
                + " > SyllFreq " + "%.1f %.1f"%(self.frequency, 
                    sum([freq for (spel,freq) in self.sortedSpellings()[:4]]))

class SyllableCollection :
    """
    Collection of all Syllables found in a lexicon/corpus
    
    syllable_names: {str : Syllable}
    syllables : [Syllable]
    """
    syllable_names = {} 
    syllables = []

    def updateSyllable(self, syllable_name:str, spelling: str, addedfrequency: float):
        """ Updates syllable from collection, adding missing ones if needed """
        if syllable_name not in self.syllable_names:
            s = Syllable(syllable_name, spelling)
            self.syllable_names[syllable_name] = s
            self.syllables.append(s)
        # Adds the spelling if it is missing
        self.syllable_names[syllable_name].increaseSpellingFrequency(spelling, addedfrequency) 

    def getSyllable(self, syllable_name:str, spelling: str, frequency : float = 0.0):
        """ Get syllable from collection, adding missing ones if needed """
        self.updatSyllable(syllable_name, spelling, frequency)
        return self.syllable_names[syllable_name] 
    
    def printTopSyllables(self, nb: int = -1) :
        self.syllables.sort(reverse=True)
        for syl in self.syllables[:nb] :
            print("Syllable:",str(syl))

