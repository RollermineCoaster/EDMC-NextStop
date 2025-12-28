from nextstop.ui.base import BaseBoard
from nextstop.ui.rows import *
from nextstop.ui.constant import *
from nextstop.util import *

import tkinter as tk
from theme import theme

class SimpleBoard(BaseBoard):

    def updateCanvas(self, moveY=True):
        super().updateCanvas()
        canvas = self.canvas
        #remove extra row object
        while len(self.rowObjs) > len(self.route):
            row = self.rowObjs.pop()
            row.clear()
        #if no route
        if len(self.route) <= 0:
            self.currentIndex = 0
            canvas.delete("all")
            canvas.create_text(0,         0, text="-------No Route-------", anchor=tk.NW, justify=tk.LEFT,  tags="noRoute")
            canvas.create_text(self.size, 0, text="-------",                anchor=tk.NE, justify=tk.RIGHT, tags="noRoute")
        else:
            canvas.delete("noRoute")
            #loop through route list
            rowHeight = self.toPix("40p")
            for index in range(len(self.route)):
                system = self.route[index]
                system["distance"] = getDistance(self.currentPos, system["pos"])
                if index >= len(self.rowObjs):
                    row = SimpleRow(self, canvas, 0, rowHeight*index, self.size, rowHeight, index+1, system)
                    row.draw()
                    self.rowObjs.append(row)
                else:
                    row = self.rowObjs[index]
                    row.setWidth(self.size)
                    row.setSystem(system)
                    row.update()
                #if not bottom
                notBottom = index+1 < len(self.route)
                row.showBottomLine(notBottom)
        self.resizeCanvas(canvas.bbox("all"), moveY)
        canvas.after(10, lambda: self.updateTheme())

    def updateTheme(self):
        super().updateTheme()
        self.canvas.itemconfigure("all", fill=theme.current["foreground"], font=theme.current["font"])
        self.canvas.itemconfigure("logo", font=(LOGOFONT, 20))

class FancyBoard(BaseBoard):

    def __init__(self, frame):
        super().__init__(frame)
        self.colors = THEME1933
        self.rowHeight = toPix(self.canvas, SIZE)/6
        #hints
        self.hintsVar = tk.StringVar()
        self.hintsLabel = tk.Label(self.canvas, fg=self.colors["textMinor"], bg=self.colors["bg"], relief=tk.RAISED, bd=1, font=('Helvetica', 9), textvariable=self.hintsVar)
        #hints and bulletLine canvas object id
        self.hintsObj = ""
        self.bulletLineObj = ""
        self.canvas.config(bg=self.colors["bg"])
    
    def updateCanvas(self, moveY=True):
        super().updateCanvas()
        canvas = self.canvas
        #remove extra row object
        while len(self.rowObjs) > len(self.route):
            row = self.rowObjs.pop()
            row.clear()
        #if no route
        if len(self.route) <= 0:
            self.currentIndex = 0
            canvas.delete("all")
            self.hintsObj = ""
            self.bulletLineObj = ""
            canvas.create_text(self.size/2, self.rowHeight/2, text="-------No Route-------", anchor=tk.CENTER, fill=self.colors["textMain"], font=('Helvetica', 12), justify=tk.CENTER, tags="noRoute")
        else:
            canvas.delete("noRoute")
            if not self.hintsObj:
                self.hintsObj = canvas.create_window(0, 0, tags="hints", window=self.hintsLabel, state=tk.HIDDEN)
            lineLength = self.rowHeight/2 + self.rowHeight*(len(self.route)-1)
            if not self.bulletLineObj:
                self.bulletLineObj = canvas.create_line(self.rowHeight/2, self.rowHeight/2, self.rowHeight/2, lineLength, fill=self.colors["main"], width="1.5p")
            else:
                canvas.coords(self.bulletLineObj, self.rowHeight/2, self.rowHeight/2, self.rowHeight/2, lineLength)
            #loop through route list
            for index in range(len(self.route)):
                rowOffset = self.rowHeight*(index)
                system = self.route[index]
                system["distance"] = getDistance(self.currentPos, system["pos"])
                if index >= len(self.rowObjs):
                    row = FancyRow(self, canvas, 0, rowOffset, self.size, self.rowHeight, index+1, system)
                    row.draw()
                    self.rowObjs.append(row)
                else:
                    row = self.rowObjs[index]
                    row.setWidth(self.size)
                    row.setSystem(system)
                    row.update()
                #if not bottom
                notBottom = index+1 < len(self.route)
                row.showBottomLine(notBottom)
        totalRow = max(len(self.route), 1)
        self.resizeCanvas((0,0 ,self.size, self.rowHeight*totalRow), moveY)

    def updateTheme(self):
        super().updateTheme()

    def showHints(self, x, y, text):
        canvas = self.canvas
        self.hintsVar.set(text)
        canvas.itemconfig("hints", state=tk.NORMAL)
        canvas.moveto("hints", self.canvas.canvasx(x), self.canvas.canvasy(y))
        bbox = canvas.bbox("hints")
        xOffset = 0
        yOffset = self.toPix("5p")
        if bbox[0] < 0:
            xOffset -= bbox[0]
        if bbox[1] < 0:
            yOffset -= bbox[1]
        if bbox[2] > self.size:
            xOffset -= bbox[2]-self.size
        totalRow = max(len(self.route), 1)
        if bbox[3]+yOffset > self.rowHeight*totalRow:
            yOffset = -(yOffset+bbox[3]-bbox[1])
        canvas.move("hints", xOffset, yOffset)
        
    def hideHints(self):
        self.hintsVar.set("")
        self.canvas.itemconfig("hints", state=tk.HIDDEN)