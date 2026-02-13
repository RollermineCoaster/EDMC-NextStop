"""Row widgets"""
import tkinter as tk

from nextstop.ui.base import BaseRow
from nextstop.ui.constant import *
from nextstop.util import *

class SimpleRow(BaseRow):
    """Row widget for SimpleBoard"""
    def get_line_text(self):
        """Get the bottom line text"""
        count = self.width/to_pix(self.canvas, "3p")
        return "-"*round(count+.5)

    def setup_style(self):
        self.styles = styles = {}
        canvas = self.canvas
        line_offset = to_pix(canvas, "10p")
        styles["system"] =       {"type": "text", "x": 0,                       "y": 0,            "options": {"anchor": tk.NW, "justify": tk.LEFT}}
        styles["starType"] =     {"type": "text", "x": 0,                       "y": line_offset,   "options": {"anchor": tk.NW, "justify": tk.LEFT}}
        styles["state"] =        {"type": "text", "x": 0,                       "y": line_offset*2, "options": {"anchor": tk.NW, "justify": tk.LEFT}}
        styles["distance"] =     {"type": "text", "x": self.width,              "y": 0,            "options": {"anchor": tk.NE, "justify": tk.RIGHT}}
        logo_offset = to_pix(canvas, "20p")
        styles["reminder"] =     {"type": "text", "x": self.width,              "y": line_offset,   "options": {"anchor": tk.NE, "justify": tk.RIGHT,  "tags": "logo", "font": (LOGO_FONT, 20)}}
        styles["edsm_logo"] =     {"type": "text", "x": self.width-logo_offset,   "y": line_offset,   "options": {"anchor": tk.NE, "justify": tk.RIGHT,  "tags": "logo", "font": (LOGO_FONT, 20)}}
        styles["thargoid_logo"] = {"type": "text", "x": self.width-logo_offset*2, "y": line_offset,   "options": {"anchor": tk.NE, "justify": tk.RIGHT,  "tags": "logo", "font": (LOGO_FONT, 20)}}
        styles["bottomLine"] =   {"type": "text", "x": self.width/2,            "y": self.height,  "options": {"anchor": tk.S,  "justify": tk.CENTER, "tags": "line"}}

        styles["system"]["options"]["text"] = f"{self.index}. {self.get_system_name()}"
        styles["starType"]["options"]["text"] = self.get_star_type_name()
        state = self.get_thargoid_state()
        if state != NORMAL_STR:
            state = f"{THARGOID_STR} {state}"
        styles["state"]["options"]["text"] = f"State: {state}"
        styles["distance"]["options"]["text"] = self.get_distance_text()
        styles["reminder"]["options"]["text"] = self.get_reminder_logo()
        edsm_logo = EDSM_LOGO if self.get_edsm_url() else ""
        styles["edsm_logo"]["options"]["text"] = edsm_logo
        styles["thargoid_logo"]["options"]["text"] = "" if self.get_thargoid_state() == NORMAL_STR else THARGOIDWAR_LOGO
        styles["bottomLine"]["options"]["text"] = self.get_line_text()

        #setup edsm logo event
        if edsm_logo:
            styles["edsm_logo"]["event"] = {"<Button-1>": self.on_edsm_click, "<Enter>": lambda event, cursor="hand2": self.on_logo_enter(event, cursor), "<Leave>": self.on_logo_leave}
        else:
            #clear event
            styles["edsm_logo"]["event"] = {"<Button-1>": "", "<Enter>": "", "<Leave>": ""}

