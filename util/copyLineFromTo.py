#!/bin/env python
#

def substituteMultipleValuesFromSourceToDest(argumentArray: list[str]) -> None:
    import sys

    argPos = 1
    fileIn = argumentArray[argPos]
    argPos += 1
    fileOut = fileIn  +".out"

    nbKeys = int(argumentArray[argPos])
    argPos += 1

    keyColumns =[int(arg) for arg in argumentArray[argPos:argPos+nbKeys]]
    argPos += nbKeys

    sourceKeyValues = argumentArray[argPos:argPos+nbKeys]
    argPos += nbKeys

    destKeyValues = argumentArray[argPos:argPos+nbKeys]
    argPos += nbKeys

    nbSubsititutions = int(argumentArray[argPos])
    argPos += 1

    substitutionColumns = [int(arg) for arg in argumentArray[argPos:argPos+nbSubsititutions]]
    argPos += nbSubsititutions
    
    bufferedText: list[str] = []
    sourceFound: list[int] = []
    destFound: list[int] = []
    with open(fileIn, "r") as fi :
        for lineNumber, line in enumerate(fi.readlines()):
            bufferedText.append(line)
            if matchKeys(keyColumns[0:1], sourceKeyValues, line) :
                #print(f"Found source {sourceKeyValues[0]}")
                if matchKeys(keyColumns, sourceKeyValues, line) :
                    sourceFound += [lineNumber]
                    #print(f"Found source line {len(sourceFound)} times at {lineNumber}")
            if matchKeys(keyColumns[0:1], destKeyValues, line) :
                #print(f"Found dest {destKeyValues[0]}")
                if matchKeys(keyColumns, destKeyValues, line) :
                    destFound += [lineNumber]
                    #print(f"Found dest line {len(destFound)} times at {lineNumber}")

    if len(sourceFound) != 1 or len(destFound) != 1:
        #print(f"Not substituting {sourceKeyValues} -> {destKeyValues}")
        #print(f"egrep \"^{sourceKeyValues[0]}\t|^{destKeyValues[0]}\t\"  {fileIn}")
        return
    else :
        modifiedDest = modifyLine(sourceFound[0], destFound[0], substitutionColumns, bufferedText)
        print("Source:\n", bufferedText[sourceFound[0]])
        print(" NB Source: ", len(sourceFound))
        print("Dest:\n", bufferedText[destFound[0]])
        print(" NB Dest: ", len(destFound))
        print("Modified dest:\n", modifiedDest)
        bufferedText[destFound[0]] = modifiedDest

    # with open(fileOut, "w") as fo :
    #     for lineNumber, line in enumerate(bufferedText):
    #         _ =fo.write(line)

def matchKeys(keyColumn: list[int], keyValues: list[str], line: str, delimiter: str="\t")-> bool:
    lineSplit = line.split(delimiter)
    for ki, key in enumerate(keyColumn) :
        if lineSplit[key] != keyValues[ki]:
            return False
    return True

def modifyLine(source: int, dest: int, subColumns: list[int], text: list[str], delimiter: str="\t") -> str:
    sourceSplit: list[str] = text[source].split(delimiter)
    destSplit = text[dest].split(delimiter)
    ret: list[str] = destSplit[:]
    for key in subColumns :
        if key >= 0 :
            ret[key] = sourceSplit[key]
        else :
            # Negative key means special processing
            # format is grapheme-phoneme.grapheme-phoneme...
            # must keep the dest grapheme and the source phonemes
            key = abs(key)
            graphemes = [pair.split("-")[0] for pair in destSplit[key].split(".")]
            phonemes = [pair.split("-")[1] for pair in sourceSplit[key].split(".")]
            ret[key] = ".".join([f"{g}-{p}" for g, p in zip(graphemes, phonemes)])
    return "\t".join(ret)

    
def main():
    import sys

    substituteMultipleValuesFromSourceToDest(sys.argv)

if  __name__ == "__main__":
    main()
