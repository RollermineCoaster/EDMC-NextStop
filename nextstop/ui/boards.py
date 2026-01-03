from nextstop.ui.base import BaseBoard
from nextstop.ui.rows import *
from nextstop.ui.constant import *
from nextstop.util import *

import tkinter as tk
from theme import theme

import time

class SimpleBoard(BaseBoard):

    def updateCanvas(self, moveY=True):
        if self.debugMode: startTime = time.perf_counter()
        
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
                system["distance"] = distance = getDistance(self.currentPos, system["pos"])
                if distance <= 0: self.currentIndex = index
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

        if self.debugMode:
            endTime = time.perf_counter()
            self.updateMetrics(endTime - startTime, len(self.rowObjs))

    def updateTheme(self):
        super().updateTheme()
        self.canvas.itemconfig("all", fill=theme.current["foreground"], font=theme.current["font"])
        self.canvas.itemconfig("logo", font=(LOGOFONT, 20))

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
        if self.debugMode: startTime = time.perf_counter()

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
                self.hintsObj = canvas.create_window(0, 0, tags="hints", window=self.hintsLabel, state=tk.HIDDEN, anchor=tk.S)
            lineLength = self.rowHeight/2 + self.rowHeight*(len(self.route)-1)
            if not self.bulletLineObj:
                self.bulletLineObj = canvas.create_line(self.rowHeight/2, self.rowHeight/2, self.rowHeight/2, lineLength, fill=self.colors["main"], width="1.5p")
            else:
                canvas.coords(self.bulletLineObj, self.rowHeight/2, self.rowHeight/2, self.rowHeight/2, lineLength)
            #loop through route list
            for index in range(len(self.route)):
                rowOffset = self.rowHeight*(index)
                system = self.route[index]
                system["distance"] = distance = getDistance(self.currentPos, system["pos"])
                if distance <= 0: self.currentIndex = index
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

        if self.debugMode:
            endTime = time.perf_counter()
            self.updateMetrics(endTime - startTime, len(self.rowObjs))

    def updateTheme(self):
        super().updateTheme()

    def showHints(self, x, y, text):
        canvas = self.canvas
        self.hintsVar.set(text)
        # Reset the anchor before measuring
        canvas.itemconfig("hints", state=tk.NORMAL, anchor=tk.S)

        canvas.coords("hints", x, y)

        #force bbox to update
        canvas.update_idletasks()

        bbox = canvas.bbox("hints") # (x1, y1, x2, y2)
        xOffset = 0
        #check if y1 off-screen
        if bbox[1] < 0:
            #flip the anchor
            canvas.itemconfig("hints", anchor=tk.N)
            #move it below logo
            canvas.coords("hints", x, y+self.toPix("20p"))
            #force bbox to update
            canvas.update_idletasks()
            bbox = canvas.bbox("hints") # (x1, y1, x2, y2)

        #check if x1 and x2 off-screen
        if bbox[0] < 0: # Left edge
            xOffset = -bbox[0]
        elif bbox[2] > self.size: # Right edge
            xOffset = self.size - bbox[2]

        canvas.move("hints", xOffset, 0)
        
    def hideHints(self):
        self.hintsVar.set("")
        self.canvas.itemconfig("hints", state=tk.HIDDEN)