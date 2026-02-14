"""Simple style widget"""
import tkinter as tk
import time

from theme import theme

from nextstop.ui.base import BaseBoard, BaseRow
from nextstop.ui.constant import (NOROUTEFULL_STR, DASH6_STR,
                                  NORMAL_STR, THARGOID_STR,
                                  LOGO_FONT, EDSM_LOGO, THARGOIDWAR_LOGO)
from nextstop.util import get_distance, to_pix

class SimpleBoard(BaseBoard):
    """Simple style board"""
    def update_canvas(self, move_y=True):
        if self.debug_mode: 
            start_time = time.perf_counter()

        super().update_canvas()
        canvas = self.canvas
        #remove extra row object
        while len(self.rows) > len(self.route):
            row = self.rows.pop()
            row.clear()
        #if no route
        if len(self.route) <= 0:
            self.current_index = 0
            canvas.delete("all")
            canvas.create_text(0,         0, text=NOROUTEFULL_STR, anchor=tk.NW, justify=tk.LEFT,  tags="noRoute")
            canvas.create_text(self.size, 0, text=DASH6_STR,       anchor=tk.NE, justify=tk.RIGHT, tags="noRoute")
        else:
            canvas.delete("noRoute")
            #loop through route list
            row_height = self.to_pix("40p")
            for index in range(len(self.route)):
                system = self.route[index]
                system["distance"] = distance = get_distance(self.current_pos, system["pos"])
                if distance <= 0: self.current_index = index
                if index >= len(self.rows):
                    row = SimpleRow(self, 0, row_height*index, self.size, row_height, index+1, system)
                    row.draw()
                    self.rows.append(row)
                else:
                    row = self.rows[index]
                    row.set_width(self.size)
                    row.set_system(system)
                    row.update()
                #if not bottom
                not_bottom = index+1 < len(self.route)
                row.show_bottom_line(not_bottom)
        self.resize_canvas(canvas.bbox("all"), move_y=move_y)
        canvas.after(10, lambda: self.update_theme())

        if self.debug_mode:
            end_time = time.perf_counter()
            self.update_metrics(end_time - start_time, len(self.rows))

    def update_theme(self):
        super().update_theme()
        self.canvas.itemconfig("all", fill=theme.current["foreground"], font=theme.current["font"])
        self.canvas.itemconfig("logo", font=(LOGO_FONT, 20))

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
