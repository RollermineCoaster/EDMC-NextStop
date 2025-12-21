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
#Scoopable
SCOOPABLE_STARS = ["O","B","A","F","G","K","M"]
#white dwarfs, neutron stars, black holes
DANGER_STARS = ["D", "DA", "DAB", "DAO", "DAZ", "DAV", "DB", "DBV", "DBZ", "DC", "DCV", "DO", "DOV", "DQ", "DX", "N", "H", "SupermassiveBlackHole"]

#color
DANGERCOLOR = "#F00"
THEME1933 = {"bg": "#FFF", "textMain": "#000", "textMinor": "#555", "main": "#F00", "minor1": "#888", "minor2": "#BBB"}
THARGOIDCOLORS = {"Alert": "#FFD00F", "Invasion": "#FF6F00", "Controlled": "#286300", "Titan": "#900", "Recovery": "#9F1BFF"}

#font
LOGOFONT = "nextstop-logo"
FUELSTARLOGO =    "\uE800"
DANGERLOGO =      "\uE801"
THARGOIDWARLOGO = "\uE810"
EDSMLOGO =        "\uE820"
BULLETBG =        "\uF111"
BULLETFG =        "\uF10C"

#string
CURRENT = "CURRENT"
DANGER = "Danger"
FUELSTAR = "Fuel Star"
OPENEDSM = "Open EDSM"

