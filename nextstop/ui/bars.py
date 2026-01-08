from nextstop.ui.base import BaseWidget
from nextstop.ui.constant import *
from nextstop.util import *

import tkinter as tk

class FancyBar(BaseWidget):

    def __init__(self, board, canvas, x, y, width, height):
        super().__init__(board, canvas, x, y, width, height)
        self.systemName = ""
        self.jumps = 0

    def setupStyle(self):
        self.styles = styles = {}
        colors = self.board.colors

        margin = toPix(self.canvas, "5p")
        lineLength = toPix(self.canvas, "17.5p")

        styles["bg"] = {"type": "rect", "x0": 0, "x1": self.width, "y0": 0, "y1": self.height, "options": {"fill": colors["bg"], "outline": ""}}

        styles["nextStop"] =  {"type": "text", "x": self.width/2,        "y": margin,                          "options": {"anchor": tk.N,      "fill": colors["textMinor"], "font": ('Helvetica', 9, 'bold')}}
        styles["system"] =    {"type": "text", "x": self.width/2,        "y": self.height/2-margin,            "options": {"anchor": tk.CENTER, "fill": colors["textMain"],  "font": ('Helvetica', 12)}}
        styles["remaining"] = {"type": "text", "x": margin,              "y": self.height-margin-lineLength/2, "options": {"anchor": tk.W,      "fill": colors["textMinor"], "font": ('Helvetica', 9)}}
        styles["jump"] =      {"type": "text", "x": self.width/2-margin, "y": self.height-margin-lineLength/2, "options": {"anchor": tk.E,      "fill": colors["textMinor"], "font": ('Helvetica', 10, 'bold')}}
        styles["min"] =       {"type": "text", "x": self.width/2+margin, "y": self.height-margin-lineLength/2, "options": {"anchor": tk.W,      "fill": colors["textMinor"], "font": ('Helvetica', 10, 'bold')}}
        
        styles["div"] =    {"type": "line", "x0": self.width/2, "x1": self.width/2, "y0": self.height-margin-lineLength, "y1": self.height-margin, "options": {"fill": colors["minor1"], "width": "1.5p"}}
        styles["bottom"] = {"type": "line", "x0": 0,            "x1": self.width,   "y0": self.height,                   "y1": self.height,        "options": {"fill": colors["minor1"], "width": "3p"}}

        styles["nextStop"]["options"]["text"] = NEXTSTOP_STR
        styles["system"]["options"]["text"] = self.systemName if self.systemName else DASH6_STR
        styles["remaining"]["options"]["text"] = REMAINING_STR
        jumpText = formatText(self.jumps, JUMP_STR, JUMPS_STR, "--")
        styles["jump"]["options"]["text"] = jumpText
        seconds = self.jumps*45
        if seconds <= 0: minText = f"-- {MIN_STR}"
        elif seconds < 60: minText = f"<1 {MIN_STR}"
        else:
            minText = ""
            hours, mins, _ = getTime(seconds)
            if hours >= 1: minText += f"{formatText(hours, HOUR_STR, HOURS_STR)} "
            if mins >= 1: minText += formatText(mins, MIN_STR, MINS_STR)
        styles["min"]["options"]["text"] = minText
    
    def updateText(self, systemName="", jumps=0):
        self._setter("systemName", systemName)
        self._setter("jumps", jumps)
        if len(self.objs) <= 0: self.draw()
        else: self.update(True)