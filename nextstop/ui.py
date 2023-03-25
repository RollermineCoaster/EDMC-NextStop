"""
NextStop UI
"""
from theme import theme

import tkinter as tk
from nextstop.util import *
import copy
from abc import ABC, abstractmethod
from config import appname, config

import logging

logger = logging.getLogger(f"{appname}.EDMC-NextStop")

#star type
SCOOPABLE = ["O","B","A","F","G","K","M"]
#white dwarfs, neutron stars, black holes
DANGER = ["D","N","H"]

class BaseBoard(ABC):

    def __init__(self, frame):
        self.route = []
        self.currentIndex = 0
        self.currentPos = [0.0, 0.0, 0.0]
        self.scale = config.get_int("ui_scale")/100
        self.size = 300*self.scale
        #create canvas
        self.canvas = tk.Canvas(frame, width=self.size, height=0, bd=0, highlightthickness=0)
        self.canvas.grid()
        #make canvas scrollable (1 scroll in Windows equal 120)
        self.canvas.bind('<MouseWheel>', lambda event : self.canvas.yview_scroll(int(-1*(event.delta/120)), tk.UNITS))

    def setRoute(self, route):
        self.route = copy.deepcopy(route)

    def getRoute(self):
        return copy.deepcopy(self.route)

    def setCurrentPos(self, currentPos):
        self.currentPos = copy.deepcopy(currentPos)

    def getCurrentPos(self):
        return copy.deepcopy(self.currentPos)

    def getSystemText(self, index):
        return self.route[index]["system"]

    def getStarTypeText(self, index):
        name = self.route[index]["starTypeName"]
        if name != "":
            return name
        starClass = self.route[index]["starClass"]
        if starClass == "L" or starClass == "T" or starClass == "Y":
            return f"{starClass} (Brown dwarf) Star"
        elif starClass == "TTS":
            return "T Tauri Star"
        elif starClass == "AeBe":
            return "Herbig Ae/Be Star"
        elif starClass[0] == "W":
            text = starClass.replace("W", " ")
            return f"Wolf-Rayet{text} Star"
        elif starClass == "MS" or starClass == "S":
            return f"{starClass}-type Star"
        elif starClass[0] == "D":
            return f"White Dwarf ({starClass}) Star"
        elif starClass == "N":
            return "Neutron Star"
        elif starClass == "H":
            return "Black Hole"
        elif starClass == "SupermassiveBlackHole":
            return "Supermassive Black Hole"
        else:
            return f"{starClass} Star"

    def getDistanceText(self, index):
        #get distance
        distance = getDistance(self.currentPos, self.route[index]["pos"])
        if distance <= 0:
            return "CURRENT"
        else:
            #format the distance "xxx.xx Ly"
            return "%.2f Ly" % distance

    def getReminderText(self, index):
        #if scoopable
        if self.route[index]["starClass"][0] in SCOOPABLE:
            return "+💧"
        #if danger
        elif self.route[index]["starClass"][0] in DANGER:
            return "⟁"
        else:
            return ""

    def resizeCanvas(self, bbox):
        self.canvas.config(scrollregion=bbox)
        #resize the canvas
        newHeight = self.size if bbox[3] >= self.size else bbox[3]
        self.canvas.config(height=newHeight)
        if len(self.route) <= 0:
            self.canvas.yview_moveto(0)
        else:
            self.canvas.yview_moveto(bbox[3]/len(self.route)*(self.currentIndex)/bbox[3])

    @abstractmethod
    def updateCanvas(self):
        pass

    def updateTheme(self):
        theme.update(self.canvas)

    def destroy(self):
        self.canvas.destroy()

