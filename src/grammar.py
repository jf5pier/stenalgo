#!/usr/bin/python
# coding: utf-8
#
import sys
from dataclasses import dataclass
from itertools import permutations, chain
from copy import deepcopy
from src.word import Word
import numpy as np
from tqdm import tqdm


@dataclass
class Phoneme:
    """
    Representation of the parts of a Syllable

    name : str
        Single char X-Sampa representation of the phoneme
        (Based on the Lexiques's version of X-Sampa that has 1
        ascii character representation of each phoneme)
    frequency : float
        Frequency of occurence in the underlying lexicon/corpus
    """

    name: str
    frequency: float = 0.0

    # There's an argument to have "w" and "j" as part of the vowels
    nucleusPhonemes: str   = "aeiE@o°§uy5O9821"  #X-Sampa alphabet with "5@§1aGN8°" for "e~a~o~g~ANJH@"
#    nucleusPhonemesIPA: str= "aeiɛɑ̃o°ɔ̃uyɛ̃ɔœɥøœ̃"  #Nasal are 2 chars istead of 1"
    consonantPhonemes: str    = "RtsplkmdvjnfbZwzSgNG"
 #   consonantPhonemesIPA: str = "ʀtsplkmdvjnfbʒwzʃgɲŋ"

    def __post_init__(self) -> None:
        # 7 phonemes is the max per syll
        self.posFrequency = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.invPosFrequency = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    def increaseFrequency(self, frequency: float, pos: int = 0, invPos: int = 0):
        self.frequency += frequency
        self.posFrequency[pos] += frequency
        self.invPosFrequency[invPos] += frequency

    def isVowel(self) -> bool:
        return self.name in self.nucleusPhonemes

    def isConsonant(self) -> bool:
        return self.name in self.consonantPhonemes

    def __eq__(self, other) -> bool:
        if type(other) is Phoneme:
            return self.name == other.name
        elif type(other) is str:
            return self.name == other
        else : return False

    def __lt__(self, other) -> bool:
        return self.frequency < other.frequency

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name + ":" + "%.1f" % self.frequency


@dataclass
class Biphoneme:
    """
    Coocurence of two phonemes in a group of phonemes (syllable or other)

    pair : (str, str)
        Pair of phonemes
    frequency :
        Occurence frequency of the pair of phoenemes
    """

    pair: tuple[str, str]
    frequency: float = 0.0

    def increaseFrequency(self, frequency: float):
        self.frequency += frequency

    def __eq__(self, other) -> bool:
        if isinstance(other, Biphoneme):
            return self.pair == other.pair
        return False

    def __lt__(self, other) -> bool:
        return self.frequency < other.frequency

    def __str__(self) -> str:
        return "(%s, %s)" % (self.pair[0], self.pair[1])

    def __repr__(self) -> str:
        return self.pair[0] + self.pair[1] + ":" + "%.1f" % self.frequency


