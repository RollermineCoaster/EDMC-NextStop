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
        while len(self.rows) > len(self.route):
            row = self.rows.pop()
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
                if index >= len(self.rows):
                    row = SimpleRow(self, canvas, 0, rowHeight*index, self.size, rowHeight, index+1, system)
                    row.draw()
                    self.rows.append(row)
                else:
                    row = self.rows[index]
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
            self.updateMetrics(endTime - startTime, len(self.rows))

    def updateTheme(self):
        super().updateTheme()
        self.canvas.itemconfig("all", fill=theme.current["foreground"], font=theme.current["font"])
        self.canvas.itemconfig("logo", font=(LOGOFONT, 20))

class FancyBoard(BaseBoard):

    def __init__(self, frame: tk.Frame):
        super().__init__(frame)
        self.colors = THEME1933
        self.rowHeight = toPix(self.canvas, SIZE)/MAX_ROWS
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
        while len(self.rows) > routeSize:
            row = self.rows.pop()
            row.clear()
        self.updateCurrentIndex()

        totalRow = max(routeSize, 1)
        self.resizeCanvas((0,0 ,self.size, self.rowHeight*totalRow), topOffset=self.barHeight, moveY=moveY)
        if moveY:
            self.updateBarPosition()

        #if no route
        if routeSize <= 0:
            self.hideHints()
            if self.bulletLineObj: canvas.itemconfig(self.bulletLineObj, state=tk.HIDDEN)
            canvas.create_text(self.size/2, self.rowHeight/2+self.barHeight, text=NOROUTEFULL_STR, anchor=tk.CENTER, fill=self.colors["textMain"], font=('Helvetica', 12), justify=tk.CENTER, tags="noRoute")
        else:
            canvas.delete("noRoute")
            lineLength = self.rowHeight/2 + self.rowHeight*(routeSize-1) + self.barHeight
            if not self.bulletLineObj:
                self.bulletLineObj = canvas.create_line(self.rowHeight/2, self.rowHeight/2+self.barHeight, self.rowHeight/2, lineLength, fill=self.colors["main"], width="1.5p")
            else:
                #show bulletLine
                canvas.itemconfig(self.bulletLineObj, state=tk.NORMAL)
                #resize bulletLine
                canvas.coords(self.bulletLineObj, self.rowHeight/2, self.rowHeight/2+self.barHeight, self.rowHeight/2, lineLength)
            self.updateRows()
        bar.setWidth(self.size)
        if self.currentIndex < 0 or self.currentIndex >= routeSize-1: bar.updateText()
        else:
            nextStopIndex = self.currentIndex+1
            bar.updateText(f"{nextStopIndex+1}. {self.route[nextStopIndex]["system"]}", routeSize-nextStopIndex)

        if self.debugMode:
            endTime = time.perf_counter()
            self.updateMetrics(endTime - startTime, len(self.rows))

    def updateRows(self):
        if self.debugMode: startTime = time.perf_counter()
        canvas = self.canvas
        routeSize = len(self.route)

        #size of the row pool
        poolSize = min(routeSize, MAX_ROWS+1)
        #current top Y after scrolling
        top = canvas.canvasy(0)
        #calculate how many row is scrolled
        routeOffset = int(top//self.rowHeight)
        #limit the offset to prevent list index out of bound
        routeOffset = min(routeOffset, routeSize-poolSize)

        #rearrange row objects to reduce the update call
        if len(self.rows) > 0:
            #how many row should rearrange
            delta = self.rows[0].getIndex() - (routeOffset+1)
            if delta != 0 and abs(delta) < len(self.rows):
                for _ in range(abs(delta)):
                    #pop the first if scroll down else last
                    popIndex = 0 if delta < 0 else -1
                    temp = self.rows.pop(popIndex)
                    if delta < 0: self.rows.append(temp) #first to last
                    else: self.rows.insert(0, temp) #last ot first
        
        #loop through route list
        for rowIndex in range(poolSize):
            routeIndex = rowIndex + routeOffset
            rowPosOffset = self.rowHeight*(routeIndex) + self.barHeight
            system = self.route[routeIndex]
            system["distance"] = getDistance(self.currentPos, system["pos"])

            if rowIndex >= len(self.rows):
                row = FancyRow(self, canvas, 0, rowPosOffset, self.size, self.rowHeight, routeIndex+1, system)
                row.draw()
                self.rows.append(row)
            else:
                row = self.rows[rowIndex]
                row.setWidth(self.size)
                row.setPos(0, rowPosOffset)
                row.setIndex(routeIndex+1)
                row.setSystem(system)
                row.update()
            #if not bottom
            notBottom = routeIndex+1 < routeSize
            row.showBottomLine(notBottom)

        if self.debugMode:
            endTime = time.perf_counter()
            self.updateMetrics(endTime - startTime, len(self.rows))

    def updateTheme(self):
        super().updateTheme()

    def updateBarPosition(self):
        x = self.canvas.canvasx(0)
        y = self.canvas.canvasy(0)
        self.bar.moveTo(x, y, True)

    def onCanvasScroll(self, event: tk.Event):
        super().onCanvasScroll(event)
        if len(self.rows) > MAX_ROWS:
            self.updateBarPosition()
            self.updateRows()

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