#!/bin/env python3
from dataclasses import dataclass, fields
from math import log,ceil
from abc  import ABC, abstractmethod
from typing import override

"""
Nomenclature and concerns :
- A key corresponds to a button pressed by a finger.
-- Some fingers are more agile and cost (weight) less to use
-- Key overuse may cause confusion, they should have a limited number of "task"

- A keypress coressponds to one or more keys pressed by one finger.
-- Keypresses of multiple keys are more tireing (weight) than simpler keypresses.

- A stroke (chord) corresponds to one or more keypresses pressed by one or more fingers.
-- Longer strokes are more tireing and prone to errors.
-- Some strokes are more difficult to type (alternating lower and upper key rows). 
--- TODO: add this weight function
"""


class FingerWeights(object):
    """
    Cost of using the different fingers in all their allowed keypresses on the keyboard.
    """
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
    def getPossibleStrokes(self, syllabicPart: str, nbKeysInStroke: int) -> list[tuple[int, ...]]:
        """
        Get all permitted strokes in a syllabic part of a given number of keys
        """
        pass

    @abstractmethod
    def printLayout(self) -> None:
        pass

    @abstractmethod
    def addToLayout(self, stroke: tuple[int, ...], phonem: str) -> None:
        """
        Add a phoneme to the layout and assign it to a keypress.
        """
        pass

    @abstractmethod
    def removeFromLayout(self, stroke: tuple[int, ...], phoneme: str) -> None:
        """
        Remove a phoneme to the layout and assign it to a keypress.
        """
        pass

    @abstractmethod
    def getPhonemesOfStroke(self, stroke: tuple[int, ...]) -> list[str]:
        pass

    @abstractmethod
    def getStrokesOfPhoneme(self, phoneme: str, syllabicPart: str) -> list[tuple[int, ...]]:
        pass

    @abstractmethod
    def getStrokeOfSyllableByPart(self, phonemesByPart: dict[str, list[str]]) -> tuple[int, ...]:
        """
        Get the stroke corresponding to a syllable with phonemes in each syllabic part.
        """
        pass

    @abstractmethod
    def strokesToString(self, strokes: tuple[tuple[int, ...], ...]) -> str:
        pass

    @abstractmethod
    def clearLayout(self) -> None:
        pass

    @staticmethod
    def strokeIsLowerThen(stroke1: tuple[int, ...], stroke2: tuple[int, ...]) -> bool:
        """ 
        Helper function for sorting lists of strokes.
        """
        if stroke1 == () and not stroke2 == ():
            return True #Empty stroke is always lower than a non-empty stroke
        elif stroke2 == ():
            return False
        elif stroke1[0] < stroke2[0]:
            return True #First key in a stroke is the most significant key
        elif stroke1[0] > stroke2[0]:
            return False
        else : 
            if stroke1[-1] < stroke2[-1]: #Last key is the second most significant
                return True
            elif stroke1[-1] > stroke2[-1]:
                return False
            else: #Begining and end are identical, strokes can only differ by their middle keys
                return Keyboard.strokeIsLowerThen(stroke1[1:-1], stroke2[1:-1]) #Compare the rest of the stroke



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
        self.phonemesAssignedToStroke: dict[tuple[int, ...], list[str]] = {}
        self.allowedKeys: list[int] = [k for k in self._possibleKeys if k not in self._reservedKeys]

        len1 = len(self.allowedKeys)
        len2 = sum(map(lambda a: a[1], nbKeysPerSyllabicPart))
        if len1 != len2 :
            raise ValueError(f"Number of allowed keys {len1} does not" +
                f" match the number of phonem keys {len2} in the partitions {nbKeysPerSyllabicPart}")

        unassignedKeys: list[int] = self.allowedKeys[:]
        self.keyIDinSyllabicPart: dict[str, list[int]] = {}
        for syllabicPart, partSize in nbKeysPerSyllabicPart:
            self.keyIDinSyllabicPart[syllabicPart] = unassignedKeys[:partSize]
            unassignedKeys = unassignedKeys[partSize:]

        #self.allowed1fingerKeypress: list[tuple[tuple[int, ...], float]] = list(
        #    filter(lambda k : len(k[0]) == len(list(
        #        filter(lambda x: x in self.allowedKeys, list(k[0])))), self._possibleKeypress.toList()))

        self.nbKeys: int = len(self._keyIndexes)
        
        #listKeypresses: list[list[tuple[int, ...]]] = list(
        #    map(lambda f: list(f.keys()), self._possibleKeypress.__dict__.values()))
        #flatKeypresses: list[tuple[int, ...]] = [item for sublist in listKeypresses for item in sublist]
        #self.maxKeyPerFinger: int = max(list(map(len, flatKeypresses)))
        return

    @override
    def printLayout(self) -> None:
        maxKeyPress = max(list(map(len, self.phonemesAssignedToStroke.keys())))
        for i in range(1, maxKeyPress+1):
            nbKeys = 0
            phonemeKeymapList = self.nbKeys * [""]
            for (keyPress, phoneme) in self.phonemesAssignedToStroke.items():
                if i  == len(keyPress):
                    nbKeys += 1
                    for key in keyPress:
                        for p in phoneme:
                            phonemeKeymapList[key] = phonemeKeymapList[key] +  p
            if nbKeys > 0:
                print("Phonemes defined by " + (f"{i} keys pressed together" if i >1 else "1 key"))
                print(self._keyboardTemplate.format(*phonemeKeymapList))

        return

    @override
    def clearLayout(self) -> None:
        self.phonemesAssignedToStroke = {}

    @override
    def addToLayout(self, stroke: tuple[int, ...], phonem: str) -> None:
        existingKeypressPhoneme = self.phonemesAssignedToStroke.get(stroke, [])
        existingKeypressPhoneme.append(phonem)
        self.phonemesAssignedToStroke[stroke] = existingKeypressPhoneme
    
    @override
    def removeFromLayout(self, stroke: tuple[int, ...], phoneme: str) -> None:
        if self.phonemesAssignedToStroke.get(stroke, None) is None:
            raise KeyError(f"Keypress {stroke} not found in the layout")
        if len(self.phonemesAssignedToStroke[stroke]) == 1 and self.phonemesAssignedToStroke[stroke][0] == phoneme:
            del self.phonemesAssignedToStroke[stroke]  # Remove the keypress if it was the only phoneme assigned to it
        elif phoneme in self.phonemesAssignedToStroke[stroke]:
            index = self.phonemesAssignedToStroke[stroke].index(phoneme)
            _ = self.phonemesAssignedToStroke[stroke].pop(index)  # Remove the phoneme from the keypress
        else:
            raise KeyError(f"Phoneme {phoneme} not found in keypress {stroke}")

    @override
    def getPhonemesOfStroke(self, stroke: tuple[int, ...]) -> list[str]:
        """
        Find all phonemes assigned to a given stroke
        """
        return self.phonemesAssignedToStroke.get(stroke, [])[:]

    @override
    def getStrokesOfPhoneme(self, phoneme: str, syllabicPart: str) -> list[tuple[int, ...]]:
        """
        Find all strokes in a syllabic part that results in a given phonem
        """
        assignedKeypress: list[tuple[int, ...]] = []
