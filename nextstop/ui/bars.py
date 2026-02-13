"""Info Bar widgets"""
import tkinter as tk

from nextstop.ui.base import BaseWidget
from nextstop.ui.constant import *
from nextstop.util import *

class FancyBar(BaseWidget):
    """FancyBar widget"""
    def __init__(self, board, x, y, width, height):
        super().__init__(board, x, y, width, height)
        self.system_name = ""
        self.jumps = 0

    def setup_style(self):
        self.styles = styles = {}
        colors = self.board.colors

        margin = to_pix(self.canvas, "5p")
        line_length = to_pix(self.canvas, "17.5p")

        styles["bg"] = {"type": "rect", "x0": 0, "x1": self.width, "y0": 0, "y1": self.height, "options": {"fill": colors["bg"], "outline": ""}}

        styles["nextStop"] =  {"type": "text", "x": self.width/2,        "y": margin,                          "options": {"anchor": tk.N,      "fill": colors["textMinor"], "font": ('Helvetica', 9, 'bold')}}
        styles["system"] =    {"type": "text", "x": self.width/2,        "y": self.height/2-margin,            "options": {"anchor": tk.CENTER, "fill": colors["textMain"],  "font": ('Helvetica', 12)}}
        styles["remaining"] = {"type": "text", "x": margin,              "y": self.height-margin-line_length/2, "options": {"anchor": tk.W,      "fill": colors["textMinor"], "font": ('Helvetica', 9)}}
        styles["jump"] =      {"type": "text", "x": self.width/2-margin, "y": self.height-margin-line_length/2, "options": {"anchor": tk.E,      "fill": colors["textMinor"], "font": ('Helvetica', 10, 'bold')}}
        styles["min"] =       {"type": "text", "x": self.width/2+margin, "y": self.height-margin-line_length/2, "options": {"anchor": tk.W,      "fill": colors["textMinor"], "font": ('Helvetica', 10, 'bold')}}
        
        styles["div"] =    {"type": "line", "x0": self.width/2, "x1": self.width/2, "y0": self.height-margin-line_length, "y1": self.height-margin, "options": {"fill": colors["minor1"], "width": "1.5p"}}
        styles["bottom"] = {"type": "line", "x0": 0,            "x1": self.width,   "y0": self.height,                   "y1": self.height,        "options": {"fill": colors["minor1"], "width": "3p"}}

        styles["nextStop"]["options"]["text"] = NEXTSTOP_STR
        styles["system"]["options"]["text"] = self.system_name if self.system_name else DASH6_STR
        styles["remaining"]["options"]["text"] = REMAINING_STR
        jump_text = format_text(self.jumps, JUMP_STR, JUMPS_STR, "--")
        styles["jump"]["options"]["text"] = jump_text
        seconds = self.jumps*45
        if seconds <= 0:
            min_text = f"-- {MIN_STR}"
        elif seconds < 60:
            min_text = f"<1 {MIN_STR}"
        else:
            min_text = ""
            hours, mins, _ = get_time(seconds)
            if hours >= 1:
                min_text += f"{format_text(hours, HOUR_STR, HOURS_STR)} "
            if mins >= 1:
                min_text += format_text(mins, MIN_STR, MINS_STR)
        styles["min"]["options"]["text"] = min_text

    def update_text(self, system_name="", jumps=0):
        """update bar text"""
        self._setter("system_name", system_name)
        self._setter("jumps", jumps)
        if len(self.objs) <= 0:
            self.draw()
        else: self.update(True)
