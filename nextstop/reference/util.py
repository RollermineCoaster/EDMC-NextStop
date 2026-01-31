def bin2Hex(text):
    return hex(int(text,2))

def hex2Bin(text):
    return bin(int(text,16))[2:].zfill(8)
    
def mergeDict(dict1, dict2):
    result = []
    for row in range(len(dict1)):
        result.append(dict1[row] + dict2[row])
    return result

def printDict(dict):
    for row in dict:
        print(row)