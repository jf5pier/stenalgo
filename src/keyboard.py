#!/bin/env python3
from dataclasses import dataclass, fields
from math import log,ceil
from abc  import ABC, abstractmethod
from typing import override

class FingerWeights(object):
    noPress: float = 0.0
    pinky1keyHome: float = 1.25
    pinky1keyOffHome: float = 1.50
    pinky2keysVertHome: float = 1.75
    pinky2keysVertOffHome: float = 2.00
    pinky2keysHorzBottom: float = 2.5
    pinky2keysHorzTop: float = 2.75
    pinky4keys: float = 3.25

    ringMid1key: float = 1.25
    ringMid2keys: float= 1.75
    
    index1keyHome: float = 1.0
    index1keyOffHome: float = 1.25
    index2keysVert: float = 1.5
    index2keysHorz: float = 1.75
    index3keys: float = 2.0
    
    thumb1key: float = 1.0
    thumb2keys: float = 1.5

@dataclass
class PositionWeights(object):
    leftPinky : dict[tuple[int, ...], float]
    leftRing : dict[tuple[int, ...], float]
    leftMiddle : dict[tuple[int, ...], float]
    leftIndex : dict[tuple[int, ...], float]
    leftThumb : dict[tuple[int, ...], float]
    rightThumb : dict[tuple[int, ...], float]
    rightIndex : dict[tuple[int, ...], float]
    rightMiddle : dict[tuple[int, ...], float]
    rightRing : dict[tuple[int, ...], float]
    rightPinky : dict[tuple[int, ...], float]

    def toList(self) -> list[tuple[tuple[int, ...], float]] :
        return (list(self.leftPinky.items())+ list(self.leftRing.items()) +
            list(self.leftMiddle.items()) + list(self.leftIndex.items()) +
            list(self.leftThumb.items()) + list(self.rightThumb.items()) +
            list(self.rightIndex.items()) + list(self.rightMiddle.items()) +
            list(self.rightRing.items()) + list(self.rightPinky.items()))

    def __iter__(self):
        return (getattr(self, field.name) for field in fields(self))

    def __getitem__(self, key: str) -> dict[tuple[int, ...], float]:
        return getattr(self, key)

class Keyboard(ABC):
    # One key keyboard template
    _keyboardTemplate: str = """
------
|{0: >4}|
------"""
    _keyIndexes: list[str] = list(map(str, range(1)))
    _fingerAssignments: list[str] = ["li"]

    _printableKeyLayout: str = ""
    _possibleKeypress: PositionWeights = PositionWeights(
        {}, {},
        {}, {},
        {}, {},
        {}, {},
        {}, {})
    def printTemplate(self) -> None:
        print("Key indexes :")
        print(self._keyboardTemplate.format(*self._keyIndexes))
        print("Fingers assignments :")
        print(self._keyboardTemplate.format(*self._fingerAssignments))

    def keypressBinaryEncodingSize(self) -> None:
        bitsNeeded = 0
        fingerKeypressDict:dict[str, dict[tuple[int, ...], float]] = self._possibleKeypress.__dict__
        for finger in fingerKeypressDict:
            #print(finger, fingerKeypressDict[finger])
            if len(fingerKeypressDict[finger]) == 0:
                print("No keypresses for", finger)
                continue
            bit = ceil(log(len(fingerKeypressDict[finger]),2))
            print(str(finger),"needs", bit, "bits")
            bitsNeeded += bit
        print("Total bits needed:", bitsNeeded)

    @abstractmethod
    def getSingleKeys(self, syllabicPart: str) -> list[int]:
        ...

    @abstractmethod
    def getMultiKeys(self, syllabicPart: str, nbKeys: int) -> list[tuple[int, ...]]:
        ...

    @abstractmethod
    def printLayout(self) -> None:
        ...

    @abstractmethod
    def addToLayout(self, keyPress: tuple[int, ...], phonem: str) -> None:
        ...

    @abstractmethod
    def clearLayout(self) -> None:
        ...


class Starboard(Keyboard):
    _keyboardTemplate: str = \