class PhonemeCollection:
    """
    Collection of Phonemes representing the existing sounds of a lexicon/corpus

    syllabicPart : str
        Part of the syllable in which the phoneme is found (all, onset, nucleus, coda)
    phonemesNames: {str:Phoneme}
        Dictionnary where each phoneme name is used as key to find its Phonem object
    phonemes : [Phoneme]
        List of all Phonemes found in this part of the syllables
    """

    def __init__(self, syllabicPart: str) -> None:
        self.syllabicPart: str = syllabicPart
        self.phonemeNames: dict[str, Phoneme] = {}
        self.phonemes: list[Phoneme] = []

    def getPhonemes(self, phoneme_names: str) -> list[Phoneme]:
        """Get phonemes from collection, adding missing ones if needed"""
        ret: list[Phoneme] = []
        for phoneme_name in phoneme_names:
            if phoneme_name not in self.phonemeNames:
                p = Phoneme(phoneme_name)
                self.phonemeNames[phoneme_name] = p
                self.phonemes.append(p)

            ret.append(self.phonemeNames[phoneme_name])
        return ret

    def getPhoneme(self, phoneme_name: str) -> Phoneme:
        return self.getPhonemes(phoneme_name)[0]

    def printTopPhonemes(self, nb: int = -1) -> None:
        self.phonemes.sort(reverse=True)
        print("Top phonemes:", self.phonemes[:nb], "\n")

    def printTopPhonemesPerPosition(self, nb: int = -1) -> None:
        for i in range(7):
            self.phonemes.sort(key=lambda p: p.posFrequency[i], reverse=True)
            print("Phonemes in pos %i" % i,
                list(map(lambda p: (p.name, "%.1f" % p.posFrequency[i]),
                        self.phonemes[:nb],)),
                "\n",
            )

    def printTopPhonemesPerInvPosition(self, nb: int = -1) -> None:
        for i in range(7):
            self.phonemes.sort(key=lambda p: p.invPosFrequency[i], reverse=True)
            print("Phonemes in inverted pos -%i" % (i + 1),
                list(map(lambda p: (p.name, "%.1f" % p.invPosFrequency[i]),
                        self.phonemes[:nb],)),
                "\n",
            )

    def printBarchart(self, phoneme_order: str,
                      exhaustive_phonemes: str, vsize: int = 10) -> None:
        maxFreq = 0.0
        excludedPhonemes: list[str] = list(
            filter(lambda p: p not in phoneme_order, exhaustive_phonemes)
        )
        for phoneme_name in exhaustive_phonemes:
            maxFreq = max(maxFreq, self.phonemeNames[phoneme_name].frequency)
        for i in range(vsize, 0, -1):
            toPrint = "> "
            for phoneme_name in phoneme_order:
                phoneme = self.phonemeNames[phoneme_name]
                toPrint += (
                    phoneme.name if phoneme.frequency >= i * maxFreq / vsize else " "
                )
            toPrint += " | "
            for phoneme_name in excludedPhonemes:
                phoneme = self.phonemeNames[phoneme_name]
                toPrint += (
                    phoneme.name if phoneme.frequency >= i * maxFreq / vsize else " "
                )
            toPrint += " <"
            print(toPrint)
        print("> " + phoneme_order + " | " + "".join(excludedPhonemes) + " <")
        barsWidth: int = len(phoneme_order) + 3
        barsWidth2: int = len(excludedPhonemes) + 3
        print("^" * (barsWidth) + "|" + "^" * (barsWidth2))
        print(" " * (barsWidth - 8) + "ordered | floating", "\n")


class BiphonemeCollection:
    """
    Collection of pairs of phonemes found in syllables

    biphonemesNames: {(str,str):Biphoneme}
        Dict of pairs of phonemes serving as key to find the
        corresponding Biphoneme object
    biphonemes : list[Biphoneme]
        List of all Biphonemes found in this part of the syllables
    bestPermutation : str
        Permutation of all Phonemes in this part of the syllables based
        on the frequency of order of all Biphonemes found in the lexicon
    bestPermutationScore : float
        Total score of the best permutation of phonemes
    bestPermutationNegativeScore : float
        Negative portion of the score of the best permutation of phonemes
    """

    def __init__(self, syllabicPart: str) -> None:
        self.syllabicPart: str = syllabicPart
        self.biphonemeNames: dict[tuple[str, str], Biphoneme] = {}
        self.biphonemes: list[Biphoneme] = []
        self.bestPermutation: str = ""
        self.bestPermutationScore: float = 0.0
        self.bestPermutationNegativeScore: float = 0.0

    def getBiphonemes(self, biphonemeNames: list[tuple[str, str]]) -> list[Biphoneme]:
        """Get biphonemes from collection, adding missing ones if needed"""
        ret: list[Biphoneme] = []
        for biphonemeName in biphonemeNames:
            if biphonemeName not in self.biphonemeNames:
                bp = Biphoneme(biphonemeName)
                self.biphonemeNames[biphonemeName] = bp
                self.biphonemes.append(bp)

            ret.append(self.biphonemeNames[biphonemeName])
        return ret

    def getBiphoneme(self, biphonemeName: tuple[str, str]) -> Biphoneme:
        return self.getBiphonemes([biphonemeName])[0]

    def printTopBiphonemes(self, nb: int = -1) -> None:
        self.biphonemes.sort(reverse=True)
        print(
            "Biphonemes:",
            list(map(lambda bp: (bp.pair, "%.1f" % bp.frequency), self.biphonemes[:nb])
            ), "\n",
        )

    def getPhonemesNames(self) -> str:
        """Extract single phonemes names from pairs of phonemes"""
        left = set(map(lambda p: p.pair[0], self.biphonemes))
        right = set(map(lambda p: p.pair[1], self.biphonemes))
        return "".join(set(list(left) + list(right)))

    def optimizeOrder(self) -> None:
        """Optimize the order of the phonemes found in the biphonemes
        to reduce the frequency where two phonemes would be typed in
        the wrong order to produce a syllable."""
        score = 0
        phonemes = list(self.getPhonemesNames())
        np.random.shuffle(phonemes)
        bestPermutation = "".join(phonemes)
        (bestScore, bestNegScore, _) = self.scorePermutation("".join(phonemes))

        # The algorithm moves a window over the phonem string and tests
        # permutations in that window exclusively.  A window scan goes over
        # every phonem substring left to right, then right to left.
        windowSize = 4
        windowScans = 400
        maxShuffleSize = 7
        randOrder = np.array(range(len(phonemes)))
        print("Optimizing biphonemes order in syllabic part : " + self.syllabicPart)
        for _ in tqdm(list(range(windowScans)), ascii=True, ncols=80, unit=" phoneme shuffle scans"):
            np.random.shuffle(randOrder)
            shuffleSize = np.random.randint(2, maxShuffleSize)
            mutatedPermutation = list(deepcopy(bestPermutation))
            tmp = bestPermutation[randOrder[0]]
            for i in range(1, shuffleSize):
                mutatedPermutation[randOrder[i - 1]] = bestPermutation[randOrder[i]]
            mutatedPermutation[randOrder[shuffleSize - 1]] = tmp
            mutatedPermutation = "".join(mutatedPermutation)

            for pos in chain(
                range(len(phonemes) - windowSize),
                range(len(phonemes) - windowSize, 0, -1),
            ):
                subPhonemes = mutatedPermutation[pos : pos + windowSize]
                for permutation in permutations(subPhonemes):
                    subp = "".join(permutation)
                    p = (
                        mutatedPermutation[:pos] + subp
                        + mutatedPermutation[pos + windowSize :]
                    )
                    score, negScore, _ = self.scorePermutation(p)
                    if score > bestScore:
                        bestScore = score
                        bestNegScore = negScore
                        bestPermutation = p
                        #bestBadOrder = badOrder
        print(
            "\nBest order (ordered score %0.1f, disordered score %0.1f):\n"
            % (bestScore, bestNegScore),
            bestPermutation, "\n"
        )
        self.bestPermutation = bestPermutation
        self.bestPermutationScore = bestScore
        self.bestPermutationNegativeScore = bestNegScore


    def scorePermutation(self, permutation: str):
        score = 0.0
        negScore = 0.0
        badOrder: list[Biphoneme] = []
        for biphoneme in self.biphonemes:
            left, right = biphoneme.pair
            if permutation.index(left) < permutation.index(right):
                score += biphoneme.frequency
            else:
                score -= biphoneme.frequency
                negScore -= biphoneme.frequency
                badOrder.append(biphoneme)
        return score, negScore, badOrder


