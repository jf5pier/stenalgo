#!/bin/env python3
from dataclasses import dataclass
from math import log,ceil

class FingerWeights(object):
    noPress: float = 0.0
    pinky1keyHome: float = 1.25
    pinky1keyOffHome: float = 1.50
    pinky2keysVertHome: float = 1.75
    pinky2keysVertOffHome: float = 2.00
    pinky2keysHorzBottom: float = 2.5
    pinky2keysHorzTop: float = 2.75

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
    left_pinky : dict[tuple[int, ...], float]
    left_ring : dict[tuple[int, ...], float]
    left_middle : dict[tuple[int, ...], float]
    left_index : dict[tuple[int, ...], float]
    left_thumb : dict[tuple[int, ...], float]
    right_thumb : dict[tuple[int, ...], float]
    right_index : dict[tuple[int, ...], float]
    right_middle : dict[tuple[int, ...], float]
    right_ring : dict[tuple[int, ...], float]
    right_pinky : dict[tuple[int, ...], float]

class Keyboard(object):
    _printableKeyLayout: str = ""
    _possible_keypress: PositionWeights = PositionWeights(
        {}, {},
        {}, {},
        {}, {},
        {}, {},
        {}, {})
    def printTemplate(self):
        print(self._printableKeyLayout)

    def keypressBinaryEncodingSize(self):
        bitsNeeded = 0
        fingerKeypressDict:dict[str, dict[tuple[int, ...], float]] = self._possible_keypress.__dict__
        for finger in fingerKeypressDict:
            bit = ceil(log(len(fingerKeypressDict[finger]),2))
            print(str(finger),"needs", bit, "bits")
            bitsNeeded += bit
        print("Total bits needed:", bitsNeeded)


class Starboard(Keyboard):
    _printableKeyLayout: str = """
Keys indexes :
-------------------------------       -------------------------------
|  0 |  2 |  4 |  6 |  8 |    |       |    | 16 | 18 | 20 | 22 | 24 |
|------------------------- 10 -       | 15 |----|----|----|----|----|
|  1 |  3 |  5 |  7 |  9 |    |       |    | 17 | 19 | 21 | 23 | 25 |
-------------------------------       -------------------------------
                       ----------- -----------
                       | 11 | 12 | | 13 | 14 |
                       ----------- -----------  
Fingers assignments :
-------------------------------       -------------------------------
| lp | lp | lr | lm | li |    |       |    | ri | rm | rr | rp | rp |
|------------------------- li -       | ri |----|----|----|----|----|
| lp | lp | lr | lm | li |    |       |    | ri | rm | rr | rp | rp |
-------------------------------       -------------------------------
                       ----------- -----------
                       | lt | lt | | rt | rt |
                       ----------- ----------- """ 

    _reserved_keys: list[int] = [0, 1, 10, 15]
    _fw: FingerWeights = FingerWeights()
    _possibleKeypress: PositionWeights = PositionWeights(
        left_pinky={
            ():_fw.noPress, (0,):_fw.pinky1keyOffHome,
            (1,):_fw.pinky1keyOffHome, (2,):_fw.pinky1keyHome,
            (3,):_fw.pinky1keyHome, (0, 1):_fw.pinky2keysVertOffHome,
            (2, 3):_fw.pinky2keysVertHome, (0, 2):_fw.pinky2keysHorzTop,
            (1, 3):_fw.pinky2keysHorzBottom},
        left_ring={
            ():_fw.noPress, (4,):_fw.ringMid1key,
            (5,):_fw.ringMid1key, (4,5):_fw.ringMid2keys},
        left_middle={
            ():_fw.noPress, (6,):_fw.ringMid1key,
            (7,):_fw.ringMid1key, (6,7):_fw.ringMid2keys},
        left_index={
            ():_fw.noPress, (8,):_fw.index1keyHome,
            (9,):_fw.index1keyHome, (10,):_fw.index1keyOffHome,
            (8,9):_fw.index2keysVert, (8,10):_fw.index2keysHorz,
            (9,10):_fw.index2keysHorz, (8,9,10):_fw.index3keys},
        left_thumb={
            ():_fw.noPress, (11,):_fw.thumb1key,
            (12,):_fw.thumb1key, (11,12):_fw.thumb2keys},
        right_thumb={
            ():_fw.noPress, (13,):_fw.thumb1key,
            (14,):_fw.thumb1key, (13,14):_fw.thumb2keys},
        right_index={
            ():_fw.noPress, (15,):_fw.index1keyOffHome,
            (16,):_fw.index1keyHome, (17,):_fw.index1keyHome,
            (16,17):_fw.index2keysVert, (15,16):_fw.index2keysHorz,
            (15,17):_fw.index2keysHorz, (15,16,17):_fw.index3keys},
        right_middle={
            ():_fw.noPress, (18,):_fw.ringMid1key,
            (19,):_fw.ringMid1key, (18,19):_fw.ringMid2keys},
        right_ring={
            ():_fw.noPress, (20,):_fw.ringMid1key,
            (21,):_fw.ringMid1key, (20,21):_fw.ringMid2keys},
        right_pinky={
            ():_fw.noPress, (22,):_fw.pinky1keyHome,
            (23,):_fw.pinky1keyHome, (24,):_fw.pinky1keyOffHome,
            (25,):_fw.pinky1keyOffHome, (22, 23):_fw.pinky2keysVertHome,
            (24, 25):_fw.pinky2keysVertOffHome, (22, 24):_fw.pinky2keysHorzTop,
            (23, 25):_fw.pinky2keysHorzBottom})

    def __init__(self):
        self._possible_keys: list[int] = list(range(26))
        self._allowed_keys: list[int] = [k for k in self._possible_keys if k not in self._reserved_keys]
        return

if __name__ == "__main__":
    sb = Starboard()
    sb.printTemplate()
    sb.keypressBinaryEncodingSize()
