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

SCOOPABLE_STARS = ["O","B","A","F","G","K","M"]
BROWN_DWARFS = ["L","T","Y"]
WOLF_RAYET = ["W","WN","WNC","WC","WO"]
WHITE_DWARFS = ["D","DA","DAB","DAO","DAZ","DAV","DB","DBV","DBZ","DC","DCV","DO","DOV","DQ","DX"]
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
CURRENT_STR = "CURRENT"
DANGER_STR = "Danger"
FUELSTAR_STR = "Fuel Star"
OPENEDSM_STR = "Open EDSM"
NORMAL_STR = "Normal"
THARGOID_STR = "Thargoid"

SIZE = "225p"

class BaseBoard(ABC):

    def __init__(self, frame):
        self.route = []
        self.thargoidSystems= {}
        self.currentIndex = 0
        self.currentPos = [0.0, 0.0, 0.0]
        self.jumping = False
        self.size = frame.winfo_fpixels(SIZE)
        self.styles = {}
        self.rowObjs = []
        #create canvas
        self.canvas = tk.Canvas(frame, width=self.size, height=0, bd=0, highlightthickness=0)
        self.canvas.grid()
        #make canvas scrollable (1 scroll in Windows equal 120)
        self.canvas.bind('<MouseWheel>', lambda event : self.canvas.yview_scroll(int(-1*(event.delta/120)), tk.UNITS))

        #try resize canvas when plugin frame changing size
        frame.bind('<Configure>', self.onFrameResize)
        #for stopping old event
        self.resizeEventID = ""

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

    def onFrameResize(self, event: tk.Event):
        #return if not parent
        if event.widget != self.canvas.master: return
        currentSize = self.canvas.winfo_width()
        #return if same size
        if event.width == currentSize: return
        #cancel resize before starting a new one
        if self.resizeEventID:
            self.canvas.after_cancel(self.resizeEventID)
            #delay longer when user dragging the window size 
            delay = 500
        else:
            delay = 100
        minSize = self.toPix(SIZE)
        self.size = event.width if event.width > minSize else minSize
        self.resizeEventID = self.canvas.after(delay, lambda: self.updateCanvas(False))

    def resizeCanvas(self, bbox, moveY=True):
        self.resizeEventID = ""
        self.canvas.config(scrollregion=bbox)
        fixedSize = self.toPix(SIZE)
        newHeight = fixedSize if bbox[3] >= fixedSize else bbox[3]
        #change canvas height
        self.canvas.config(height=newHeight)
        #change plugin frame height
        self.canvas.master.config(height=newHeight)
        #change canvas widths
        self.canvas.config(width=self.size)
        if not moveY: return
        if len(self.route) <= 0:
            self.canvas.yview_moveto(0)
        else:
            self.canvas.yview_moveto(bbox[3]/len(self.route)*(self.currentIndex)/bbox[3])

    @abstractmethod
    def updateCanvas(self, moveY=True):
        pass

    def updateTheme(self):
        theme.update(self.canvas)

    def destroy(self):
        self.canvas.destroy()

    def toPix(self, distance):
        try:
            return self.canvas.winfo_fpixels(distance)
        except Exception as e:
            logger.error(f"Failed to get number of pixels! {e}")
            return 0.0