class SimpleBoard(BaseBoard):

    def __init__(self, frame):
        super().__init__(frame)
        #display text
        self.textLVar = tk.StringVar()
        self.textRVar = tk.StringVar()
        #create display text widget
        self.textLWidget = tk.Label(self.canvas, textvariable=self.textLVar, justify=tk.LEFT)
        self.textRWidget = tk.Label(self.canvas, textvariable=self.textRVar, justify=tk.RIGHT)
        #update the theme of text widget
        self.textLWidget.after(10, lambda: theme.update(self.textLWidget))
        self.textRWidget.after(10, lambda: theme.update(self.textRWidget))
        #put text widget inside canvas
        self.canvas.create_window(0, 0, anchor=tk.NW, window=self.textLWidget)
        self.canvas.create_window(self.size, 0, anchor=tk.NE, window=self.textRWidget)
        #make canvas scrollable (1 scroll in Windows equal 120)
        self.textLWidget.bind('<MouseWheel>', lambda event : self.canvas.yview_scroll(int(-1*(event.delta/120)), tk.UNITS))
        self.textRWidget.bind('<MouseWheel>', lambda event : self.canvas.yview_scroll(int(-1*(event.delta/120)), tk.UNITS))
        self.updateCanvas()

    def updateCanvas(self):
        #if no route
        if len(self.route) <= 0:
            self.currentIndex = 0
            self.textLVar.set("-------No Route-------")
            self.textRVar.set("-------")
        else:
            textL = ""
            textR = ""
            #loop through route list
            for index in range(len(self.route)):
                #build display text on the left
                textL += str(index+1)+". "+self.getSystemText(index)+"\n"
                textL += self.getStarTypeText(index)+"\n"
                #build display text on the right
                textR += self.getDistanceText(index)+"\n"
                if textR == "CURRENT":
                    self.currentIndex = index
                textR += self.getReminderText(index)+"\n"
                #if not bottom
                if index < len(self.route)-1:
                    textL += "---------------------------------------------\n"
                    textR += "------------\n"
            self.textLVar.set(textL)
            self.textRVar.set(textR)
        self.resizeCanvas(self.canvas.bbox("all"))

    def updateTheme(self):
        super().updateTheme()
        theme.update(self.textLWidget)
        theme.update(self.textRWidget)