class BaseBoard(ABC):

    def __init__(self, frame):
        self.route = []
        self.thargoidSystems= {}
        self.currentIndex = 0
        self.currentPos = [0.0, 0.0, 0.0]
        self.jumping = False
        self.size = frame.winfo_fpixels("225p")
        #create canvas
        self.canvas = tk.Canvas(frame, width=self.size, height=0, bd=0, highlightthickness=0)
        self.canvas.grid()
        #make canvas scrollable (1 scroll in Windows equal 120)
        self.canvas.bind('<MouseWheel>', lambda event : self.canvas.yview_scroll(int(-1*(event.delta/120)), tk.UNITS))

    def setRoute(self, route):
        self.route = copy.deepcopy(route)

    def getRoute(self):
        return copy.deepcopy(self.route)

    def setThargoidSystems(self, thargoidSystems):
        self.thargoidSystems = copy.deepcopy(thargoidSystems)

    def getThargoidSystems(self):
        return copy.deepcopy(self.thargoidSystems)

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
        match starClass:
            #* mean uncertain because NavRoute didn't have that info
            #Scoopable
            case "O":
                return f"O (Blue-White) Star"
            case "B" | "A":
                return f"{starClass} (Blue-White*) Star"
            case "F":
                return "F (White*) Star"
            case "G":
                return "G (White-Yellow*) Star"
            case "K":
                return "K (Yellow-Orange*) Star"
            case "M":
                return "M (Red*) Star"
            #case "B_BlueWhiteSuperGiant" | "A_BlueWhiteSuperGiant":
                #return f"{starClass[0]} (Blue-White super giant) Star"
            #case "F_WhiteSuperGiant":
                #return "F (White super giant) Star"
            #case "G_WhiteSuperGiant":
                #return "G (White-Yellow super giant)"
            #case "K_OrangeGiant":
                #return "K (Yellow-Orange giant) Star"
            #case "M_RedGiant":
                #return "M (Red giant) Star"
            #case "M_RedSuperGiant":
                #return "M (Red super giant) Star"
            
            #Brown Dwarfs
            case "L" | "T" | "Y":
                return f"{starClass} (Brown dwarf) Star"
            
            #Proto-stars
            case "TTS":
                return "T Tauri Star"
            case "AeBe":
                return "Herbig Ae/Be Star"
            
            #Wolf-Rayet
            case "W":
                return f"Wolf-Rayet Star"
            case "WN" | "WNC" | "WC" | "WO":
                text = starClass.replace("W", "")
                return f"Wolf-Rayet {text} Star"
            
            #Rare
            case "MS" | "S":
                return f"{starClass}-type Star"
            
            #White Dwarfs
            case "D" | "DA" | "DAB" | "DAO" | "DAZ" | "DAV" | "DB" | "DBV" | "DBZ" | "DC" | "DCV" | "DO" | "DOV" | "DQ" | "DX":
                return f"White Dwarf ({starClass}) Star"
            
            #Others
            case "N":
                return "Neutron Star"
            case "H":
                return "Black Hole"
            case "SupermassiveBlackHole":
                return "Supermassive Black Hole"
            
            #Default
            case _:
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
        if self.route[index]["starClass"] in SCOOPABLE_STARS:
            return FUELSTARLOGO
        #if danger
        elif self.route[index]["starClass"] in DANGER_STARS:
            return DANGERLOGO
        else:
            return ""

    def getEDSMUrl(self, index):
        return self.route[index]["edsmUrl"]

    def getID64(self, index):
        return self.route[index]["id64"]

    def getStateText(self, index):
        return ("Normal" if self.getID64(index) not in self.thargoidSystems else "Thargoid "+self.thargoidSystems[self.getID64(index)])

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
        self.styles = {}
        self.styles["system"] =       {"x": 0,               "option": {"anchor": tk.NW, "justify": tk.LEFT}}
        self.styles["starType"] =     {"x": 0,               "option": {"anchor": tk.NW, "justify": tk.LEFT}}
        self.styles["state"] =        {"x": 0,               "option": {"anchor": tk.NW, "justify": tk.LEFT}}
        self.styles["distance"] =     {"x": self.size,       "option": {"anchor": tk.NE, "justify": tk.RIGHT}}
        self.styles["reminder"] =     {"x": self.size,       "option": {"anchor": tk.NE, "justify": tk.RIGHT, "tags": "logo", "font": (LOGOFONT, 20)}}
        self.styles["edsmLogo"] =     {"x": self.size*.91,   "option": {"anchor": tk.NE, "justify": tk.RIGHT, "tags": "logo", "font": (LOGOFONT, 20)}}
        self.styles["thargoidLogo"] = {"x": self.size*.82,   "option": {"anchor": tk.NE, "justify": tk.RIGHT, "tags": "logo", "font": (LOGOFONT, 20)}}
        self.styles["bottomLine"] =   {"x": self.size/2, "option": {"anchor": tk.N,  "justify": tk.CENTER}}
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
                    rowObj["system"] =       self.canvas.create_text(self.styles["system"]["x"],           cursorY, **self.styles["system"]["option"])
                    rowObj["distance"] =     self.canvas.create_text(self.styles["distance"]["x"],         cursorY, **self.styles["distance"]["option"])
                    cursorY += max(getCanvasObjHeight(self.canvas, rowObj["system"]), getCanvasObjHeight(self.canvas, rowObj["distance"]))
                    rowObj["starType"] =     self.canvas.create_text(self.styles["starType"]["x"],         cursorY, **self.styles["starType"]["option"])
                    rowObj["reminder"] =     self.canvas.create_text(self.styles["reminder"]["x"],         cursorY, **self.styles["reminder"]["option"])
                    rowObj["edsmLogo"] =     self.canvas.create_text(self.styles["edsmLogo"]["x"],         cursorY, **self.styles["edsmLogo"]["option"])
                    rowObj["thargoidLogo"] = self.canvas.create_text(self.styles["thargoidLogo"]["x"], cursorY, **self.styles["thargoidLogo"]["option"])
                    cursorY += getCanvasObjHeight(self.canvas, rowObj["starType"])
                    rowObj["state"] =        self.canvas.create_text(self.styles["state"]["x"],            cursorY, **self.styles["state"]["option"])
                    cursorY += getCanvasObjHeight(self.canvas, rowObj["state"])
                    self.rowObjs.append(rowObj)
                else:
                    rowObj = self.rowObjs[index]
                self.canvas.itemconfigure(rowObj["system"],   text=str(index+1)+". "+self.getSystemText(index))
                self.canvas.itemconfigure(rowObj["distance"], text=self.getDistanceText(index))
                self.canvas.itemconfigure(rowObj["starType"], text=self.getStarTypeText(index))
                self.canvas.itemconfigure(rowObj["state"],    text="State: "+self.getStateText(index))
                self.canvas.itemconfigure(rowObj["reminder"], text=self.getReminderText(index))
                if self.getDistanceText(index) == CURRENT:
                    self.currentIndex = index
                if self.getReminderText(index) == DANGERLOGO:
                    self.canvas.addtag_withtag("danger", rowObj["reminder"])
                else:
                    self.canvas.itemconfigure(rowObj["reminder"], tags="logo")
                if self.getEDSMUrl(index) == "":
                    self.canvas.itemconfigure(rowObj["edsmLogo"], text="")
                    self.canvas.tag_unbind(rowObj["edsmLogo"], "<Button-1>")
                    self.canvas.tag_unbind(rowObj["edsmLogo"], "<Enter>")
                    self.canvas.tag_unbind(rowObj["edsmLogo"], "<Leave>")
                else:
                    self.canvas.itemconfigure(rowObj["edsmLogo"], text=EDSMLOGO)
                    self.canvas.tag_bind(rowObj["edsmLogo"], "<Button-1>", lambda event, url=self.getEDSMUrl(index) : webbrowser.open(url))
                    self.canvas.tag_bind(rowObj["edsmLogo"], "<Enter>", lambda event: self.canvas.config(cursor="hand2"))
                    self.canvas.tag_bind(rowObj["edsmLogo"], "<Leave>", lambda event: self.canvas.config(cursor=""))
                if self.getID64(index) in self.thargoidSystems:
                    self.canvas.itemconfigure(rowObj["thargoidLogo"], text=THARGOIDWARLOGO)
                else:
                    self.canvas.itemconfigure(rowObj["thargoidLogo"], text="")
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
        self.canvas.itemconfigure("logo", font=(LOGOFONT, 20))
        text = ""
        while len(self.route) > 0 and getCanvasObjWidth(self.canvas, "line") < self.size:
            text += "-"
            self.canvas.itemconfigure("line", text=text)