class BaseRow(ABC):

    def __init__(self, board, canvas, x, y, width, height, index, system):
        self.board = board
        self.canvas = canvas
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.setIndex(index)
        self.setSystem(system)
        self.objs = {}
        self.styles = {}

    def setWidth(self, width): self.width = width
    def setIndex(self, index): self.index = index
    def setSystem(self, system): self.system = copy.deepcopy(system)

    def getSystemText(self): return self.system["system"]
    def getEDSMUrl(self): return self.system["edsmUrl"]
    def getID64(self): return self.system["id64"]
    def getThargoidState(self): return (NORMAL_STR if self.getID64() not in self.board.thargoidSystems else self.board.thargoidSystems[self.getID64()])

    def getStarTypeText(self):
        name = self.system["starTypeName"]
        if name != "": return name
        starClass = self.system["starClass"]
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
            case v if v in BROWN_DWARFS:
                return f"{starClass} (Brown dwarf) Star"
            
            #Proto-stars
            case "TTS":
                return "T Tauri Star"
            case "AeBe":
                return "Herbig Ae/Be Star"
            
            #Wolf-Rayet
            case "W":
                return f"Wolf-Rayet Star"
            case v if v in WOLF_RAYET:
                text = starClass.replace("W", "")
                return f"Wolf-Rayet {text} Star"
            
            #Rare
            case "MS" | "S":
                return f"{starClass}-type Star"
            
            #White Dwarfs
            case v if v in WHITE_DWARFS:
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

    def getDistanceText(self):
        #get distance
        distance = self.system["distance"]
        #format the distance "xxx.xx Ly"
        return CURRENT_STR if distance <= 0 else "%.2f Ly" % distance

    def getReminderLogo(self):
        match self.system["starClass"]:
            #if scoopable
            case v if v in SCOOPABLE_STARS:
                return FUELSTARLOGO
            #if danger
            case v if v in DANGER_STARS:
                return DANGERLOGO
            case _:
                return ""

    @abstractmethod
    def setupStyle(self):
        pass

    def draw(self):
        self.setupStyle()
        canvas = self.canvas
        if len(self.objs) > 0: self.clear()
        for k, v in self.styles.items():
            if v["type"] == "text":
                self.objs[k] = obj = canvas.create_text(self.x+v["x"], self.y+v["y"], **v["options"])
            elif v["type"] == "line":
                self.objs[k] = canvas.create_line(self.x+v["x0"], self.y+v["y0"], self.x+v["x1"], self.y+v["y1"], **v["options"])
            else:
                logger.error(f"Unknown object type! {k}: {v}")
                return
            if "event" in v:
                for name, event in v["event"].items():
                    canvas.tag_bind(obj, name, event)

    def update(self):
        self.setupStyle()
        canvas = self.canvas
        for k, v in self.styles.items():
            obj = self.objs[k]
            if v["type"] == "text":
                canvas.coords(obj, self.x+v["x"], self.y+v["y"])
            elif v["type"] == "line":
                canvas.coords(obj, self.x+v["x0"], self.y+v["y0"], self.x+v["x1"], self.y+v["y1"])
            canvas.itemconfig(obj, **v["options"])
            if "event" in v:
                for name, event in v["event"].items():
                    canvas.tag_bind(obj, name, event)

    def updateObj(self, objName, **options):
        if objName in self.objs:
            self.canvas.itemconfig(objName, **options)
        else:
            logger.error(f"Object ({objName}) not found!")

    def clear(self):
        for id in self.objs.values():
            self.canvas.delete(id)
        self.objs.clear()

    def showBottomLine(self, show):
        state = tk.NORMAL if show else tk.HIDDEN
        self.canvas.itemconfig(self.objs["bottomLine"], state=state)

    def onEDSMClick(self, event): webbrowser.open(self.getEDSMUrl())
    def onLogoEnter(self, event, cursor=""): self.canvas.config(cursor=cursor)
    def onLogoLeave(self, event): self.canvas.config(cursor="")

