#!/usr/bin/python
# coding: utf-8
#
from dataclasses import dataclass

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
    def __post_init__(self) :
        # 7 phonemes is the max per syll
        self.posFrequency = [0.0,0.0,0.0,0.0,0.0,0.0,0.0] 
        self.invPosFrequency = [0.0,0.0,0.0,0.0,0.0,0.0,0.0] 

    def increaseFrequency(self, frequency: float, pos : int, invPos : int):
        self.frequency += frequency
        self.posFrequency[pos] += frequency
        self.invPosFrequency[invPos] += frequency

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
        phonemes = Syllable.phonemeCol.getPhonemes(phoneme_names)
        for pos,phoneme in enumerate(phonemes):
            phoneme.increaseFrequency(frequency, pos=pos, invPos=len(phonemes)-pos-1 )
            self.phonemes.append(phoneme)
        self.frequency = frequency
        self.spellings[spelling] = frequency

    def increaseFrequency(self, frequency: float):
        self.frequency += frequency
        for pos,phoneme in enumerate(self.phonemes) :
            phoneme.increaseFrequency(frequency, pos=pos, invPos=len(self.phonemes)-pos-1)

    def increaseSpellingFrequency(self, spelling: str, frequency: float):
        spelling_frequency = self.spellings.get(spelling, 0.0) + frequency
        self.spellings[spelling] = spelling_frequency
        self.increaseFrequency(frequency)

    def printTopPhonemesPerPosition(nb: int =-1 ):
        Syllable.phonemeCol.printTopPhonemesPerPosition( nb )

    def printTopPhonemesPerInvPosition(nb: int =-1 ):
        Syllable.phonemeCol.printTopPhonemesPerInvPosition( nb )

    def printTopPhonemes(nb: int =-1 ):
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
                ", ".join([str(spel)+": %.1f"%freq for (spel,freq) in \
                    self.sortedSpellings()[:4]]) \
                + " > SyllFreq " + "%.1f %.1f"%(self.frequency, 
                    sum([freq for (spel,freq) in self.sortedSpellings()[:4]]))

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

    def printTopPhonemPerPositon(self) :
        return