class FancyBoard(BaseBoard):

    def __init__(self, frame):
        super().__init__(frame)
        self.colors = THEME1933
        self.rowHeight = self.size/6
        self.styles = {}
        #text style
        self.styles["bulletBG"] =     {"type": "text", "x": self.rowHeight/2, "y": self.rowHeight/2,  "option": {"anchor": tk.CENTER, "fill": self.colors["minor2"],    "font": (LOGOFONT,    12), "text":BULLETBG}}
        self.styles["bulletFG"] =     {"type": "text", "x": self.rowHeight/2, "y": self.rowHeight/2,  "option": {"anchor": tk.CENTER, "fill": self.colors["minor1"],    "font": (LOGOFONT,    12), "text":BULLETFG}}
        self.styles["system"] =       {"type": "text", "x": self.rowHeight,   "y": self.rowHeight*.3, "option": {"anchor": tk.W,      "fill": self.colors["textMain"],  "font": ('Helvetica', 12)}}
        self.styles["starType"] =     {"type": "text", "x": self.rowHeight,   "y": self.rowHeight*.7, "option": {"anchor": tk.W,      "fill": self.colors["textMinor"], "font": ('Helvetica', 9)}}
        self.styles["distance"] =     {"type": "text", "x": self.size*.95,    "y": self.rowHeight*.3, "option": {"anchor": tk.E,      "fill": self.colors["textMinor"], "font": ('Helvetica', 11)}}
        self.styles["reminder"] =     {"type": "text", "x": self.size*.95,    "y": self.rowHeight*.7, "option": {"anchor": tk.E,      "fill": self.colors["textMinor"], "font": (LOGOFONT,    20)}}
        self.styles["edsmLogo"] =     {"type": "text", "x": self.size*.86,    "y": self.rowHeight*.7, "option": {"anchor": tk.E,      "fill": self.colors["textMinor"], "font": (LOGOFONT,    20)}}
        self.styles["thargoidLogo"] = {"type": "text", "x": self.size*.77,    "y": self.rowHeight*.7, "option": {"anchor": tk.E,      "fill": self.colors["textMinor"], "font": (LOGOFONT,    20)}}
        #line style
        self.styles["bottomLine"] = {"type": "line", "x0": self.size*.025,   "x1": self.size*.975,   "y0": self.rowHeight,   "y1": self.rowHeight,   "option": {"fill": self.colors["minor1"], "width": "0.766p"}}
        self.styles["bulletLine"] = {"type": "line", "x0": self.rowHeight/2, "x1": self.rowHeight/2, "y0": self.rowHeight/2, "y1": self.rowHeight/2, "option": {"fill": self.colors["main"],   "width": "1.5p"}}
        self.rowObjs = []
        #tooltips
        self.tooltipsVar = tk.StringVar()
        self.tooltipsObj = tk.Label(self.canvas, fg=self.colors["textMinor"], bg=self.colors["bg"], relief=tk.RAISED, bd=1, font=('Helvetica', 9), textvariable=self.tooltipsVar)
        self.tooltips = None
        self.canvas.config(bg=self.colors["bg"])
        self.updateCanvas()

    def setHoverEvent(self, objID, cursor, text):
        self.canvas.tag_bind(objID, "<Enter>", lambda event: self.canvas.config(cursor=cursor))
        self.canvas.tag_bind(objID, "<Enter>", lambda event: self.showTooltips(event.x, event.y, text), "+")
        self.canvas.tag_bind(objID, "<Leave>", lambda event: self.canvas.config(cursor=""))
        self.canvas.tag_bind(objID, "<Leave>", lambda event: self.hideTooltips(), "+")
    
    def removeHoverEvent(self, objID):
        self.canvas.tag_unbind(objID, "<Enter>")
        self.canvas.tag_unbind(objID, "<Leave>")

    def showTooltips(self, x, y, text):    
        self.tooltipsVar.set(text)
        self.canvas.itemconfigure("tooltips", state=tk.NORMAL)
        self.canvas.moveto("tooltips", self.canvas.canvasx(x), self.canvas.canvasy(y))
        bbox = self.canvas.bbox("tooltips")
        xOffset = 0
        yOffset = self.canvas.winfo_fpixels("5p")
        if bbox[0] < 0:
            xOffset -= bbox[0]
        if bbox[1] < 0:
            yOffset -= bbox[1]
        if bbox[2] > self.size:
            xOffset -= bbox[2]-self.size
        totalRow = max(len(self.route), 1)
        if bbox[3]+yOffset > self.rowHeight*totalRow:
            yOffset = -(yOffset+bbox[3]-bbox[1])
        self.canvas.move("tooltips", xOffset, yOffset)
        
    def hideTooltips(self):
        if self.tooltips:
            self.tooltips.destroy()
        self.tooltipsVar.set("")
        self.canvas.itemconfigure("tooltips", state=tk.HIDDEN)
    
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
                self.canvas.create_window(0, 0, tags="tooltips", window=self.tooltipsObj, state=tk.HIDDEN)
                self.rowObjs = []
                self.canvas.create_line(self.styles["bulletLine"]["x0"], self.styles["bulletLine"]["y0"], self.styles["bulletLine"]["x1"], self.styles["bulletLine"]["y1"]+self.rowHeight*(len(self.route)-1), **self.styles["bulletLine"]["option"])
            #loop through route list
            for index in range(len(self.route)):
                if len(self.rowObjs) != len(self.route):
                    rowObj = {}
                    texts = ["bulletBG", "bulletFG", "system", "starType", "distance", "reminder", "edsmLogo", "thargoidLogo"]
                    for k in texts:
                        rowObj[k] = self.canvas.create_text(self.styles[k]["x"], self.styles[k]["y"]+self.rowHeight*(index), **self.styles[k]["option"])
                    self.rowObjs.append(rowObj)
                else:
                    rowObj = self.rowObjs[index]
                self.canvas.itemconfigure(rowObj["system"], **self.styles["system"]["option"], text=str(index+1)+". "+self.getSystemText(index))
                self.canvas.itemconfigure(rowObj["starType"], text=self.getStarTypeText(index))
                self.canvas.itemconfigure(rowObj["distance"], **self.styles["distance"]["option"] , text=self.getDistanceText(index))
                #make text resize dynamically
                resizeCanvasText(self.canvas, rowObj["system"], "127p")
                resizeCanvasText(self.canvas, rowObj["starType"], "116p")
                resizeCanvasText(self.canvas, rowObj["distance"], "52p")
                #setup bullet
                if self.getDistanceText(index) == CURRENT:
                    self.currentIndex = index
                    self.canvas.itemconfigure(rowObj["bulletBG"], fill=self.colors["main"])
                    self.canvas.itemconfigure(rowObj["bulletFG"], fill=self.colors["main"])
                else:
                    self.canvas.itemconfigure(rowObj["bulletBG"], fill=self.colors["minor2"])
                    self.canvas.itemconfigure(rowObj["bulletFG"], fill=self.colors["minor1"])
                #setup reminder logo
                reminderText = self.getReminderText(index)
                self.canvas.itemconfigure(rowObj["reminder"], text=reminderText)
                if reminderText == DANGERLOGO:
                    self.canvas.itemconfigure(rowObj["reminder"], fill=DANGERCOLOR)
                    self.setHoverEvent(rowObj["reminder"], "", DANGER)
                elif reminderText == FUELSTARLOGO:
                    self.canvas.itemconfigure(rowObj["reminder"], fill=self.colors["textMinor"])
                    self.setHoverEvent(rowObj["reminder"], "", FUELSTAR)
                #setup edsm logo
                if self.getEDSMUrl(index) == "":
                    self.canvas.itemconfigure(rowObj["edsmLogo"], text="")
                    self.canvas.tag_unbind(rowObj["edsmLogo"], "<Button-1>")
                    self.removeHoverEvent(rowObj["edsmLogo"])
                else:
                    self.canvas.itemconfigure(rowObj["edsmLogo"], text=EDSMLOGO)
                    self.canvas.tag_bind(rowObj["edsmLogo"], "<Button-1>", lambda event, url=self.getEDSMUrl(index) : webbrowser.open(url))
                    self.setHoverEvent(rowObj["edsmLogo"], "hand2", OPENEDSM)
                #setup thargoid logo
                if self.getID64(index) in self.thargoidSystems:
                    self.canvas.itemconfigure(rowObj["thargoidLogo"], text=THARGOIDWARLOGO, fill=THARGOIDCOLORS[self.thargoidSystems[self.getID64(index)]])
                    self.setHoverEvent(rowObj["thargoidLogo"], "", self.getStateText(index))
                else:
                    self.canvas.itemconfigure(rowObj["thargoidLogo"], text="")
                    self.removeHoverEvent(rowObj["thargoidLogo"])
                #if not bottom
                if len(self.rowObjs) != len(self.route):
                    self.canvas.create_line(self.styles["bottomLine"]["x0"], self.styles["bottomLine"]["y0"]+self.rowHeight*(index), self.styles["bottomLine"]["x1"], self.styles["bottomLine"]["y1"]+self.rowHeight*(index), **self.styles["bottomLine"]["option"])
        totalRow = max(len(self.route), 1)
        self.resizeCanvas((0,0 ,self.size, self.rowHeight*totalRow))

    def updateTheme(self):
        super().updateTheme()
