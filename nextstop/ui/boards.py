from nextstop.ui.base import BaseBoard
from nextstop.ui.rows import *
from nextstop.ui.bars import *
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
            canvas.create_text(0,         0, text=NOROUTEFULL_STR, anchor=tk.NW, justify=tk.LEFT,  tags="noRoute")
            canvas.create_text(self.size, 0, text=DASH6_STR,                              anchor=tk.NE, justify=tk.RIGHT, tags="noRoute")
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
        self.resizeCanvas(canvas.bbox("all"), moveY=moveY)
        canvas.after(10, lambda: self.updateTheme())

        if self.debugMode:
            endTime = time.perf_counter()
            self.updateMetrics(endTime - startTime, len(self.rowObjs))

    def updateTheme(self):
        super().updateTheme()
        self.canvas.itemconfig("all", fill=theme.current["foreground"], font=theme.current["font"])
        self.canvas.itemconfig("logo", font=(LOGOFONT, 20))

class FancyBoard(BaseBoard):

    def __init__(self, frame: tk.Frame):
        super().__init__(frame)
        self.colors = THEME1933
        self.rowHeight = toPix(self.canvas, SIZE)/6
        self.barHeight = self.rowHeight*1.5
        #hints
        self.hintsVar = tk.StringVar()
        self.hintsLabel = tk.Label(self.canvas, fg=self.colors["textMinor"], bg=self.colors["bg"], relief=tk.RAISED, bd=1, font=('Helvetica', 9), textvariable=self.hintsVar)
        #hints and bulletLine canvas object id
        self.hintsObj = self.canvas.create_window(0, 0, tags="hints", window=self.hintsLabel, state=tk.HIDDEN, anchor=tk.S)
        self.bulletLineObj = ""
        self.bar = FancyBar(self, self.canvas, 0, 0, self.size, self.rowHeight*1.5)
        self.bar.draw()
        self.canvas.config(bg=self.colors["bg"])
    
    def updateCanvas(self, moveY=True):
        if self.debugMode: startTime = time.perf_counter()

        super().updateCanvas()
        canvas = self.canvas
        bar = self.bar
        routeSize = len(self.route)
        #remove extra row object
        while len(self.rowObjs) > routeSize:
            row = self.rowObjs.pop()
            row.clear()
        #if no route
        if routeSize <= 0:
            self.currentIndex = 0
            self.hideHints()
            if self.bulletLineObj: canvas.itemconfig(self.bulletLineObj, state=tk.HIDDEN)
            canvas.create_text(self.size/2, self.rowHeight/2+self.barHeight, text=NOROUTEFULL_STR, anchor=tk.CENTER, fill=self.colors["textMain"], font=('Helvetica', 12), justify=tk.CENTER, tags="noRoute")
        else:
            canvas.delete("noRoute")
            lineLength = self.rowHeight/2 + self.rowHeight*(routeSize-1) + self.barHeight
            if not self.bulletLineObj:
                self.bulletLineObj = canvas.create_line(self.rowHeight/2, self.rowHeight/2+self.barHeight, self.rowHeight/2, lineLength, fill=self.colors["main"], width="1.5p")
            else:
                canvas.itemconfig(self.bulletLineObj, state=tk.NORMAL)
                canvas.coords(self.bulletLineObj, self.rowHeight/2, self.rowHeight/2+self.barHeight, self.rowHeight/2, lineLength)
            #loop through route list
            for index in range(routeSize):
                rowOffset = self.rowHeight*(index) + self.barHeight
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
                notBottom = index+1 < routeSize
                row.showBottomLine(notBottom)
        bar.setWidth(self.size)
        if routeSize <= 0 or self.currentIndex >= routeSize-1: bar.updateText()
        else:
            nextStopIndex = self.currentIndex+1
            bar.updateText(f"{nextStopIndex+1}. {self.route[nextStopIndex]["system"]}", routeSize-nextStopIndex)
        totalRow = max(routeSize, 1)
        self.resizeCanvas((0,0 ,self.size, self.rowHeight*totalRow), topOffset=self.barHeight, moveY=moveY)

        if self.debugMode:
            endTime = time.perf_counter()
            self.updateMetrics(endTime - startTime, len(self.rowObjs))

    def updateTheme(self):
        super().updateTheme()

    def updateBarPosition(self):
        x = self.canvas.canvasx(0)
        y = self.canvas.canvasy(0)
        self.bar.moveTo(x, y)

    def onCanvasScroll(self, event: tk.Event):
        super().onCanvasScroll(event)
        self.updateBarPosition()

    def resizeCanvas(self, bbox, topOffset=0, moveY=True):
        super().resizeCanvas(bbox, topOffset, moveY)
        if moveY: self.updateBarPosition()

    def showHints(self, x: int, y: int, text: str):
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