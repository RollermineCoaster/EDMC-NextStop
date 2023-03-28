"""
NextStop UI
"""
from theme import theme

import tkinter as tk
from nextstop.util import *
import copy
from abc import ABC, abstractmethod
from config import appname, config
import webbrowser

import os
from os.path import basename, dirname, join
import ctypes
from ctypes.wintypes import DWORD, LPCVOID, LPCWSTR
AddFontResourceEx = ctypes.windll.gdi32.AddFontResourceExW
AddFontResourceEx.restypes = [LPCWSTR, DWORD, LPCVOID]  # type: ignore
FR_PRIVATE = 0x10
AddFontResourceEx(join(os.path.dirname(__file__), 'assets/nextstop-logo.ttf'), FR_PRIVATE, 0)

import logging

logger = logging.getLogger(f"{appname}.EDMC-NextStop")
#star type
SCOOPABLE = ["O","B","A","F","G","K","M"]
#white dwarfs, neutron stars, black holes
DANGER = ["D","N","H"]

LOGOFONT = "nextstop-logo"
FUELSTARLOGO =    "\uE800"
DANGERLOGO =      "\uE801"
THARGOIDWARLOGO = "\uE810"
EDSMLOGO =        "\uE820"
BULLETBG =        "\uF111"
BULLETFG =        "\uF10C"

CURRENT = "CURRENT"

class BaseBoard(ABC):

    def __init__(self, frame):
        self.route = []
        self.currentIndex = 0
        self.currentPos = [0.0, 0.0, 0.0]
        self.size = 300*config.get_int("ui_scale")/100
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
            return CURRENT
        else:
            #format the distance "xxx.xx Ly"
            return "%.2f Ly" % distance

    def getReminderText(self, index):
        #if scoopable
        if self.route[index]["starClass"][0] in SCOOPABLE:
            return FUELSTARLOGO
        #if danger
        elif self.route[index]["starClass"][0] in DANGER:
            return DANGERLOGO
        else:
            return ""

    def getEDSMUrl(self, index):
        return self.route[index]["edsmUrl"]

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
        self.colors = {"danger": "#f00"}
        self.styles = {}
        self.styles["system"] =     {"x": 0,           "option": {"anchor": tk.NW, "justify": tk.LEFT}}
        self.styles["starType"] =   {"x": 0,           "option": {"anchor": tk.NW, "justify": tk.LEFT}}
        self.styles["distance"] =   {"x": self.size,   "option": {"anchor": tk.NE, "justify": tk.RIGHT}}
        self.styles["reminder"] =   {"x": self.size,   "option": {"anchor": tk.NE, "justify": tk.RIGHT}}
        self.styles["bottomLine"] = {"x": self.size/2, "option": {"anchor": tk.N,  "justify": tk.CENTER}}
        self.rowObjs = []
        self.updateCanvas()

    def updateCanvas(self):
        #if no route
        if len(self.route) <= 0:
            self.currentIndex = 0
            self.canvas.delete("all")
            self.rowObjs = []
            self.canvas.create_text(self.styles["system"]["x"],   0, **self.styles["system"]["option"],   text="-------No Route-------")
            self.canvas.create_text(self.styles["distance"]["x"], 0, **self.styles["distance"]["option"], text="-------")
        else:
            if len(self.rowObjs) != len(self.route):
                self.canvas.delete("all")
                self.rowObjs = []
            #loop through route list
            cursorY = 0
            for index in range(len(self.route)):
                if len(self.rowObjs) != len(self.route):
                    rowObj = {}
                    rowObj["system"] =   self.canvas.create_text(self.styles["system"]["x"],   cursorY, **self.styles["system"]["option"])
                    rowObj["distance"] = self.canvas.create_text(self.styles["distance"]["x"], cursorY, **self.styles["distance"]["option"])
                    cursorY += max(getCanvasObjHeight(self.canvas, rowObj["system"]), getCanvasObjHeight(self.canvas, rowObj["distance"]))
                    rowObj["starType"] = self.canvas.create_text(self.styles["starType"]["x"], cursorY, **self.styles["starType"]["option"])
                    rowObj["reminder"] = self.canvas.create_text(self.styles["reminder"]["x"], cursorY, **self.styles["reminder"]["option"])
                    self.canvas.addtag_withtag("logo", rowObj["reminder"])
                    cursorY += max(getCanvasObjHeight(self.canvas, rowObj["starType"]), getCanvasObjHeight(self.canvas, rowObj["reminder"]))
                    self.rowObjs.append(rowObj)
                else:
                    rowObj = self.rowObjs[index]
                self.canvas.itemconfigure(rowObj["system"],   text=str(index+1)+". "+self.getSystemText(index))
                self.canvas.itemconfigure(rowObj["distance"], text=self.getDistanceText(index))
                self.canvas.itemconfigure(rowObj["starType"], text=self.getStarTypeText(index))
                self.canvas.itemconfigure(rowObj["reminder"], text=self.getReminderText(index))
                if self.getDistanceText(index) == CURRENT:
                    self.currentIndex = index
                if self.getReminderText(index) == DANGERLOGO:
                    self.canvas.itemconfigure(rowObj["reminder"])
                    self.canvas.addtag_withtag("danger", rowObj["reminder"])
                #if not bottom
                if len(self.rowObjs) != len(self.route):
                    bottomLine = self.canvas.create_text(self.styles["bottomLine"]["x"], cursorY, **self.styles["bottomLine"]["option"])
                    self.canvas.addtag_withtag("line", bottomLine)
                    cursorY += getCanvasObjHeight(self.canvas, bottomLine)
        self.resizeCanvas(self.canvas.bbox("all"))
        self.canvas.after(10, lambda: self.updateTheme())

    def updateTheme(self):
        super().updateTheme()
        self.canvas.itemconfigure("all", fill=theme.current["foreground"], font=theme.current["font"])
        self.canvas.itemconfigure("logo", font=(LOGOFONT, 12))
        self.canvas.itemconfigure("danger", fill=self.colors["danger"])
        text = ""
        while getCanvasObjWidth(self.canvas, "line") < self.size:
            text += "-"
            self.canvas.itemconfigure("line", text=text)