class SimpleRow(BaseRow):

    def getLineText(self):
        count = self.width/toPix(self.canvas, "3p")
        return "-"*round(count+.5)

    def setupStyle(self):
        self.styles = styles = {}
        canvas = self.canvas
        lineOffset = toPix(canvas, "10p")
        styles["system"] =       {"type": "text", "x": 0,                       "y": 0,            "options": {"anchor": tk.NW, "justify": tk.LEFT}}
        styles["starType"] =     {"type": "text", "x": 0,                       "y": lineOffset,   "options": {"anchor": tk.NW, "justify": tk.LEFT}}
        styles["state"] =        {"type": "text", "x": 0,                       "y": lineOffset*2, "options": {"anchor": tk.NW, "justify": tk.LEFT}}
        styles["distance"] =     {"type": "text", "x": self.width,              "y": 0,            "options": {"anchor": tk.NE, "justify": tk.RIGHT}}
        logoOffset = toPix(canvas, "20p")
        styles["reminder"] =     {"type": "text", "x": self.width,              "y": lineOffset,   "options": {"anchor": tk.NE, "justify": tk.RIGHT,  "tags": "logo", "font": (LOGOFONT, 20)}}
        styles["edsmLogo"] =     {"type": "text", "x": self.width-logoOffset,   "y": lineOffset,   "options": {"anchor": tk.NE, "justify": tk.RIGHT,  "tags": "logo", "font": (LOGOFONT, 20)}}
        styles["thargoidLogo"] = {"type": "text", "x": self.width-logoOffset*2, "y": lineOffset,   "options": {"anchor": tk.NE, "justify": tk.RIGHT,  "tags": "logo", "font": (LOGOFONT, 20)}}
        styles["bottomLine"] =   {"type": "text", "x": self.width/2,            "y": self.height,  "options": {"anchor": tk.S,  "justify": tk.CENTER, "tags": "line"}}

        styles["system"]["options"]["text"] = f"{self.index}. {self.getSystemText()}"
        styles["starType"]["options"]["text"] = self.getStarTypeText()
        state = self.getThargoidState()
        if state != NORMAL_STR: state = f"{THARGOID_STR} {state}"
        styles["state"]["options"]["text"] = f"State: {state}"
        styles["distance"]["options"]["text"] = self.getDistanceText()
        styles["reminder"]["options"]["text"] = self.getReminderLogo()
        edsmLogo = EDSMLOGO if self.getEDSMUrl() else ""
        styles["edsmLogo"]["options"]["text"] = edsmLogo
        styles["thargoidLogo"]["options"]["text"] = "" if self.getThargoidState() == NORMAL_STR else THARGOIDWARLOGO
        styles["bottomLine"]["options"]["text"] = self.getLineText()

        #setup edsm logo event
        if edsmLogo:
            styles["edsmLogo"]["event"] = {"<Button-1>": self.onEDSMClick, "<Enter>": lambda event, cursor="hand2": self.onLogoEnter(event, cursor), "<Leave>": self.onLogoLeave}
        else:
            #clear event
            styles["edsmLogo"]["event"] = {"<Button-1>": "", "<Enter>": "", "<Leave>": ""}

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
                system["thargoidState"] = self.getStateText(index)
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

