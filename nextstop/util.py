import math

def getDistance(pos1, pos2):
    return math.sqrt((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2 + (pos1[2]-pos2[2])**2)

def getCanvasObjHeight(canvas, id):
    _, y1, _, y2 = canvas.bbox(id)
    return abs(y2-y1)

def getCanvasObjWidth(canvas, id):
    x1, _, x2, _ = canvas.bbox(id)
    return abs(x2-x1)

def resizeCanvasText(canvas, id, width):
    #remove the width limit of the object
    canvas.itemconfigure(id, width=0)
    if type(width) == "str":
        width = canvas.winfo_fpixels(width)
    #make system name resize dynamically
    textHeight = getCanvasObjHeight(canvas, id)
    textFont, textSize = canvas.itemcget(id, "font").split()
    textSize = int(textSize)
    #limit the width of the object
    canvas.itemconfigure(id, width=width)
    #while text size > 1pt and current text height > old text height
    while textSize > 1 and getCanvasObjHeight(canvas, id) > textHeight:
        textSize -= 1
        canvas.itemconfigure(id, font=(textFont, textSize))