class FancyBoard(BaseBoard):

    def __init__(self, frame):
        super().__init__(frame)
        self.colors = {"bg": "#fff", "textMain": "#000", "textMinor": "#555", "main": "#f00", "minor1": "#888", "minor2": "#bbb", "danger": "#f00"}
        self.rowHeight = self.size/7
        self.styles = {}
        self.styles["bulletBG"] = {"x": self.rowHeight/2, "y": self.rowHeight/2,    "option": {"anchor": tk.CENTER, "fill": self.colors["minor2"],    "font": (LOGOFONT,    12), "justify": tk.CENTER, "text":BULLETBG}}
        self.styles["bulletFG"] = {"x": self.rowHeight/2, "y": self.rowHeight/2,    "option": {"anchor": tk.CENTER, "fill": self.colors["minor1"],    "font": (LOGOFONT,    12), "justify": tk.CENTER, "text":BULLETFG}}
        self.styles["system"] =   {"x": self.rowHeight,   "y": self.rowHeight*.15,  "option": {"anchor": tk.NW,     "fill": self.colors["textMain"],  "font": ('Helvetica', 12), "justify": tk.LEFT}}
        self.styles["starType"] = {"x": self.rowHeight,   "y": self.rowHeight*.55,  "option": {"anchor": tk.NW,     "fill": self.colors["textMinor"], "font": ('Helvetica', 9),  "justify": tk.LEFT}}
        self.styles["distance"] = {"x": self.size*.95,    "y": self.rowHeight*.15,  "option": {"anchor": tk.NE,     "fill": self.colors["textMinor"], "font": ('Helvetica', 11), "justify": tk.RIGHT}}
        self.styles["reminder"] = {"x": self.size*.95,    "y": self.rowHeight*.5,   "option": {"anchor": tk.NE,     "fill": self.colors["textMinor"], "font": (LOGOFONT,    12), "justify": tk.RIGHT}}
        self.styles["edsmLogo"] = {"x": self.size*.90,    "y": self.rowHeight*.5,   "option": {"anchor": tk.NE,     "fill": self.colors["textMinor"], "font": (LOGOFONT,    12), "justify": tk.RIGHT}}
        self.styles["bottomLine"] = {"x0": self.size*.025,   "x1": self.size*.975,   "y0": self.rowHeight,   "y1": self.rowHeight,   "option": {"fill": self.colors["minor1"], "width": "0.766p"}}
        self.styles["bulletLine"] = {"x0": self.rowHeight/2, "x1": self.rowHeight/2, "y0": self.rowHeight/2, "y1": self.rowHeight/2, "option": {"fill": self.colors["main"],   "width": "1.5p"}}
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
                    rowObj["bulletBG"] = self.canvas.create_text(self.styles["bulletBG"]["x"], self.styles["bulletBG"]["y"]+self.rowHeight*(index), **self.styles["bulletBG"]["option"])
                    rowObj["bulletFG"] = self.canvas.create_text(self.styles["bulletFG"]["x"], self.styles["bulletFG"]["y"]+self.rowHeight*(index), **self.styles["bulletFG"]["option"])
                    rowObj["system"] =   self.canvas.create_text(self.styles["system"]["x"],   self.styles["system"]["y"]+self.rowHeight*(index),   **self.styles["system"]["option"])
                    rowObj["starType"] = self.canvas.create_text(self.styles["starType"]["x"], self.styles["starType"]["y"]+self.rowHeight*(index), **self.styles["starType"]["option"])
                    rowObj["distance"] = self.canvas.create_text(self.styles["distance"]["x"], self.styles["distance"]["y"]+self.rowHeight*(index), **self.styles["distance"]["option"])
                    rowObj["reminder"] = self.canvas.create_text(self.styles["reminder"]["x"], self.styles["reminder"]["y"]+self.rowHeight*(index), **self.styles["reminder"]["option"])
                    rowObj["edsmLogo"] = self.canvas.create_text(self.styles["edsmLogo"]["x"], self.styles["edsmLogo"]["y"]+self.rowHeight*(index), **self.styles["edsmLogo"]["option"])
                    self.rowObjs.append(rowObj)
                else:
                    rowObj = self.rowObjs[index]
                self.canvas.itemconfigure(rowObj["system"], **self.styles["system"]["option"], text=str(index+1)+". "+self.getSystemText(index))
                #make system resize dynamically
                resizeCanvasText(self.canvas, rowObj["system"], "127p")
                self.canvas.itemconfigure(rowObj["starType"], text=self.getStarTypeText(index))
                self.canvas.itemconfigure(rowObj["distance"], **self.styles["distance"]["option"] , text=self.getDistanceText(index))
                #make distance resize dynamically
                resizeCanvasText(self.canvas, rowObj["distance"], "52p")

                self.canvas.itemconfigure(rowObj["reminder"], text=self.getReminderText(index))
                if self.getEDSMUrl(index) == "":
                    self.canvas.itemconfigure(rowObj["edsmLogo"], text="")
                    self.canvas.tag_unbind(rowObj["edsmLogo"], "<Button-1>")
                else:
                    self.canvas.itemconfigure(rowObj["edsmLogo"], text=EDSMLOGO)
                    self.canvas.tag_bind(rowObj["edsmLogo"], "<Button-1>", lambda event, url=self.getEDSMUrl(index) : webbrowser.open(url))
                if self.getDistanceText(index) == CURRENT:
                    self.currentIndex = index
                    self.canvas.itemconfigure(rowObj["bulletBG"], fill=self.colors["main"])
                    self.canvas.itemconfigure(rowObj["bulletFG"], fill=self.colors["main"])
                else:
                    self.canvas.itemconfigure(rowObj["bulletBG"], fill=self.colors["minor2"])
                    self.canvas.itemconfigure(rowObj["bulletFG"], fill=self.colors["minor1"])
                if self.getReminderText(index) == DANGERLOGO:
                    self.canvas.itemconfigure(rowObj["reminder"], fill=self.colors["danger"])
                #if not bottom
                if len(self.rowObjs) != len(self.route):
                    self.canvas.create_line(self.styles["bottomLine"]["x0"], self.styles["bottomLine"]["y0"]+self.rowHeight*(index), self.styles["bottomLine"]["x1"], self.styles["bottomLine"]["y1"]+self.rowHeight*(index), **self.styles["bottomLine"]["option"])
        totalRow = max(len(self.route), 1)
        self.resizeCanvas((0,0 ,self.size, self.rowHeight*totalRow))