class Syllable:
    """
    Representation of a unique sound part of a word

    phonemes : [Phoneme]
        List of Phonemes sounding the Syllable
    spellings : {str: float}
        Dict of orthographic spelling that sound the same Syllable
    frequency : float
        Frequency of occurence in the underlying lexicon/corpus
    phonemeCol : PhonemeCollection
        Collection of Phonemes found in the underlying lexicon/corpus
    onsetPhonemCol : PhonemeCollection
        Collection of phonemes found before the vowels of a syllable
    codaPhonemCol : PhonemeCollection
        Collection of phonemes found after the vowels of a syllable
    nucleusPhonemCol : PhonemeCollection
        Collection phonemes found in the vowels part syllable
    onsetBiphonemCol : BiphonemeCollection
        Collection of pair of phonemes found before the vowels of a syllable
    codaBiphonemCol : BiphonemeCollection
        Collection of pair of phonemes found after the vowels of a syllable
    multiVowelBiphonemeCol : BiphonemeCollection
        Collection of pair of phonemes found in multi-vowels syllable
    phono_words : Word
        Dictionnary of words grouped by their phonology from the Lexicon that
        contain that syllable
    """

    phonemeCol: PhonemeCollection = PhonemeCollection("all")
    onsetPhonemCol: PhonemeCollection = PhonemeCollection("onset")
    nucleusPhonemCol: PhonemeCollection = PhonemeCollection("nucleus")
    codaPhonemCol: PhonemeCollection = PhonemeCollection("coda")
    onsetBiphonemCol: BiphonemeCollection = BiphonemeCollection("onset")
    multiVowelBiphonemeCol: BiphonemeCollection = BiphonemeCollection("nucleus")
    codaBiphonemCol: BiphonemeCollection = BiphonemeCollection("coda")

    def __init__(self, phoneme_names: str, spelling: str, frequency: float = 0.0) -> None:
        self.phonemes: list[Phoneme] = []
        self.name: str = ""
        self.phonemesOnset: list[Phoneme] = []
        self.phonemesCoda: list[Phoneme] = []
        self.phonemesNucleus: list[Phoneme] = []
        self.biphonemesOnset: list[Biphoneme] = []
        self.biphonemesCoda: list[Biphoneme] = []
        self.biphonemesNucleus: list[Biphoneme] = []
        self.spellings: dict[str, float] = {}
        self.phono_words: dict[str, list[Word]] = {}

        phonemes: list[Phoneme] = Syllable.phonemeCol.getPhonemes(phoneme_names)
        self.name = "".join(list(map(lambda p: p.name, phonemes)))
        self.frequency : float = frequency
        self.spellings[spelling] = frequency


        firstVowelPos = -1
        lastVowelPos = -1
        verbose = True if phoneme_names == "" else False
        for pos, phoneme in enumerate(phonemes):
            phoneme.increaseFrequency(
                frequency, pos=pos, invPos=len(phonemes) - pos - 1
            )
            if verbose:
                print(phoneme, phoneme.frequency)
            self.phonemes.append(phoneme)
            if firstVowelPos == -1 and not phoneme.isVowel():
                if verbose:
                    print("Left hand consonant", phoneme)
                onsetPhoneme = Syllable.onsetPhonemCol.getPhoneme(phoneme.name)
                onsetPhoneme.increaseFrequency(frequency)
                self.phonemesOnset.append(onsetPhoneme)
            elif firstVowelPos != -1 and not phoneme.isVowel():
                if verbose:
                    print("Right hand consonant", phoneme)
                codaPhoneme = Syllable.codaPhonemCol.getPhoneme(phoneme.name)
                codaPhoneme.increaseFrequency(frequency)
                self.phonemesCoda.append(codaPhoneme)
            # Break down the syllable into consonants-vowels-consonants
            if phoneme.isVowel():
                if verbose:
                    print("Vowel", phoneme)
                nucleusPhoneme = Syllable.nucleusPhonemCol.getPhoneme(phoneme.name)
                nucleusPhoneme.increaseFrequency(frequency)
                self.phonemesNucleus.append(nucleusPhoneme)

                if firstVowelPos == -1:
                    firstVowelPos = pos
                lastVowelPos = pos

        # Track the cooccurences of phonemes pairs in the first
        # consonnants group
        if firstVowelPos >= 2:
            for pos1, phoneme1 in enumerate(phonemes[: firstVowelPos - 1]):
                for phoneme2 in phonemes[pos1 + 1 : firstVowelPos]:
                    biphoneme = Syllable.onsetBiphonemCol.getBiphoneme(
                        (phoneme1.name, phoneme2.name)
                    )
                    biphoneme.increaseFrequency(frequency)
                    if verbose:
                        print("Left hand biphoneme", biphoneme)
                    self.biphonemesOnset.append(biphoneme)

        # Track the cooccurences of phonemes pairs in the last
        # consonnants group
        if lastVowelPos <= len(phonemes) - 3:
            for pos1, phoneme1 in enumerate(phonemes[lastVowelPos + 1 : -1]):
                for phoneme2 in phonemes[lastVowelPos + pos1 + 2 :]:
                    biphoneme = Syllable.codaBiphonemCol.getBiphoneme(
                        (phoneme1.name, phoneme2.name)
                    )
                    biphoneme.increaseFrequency(frequency)
                    if verbose:
                        print("Right hand biphoneme", biphoneme)
                    self.biphonemesCoda.append(biphoneme)

        # Track the cases where multiple vowels are part of the
        # middle (inclue semivowels??)
        if firstVowelPos < lastVowelPos:
            for pos1, phoneme1 in enumerate(phonemes[firstVowelPos:lastVowelPos]):
                for phoneme2 in phonemes[firstVowelPos + pos1 + 1 : lastVowelPos + 1]:
                    biphoneme = Syllable.multiVowelBiphonemeCol.getBiphoneme(
                        (phoneme1.name, phoneme2.name)
                    )
                    biphoneme.increaseFrequency(frequency)
                    if verbose:
                        print("Vowel biphoneme", biphoneme)
                    self.biphonemesNucleus.append(biphoneme)

        # print("pho",self.phonemes, "pre",self.phonemes_onset,
        # "post",self.phonemes_coda,
        #      "vow",self.phonemes_nucleus, "bpre", self.biphonemes_onset, "bpost",
        #      self.biphonemes_coda, "bvow",self.biphonemes_nucleus)

    def increaseFrequency(self, frequency: float):
        self.frequency += frequency
        for pos, phoneme in enumerate(self.phonemes):
            phoneme.increaseFrequency(
                frequency, pos=pos, invPos=len(self.phonemes) - pos - 1
            )
        for phoneme in self.phonemesOnset:
            phoneme.increaseFrequency(frequency)
        for phoneme in self.phonemesCoda:
            phoneme.increaseFrequency(frequency)
        for phoneme in self.phonemesNucleus:
            phoneme.increaseFrequency(frequency)
        for biphoneme in self.biphonemesOnset:
            biphoneme.increaseFrequency(frequency)
        for biphoneme in self.biphonemesCoda:
            biphoneme.increaseFrequency(frequency)
        for biphoneme in self.biphonemesNucleus:
            biphoneme.increaseFrequency(frequency)

    def increaseSpellingFrequency(self, spelling: str, frequency: float):
        spelling_frequency = self.spellings.get(spelling, 0.0) + frequency
        self.spellings[spelling] = spelling_frequency
        self.increaseFrequency(frequency)

    @staticmethod
    def sortPhonemesCollections() -> None:
        Syllable.phonemeCol.phonemes.sort(reverse=True)
        Syllable.onsetPhonemCol.phonemes.sort(reverse=True)
        Syllable.codaPhonemCol.phonemes.sort(reverse=True)
        Syllable.nucleusPhonemCol.phonemes.sort(reverse=True)
        Syllable.onsetBiphonemCol.biphonemes.sort(reverse=True)
        Syllable.codaBiphonemCol.biphonemes.sort(reverse=True)
        Syllable.multiVowelBiphonemeCol.biphonemes.sort(reverse=True)

    def trackWord(self, word: Word):
        if word.phonology in self.phono_words:
            self.phono_words[word.phonology].append(word)
        else:
            self.phono_words[word.phonology] = [word]

    @staticmethod
    def printTopPhonemesPerPosition(nb: int = -1):
        Syllable.phonemeCol.printTopPhonemesPerPosition(nb)

    @staticmethod
    def printTopPhonemesPerInvPosition(nb: int = -1):
        Syllable.phonemeCol.printTopPhonemesPerInvPosition(nb)

    @staticmethod
    def printTopPhonemes(nb: int = -1):
        print("Whole words phonemes:")
        Syllable.phonemeCol.printTopPhonemes(nb)
        print("Pre-vowel (onset) phonemes :")
        Syllable.onsetPhonemCol.printTopPhonemes(nb)
        print("Vowel (nucleus) phonemes :")
        Syllable.nucleusPhonemCol.printTopPhonemes(nb)
        print("Post-vowel (coda) phonemes :")
        Syllable.codaPhonemCol.printTopPhonemes(nb)

    @staticmethod
    def printTopBiphonemes(nb: int = -1):
        print("Pre-vowels biphonemes")
        Syllable.onsetBiphonemCol.printTopBiphonemes(nb)
        print("Vowel biphonemes")
        Syllable.multiVowelBiphonemeCol.printTopBiphonemes(nb)
        print("Post-vowels biphonemes")
        Syllable.codaBiphonemCol.printTopBiphonemes(nb)

    @staticmethod
    def optimizeBiphonemeOrder() -> None:
        Syllable.onsetBiphonemCol.optimizeOrder()
        Syllable.codaBiphonemCol.optimizeOrder()
        Syllable.multiVowelBiphonemeCol.optimizeOrder()

    @staticmethod
    def printOptimizedBiphonemeOrder() -> None:
        print("Left hand (syllable onset) consonant optimization :")
        left_hand_order = Syllable.onsetBiphonemCol.bestPermutation
        Syllable.onsetPhonemCol.printBarchart(left_hand_order, Phoneme.consonantPhonemes)

        print("Thumbs (syllable nucleus) vowel optimization :")
        nucleus_order = Syllable.multiVowelBiphonemeCol.bestPermutation
        Syllable.nucleusPhonemCol.printBarchart(nucleus_order, Phoneme.nucleusPhonemes)

        print("Right hand (syllale coda) consonant optimization :")
        right_hand_order = Syllable.codaBiphonemCol.bestPermutation
        Syllable.codaPhonemCol.printBarchart(right_hand_order, Phoneme.consonantPhonemes)

        print("")

    def replacePhonemeInPos(self, phoneme1: Phoneme|str, phoneme2: Phoneme|str, pos: str):
        """Replace a phoneme in one of 3 positions in a syllable"""
        if pos == "onset":
            onset= "".join(map(str, self.phonemesOnset))
            onset= onset.replace(str(phoneme1), str(phoneme2))
            return (
                onset 
                + "".join(map(str, self.phonemesNucleus))
                + "".join(map(str, self.phonemesCoda))
            )
        elif pos == "coda":
            coda= "".join(map(str, self.phonemesCoda))
            coda= coda.replace(str(phoneme1), str(phoneme2))
            return (
                "".join(map(str, self.phonemesOnset))
                + "".join(map(str, self.phonemesNucleus))
                + coda 
            )
        elif pos == "nucleus":
            nucleus= "".join(map(str, self.phonemesNucleus))
            nucleus = nucleus.replace(str(phoneme1), str(phoneme2))
            return (
                "".join(map(str, self.phonemesOnset))
                + nucleus
                + "".join(map(str, self.phonemesCoda))
            )
        else:
            return "".join(map(str, self.phonemes))

    def sortedSpellings(self):
        spel_freq = [(k, v) for k, v in self.spellings.items()]
        spel_freq.sort(key=lambda kv: kv[1], reverse=True)
        return spel_freq

    def __eq__(self, other) -> bool:
        if isinstance(other, Syllable):
            return self.phonemes == other.phonemes
        return False

    def __lt__(self, other) -> bool:
        return self.frequency < other.frequency

    def __str__(self) -> str:
        return ( "".join([str(p) for p in self.phonemes])
            + " > " + ", ".join([
                    str(spel) + ": %.1f" % freq
                    for (spel, freq) in self.sortedSpellings()[:4]
                ])
            + " > SyllFreq " + "%.1f %.1f"
            % ( self.frequency,
                sum([freq for (_, freq) in self.sortedSpellings()[:4]]),
            )
        )