class FancyBoard(BaseBoard):

    def __init__(self, frame):
        super().__init__(frame)
        self.colors = {"bg": "#fff", "textMain": "#000", "textMinor": "#555", "main": "#f00", "minor1": "#888", "minor2": "#bbb", "danger": "#f00"}
        self.rowHeight = self.size/7
        self.styles = {}
        self.styles["bullet"] = {"x0": self.rowHeight/2-self.rowHeight/8, "y0": self.rowHeight/2-self.rowHeight/8,
                                 "x1": self.rowHeight/2+self.rowHeight/8, "y1": self.rowHeight/2+self.rowHeight/8,
                                 "option1": {"fill": self.colors["main"],  "outline": self.colors["main"],  "width": 2*self.scale},
                                 "option2": {"fill": self.colors["minor2"], "outline": self.colors["minor1"], "width": 2*self.scale}}
        self.styles["system"] =   {"x": self.rowHeight,   "y": self.rowHeight*.15,  "option": {"anchor": tk.NW, "fill": self.colors["textMain"],  "font": ('Helvetica', int(-16*self.scale)), "justify": tk.LEFT}}
        self.styles["starType"] = {"x": self.rowHeight,   "y": self.rowHeight*.55,  "option": {"anchor": tk.NW, "fill": self.colors["textMinor"], "font": ('Helvetica', int(-12*self.scale)), "justify": tk.LEFT}}
        self.styles["distance"] = {"x": self.size*.95, "y": self.rowHeight*.15,  "option": {"anchor": tk.NE, "fill": self.colors["textMinor"], "font": ('Helvetica', int(-14*self.scale)), "justify": tk.RIGHT}}
        self.styles["reminder"] = {"x": self.size*.95, "y": self.rowHeight*.5,   "option": {"anchor": tk.NE, "fill": self.colors["textMinor"], "font": ('Helvetica', int(-16*self.scale)), "justify": tk.RIGHT}}
        self.styles["bottomLine"] = {"x0": self.size*.025, "x1": self.size*.975, "y0": self.rowHeight, "y1": self.rowHeight,   "option": {"fill": self.colors["minor1"], "width": 1*self.scale}}
        self.styles["bulletLine"] = {"x0": self.rowHeight/2, "x1": self.rowHeight/2, "y0": self.rowHeight/2, "y1": self.rowHeight/2, "option": {"fill": self.colors["main"], "width": 2*self.scale}}
        self.rowObjs = []
        self.canvas.config(bg=self.colors["bg"])
        self.updateCanvas()

    def updateCanvas(self):
        #if no route
        if len(self.route) <= 0:
            self.currentIndex = 0
            self.canvas.delete("all")
            self.rowObjs = []
            self.canvas.create_text(self.size/2, self.rowHeight/2, anchor=tk.CENTER, fill=self.colors["textMain"], font=self.styles["system"]["option"]["font"], justify=tk.CENTER, text="-------No Route-------")
        else:
            if len(self.rowObjs) != len(self.route):
                self.canvas.delete("all")
                self.rowObjs = []
                self.canvas.create_line(self.styles["bulletLine"]["x0"], self.styles["bulletLine"]["y0"], self.styles["bulletLine"]["x1"], self.styles["bulletLine"]["y1"]+self.rowHeight*(len(self.route)-1), **self.styles["bulletLine"]["option"])
            #loop through route list
            for index in range(len(self.route)):
                if len(self.rowObjs) != len(self.route):
                    rowObj = {}
                    rowObj["bullet"] =   self.canvas.create_oval(self.styles["bullet"]["x0"], self.styles["bullet"]["y0"]+self.rowHeight*(index), self.styles["bullet"]["x1"], self.styles["bullet"]["y1"]+self.rowHeight*(index))
                    rowObj["system"] =   self.canvas.create_text(self.styles["system"]["x"],   self.styles["system"]["y"]+self.rowHeight*(index),   **self.styles["system"]["option"])
                    rowObj["starType"] = self.canvas.create_text(self.styles["starType"]["x"], self.styles["starType"]["y"]+self.rowHeight*(index), **self.styles["starType"]["option"])
                    rowObj["distance"] = self.canvas.create_text(self.styles["distance"]["x"], self.styles["distance"]["y"]+self.rowHeight*(index), **self.styles["distance"]["option"])
                    rowObj["reminder"] = self.canvas.create_text(self.styles["reminder"]["x"], self.styles["reminder"]["y"]+self.rowHeight*(index), **self.styles["reminder"]["option"])
                    self.rowObjs.append(rowObj)
                else:
                    rowObj = self.rowObjs[index]
                self.canvas.itemconfigure(rowObj["system"], text=str(index+1)+". "+self.getSystemText(index))

                #make system name resize dynamically
                textHeight = self.canvas.bbox(rowObj["system"])[3]
                textFont = self.styles["system"]["option"]["font"][0]
                textSize = self.styles["system"]["option"]["font"][1]
                #limit the width of the object
                self.canvas.itemconfigure(rowObj["system"], width=169/300*self.size)
                #while text size > 1px and current text height > old text height
                while textSize < -1 and self.canvas.bbox(rowObj["system"])[3] > textHeight:
                    textSize += 1
                    self.canvas.itemconfigure(rowObj["system"], font=(textFont, textSize))

                self.canvas.itemconfigure(rowObj["starType"], text=self.getStarTypeText(index))
                self.canvas.itemconfigure(rowObj["distance"], text=self.getDistanceText(index))

                #make distance resize dynamically
                textHeight = self.canvas.bbox(rowObj["distance"])[3]
                textFont = self.styles["distance"]["option"]["font"][0]
                textSize = self.styles["distance"]["option"]["font"][1]
                #limit the width of the object
                self.canvas.itemconfigure(rowObj["distance"], width=69/300*self.size)
                #while text size > 1px and current text height > old text height
                while textSize < -1 and self.canvas.bbox(rowObj["distance"])[3] > textHeight:
                    textSize += 1
                    self.canvas.itemconfigure(rowObj["distance"], font=(textFont, textSize))

                self.canvas.itemconfigure(rowObj["reminder"], text=self.getReminderText(index))
                if self.getDistanceText(index) == "CURRENT":
                    self.currentIndex = index
                    self.canvas.itemconfigure(rowObj["bullet"], **self.styles["bullet"]["option1"])
                else:
                    self.canvas.itemconfigure(rowObj["bullet"], **self.styles["bullet"]["option2"])
                if self.getReminderText(index) == "⟁":
                    self.canvas.itemconfigure(rowObj["reminder"], fill=self.colors["danger"])
                #if not bottom
                if index < len(self.route)-1:
                    self.canvas.create_line(self.styles["bottomLine"]["x0"], self.styles["bottomLine"]["y0"]+self.rowHeight*(index), self.styles["bottomLine"]["x1"], self.styles["bottomLine"]["y1"]+self.rowHeight*(index), **self.styles["bottomLine"]["option"])
        totalRow = max(len(self.route), 1)
        self.resizeCanvas((0,0 ,self.size, self.rowHeight*totalRow))
