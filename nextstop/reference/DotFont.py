import json
from util import hex2Bin, mergeDict, printDict

class DotFont:
    
    def __init__(self, file, zero="□", one="■"):
        jsonData = json.load(file)
        self.width = jsonData["width"]
        self.height = jsonData["height"]
        self.charDict = jsonData["dict"]
        self.zero = zero
        self.one = one
        
    def getChar(self, char):
        result = []
        if self.charDict.get(char):
            for row in range(self.height):
                text = hex2Bin(self.charDict[char][row]).replace("0", self.zero).replace("1", self.one)
                result.append(text)
        else:
            for row in range(self.height):
                text = ""
                for col in range(self.width):
                    text += self.zero
                result.append(text)
        return result
    
    def printChar(self, char):
        printDict(self.getChar(char))
    
    def getString(self, string):
        result = []
        for char in string:
            if len(result) > 0:
                result = mergeDict(result, self.getChar(char))
            else:
                result = self.getChar(char)
        return result
    
    def printString(self, string):
        printDict(self.getString(string))