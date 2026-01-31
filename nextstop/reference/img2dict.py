from PIL import Image
import json

def getChar(img, left, upper, right, lower):
    result = []
    width = right-left
    height = lower-upper
    charImg = img.crop((left, upper, right, lower))
    cursorX = 1
    cursorY = 1
    while cursorY < height:
        text = ""
        cursorX = 1
        while cursorX < width:
            px = charImg.getpixel((cursorX, cursorY))
            if px[0] == 0 and px[1] == 0 and px[2] == 0:
                text += "0"
            else:
                text += "1"
            cursorX += 4
        cursorY += 4
        result.append(text)
    return result

def bin2Hex(text):
    return hex(int(text,2))

def hex2Bin(text):
    return bin(int(text,16))[2:].zfill(8)

def getCharFromImg(path, offset1, count1, offset2, count2):
    result = []
    img = Image.open(path)
    for i in range(count1):
        result.append(getChar(img, offset1+32*i, 1, offset1+32*(i+1), 64))
        print()

    for i in range(count2):
        result.append(getChar(img, offset2+32*i, 66, offset2+32*(i+1), 129))
        print()
    return result

def printCharSet(charSet):
    text = ["","","","","","","","","","","","","","","",""]
    for char in charSet.values():
        row = 0
        for rowData in char:
            text[row] += hex2Bin(rowData).replace("0", "□").replace("1", "■")
            row += 1
    for row in text:
        print(row)

bigKMB = {}

bigData1 = getCharFromImg("bigtext1.bmp", 48, 13, 48, 13)
bigText1 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
for i in range(len(bigText1)):
    bigKMB[bigText1[i]] = bigData1[i]

bigData2 = getCharFromImg("bigtext2.bmp", 48, 13, 48, 13)
bigText2 = "abcdefghijklmnopqrstuvwxyz"
for i in range(len(bigText2)):
    bigKMB[bigText2[i]] = bigData2[i]

bigData3 = getCharFromImg("bigtext3.bmp", 96, 10, 0, 0)
bigText3 = "0123456789"
for i in range(len(bigText3)):
    bigKMB[bigText3[i]] = bigData3[i]

bigData4 = getCharFromImg("bigtext4.bmp", 0, 16, 0, 16)
bigText4 = ".,\"'?!@_*#$%&()+-/:;<=>[\\]^`{|}~"
for i in range(len(bigText4)):
    bigKMB[bigText4[i]] = bigData4[i]

for char,data in bigKMB.items():
    for i in range(len(data)):
        bigKMB[char][i] = bin2Hex(data[i])

print(bigKMB)
printCharSet(bigKMB)

outputData = {"width":8, "height":16, "dict":bigKMB}

with open("bigKMB.json", "w") as file:
    json.dump(outputData, file)