class FancyRow(BaseRow):
    """Row widget for FancyBoard"""
    def setup_style(self):
        self.styles = styles = {}
        colors = self.board.colors
        #text style
        if self.get_distance_text() == CURRENT_STR:
            bullet_bg_color = bullet_fg_color = colors["main"]
        else:
            bullet_bg_color = colors["minor2"]
            bullet_fg_color = colors["minor1"]
        styles["bulletBG"] =     {"type": "text", "x": self.height/2,                       "y": self.height/2,  "options": {"anchor": tk.CENTER, "fill": bullet_bg_color,       "font": (LOGO_FONT,    12), "text":BULLET_BG}}
        styles["bulletFG"] =     {"type": "text", "x": self.height/2,                       "y": self.height/2,  "options": {"anchor": tk.CENTER, "fill": bullet_fg_color,       "font": (LOGO_FONT,    12), "text":BULLET_FG}}
        styles["routeI"] =       {"type": "text", "x": self.height,                         "y": self.height*.3, "options": {"anchor": tk.W,      "fill": colors["textMain"],  "font": ('Helvetica', 12)}}
        #count the route index digit
        index_digit = len(f"{self.index}")
        sys_tex_offset = to_pix(self.canvas, f"{index_digit*6 + 8}p")
        styles["system"] =       {"type": "text", "x": self.height+sys_tex_offset,            "y": self.height*.3, "options": {"anchor": tk.W,      "fill": colors["textMain"],  "font": ('Helvetica', 12)}}
        styles["starType"] =     {"type": "text", "x": self.height,                         "y": self.height*.7, "options": {"anchor": tk.W,      "fill": colors["textMinor"], "font": ('Helvetica', 9)}}
        right_offset = to_pix(self.canvas, "12p")
        styles["distance"] =     {"type": "text", "x": self.width-right_offset,              "y": self.height*.3, "options": {"anchor": tk.E,      "fill": colors["textMinor"], "font": ('Helvetica', 11)}}
        logo_offset = to_pix(self.canvas, "20p")
        styles["reminder"] =     {"type": "text", "x": self.width-right_offset,              "y": self.height*.7, "options": {"anchor": tk.E,      "fill": colors["textMinor"], "font": (LOGO_FONT,    20)}}
        styles["edsm_logo"] =     {"type": "text", "x": self.width-right_offset-logo_offset,   "y": self.height*.7, "options": {"anchor": tk.E,      "fill": colors["textMinor"], "font": (LOGO_FONT,    20)}}
        styles["thargoid_logo"] = {"type": "text", "x": self.width-right_offset-logo_offset*2, "y": self.height*.7, "options": {"anchor": tk.E,      "fill": colors["textMinor"], "font": (LOGO_FONT,    20)}}
        #line style
        line_offset = to_pix(self.canvas, "6p")
        styles["bottomLine"] =   {"type": "line", "x0": line_offset,    "x1": self.width-line_offset, "y0": self.height,   "y1": self.height,   "options": {"fill": colors["minor1"], "width": "0.766p"}}

        styles["routeI"]["options"]["text"] = f"{self.index}. "
        styles["system"]["options"]["text"] = self.get_system_name()
        styles["starType"]["options"]["text"] = self.get_star_type_name()
        styles["distance"]["options"]["text"] = self.get_distance_text()
        reminder_logo = self.get_reminder_logo()
        styles["reminder"]["options"]["text"] = reminder_logo
        edsm_logo = EDSM_LOGO if self.get_edsm_url() else ""
        styles["edsm_logo"]["options"]["text"] = edsm_logo
        thargoid_logo = "" if self.get_thargoid_state() == NORMAL_STR else THARGOIDWAR_LOGO
        styles["thargoid_logo"]["options"]["text"] = thargoid_logo

        #setup reminder logo
        if reminder_logo:
            if reminder_logo == DANGER_LOGO:
                hints_text = DANGER_STR
                styles["reminder"]["options"]["fill"] = DANGER_COLOR
            elif reminder_logo == FUELSTAR_LOGO:
                hints_text = FUELSTAR_STR
            styles["reminder"]["event"] = {"<Enter>": lambda event, text=hints_text: self.on_logo_enter(event, "reminder", text=text), "<Leave>": self.on_logo_leave}
        else:
            #clear event
            styles["reminder"]["event"] = {"<Enter>": "", "<Leave>": ""}

        #setup edsm logo event
        if edsm_logo:
            styles["edsm_logo"]["event"] = {"<Button-1>": self.on_edsm_click, "<Enter>": lambda event: self.on_logo_enter(event, "edsm_logo", "hand2", OPENEDSM_STR), "<Leave>": self.on_logo_leave}
        else:
            #clear event
            styles["edsm_logo"]["event"] = {"<Button-1>": "", "<Enter>": "", "<Leave>": ""}

        #setup thargoid logo
        if thargoid_logo:
            styles["thargoid_logo"]["options"]["fill"] = THARGOID_COLORS[self.get_thargoid_state()]
            styles["thargoid_logo"]["event"] = {"<Enter>": lambda event, text=f"{THARGOID_STR} {self.get_thargoid_state()}": self.on_logo_enter(event, "thargoid_logo", text=text), "<Leave>": self.on_logo_leave}
        else:
            #clear event
            styles["thargoid_logo"]["event"] = {"<Enter>": "", "<Leave>": ""}

    def draw(self):
        super().draw()
        self.resize_canvas_text()

    def update(self, to_top=False):
        if super().update():
            self.resize_canvas_text()

    def on_logo_enter(self, event: tk.Event, objName, cursor="", text=""):
        super().on_logo_enter(event, cursor)
        if objName in self.objs:
            bbox = self.canvas.bbox(self.objs[objName])
            x = (bbox[0]+bbox[2])/2 #(x1-x2)/2
            y = bbox[1] #y1
        else:
            x = self.canvas.canvasx(event.x)
            gap = to_pix(self.canvas, "5p")
            y = self.canvas.canvasy(event.y)-gap
        self.board.show_hints(x, y, text)

    def on_logo_leave(self, event: tk.Event):
        super().on_logo_leave(event)
        self.board.hide_hints()

    def resize_canvas_text(self):
        """Reduce font size to fit the width"""
        objs = self.objs
        #count the route index digit
        index_digit = len(f"{self.index}")
        sys_tex_offset = to_pix(self.canvas, f"{index_digit*6 + 8}p")
        #make text resize dynamically
        resize_canvas_text(self.canvas, objs["system"],   self.width*.56-sys_tex_offset)
        resize_canvas_text(self.canvas, objs["starType"], self.width*.52)
        resize_canvas_text(self.canvas, objs["distance"], self.width*.23)
