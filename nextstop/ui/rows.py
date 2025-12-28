from nextstop.ui.base import BaseRow
from nextstop.ui.constant import *
from nextstop.util import *

import tkinter as tk

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