class SyllableCollection:
    """
    Collection of all Syllables found in a lexicon/corpus

    syllable_names: dict[str, Syllable]
    syllables : [Syllable]
    """

    syllable_names: dict[str, Syllable] = {}
    syllables: list[Syllable] = []

    def updateSyllable(self, syllable_name: str, spelling: str,
                       addedfrequency: float, word: Word | None = None,):
        """Updates syllable from collection, adding missing ones if needed"""
        if syllable_name not in self.syllable_names:
            s = Syllable(syllable_name, spelling)
            self.syllable_names[syllable_name] = s
            self.syllables.append(s)
        # Adds the spelling if it is missing
        self.syllable_names[syllable_name].increaseSpellingFrequency(
            spelling, addedfrequency
        )
        # Keep track of words using syllable
        if word is not None:
            self.syllable_names[syllable_name].trackWord(word)

    def getSyllable(self, syllable_name: str) -> Syllable | None:
        """Get syllable from collection, or None"""
        #if spelling is not None:
        #    self.updateSyllable(syllable_name, spelling, frequency)
        return self.syllable_names[syllable_name] \
            if syllable_name in self.syllable_names else None

    def getFrequency(self, syllable: Syllable | str) -> float:
        if type(syllable) is Syllable:
            name = syllable.name
        elif type(syllable) is str:
            name = syllable
        else:
            print("Type syllable|str not found", syllable)
            sys.exit(1)

        if name not in self.syllable_names:
            #print("Not found syllable", name)
            return 0.0
        else:
            # print("Found", name, self.syllable_names[name].frequency )
            return self.syllable_names[name].frequency

    def syllabicAmbiguityScore(self, phoneme1: str, phoneme2: str, pos: str) -> float:
        """Ambiguity is defined by the existance of two syllables that are
        different by only one phoneme, or that contain a pair of phonemes.
        If a single key is assigned to those different single phonemes or
        to that pair of phonemes or, then using that key will be ambigous.
        The score is defined by the frequency of the least frequent
        ambigous syllable of the pair."""

        def phonemesByPos(syllable: Syllable, pos: str):
            """Helper function"""
            if pos == "onset":
                return syllable.phonemesOnset
            elif pos == "coda":
                return syllable.phonemesCoda
            elif pos == "nucleus":
                return syllable.phonemesNucleus
            else:
                return ""

        phoneme1_syllables = list(
            filter(lambda s: phoneme1 in phonemesByPos(s, pos), self.syllables)
        )

        score: float = 0.0
        for syll1 in phoneme1_syllables:
            if phoneme2 in phonemesByPos(syll1, pos):
                # Case where both phonemes are part of the same syllable
                # This is a tripple ambiguity with the 2 syllables that only
                # contains one of the 2 phonemes. Score is the sum of the 2
                # least frequent syllables
                short_syllable1 = syll1.replacePhonemeInPos(phoneme1, "", pos)
                short_syllable2 = syll1.replacePhonemeInPos(phoneme2, "", pos)

                # short_syllable1.pop( syll1.index(phoneme2) )
                score += (
                    self.getFrequency(syll1.name)
                    + self.getFrequency(short_syllable1)
                    + self.getFrequency(short_syllable2)
                    - max(
                        self.getFrequency(syll1.name),
                        self.getFrequency(short_syllable1),
                        self.getFrequency(short_syllable2),
                    )
                )
            #                print("Score1",score)
            else:
                # Score is only defined by the 2 syllables that
                # have 1 phoneme different
                p1_to_p2 = syll1.replacePhonemeInPos(phoneme1, phoneme2, pos)
                score += min(self.getFrequency(syll1.name), self.getFrequency(p1_to_p2))
        #                print("Score2",score)
        return score

    def lexicalAmbiguityScore(self, phoneme1: str, phoneme2: str, pos: str) -> float:
        """Ambiguity is defined by the existance of two words that are
        different by only one phoneme, or that contain a pair of phonemes.
        If a single key is assigned to those different single phonemes or
        to that pair of phonemes, then using that key will be ambigous.
        The score is defined by the frequnecy of the sum of least frequent
        ambgious words."""

        def phonemesByPos(syllable: Syllable, pos: str):
            """Helper function"""
            if pos == "onset":
                return syllable.phonemesOnset
            elif pos == "coda":
                return syllable.phonemesCoda
            elif pos == "nucleus":
                return syllable.phonemesNucleus
            else:
                return ""

        phoneme1_syllables = list(
            filter(lambda s: phoneme1 in phonemesByPos(s, pos), self.syllables)
        )
        score: float = 0.0
        for syll1 in phoneme1_syllables:
            if phoneme2 in phonemesByPos(syll1, pos):
                # Case where both phonemes are part of the same syllable
                # This is a tripple ambiguity with the 2 syllables that only
                # contains one of the 2 phonemes. Score is the sum of the 2
                # least frequent syllables
                base_score_short1 = 0.0
                base_score_short2 = 0.0
                short_syllable1 = syll1.replacePhonemeInPos(phoneme1, "", pos)
                short_syllable2 = syll1.replacePhonemeInPos(phoneme2, "", pos)
                for phono_word1 in syll1.phono_words:
                    base_score1 = sum(map(lambda w: w.frequency, syll1.phono_words[phono_word1]))
                    word: Word = syll1.phono_words[phono_word1][0]
                    phono_short_word1 = word.replaceSyllables(
                        syll1.name, short_syllable1
                    )
                    phono_short_syll1 = self.getSyllable(phono_short_word1)
                    if phono_short_syll1 is not None:
                        phono_short_words1 = phono_short_syll1.phono_words
                        base_score_short1 = (
                            sum(map(lambda w: w.frequency, phono_short_words1[phono_short_word1]))
                            if phono_short_word1 in phono_short_words1
                            else 0.0
                        )

                    phono_short_word2 = word.replaceSyllables(
                        syll1.name, short_syllable2)
                    phono_short_syll2 = self.getSyllable(phono_short_word2)
                    if phono_short_syll2 is not None:
                        phono_short_words2 = phono_short_syll2.phono_words
                        base_score_short2 = (
                            sum(map(lambda w: w.frequency, phono_short_words2[phono_short_word2]))
                            if phono_short_word2 in phono_short_words2
                            else 0.0
                        )
                    least_scores = sum(sorted(
                        [base_score1, base_score_short1, base_score_short2])[:-1])
                    score += least_scores
            else:
                # Score is only defined by the 2 syllables that
                # have 1 phoneme different
                p1_to_p2 = syll1.replacePhonemeInPos(phoneme1, phoneme2, pos)
                for phono_word1 in syll1.phono_words:
                    base_score1 = sum(map(lambda w: w.frequency, syll1.phono_words[phono_word1]))
                    word = syll1.phono_words[phono_word1][0]
                    phono_word2 = word.replaceSyllables(syll1.name, p1_to_p2)
                    phono_syll2= self.getSyllable(p1_to_p2)
                    if phono_syll2 is not None :
                        phono_words2 = phono_syll2.phono_words
                        if phono_word2 in phono_words2:
                            base_score2 = sum(map(lambda w: w.frequency, phono_words2[phono_word2]))
                            score += min(base_score1, base_score2)
        return score

    def analysePhonemSyllabicAmbiguity(self):
        """Determines the ambiguity of assigning multiple phonemes to a
        single keypress. Low ambiguity mean a keypress can mean two
        different phonemes and the other keypressess of the syllable will
        give enough context to resolve the right phonem of the syllable."""

        def _getSyllabicAmbiguityScores(phonemes: str, pos: str):
            syllAmbiguity: dict[tuple[str,str], float] = {}
            for p1i, p1 in tqdm(list(enumerate(phonemes[:-1])), ascii=True, ncols=80, unit=" phonemes pairs"):
                for p2 in phonemes[p1i + 1 :]:
                    conflict = self.syllabicAmbiguityScore(p1, p2, pos)
                    syllAmbiguity[(p1, p2)] = conflict
            return {
                (k1, k2): v for (k1, k2), v in sorted(syllAmbiguity.items(),
                                                      key=lambda item: item[1]) } 
        
        print("Left hand ambiguity optimization")
        onset_inter_syll_ambiguity = _getSyllabicAmbiguityScores(Phoneme.consonantPhonemes, "onset")
        print("Middle keys ambiguity optimization")
        nucleus_inter_syll_ambiguity = _getSyllabicAmbiguityScores(Phoneme.nucleusPhonemes, "nucleus")
        print("Right hand ambiguity optimization")
        coda_inter_syll_ambiguity = _getSyllabicAmbiguityScores(Phoneme.consonantPhonemes, "coda")
        
        print("")
        return (onset_inter_syll_ambiguity, nucleus_inter_syll_ambiguity, coda_inter_syll_ambiguity)


    def analysePhonemLexicalAmbiguity(self):
        """Similairly to the Syllabic Ambiguity, but over the whole lexicon:
        determines if a key assigned  to two phonemes will create
        ambiguities when typing a full word. Low ambiguity means that the
        other keys in the syllable and the other syllables of the word
        provide enough context to identify which of the multiple phonemes
        assgined to a keypress to choose."""

        def _getLexicalAmbiguityScores(phonemes: str,  pos: str):
            lexicalAmbiguity: dict[tuple[str,str], float] = {}
            for p1i, p1 in tqdm(list(enumerate(phonemes[:-1])), ascii=True, ncols=80, unit=" phonemes pairs") :
                for p2 in phonemes[p1i + 1 :]:
                    conflict = self.lexicalAmbiguityScore(p1, p2, pos)
                    lexicalAmbiguity[(p1, p2)] = conflict
            return {
                (k1, k2): v for (k1, k2), v in sorted(lexicalAmbiguity.items(),
                                                      key=lambda item: item[1]) }

        print("Left hand ambiguity optimization")
        onset_inter_syll_ambiguity = _getLexicalAmbiguityScores(Phoneme.consonantPhonemes, "onset")
        print("Middle keys ambiguity optimization")
        nucleus_inter_syll_ambiguity = _getLexicalAmbiguityScores(Phoneme.nucleusPhonemes, "nucleus")
        print("Right hand ambiguity optimization")
        coda_inter_syll_ambiguity = _getLexicalAmbiguityScores(Phoneme.consonantPhonemes, "coda")

        return (onset_inter_syll_ambiguity, nucleus_inter_syll_ambiguity, coda_inter_syll_ambiguity)

    def printSyllacbicAmbiguityStats(self, sorted_onset: dict[tuple[str,str], float],
                                     sorted_nucleus: dict[tuple[str,str], float],
                                     sorted_coda: dict[tuple[str,str], float], nb: int = -1):

        print("Left hand syllabic minimal-ambiguity phonemes pairs")
        for (p1, p2), score in list(sorted_onset.items())[:nb]:
            print(" Pair:", p1, p2, "score: %.1f" % score)

        print("Vowels syllabic minimal-ambiguity phonemes pairs")
        for (p1, p2), score in list(sorted_nucleus.items())[:nb]:
            print(" Pair:", p1, p2, "score: %.1f" % score)

        print("Right hand syllabic minimal-ambiguity phonemes pairs")
        for (p1, p2), score in list(sorted_coda.items())[:nb]:
            print(" Pair:", p1, p2, "score: %.1f" % score)

    def printLexicalAmbiguityStats(self, sorted_onset: dict[tuple[str,str], float],
                                   sorted_nucleus: dict[tuple[str,str], float],
                                   sorted_coda: dict[tuple[str,str], float],  nb: int = -1):

        print("Left hand lexical minimal-ambiguity phonemes pairs")
        for (p1, p2), score in list(sorted_onset.items())[:nb]:
            print(" Pair:", p1, p2, "score: %.1f" % score)

        print("Vowels lexical minimal-ambiguity phonemes pairs")
        for (p1, p2), score in list(sorted_nucleus.items())[:nb]:
            print(" Pair:", p1, p2, "score: %.1f" % score)

        print("Right hand lexical minimal-ambiguity phonemes pairs")
        for (p1, p2), score in list(sorted_coda.items())[:nb]:
            print(" Pair:", p1, p2, "score: %.1f" % score)

    def printTopSyllables(self, nb: int = -1):
        self.syllables.sort(reverse=True)
        for syl in self.syllables[:nb]:
            print("Syllable:", str(syl))