"""
┏━━━━┳━━━━┳━━━━┳━━━━┳━━━━┳━━━━┓       ┏━━━━┳━━━━┳━━━━┳━━━━┳━━━━┳━━━━┓
┃{0: ^4}┃{2: ^4}┃{4: ^4}┃{6: ^4}┃{8: ^4}┃    ┃       ┃    ┃{16: ^4}┃{18: ^4}┃{20: ^4}┃{22: ^4}┃{24: ^4}┃
┣━━━━╋━━━━╋━━━━╋━━━━╋━━━━┫{10: ^4}┃       ┃{15: ^4}┣━━━━╋━━━━╋━━━━╋━━━━╋━━━━┫
┃{1: ^4}┃{3: ^4}┃{5: ^4}┃{7: ^4}┃{9: ^4}┃    ┃       ┃    ┃{17: ^4}┃{19: ^4}┃{21: ^4}┃{23: ^4}┃{25: ^4}┃
┗━━━━┻━━━━┻━━━━┻━━━━┻━━┳━┻━━┳━┻━━┓ ┏━━┻━┳━━┻━┳━━┻━━━━┻━━━━┻━━━━┻━━━━┛
                       ┃{11: ^4}┃{12: ^4}┃ ┃{13: ^4}┃{14: ^4}┃
                       ┗━━━━┻━━━━┛ ┗━━━━┻━━━━┛"""

    _printableKeyLayout: str = """
Keys indexes :
-------------------------------       -------------------------------
|  0 |  2 |  4 |  6 |  8 |    |       |    | 16 | 18 | 20 | 22 | 24 |
|----|----|----|----|----| 10 |       | 15 |----|----|----|----|----|
|  1 |  3 |  5 |  7 |  9 |    |       |    | 17 | 19 | 21 | 23 | 25 |
-------------------------------       -------------------------------
                       ----------- -----------
                       | 11 | 12 | | 13 | 14 |
                       ----------- -----------
Fingers assignments :
-------------------------------       -------------------------------
| lp | lp | lr | lm | li |    |       |    | ri | rm | rr | rp | rp |
|----|----|----|----|----| li |       | ri |----|----|----|----|----|
| lp | lp | lr | lm | li |    |       |    | ri | rm | rr | rp | rp |
-------------------------------       -------------------------------
                       ----------- -----------
                       | lt | lt | | rt | rt |
                       ----------- ----------- """

    _reservedKeys: list[int] = [0, 1, 10, 15]
    _possibleKeys: list[int] = list(range(26))
    _fingerAssignments: list[str] = 4*["lp"] + 2*["lr"] + 2*["lm"] + 3*["li"] +2*["lt"] + \
        2*["rt"] + 3* ["ri"] + 2*["rm"] +2*["rr"] +4*["rp"]
    _keyIndexes: list[str] = list(map(str, _possibleKeys))
    _fw: FingerWeights = FingerWeights()
    _possibleKeypress: PositionWeights = PositionWeights(
        leftPinky={
            ():_fw.noPress, (0,):_fw.pinky1keyOffHome,
            (1,):_fw.pinky1keyOffHome, (2,):_fw.pinky1keyHome,
            (3,):_fw.pinky1keyHome, (0, 1):_fw.pinky2keysVertOffHome,
            (2, 3):_fw.pinky2keysVertHome, (0, 2):_fw.pinky2keysHorzTop,
            (1, 3):_fw.pinky2keysHorzBottom, (0,1,2,3):_fw.pinky4keys},
        leftRing={
            ():_fw.noPress, (4,):_fw.ringMid1key,
            (5,):_fw.ringMid1key, (4,5):_fw.ringMid2keys},
        leftMiddle={
            ():_fw.noPress, (6,):_fw.ringMid1key,
            (7,):_fw.ringMid1key, (6,7):_fw.ringMid2keys},
        leftIndex={
            ():_fw.noPress, (8,):_fw.index1keyHome,
            (9,):_fw.index1keyHome, (10,):_fw.index1keyOffHome,
            (8,9):_fw.index2keysVert, (8,10):_fw.index2keysHorz,
            (9,10):_fw.index2keysHorz, (8,9,10):_fw.index3keys},
        leftThumb={
            ():_fw.noPress, (11,):_fw.thumb1key,
            (12,):_fw.thumb1key, (11,12):_fw.thumb2keys},
        rightThumb={
            ():_fw.noPress, (13,):_fw.thumb1key,
            (14,):_fw.thumb1key, (13,14):_fw.thumb2keys},
        rightIndex={
            ():_fw.noPress, (15,):_fw.index1keyOffHome,
            (16,):_fw.index1keyHome, (17,):_fw.index1keyHome,
            (16,17):_fw.index2keysVert, (15,16):_fw.index2keysHorz,
            (15,17):_fw.index2keysHorz, (15,16,17):_fw.index3keys},
        rightMiddle={
            ():_fw.noPress, (18,):_fw.ringMid1key,
            (19,):_fw.ringMid1key, (18,19):_fw.ringMid2keys},
        rightRing={
            ():_fw.noPress, (20,):_fw.ringMid1key,
            (21,):_fw.ringMid1key, (20,21):_fw.ringMid2keys},
        rightPinky={
            ():_fw.noPress, (22,):_fw.pinky1keyHome,
            (23,):_fw.pinky1keyHome, (24,):_fw.pinky1keyOffHome,
            (25,):_fw.pinky1keyOffHome, (22, 23):_fw.pinky2keysVertHome,
            (24, 25):_fw.pinky2keysVertOffHome, (22, 24):_fw.pinky2keysHorzTop,
            (23, 25):_fw.pinky2keysHorzBottom, (22,23,24,25):_fw.pinky4keys})

    def __init__(self, nbKeysPerSyllabicPart: tuple[tuple[str, int], ...] =
                 (("onset", 8), ("nucleus", 4), ("coda", 10))) -> None:
        self.keypressPhonemMap: dict[tuple[int, ...], list[str]] = {}
        self.allowedKeys: list[int] = [k for k in self._possibleKeys if k not in self._reservedKeys]

        len1 = len(self.allowedKeys)
        len2 = sum(map(lambda a: a[1], nbKeysPerSyllabicPart))
        if len1 != len2 :
            raise ValueError(f"Number of allowed keys {len1} does not match the number of phonem keys {len2} in the partitions {nbKeysPerSyllabicPart}")

        unassignedKeys: list[int] = self.allowedKeys[:]
        self.keyIDinSyllabicPart: dict[str, list[int]] = {}
        for syllabicPart, partSize in nbKeysPerSyllabicPart:
            self.keyIDinSyllabicPart[syllabicPart] = unassignedKeys[:partSize]
            unassignedKeys = unassignedKeys[partSize:]