class FancyRow(BaseRow):

    def setupStyle(self):
        self.styles = styles = {}
        colors = self.board.colors
        #text style
        if self.getDistanceText() == CURRENT_STR:
            bulletBGColor = bulletFGColor = colors["main"]
        else:
            bulletBGColor = colors["minor2"]
            bulletFGColor = colors["minor1"]
        styles["bulletBG"] =     {"type": "text", "x": self.height/2,                       "y": self.height/2,  "options": {"anchor": tk.CENTER, "fill": bulletBGColor,            "font": (LOGOFONT,    12), "text":BULLETBG}}
        styles["bulletFG"] =     {"type": "text", "x": self.height/2,                       "y": self.height/2,  "options": {"anchor": tk.CENTER, "fill": bulletFGColor,            "font": (LOGOFONT,    12), "text":BULLETFG}}
        styles["routeI"] =       {"type": "text", "x": self.height,                         "y": self.height*.3, "options": {"anchor": tk.W,      "fill": colors["textMain"],  "font": ('Helvetica', 12)}}
        #count the route index digit
        indexDigit = len(f"{self.index}")
        sysTexOffset = toPix(self.canvas, f"{indexDigit*6 + 8}p")
        styles["system"] =       {"type": "text", "x": self.height+sysTexOffset,            "y": self.height*.3, "options": {"anchor": tk.W,      "fill": colors["textMain"],  "font": ('Helvetica', 12)}}
        styles["starType"] =     {"type": "text", "x": self.height,                         "y": self.height*.7, "options": {"anchor": tk.W,      "fill": colors["textMinor"], "font": ('Helvetica', 9)}}
        rightOffset = toPix(self.canvas, "12p")
        styles["distance"] =     {"type": "text", "x": self.width-rightOffset,              "y": self.height*.3, "options": {"anchor": tk.E,      "fill": colors["textMinor"], "font": ('Helvetica', 11)}}
        logoOffset = toPix(self.canvas, "20p")
        styles["reminder"] =     {"type": "text", "x": self.width-rightOffset,              "y": self.height*.7, "options": {"anchor": tk.E,      "fill": colors["textMinor"], "font": (LOGOFONT,    20)}}
        styles["edsmLogo"] =     {"type": "text", "x": self.width-rightOffset-logoOffset,   "y": self.height*.7, "options": {"anchor": tk.E,      "fill": colors["textMinor"], "font": (LOGOFONT,    20)}}
        styles["thargoidLogo"] = {"type": "text", "x": self.width-rightOffset-logoOffset*2, "y": self.height*.7, "options": {"anchor": tk.E,      "fill": colors["textMinor"], "font": (LOGOFONT,    20)}}
        #line style
        lineOffset = toPix(self.canvas, "6p")
        styles["bottomLine"] =   {"type": "line", "x0": lineOffset,    "x1": self.width-lineOffset, "y0": self.height,   "y1": self.height,   "options": {"fill": colors["minor1"], "width": "0.766p"}}

        styles["routeI"]["options"]["text"] = f"{self.index}. "
        styles["system"]["options"]["text"] = self.getSystemText()
        styles["starType"]["options"]["text"] = self.getStarTypeText()
        styles["distance"]["options"]["text"] = self.getDistanceText()
        reminderLogo = self.getReminderLogo()
        styles["reminder"]["options"]["text"] = reminderLogo
        edsmLogo = EDSMLOGO if self.getEDSMUrl() else ""
        styles["edsmLogo"]["options"]["text"] = edsmLogo
        thargoidLogo = "" if self.getThargoidState() == NORMAL_STR else THARGOIDWARLOGO
        styles["thargoidLogo"]["options"]["text"] = thargoidLogo

        #setup reminder logo
        if reminderLogo:
            if reminderLogo == DANGERLOGO:
                hintsText = DANGER_STR
                styles["reminder"]["options"]["fill"] = DANGERCOLOR
            elif reminderLogo == FUELSTARLOGO:
                hintsText = FUELSTAR_STR
            styles["reminder"]["event"] = {"<Enter>": lambda event, text=hintsText: self.onLogoEnter(event, text=text), "<Leave>": self.onLogoLeave}
        else:
            #clear event
            styles["reminder"]["event"] = {"<Enter>": "", "<Leave>": ""}
        
        #setup edsm logo event
        if edsmLogo:
            styles["edsmLogo"]["event"] = {"<Button-1>": self.onEDSMClick, "<Enter>": lambda event, cursor="hand2", text=OPENEDSM_STR: self.onLogoEnter(event, cursor, text), "<Leave>": self.onLogoLeave}
        else:
            #clear event
            styles["edsmLogo"]["event"] = {"<Button-1>": "", "<Enter>": "", "<Leave>": ""}

        #setup thargoid logo
        if thargoidLogo:
            styles["thargoidLogo"]["options"]["fill"] = THARGOIDCOLORS[self.getThargoidState()]
            styles["thargoidLogo"]["event"] = {"<Enter>": lambda event, text=f"{THARGOID_STR} {self.getThargoidState()}": self.onLogoEnter(event, text=text), "<Leave>": self.onLogoLeave}            
        else:
            #clear event
            styles["thargoidLogo"]["event"] = {"<Enter>": "", "<Leave>": ""}

    def draw(self):
        super().draw()
        self.resizeCanvasText()

    def update(self):
        super().update()
        self.resizeCanvasText()

    def onLogoEnter(self, event, cursor="", text=""):
        super().onLogoEnter(event, cursor)
        self.board.showHints(event.x, event.y, text)

    def onLogoLeave(self, event):
        super().onLogoLeave(event)
        self.board.hideHints()

    def resizeCanvasText(self):
        objs = self.objs
        #count the route index digit
        indexDigit = len(f"{self.index}")
        sysTexOffset = toPix(self.canvas, f"{indexDigit*6 + 8}p")
        #make text resize dynamically
        resizeCanvasText(self.canvas, objs["system"],   self.width*.56-sysTexOffset)
        resizeCanvasText(self.canvas, objs["starType"], self.width*.52)
        resizeCanvasText(self.canvas, objs["distance"], self.width*.23)

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