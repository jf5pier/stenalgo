#!/usr/bin/python
# coding: utf-8
#
import sys
from typing import ClassVar, Any, override
from dataclasses import dataclass
from itertools import permutations, chain
from copy import deepcopy
from src.word import Word
import numpy as np
from tqdm import tqdm
from rich.table import Table
from rich.console import Console
from multiprocessing import Process, Pipe
from multiprocessing.connection import Connection

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
    nucleusPhonemes: ClassVar[str] = "aeiE@o°§uy5O9821"  #X-Sampa alphabet with "5@§1aGN8°" for "e~a~o~g~ANJH@"
    consonantPhonemes: ClassVar[str] = "RtsplkmdvjnfbZwzSgNG"
    temporaryPhonemes: ClassVar[str] = "x"
    phonemesByPart: ClassVar[dict[str, str]]= {
        "onset": consonantPhonemes + temporaryPhonemes,
        "nucleus": nucleusPhonemes,
        "coda": consonantPhonemes + temporaryPhonemes
    }

    def __post_init__(self) -> None:
        # 7 phonemes is the max per syll
        self.posFrequency = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.invPosFrequency = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        if not (self.isVowel() or self.isConsonant()
                or self.isTemporaryPhoneme()):
            raise ValueError("Phoneme %s is not a vowel or consonant" % self.name)

    def increaseFrequency(self, frequency: float, pos: int = 0, invPos: int = 0):
        self.frequency += frequency
        self.posFrequency[pos] += frequency
        self.invPosFrequency[invPos] += frequency

    def isVowel(self) -> bool:
        return self.name in self.nucleusPhonemes

    def isConsonant(self) -> bool:
        return self.name in self.consonantPhonemes

    def isTemporaryPhoneme(self) -> bool:
        return self.name in self.temporaryPhonemes

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

    def printBarchart(self, phoneme_order: str, pairwise_order: dict[tuple[str,str],str],
                      exhaustive_phonemes: str, vsize: int = 10) -> None:
        maxFreq = 0.0
        excludedPhonemes: list[str] = list(
            filter(lambda p: p not in phoneme_order, exhaustive_phonemes)
        )
        for phoneme_name in exhaustive_phonemes:
            maxFreq = max(maxFreq, self.phonemeNames[phoneme_name].frequency)
        for i in range(vsize, 0, -1):
            toPrint = "┃ "
            for phoneme_name in phoneme_order:
                phoneme = self.phonemeNames[phoneme_name]
                toPrint += (
                    phoneme.name if phoneme.frequency >= i * maxFreq / vsize else " "
                )
            toPrint += " ┃ "
            for phoneme_name in excludedPhonemes:
                phoneme = self.phonemeNames[phoneme_name]
                toPrint += (
                    phoneme.name if phoneme.frequency >= i * maxFreq / vsize else " "
                )
            toPrint += " ┃"
            print(toPrint)
        print("┃ " + phoneme_order + " ┃ " + "".join(excludedPhonemes) + " ┃")
        barsWidth: int = len(phoneme_order) + 3
        barsWidth2: int = len(excludedPhonemes) + 3
        print("┗" + "━" * (barsWidth-1) + "╋" + "━" * (barsWidth2-1) +"┛")
        print(" " * (barsWidth - 8) + "ordered ┃ floating", "\n")

        print("Pairwise order of each pair of phonemes")
        all_phonemes_ordered = phoneme_order + "".join(excludedPhonemes)
        print(" ┃" + all_phonemes_ordered)
        print("━╋" + "━"*(len(all_phonemes_ordered)))
        for p1 in all_phonemes_ordered:
            toPrint = p1 + "┃"
            for p2 in all_phonemes_ordered:
                pair = (p1, p2)
                if pair in pairwise_order:
                    toPrint += pairwise_order[pair]
                else:
                    toPrint += "="
            print(toPrint)



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
    pairwiseBiphonemeOrder : dict[tuple[str, str], str]
        Prefered order of a pair of phonemes that maximises the order score
        ">" : phoneme1 occures more often to the left of phoneme2
        "<" : phoneme1 occures more often to the right of phoneme2
        "=" : phoneme1 and phoneme2's positions are independant
    pairwiseBiphonemeOrderScore : dict[tuple[str, str], float]
        Score difference between the order phoneme1:phoneme2 versus
        the order phoeme2:phoneme1
    """

    def __init__(self, syllabicPart: str) -> None:
        self.syllabicPart: str = syllabicPart
        self.biphonemeNames: dict[tuple[str, str], Biphoneme] = {}
        self.biphonemes: list[Biphoneme] = []
        self.bestPermutation: str = ""
        self.bestPermutationScore: float = 0.0
        self.bestPermutationNegativeScore: float = 0.0
        self.pairwiseBiphonemeOrder: dict[tuple[str, str], str] = {}
        self.pairwiseBiphonemeOrderScore: dict[tuple[str, str], float] = {}

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

    def registerBestPermutation(self, bestPermutation: str, bestScore: float, bestNegScore: float) -> None:
        self.bestPermutation = bestPermutation
        self.bestPermutationScore = bestScore
        self.bestPermutationNegativeScore = bestNegScore

    def optimizeOrder(self, send_end: Connection|None = None) -> None:
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
            mutatedPermutationList: list[str] = list(deepcopy(bestPermutation))
            tmp = bestPermutation[randOrder[0]]
            for i in range(1, shuffleSize):
                mutatedPermutationList[randOrder[i - 1]] = bestPermutation[randOrder[i]]
            mutatedPermutationList[randOrder[shuffleSize - 1]] = tmp
            mutatedPermutation: str = "".join(mutatedPermutationList)

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
        self.registerBestPermutation(bestPermutation, bestScore, bestNegScore)
        if send_end is not None :
            send_end.send((bestPermutation, bestScore, bestNegScore))


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

    def generateBiphonemeOrderMatrix(self) ->  None:
        """
        Generate a matrix of biphonemes order based on the best permutation
            stored in a dictionnary to be order-independant
        """
        bestPermut = list(self.bestPermutation)
        self.pairwiseBiphonemeOrder = {}
        for p1 in range(len(bestPermut) -1):
            phoneme1: str = bestPermut[p1]
            permut_without_phonem = bestPermut[:p1] + bestPermut[p1+1:]
            for p2 in range(len(permut_without_phonem)):
                phoneme2: str = permut_without_phonem[p2]
                left_permut = permut_without_phonem[:p2] + [phoneme1, phoneme2] + permut_without_phonem[p2+1:]
                right_permut = permut_without_phonem[:p2] + [phoneme2, phoneme1] + permut_without_phonem[p2+1:]
                left_score,_,_= self.scorePermutation("".join(left_permut))
                right_score,_,_= self.scorePermutation("".join(right_permut))
                if right_score < left_score:
                    self.pairwiseBiphonemeOrder[(phoneme1, phoneme2)] = ">"
                    self.pairwiseBiphonemeOrder[(phoneme2, phoneme1)] = "<"
                elif right_score > left_score :
                    self.pairwiseBiphonemeOrder[(phoneme1, phoneme2)] = "<"
                    self.pairwiseBiphonemeOrder[(phoneme2, phoneme1)] = ">"
                else :
                    self.pairwiseBiphonemeOrder[(phoneme1, phoneme2)] = "="
                    self.pairwiseBiphonemeOrder[(phoneme2, phoneme1)] = "="

                self.pairwiseBiphonemeOrderScore[(phoneme1, phoneme2)] = right_score - left_score




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
    phonemeColByPart["onset"]: PhonemeCollection
        Collection of phonemes found before the vowels of a syllable
    phonemeColByPart["nucleus"] : PhonemeCollection
        Collection phonemes found in the vowels part syllable
    phonemeColByPart["coda"]: PhonemeCollection
        Collection of phonemes found after the vowels of a syllable
    biphonemeColByPart["onset"] : BiphonemeCollection
        Collection of pair of phonemes found before the vowels of a syllable
    biphonemeColByPart["nucleus"] : BiphonemeCollection
        Collection of pair of phonemes found in multi-vowels syllable
    biphonemeColByPart["coda"] : BiphonemeCollection
        Collection of pair of phonemes found after the vowels of a syllable
    phonoWords : Word
        Dictionnary of words grouped by their phonology from the Lexicon that
        contain that syllable
    """

    allPhonemeCol: PhonemeCollection = PhonemeCollection("all")
    phonemeColByPart: dict[str, PhonemeCollection] = {
        "onset": PhonemeCollection("onset"),
        "nucleus": PhonemeCollection("nucleus"),
        "coda": PhonemeCollection("coda")
    }
    biphonemeColByPart: dict[str, BiphonemeCollection] = {
        "onset": BiphonemeCollection("onset"),
        "nucleus": BiphonemeCollection("nucleus"),
        "coda": BiphonemeCollection("coda")
    }

    def __init__(self, phoneme_names: str, spelling: str, frequency: float = 0.0) -> None:
        self.phonemes: list[Phoneme] = []
        self.name: str = ""
        self.phonemesByPart: dict[str, list[Phoneme]] = {
            "onset": [], "coda": [], "nucleus": []
        }
        self.biphonemesByPart: dict[str, list[Biphoneme]] = {
            "onset": [], "coda": [], "nucleus": []
        }
        self.spellings: dict[str, float] = {}
        self.phonoWords: dict[str, list[Word]] = {}

        phonemes: list[Phoneme] = Syllable.allPhonemeCol.getPhonemes(phoneme_names)
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
                onsetPhoneme = Syllable.phonemeColByPart["onset"].getPhoneme(phoneme.name)
                onsetPhoneme.increaseFrequency(frequency)
                self.phonemesByPart["onset"].append(onsetPhoneme)
            elif firstVowelPos != -1 and not phoneme.isVowel():
                if verbose:
                    print("Right hand consonant", phoneme)
                codaPhoneme = Syllable.phonemeColByPart["coda"].getPhoneme(phoneme.name)
                codaPhoneme.increaseFrequency(frequency)
                self.phonemesByPart["coda"].append(codaPhoneme)
            # Break down the syllable into consonants-vowels-consonants
            if phoneme.isVowel():
                if verbose:
                    print("Vowel", phoneme)
                nucleusPhoneme = Syllable.phonemeColByPart["nucleus"].getPhoneme(phoneme.name)
                nucleusPhoneme.increaseFrequency(frequency)
                self.phonemesByPart["nucleus"].append(nucleusPhoneme)

                if firstVowelPos == -1:
                    firstVowelPos = pos
                lastVowelPos = pos

        # Track the cooccurences of phonemes pairs in the first
        # consonnants group
        if firstVowelPos >= 2:
            for pos1, phoneme1 in enumerate(phonemes[: firstVowelPos - 1]):
                for phoneme2 in phonemes[pos1 + 1 : firstVowelPos]:
                    biphoneme = Syllable.biphonemeColByPart["onset"].getBiphoneme(
                        (phoneme1.name, phoneme2.name)
                    )
                    biphoneme.increaseFrequency(frequency)
                    if verbose:
                        print("Left hand biphoneme", biphoneme)
                    self.biphonemesByPart["onset"].append(biphoneme)

        # Track the cooccurences of phonemes pairs in the last
        # consonnants group
        if lastVowelPos <= len(phonemes) - 3:
            for pos1, phoneme1 in enumerate(phonemes[lastVowelPos + 1 : -1]):
                for phoneme2 in phonemes[lastVowelPos + pos1 + 2 :]:
                    biphoneme = Syllable.biphonemeColByPart["coda"].getBiphoneme(
                        (phoneme1.name, phoneme2.name)
                    )
                    biphoneme.increaseFrequency(frequency)
                    if verbose:
                        print("Right hand biphoneme", biphoneme)
                    self.biphonemesByPart["coda"].append(biphoneme)

        # Track the cases where multiple vowels are part of the
        # middle (inclue semivowels??)
        if firstVowelPos < lastVowelPos:
            for pos1, phoneme1 in enumerate(phonemes[firstVowelPos:lastVowelPos]):
                for phoneme2 in phonemes[firstVowelPos + pos1 + 1 : lastVowelPos + 1]:
                    biphoneme = Syllable.biphonemeColByPart["nucleus"].getBiphoneme(
                        (phoneme1.name, phoneme2.name)
                    )
                    biphoneme.increaseFrequency(frequency)
                    if verbose:
                        print("Vowel biphoneme", biphoneme)
                    self.biphonemesByPart["nucleus"].append(biphoneme)

        # print("pho",self.phonemes, "pre",self.phonemes_onset,
        # "post",self.phonemes_coda,
        #      "vow",self.phonemes_nucleus, "bpre", self.biphonemes_onset, "bpost",
        #      self.biphonemes_coda, "bvow",self.biphonemes_nucleus)
        #

    def phonemeNamesByPart(self) -> dict[str, list[str]]:
        return {"onset": list(map(lambda p: p.name, self.phonemesByPart["onset"])),
                "nucleus": list(map(lambda p: p.name, self.phonemesByPart["nucleus"])),
                "coda": list(map(lambda p: p.name, self.phonemesByPart["coda"]))}

    def increaseFrequency(self, frequency: float):
        self.frequency += frequency
        for pos, phoneme in enumerate(self.phonemes):
            phoneme.increaseFrequency(
                frequency, pos=pos, invPos=len(self.phonemes) - pos - 1
            )
        for syllabicPart in ["onset", "nucleus", "coda"]:
            for phoneme in self.phonemesByPart[syllabicPart]:
                phoneme.increaseFrequency(frequency)
            for biphoneme in self.biphonemesByPart[syllabicPart]:
                biphoneme.increaseFrequency(frequency)

    def increaseSpellingFrequency(self, spelling: str, frequency: float):
        spelling_frequency = self.spellings.get(spelling, 0.0) + frequency
        self.spellings[spelling] = spelling_frequency
        self.increaseFrequency(frequency)

    @staticmethod
    def sortPhonemesCollections() -> None:
        Syllable.allPhonemeCol.phonemes.sort(reverse=True)
        for syllabicPart in ["onset", "nucleus", "coda"]:
            Syllable.phonemeColByPart[syllabicPart].phonemes.sort(reverse=True)
            Syllable.biphonemeColByPart[syllabicPart].biphonemes.sort(reverse=True)

    def trackWord(self, word: Word):
        if word.phonology in self.phonoWords:
            self.phonoWords[word.phonology].append(word)
        else:
            self.phonoWords[word.phonology] = [word]

    @staticmethod
    def printTopPhonemesPerPosition(nb: int = -1):
        Syllable.allPhonemeCol.printTopPhonemesPerPosition(nb)

    @staticmethod
    def printTopPhonemesPerInvPosition(nb: int = -1):
        Syllable.allPhonemeCol.printTopPhonemesPerInvPosition(nb)

    @staticmethod
    def printTopPhonemes(nb: int = -1):
        print("Whole words phonemes:")
        Syllable.allPhonemeCol.printTopPhonemes(nb)
        print("Pre-vowel (onset) phonemes :")
        Syllable.phonemeColByPart["onset"].printTopPhonemes(nb)
        print("Vowel (nucleus) phonemes :")
        Syllable.phonemeColByPart["nucleus"].printTopPhonemes(nb)
        print("Post-vowel (coda) phonemes :")
        Syllable.phonemeColByPart["coda"].printTopPhonemes(nb)

    @staticmethod
    def printTopBiphonemes(nb: int = -1):
        print("Pre-vowels biphonemes")
        Syllable.biphonemeColByPart["onset"].printTopBiphonemes(nb)
        print("Vowel biphonemes")
        Syllable.biphonemeColByPart["nucleus"].printTopBiphonemes(nb)
        print("Post-vowels biphonemes")
        Syllable.biphonemeColByPart["coda"].printTopBiphonemes(nb)

    @staticmethod
    def optimizeBiphonemeOrder_old() -> None:
        Syllable.biphonemeColByPart["onset"].optimizeOrder()
        Syllable.biphonemeColByPart["coda"].optimizeOrder()
        Syllable.biphonemeColByPart["nucleus"].optimizeOrder()

    @staticmethod
    def optimizeBiphonemeOrder() -> None:
        send1, recv1 = Pipe()
        p1 = Process(target = Syllable.biphonemeColByPart["onset"].optimizeOrder, args=(send1,))
        p1.start()
        send2, recv2 = Pipe()
        p2 = Process(target = Syllable.biphonemeColByPart["coda"].optimizeOrder, args=(send2,))
        p2.start()
        send3, recv3 = Pipe()
        p3 = Process(target = Syllable.biphonemeColByPart["nucleus"].optimizeOrder, args=(send3,))
        p3.start()
        p1.join()
        p2.join()
        p3.join()
        Syllable.biphonemeColByPart["onset"].registerBestPermutation(*(recv1.recv()))
        Syllable.biphonemeColByPart["coda"].registerBestPermutation(*(recv2.recv()))
        Syllable.biphonemeColByPart["nucleus"].registerBestPermutation(*(recv3.recv()))

        Syllable.biphonemeColByPart["onset"].generateBiphonemeOrderMatrix()
        Syllable.biphonemeColByPart["coda"].generateBiphonemeOrderMatrix()
        Syllable.biphonemeColByPart["nucleus"].generateBiphonemeOrderMatrix()

    @staticmethod
    def printOptimizedBiphonemeOrder() -> None:
        print("Left hand (syllable onset) consonant optimization :")
        left_hand_order = Syllable.biphonemeColByPart["onset"].bestPermutation
        left_hand_pairwise_order = Syllable.biphonemeColByPart["onset"].pairwiseBiphonemeOrder
        Syllable.phonemeColByPart["onset"].printBarchart(left_hand_order, 
                                              left_hand_pairwise_order,
                                              Phoneme.consonantPhonemes)

        print("Thumbs (syllable nucleus) vowel optimization :")
        nucleus_order = Syllable.biphonemeColByPart["nucleus"].bestPermutation
        nucleus_pairwise_order = Syllable.biphonemeColByPart["nucleus"].pairwiseBiphonemeOrder
        Syllable.phonemeColByPart["nucleus"].printBarchart(nucleus_order, 
                                                nucleus_pairwise_order,
                                                Phoneme.nucleusPhonemes)

        print("Right hand (syllable coda) consonant optimization :")
        right_hand_order = Syllable.biphonemeColByPart["coda"].bestPermutation
        right_hand_pairwise_order = Syllable.biphonemeColByPart["coda"].pairwiseBiphonemeOrder
        Syllable.phonemeColByPart["coda"].printBarchart(right_hand_order, 
                                             right_hand_pairwise_order,
                                             Phoneme.consonantPhonemes)

        print("")

    @staticmethod
    def phonemeCollectionByPart(syllabicPart:str) -> PhonemeCollection:
        return Syllable.phonemeColByPart[syllabicPart]

    @staticmethod
    def biphonemeCollectionByPart(syllabicPart:str) -> BiphonemeCollection:
        return Syllable.biphonemeColByPart[syllabicPart]

    def replacePhonemeInSyllabicPart(self, phoneme1: Phoneme|str, phoneme2: Phoneme|str, syllabicPart: str):
        """Replace a phoneme in one of 3 positions in a syllable"""
        if syllabicPart == "onset":
            onset= "".join(map(str, self.phonemesByPart["onset"]))
            onset= onset.replace(str(phoneme1), str(phoneme2))
            return (
                onset 
                + "".join(map(str, self.phonemesByPart["nucleus"]))
                + "".join(map(str, self.phonemesByPart["coda"]))
            )
        elif syllabicPart == "coda":
            coda= "".join(map(str, self.phonemesByPart["coda"]))
            coda= coda.replace(str(phoneme1), str(phoneme2))
            return (
                "".join(map(str, self.phonemesByPart["onset"]))
                + "".join(map(str, self.phonemesByPart["nucleus"]))
                + coda 
            )
        elif syllabicPart == "nucleus":
            nucleus= "".join(map(str, self.phonemesByPart["nucleus"]))
            nucleus = nucleus.replace(str(phoneme1), str(phoneme2))
            return (
                "".join(map(str, self.phonemesByPart["onset"]))
                + nucleus
                + "".join(map(str, self.phonemesByPart["coda"]))
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

    syllable_names: dict[str, Syllable]
    syllables: list[Syllable]

    def __init__(self) -> None:
        self.syllable_names = {}
        self.syllables = []


    @override
    def __str__(self) -> str:
        return "SyllableCollection with %i syllables and %i syllable_names" %(len(self.syllables), len(self.syllable_names))

    @override
    def __repr__(self) -> str:
        return self.__str__()

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

    def syllabicAmbiguityScore(self, phoneme1: str, phoneme2: str, syllabicPart: str) -> float:
        """Ambiguity is defined by the existance of two syllables that are
        different by only one phoneme, or that contain a pair of phonemes.
        If a single key is assigned to those different single phonemes or
        to that pair of phonemes or, then using that key will be ambigous.
        The score is defined by the frequency of the least frequent
        ambigous syllable of the pair."""

        phoneme1_syllables = list(
            filter(lambda syll: phoneme1 in syll.phonemesByPart[syllabicPart], self.syllables)
        )

        score: float = 0.0
        for syll1 in phoneme1_syllables:
            if phoneme2 in syll1.phonemesByPart[syllabicPart]:
                # Case where both phonemes are part of the same syllable
                # This is a tripple ambiguity with the 2 syllables that only
                # contains one of the 2 phonemes. Score is the sum of the 2
                # least frequent syllables
                short_syllable1 = syll1.replacePhonemeInSyllabicPart(phoneme1, "", syllabicPart)
                short_syllable2 = syll1.replacePhonemeInSyllabicPart(phoneme2, "", syllabicPart)

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
                p1_to_p2 = syll1.replacePhonemeInSyllabicPart(phoneme1, phoneme2, syllabicPart)
                score += min(self.getFrequency(syll1.name), self.getFrequency(p1_to_p2))
        #                print("Score2",score)
        return score

    def lexicalAmbiguityScore(self, phoneme1: str, phoneme2: str, syllabicPart: str) -> float:
        """Ambiguity is defined by the existance of two words that are
        different by only one phoneme, or that contain a pair of phonemes.
        If a single key is assigned to those different single phonemes or
        to that pair of phonemes, then using that key will be ambigous.
        The score is defined by the frequnecy of the sum of least frequent
        ambgious words."""

        phoneme1_syllables = list(
            filter(lambda syll: phoneme1 in syll.phonemesByPart[syllabicPart], self.syllables)
        )
        score: float = 0.0
        for syll1 in phoneme1_syllables:
            if phoneme2 in list(map(str, syll1.phonemesByPart[syllabicPart])) :
                # Case where both phonemes are part of the same syllable
                # This is a tripple ambiguity with the 2 syllables that only
                # contains one of the 2 phonemes. Score is the sum of the 2
                # least frequent syllables
                # French example : if a single key represented both "p" and "l" phonemes,
                # we would get a triple ambiguity with words "plurent", "lurent", and "purent"
                # and all other words matching phonology regex "^(p|l|pl)uR"
                short_syllable1 = syll1.replacePhonemeInSyllabicPart(phoneme1, "", syllabicPart)
                short_syllable2 = syll1.replacePhonemeInSyllabicPart(phoneme2, "", syllabicPart)
                for phono_word1 in syll1.phonoWords:
                    base_score1: float = sum(map(lambda w: w.frequency, syll1.phonoWords[phono_word1]))
                    base_words_ortho = list(map(lambda w: w.ortho, syll1.phonoWords[phono_word1]))
                    word: Word = syll1.phonoWords[phono_word1][0]
                    phono_short_word1 = word.replaceSyllables(
                        syll1.name, short_syllable1
                    )
                    phono_short_syll1 = self.getSyllable(phono_short_word1)
                    listOrthoOtherWords1 = []
                    base_score_short1: float = 0.0
                    if phono_short_syll1 is not None:
                        phono_short_words1 = phono_short_syll1.phonoWords
                        base_score_short1 = (
                            sum(map(lambda w: w.frequency, phono_short_words1[phono_short_word1]))
                            if phono_short_word1 in phono_short_words1
                            else 0.0
                        )
                        listOrthoOtherWords1 = [phono_short_word1]+ list(
                            map(lambda w: w.ortho, phono_short_words1[phono_short_word1])
                            if phono_short_word1 in phono_short_words1
                            else []
                        )

                    phono_short_word2 = word.replaceSyllables(
                        syll1.name, short_syllable2)
                    phono_short_syll2 = self.getSyllable(phono_short_word2)
                    listOrthoOtherWords2 = []
                    base_score_short2: float = 0.0
                    if phono_short_syll2 is not None:
                        phono_short_words2 = phono_short_syll2.phonoWords
                        base_score_short2  = (
                            sum(map(lambda w: w.frequency, phono_short_words2[phono_short_word2]))
                            if phono_short_word2 in phono_short_words2
                            else 0.0
                        )
                        listOrthoOtherWords2 = [phono_short_word2]+ list(
                            map(lambda w: w.ortho, phono_short_words2[phono_short_word2])
                            if phono_short_word2 in phono_short_words2
                            else []
                        )

                    least_scores = sum(sorted(
                        [base_score1, base_score_short1, base_score_short2])[:-1])
                    score += least_scores
                    # if (phoneme1, phoneme2) in [("p","l"), ("l","p")] and least_scores > 0.0 and syllabicPart == "onset":
                    #     print("AMBIGUITY1,", ",".join(map(str,[phoneme1, phoneme2, syll1.name, phono_word1,
                    #         base_score1, base_words_ortho, base_score_short1, listOrthoOtherWords1, 
                    #         base_score_short2, listOrthoOtherWords2, "%.1f"%least_scores, "%.1f"%score, word.ortho
                    #         ])))

            else:
                # Score is only defined by the 2 syllables that
                # have 1 phoneme different
                p1_to_p2 = syll1.replacePhonemeInSyllabicPart(phoneme1, phoneme2, syllabicPart)
                for phono_word1 in syll1.phonoWords:
                    base_score1 = sum(map(lambda w: w.frequency, syll1.phonoWords[phono_word1]))
                    word = syll1.phonoWords[phono_word1][0]
                    phono_word2 = word.replaceSyllables(syll1.name, p1_to_p2)
                    phono_syll2= self.getSyllable(p1_to_p2)
                    if phono_syll2 is not None :
                        phono_words2 = phono_syll2.phonoWords
                        if phono_word2 in phono_words2:
                            base_score2: float = sum(map(lambda w: w.frequency, phono_words2[phono_word2]))
                            least_scores = min(base_score1, base_score2)
                            score += least_scores
                            # if (phoneme1, phoneme2) in [("p","l"), ("l","p")] and least_scores > 0.0 and syllabicPart == "onset":
                            #     print("AMBIGUITY2,", ",".join(map(str, [phoneme1, phoneme2, syll1.name, len(phono_word1), phono_word1,
                            #         base_score1, base_score2, 0.0, least_scores, score])))
        return score

    def analysePhonemSyllabicAmbiguity_old(self):
        """Determines the ambiguity of assigning multiple phonemes to a
        single keypress. Low ambiguity mean a keypress can mean two
        different phonemes and the other keypressess of the syllable will
        give enough context to resolve the right phonem of the syllable."""

        def _getSyllabicAmbiguityScores(phonemes: str, syllabicPart: str):
            syllAmbiguity: dict[tuple[str,str], float] = {}
            for p1i, p1 in tqdm(list(enumerate(phonemes[:-1])), ascii=True, ncols=80, unit=" phonemes pairs"):
                for p2 in phonemes[p1i + 1 :]:
                    conflict = self.syllabicAmbiguityScore(p1, p2, syllabicPart)
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

    def analysePhonemSyllabicAmbiguity(self):
        """Determines the ambiguity of assigning multiple phonemes to a
        single keypress. Low ambiguity mean a keypress can mean two
        different phonemes and the other keypressess of the syllable will
        give enough context to resolve the right phonem of the syllable."""

        def _getSyllabicAmbiguityScores(phonemes: str, syllabicPart: str, send_end) -> None:
            syllAmbiguity: dict[tuple[str,str], float] = {}
            for p1i, p1 in tqdm(list(enumerate(phonemes[:-1])), ascii=True, ncols=80, unit=" phonemes pairs"):
                for p2 in phonemes[p1i + 1 :]:
                    conflict = self.syllabicAmbiguityScore(p1, p2, syllabicPart)
                    syllAmbiguity[(p1, p2)] = conflict

            send_end.send({
                 (k1, k2): v for (k1, k2), v in sorted(syllAmbiguity.items(),
                                                       key=lambda item: item[1]) 
            })

        print("Left hand ambiguity optimization")
        onset_recv, onset_send = Pipe()
        p1 = Process(target = _getSyllabicAmbiguityScores, args = (Phoneme.consonantPhonemes, "onset", onset_send))
        p1.start()

        print("Middle keys ambiguity optimization")
        nucleus_recv, nucleus_send = Pipe()
        p2 = Process(target = _getSyllabicAmbiguityScores, args = (Phoneme.nucleusPhonemes, "nucleus", nucleus_send))
        p2.start()

        print("Right hand ambiguity optimization")
        coda_recv, coda_send = Pipe()
        p3 = Process(target = _getSyllabicAmbiguityScores, args = (Phoneme.consonantPhonemes, "coda", coda_send))
        p3.start()

        p1.join()
        p2.join()
        p3.join()
        print("")
        return(onset_recv.recv(), nucleus_recv.recv(), coda_recv.recv())

    def analysePhonemLexicalAmbiguity_old(self):
        """Similairly to the Syllabic Ambiguity, but over the whole lexicon:
        determines if a key assigned  to two phonemes will create
        ambiguities when typing a full word. Low ambiguity means that the
        other keys in the syllable and the other syllables of the word
        provide enough context to identify which of the multiple phonemes
        assgined to a keypress to choose."""

        def _getLexicalAmbiguityScores(phonemes: str,  syllabicPart: str):
            lexicalAmbiguity: dict[tuple[str,str], float] = {}
            for p1i, p1 in tqdm(list(enumerate(phonemes[:-1])), ascii=True, ncols=80, unit=" phonemes pairs") :
                for p2 in phonemes[p1i + 1 :]:
                    conflict = self.lexicalAmbiguityScore(p1, p2, syllabicPart)
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

    def analysePhonemLexicalAmbiguity(self):
        """Similairly to the Syllabic Ambiguity, but over the whole lexicon:
        determines if a key assigned  to two phonemes will create
        ambiguities when typing a full word. Low ambiguity means that the
        other keys in the syllable and the other syllables of the word
        provide enough context to identify which of the multiple phonemes
        assgined to a keypress to choose."""

        def _getLexicalAmbiguityScores(phonemes: str,  syllabicPart: str, send_end):
            lexicalAmbiguity: dict[tuple[str,str], float] = {}
            for p1i, p1 in tqdm(list(enumerate(phonemes[:-1])), ascii=True, ncols=80, unit=" phonemes pairs") :
                for p2 in phonemes[p1i + 1 :]:
                    conflict = self.lexicalAmbiguityScore(p1, p2, syllabicPart)
                    lexicalAmbiguity[(p1, p2)] = conflict
            send_end.send({
                (k1, k2): v for (k1, k2), v in sorted(lexicalAmbiguity.items(),
                                                      key=lambda item: item[1]) })

        print("Left hand ambiguity optimization")
        onset_send, onset_recv = Pipe()
        #onset_inter_syll_ambiguity = _getLexicalAmbiguityScores(Phoneme.consonantPhonemes, "onset")
        p1 = Process(target = _getLexicalAmbiguityScores, args = (Phoneme.consonantPhonemes, "onset", onset_send))
        p1.start()
        print("Middle keys ambiguity optimization")
        nucleus_send, nucleus_recv = Pipe()
        #nucleus_inter_syll_ambiguity = _getLexicalAmbiguityScores(Phoneme.nucleusPhonemes, "nucleus")
        p2 = Process(target = _getLexicalAmbiguityScores, args = (Phoneme.nucleusPhonemes, "nucleus", nucleus_send))
        p2.start()
        print("Right hand ambiguity optimization")
        coda_send, coda_recv = Pipe()
        #coda_inter_syll_ambiguity = _getLexicalAmbiguityScores(Phoneme.consonantPhonemes, "coda")
        p3 = Process(target = _getLexicalAmbiguityScores, args = (Phoneme.consonantPhonemes, "coda", coda_send))
        p3.start()
        
        p1.join()
        p2.join()
        p3.join()
        return (onset_recv.recv(), nucleus_recv.recv(), coda_recv.recv())
        #return (onset_inter_syll_ambiguity, nucleus_inter_syll_ambiguity, coda_inter_syll_ambiguity)

    def _richBiphonemePrint(self, biphonemeScores: dict[tuple[str,str], float], quantization: int = 100, triangular: bool = False) -> None:
        uniquePhonemes1 = list(set(map(lambda t: t[0], biphonemeScores.keys())))
        uniquePhonemes2 = list(set(map(lambda t: t[1], biphonemeScores.keys())))
        uniquePhonemes = sorted(list(set(uniquePhonemes1 + uniquePhonemes2)))

        maxTotalScore = max(biphonemeScores.values(), default=0.0)
        table = Table("Phonemes")
        for p in uniquePhonemes:
            table.add_column(p)
        if not triangular:
            table.add_column("sum")
        for i,p1 in enumerate(uniquePhonemes):
            pScores: list[str] = []
            pScoreSum: int|float = 0
            for j,p2 in enumerate(uniquePhonemes):
                if triangular and j <= i:
                    pScores.append("")
                else:
                    maxScoreFloat: float = max(biphonemeScores.get((p1, p2), 0.0),
                                   biphonemeScores.get((p2, p1), 0.0) )
                    if quantization > 0:
                        maxScoreInt: int = int(maxScoreFloat/maxTotalScore * quantization)
                        pScores.append(str(maxScoreInt))
                        pScoreSum += maxScoreInt
                    else:
                        pScores.append("%.1f"%(maxScoreFloat))
                        pScoreSum += maxScoreFloat
            if not triangular:
                table.add_row(p1, *pScores, str(pScoreSum))
            else :
                table.add_row(p1, *pScores)

        console = Console(color_system="auto")
        console.print(table)
        if quantization > 0:
            print("Quantization scale: 0-%d, while real value of max score is %0.1f\n" % (quantization, maxTotalScore))

    def printAmbiguityStats(self, sortedAmbiguities: dict[str, dict[tuple[str,str], float]], ambiguityType: str) -> None:

        print(f"Left hand (onset) {ambiguityType} minimal-ambiguity phonemes pairs")
        self._richBiphonemePrint(sortedAmbiguities["onset"])

        print(f"Thumb vowels (nucleus) {ambiguityType} minimal-ambiguity phonemes pairs")
        self._richBiphonemePrint(sortedAmbiguities["nucleus"])

        print(f"Right hand (coda) {ambiguityType} minimal-ambiguity phonemes pairs")
        self._richBiphonemePrint(sortedAmbiguities["coda"])

    def printTopSyllables(self, nb: int = -1):
        self.syllables.sort(reverse=True)
        for syl in self.syllables[:nb]:
            print("Syllable:", str(syl))


#    nucleusPhonemesIPA: str= "aeiɛɑ̃o°ɔ̃uyɛ̃ɔœɥøœ̃"  #Nasal are 2 chars istead of 1"
#   consonantPhonemesIPA: str = "ʀtsplkmdvjnfbʒwzʃgɲŋ"