#        print(self.keyIDinSyllabicPart)
#        sys.exit(1)

        self.allowed1fingerKeypress: list[tuple[tuple[int, ...], float]] = list(
            filter(lambda k : len(k[0]) == len(list(
                filter(lambda x: x in self.allowedKeys, list(k[0])))), self._possibleKeypress.toList()))
        self.nbKeys: int = len(self._keyIndexes)
        listKeypresses: list[list[tuple[int, ...]]] = list(
            map(lambda f: list(f.keys()), self._possibleKeypress.__dict__.values()))
        flatKeypresses: list[tuple[int, ...]] = [item for sublist in listKeypresses for item in sublist]
        self.maxKeyPerFinger: int = max(list(map(len, flatKeypresses)))
        return

    @override
    def printLayout(self) -> None:
        maxKeyPress = max(list(map(len, self.keypressPhonemMap.keys())))
        for i in range(1, maxKeyPress+1):
            nbKeys = 0
            phonemKeymapList = self.nbKeys * [""]
            for (keyPress, phonem) in self.keypressPhonemMap.items():
                if i  == len(keyPress):
                    nbKeys += 1
                    for key in keyPress:
                        for p in phonem:
                            phonemKeymapList[key] = phonemKeymapList[key] +  p
            if nbKeys > 0:
                print("Phonemes defined by " + (f"{i} keys pressed together" if i >1 else "1 key"))
                print(self._keyboardTemplate.format(*phonemKeymapList))

        return

    @override
    def clearLayout(self) -> None:
        self.keypressPhonemMap = {}

    @override
    def addToLayout(self, keyPress: tuple[int, ...], phonem: str) -> None:
        existingKeypressPhonem = self.keypressPhonemMap.get(keyPress, [])
        existingKeypressPhonem.append(phonem)
        self.keypressPhonemMap[keyPress] = existingKeypressPhonem
    
    @override
    def getSingleKeys(self, syllabicPart: str) -> list[int]:
        """ 
        Return key IDs for keys that can be pressed alone to register a phoneme 
        """
        return self.keyIDinSyllabicPart[syllabicPart][:]

    @override
    def getMultiKeys(self, syllabicPart: str, nbKeys: int) -> list[tuple[int, ...]]:
        """ 
        Return key IDs for keys that can be pressed together to register a phoneme 
        """
        fingersInSyllabicPart: list[str] = []
        for finger in self._possibleKeypress.__dict__:
            for keyPress in self._possibleKeypress[finger]:
                if 0 < len(list(filter(lambda k: k in self.keyIDinSyllabicPart[syllabicPart], keyPress))):
                    fingersInSyllabicPart.append(finger)
                    break

        def _addKeypress(accumulator:list[tuple[int, ...]],
                         fingers: list[str], nbKeysLeft: int,
                         chord: list[int], syllabicPart: str) -> None:
            if(len(fingers) == 0 or nbKeysLeft <= 0):
                if len(chord) > 0 and nbKeysLeft == 0:
                    accumulator.insert(0, tuple(chord))  #Chords are explored in reverse order, this reverses it
                return

            fingerKeypress = self._possibleKeypress[fingers[0]]
            for keyPress in fingerKeypress:
                # Case were we skip this finger in composing a chord (keypress = no press)
                if len(keyPress) == 0 :
                    _addKeypress(accumulator, fingers[1:], nbKeysLeft, chord, syllabicPart)

                elif len(keyPress) <= nbKeysLeft:
                    keysInPart = list(filter(lambda k: k in self.keyIDinSyllabicPart[syllabicPart], keyPress))
                    if len(keysInPart) == len(keyPress):
                        _addKeypress(accumulator, fingers[1:],
                                     nbKeysLeft - len(keyPress),
                                     chord + keysInPart , syllabicPart)
            return



        keypresses: list[tuple[int, ...]] = []
        _addKeypress(keypresses, fingersInSyllabicPart, nbKeys, [], syllabicPart)
        return keypresses[:]

    def setIrelandEnglishLayout(self) -> None:
        layout: list[tuple[tuple[int, ...], str]] = [
            ((2,),"s"), ((3,),"s"), ((4,),"t"), ((5,),"k"), ((6,),"p"), ((7,),"w"), 
            ((8,),"h"), ((9,),"r"), ((10,),"*"), ((11,),"a"), ((12,),"o"), ((13,),"e"), 
            ((14,),"u"), ((15,),"*"), ((16,),"f"), ((16,),"v"), ((17,),"r"), ((18,),"p"), 
            ((19,),"b"), ((20,),"l"), ((21,),"g"), ((22,),"t"), ((23,),"s"), ((24,),"d"), 
            ((25,),"z"), ((2,4),"f"), ((3,4),"x"), ((3,5),"q"), ((3,9),"v"), ((4,5),"d"), 
            ((5,9),"c"), ((6,7),"b"), ((6,8),"m"), ((8,9),"l"), ((13,14),"i"), ((18,19),"n"), 
            ((18,20),"m"), ((19,21),"k"), ((4,6,8),"n"), ((5,7,9),"y"), ((19,21,23),"x"), 
            ((3,5,7,9),"j"), ((4,5,6,7),"g"), ((18,19,20,21),"j"), ((3,4,5,6,7),"z")]

        self.clearLayout()
        for (keyPress, phonem) in layout:
            self.addToLayout(keyPress, phonem)
                                        
if __name__ == "__main__":
    sb = Starboard()
    sb.printTemplate()
    sb.keypressBinaryEncodingSize()

    print("\nPhonetic rules of the english Ireland layout on the Starboard keyboard")
    sb.setIrelandEnglishLayout()
    sb.printLayout()  