#        print(f"Searching for phoneme {phoneme} in syllabic part {syllabicPart}")
        for keypress, phonemes in self.phonemesAssignedToStroke.items():
#            print(f"Checking keypress {keypress} with phonemes {phonemes}")
            if keypress[0] in self.keyIDinSyllabicPart[syllabicPart] and phoneme in phonemes:
                assignedKeypress.append(keypress)
        return assignedKeypress[:]

    def getSinglekeyKeypress(self, syllabicPart: str) -> list[tuple[int]]:
        """ 
        Return key IDs for keys that can be pressed alone to register a phoneme 
        """
        return list(map(lambda k : (k,), self.keyIDinSyllabicPart[syllabicPart]))

    def getFingersInSyllabicPart(self, syllabicPart: str) -> list[str]:
        """ 
        Return the fingers that can be used to press keys in the given syllabic part
        """
        fingers: list[str] = []
        for finger in self._possibleKeypress.__dict__:
            for keyPress in self._possibleKeypress[finger]:
                if 0 < len(list(filter(lambda k: k in self.keyIDinSyllabicPart[syllabicPart], keyPress))):
                    fingers.append(finger)
                    break
        return fingers[:]

    def buildStrokes(self, accumulator:list[tuple[int, ...]], fingers: list[str],
                     nbKeysLeft: int, stroke: list[int], syllabicPart: str) -> None:
        """
        Recursively build all possible strokes using the given fingers and number of keys left to press.
        """
        if(len(fingers) == 0 or nbKeysLeft <= 0):
            if len(stroke) > 0 and nbKeysLeft == 0:
                accumulator.insert(0, tuple(stroke))  #Strokes are explored in reverse order, this reverses it
            return

        fingerKeypress = self._possibleKeypress[fingers[0]]
        for keyPress in fingerKeypress:
            # Case were we skip this finger in composing a stroke (keypress = no press)
            if len(keyPress) == 0 :
                self.buildStrokes(accumulator, fingers[1:], nbKeysLeft, stroke, syllabicPart)

            elif len(keyPress) <= nbKeysLeft:
                keysInPart = list(filter(lambda k: k in self.keyIDinSyllabicPart[syllabicPart], keyPress))
                if len(keysInPart) == len(keyPress): #Keypress doesnt mix between syllabic parts
                    self.buildStrokes(accumulator, fingers[1:],
                                        nbKeysLeft - len(keyPress),
                                        stroke + keysInPart , syllabicPart)
        return

    @override
    def getPossibleStrokes(self, syllabicPart: str, nbKeysInStroke: int) -> list[tuple[int, ...]]:
        """ 
        Return key IDs for keys that can be pressed together to register a phoneme, 
        forming strokes of a given number of keys.
        """
        if nbKeysInStroke == 1 :
            return self.getSinglekeyKeypress(syllabicPart)

        fingersInSyllabicPart: list[str] = self.getFingersInSyllabicPart(syllabicPart)

        strokes: list[tuple[int, ...]] = []
        self.buildStrokes(strokes, fingersInSyllabicPart, nbKeysInStroke, [], syllabicPart)
        return strokes[:]

    @override
    def getStrokeOfSyllableByPart(self, phonemesByPart: dict[str, list[str]]) -> tuple[int, ...]:
        """
        Get the list of strokes that builds a syllable.
        """
        strokes: list[int] = []
        for syllabicPart, phonemes in phonemesByPart.items():
            for phoneme in phonemes:
                strokesOfPhoneme = self.getStrokesOfPhoneme(phoneme, syllabicPart)
                for key in strokesOfPhoneme[0]:
                    strokes.append(key)
            #if len(strokes) == 0:
            #    print("phonemesByPart", phonemesByPart)
        return tuple(strokes)

    @override
    def strokesToString(self, strokes: tuple[tuple[int, ...], ...]) -> str:
        """
        Convert a list of strokes to a string representation.
        """
        strokeString = ""
        for stroke in strokes:
            if not strokeString == "":
                strokeString += "/"
            syllableString ={"onset": "", "nucleus": "", "coda": ""}
            for key in stroke:
                syllabicPart = next((part for part, keys in self.keyIDinSyllabicPart.items() if key in keys), "")
                phoneme = self.getPhonemesOfStroke((key,))[0]
                syllableString[syllabicPart] += phoneme
            if syllableString["nucleus"] == "" :
                syllableString["nucleus"] = "-"
            strokeString += f"{syllableString['onset']}{syllableString['nucleus']}{syllableString['coda']}"

        return strokeString

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
