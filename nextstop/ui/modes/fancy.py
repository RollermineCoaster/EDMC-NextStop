"""Fancy style widget"""
import tkinter as tk
import time

from nextstop.ui.base import BaseWidget, BaseBoard, BaseRow
from nextstop.ui.constant import (THEME_1933, DANGER_COLOR, THARGOID_COLORS, SIZE, MAX_ROWS,
                                  NOROUTEFULL_STR, CURRENT_STR, NORMAL_STR, DANGER_STR, FUELSTAR_STR, OPENEDSM_STR,
                                  THARGOID_STR, NEXTSTOP_STR, DASH6_STR, REMAINING_STR,
                                  JUMP_STR, JUMPS_STR, MIN_STR, MINS_STR, HOUR_STR, HOURS_STR,
                                  LOGO_FONT, BULLET_BG, BULLET_FG, THARGOIDWAR_LOGO, EDSM_LOGO, DANGER_LOGO, FUELSTAR_LOGO)
from nextstop.util import to_pix, get_distance, resize_canvas_text, format_text, get_time

class FancyBoard(BaseBoard):
    """Fancy style board"""
    def __init__(self, frame: tk.Frame):
        super().__init__(frame)
        self.colors = THEME_1933
        self.row_height = to_pix(self.canvas, SIZE)/MAX_ROWS
        self.bar_height = self.row_height*1.5
        #hints
        self.hints_var = tk.StringVar()
        self.hints_label = tk.Label(self.canvas, fg=self.colors["textMinor"], bg=self.colors["bg"], relief=tk.RAISED, bd=1, font=('Helvetica', 9), textvariable=self.hints_var)
        #hints and bulletLine canvas object id
        self.hints_obj = self.canvas.create_window(0, 0, tags="hints", window=self.hints_label, state=tk.HIDDEN, anchor=tk.S)
        self.bullet_line_obj = ""
        self.no_route_obj = ""
        self.info_bar = FancyBar(self, 0, 0, self.size, self.row_height*1.5)
        self.info_bar.draw()
        self.canvas.config(bg=self.colors["bg"])

    def update_canvas(self, move_y=True):
        if self.debug_mode:
            start_time = time.perf_counter()

        super().update_canvas()
        canvas = self.canvas
        info_bar = self.info_bar
        route_size = len(self.route)

        #remove extra row object
        while len(self.rows) > route_size:
            row = self.rows.pop()
            row.clear()
        self.update_current_index()

        total_row = max(route_size, 1)
        self.resize_canvas((0,0 ,self.size, self.row_height*total_row), int(self.bar_height), move_y=move_y)
        if move_y:
            self.update_info_bar_position()

        #if no route
        if route_size <= 0:
            self.hide_hints()
            if self.bullet_line_obj:
                canvas.itemconfig(self.bullet_line_obj, state=tk.HIDDEN)
            if not self.no_route_obj:
                self.no_route_obj = canvas.create_text(self.size/2, self.row_height/2+self.bar_height, text=NOROUTEFULL_STR, anchor=tk.CENTER, fill=self.colors["textMain"], font=('Helvetica', 12), justify=tk.CENTER)
            else:
                canvas.itemconfig(self.no_route_obj, state=tk.NORMAL)
                canvas.coords(self.no_route_obj, self.size/2, self.row_height/2+self.bar_height)
        else:
            if self.no_route_obj:
                canvas.itemconfig(self.no_route_obj, state=tk.HIDDEN)
            line_length = self.row_height/2 + self.row_height*(route_size-1) + self.bar_height
            if not self.bullet_line_obj:
                self.bullet_line_obj = canvas.create_line(self.row_height/2, self.row_height/2+self.bar_height, self.row_height/2, line_length, fill=self.colors["main"], width="1.5p")
            else:
                #show bulletLine
                canvas.itemconfig(self.bullet_line_obj, state=tk.NORMAL)
                #resize bulletLine
                canvas.coords(self.bullet_line_obj, self.row_height/2, self.row_height/2+self.bar_height, self.row_height/2, line_length)
            self.update_rows()
        info_bar.set_width(self.size)
        if self.current_index < 0 or self.current_index >= route_size-1:
            info_bar.update_text()
        else:
            next_stop_index = self.current_index+1
            info_bar.update_text(f"{next_stop_index+1}. {self.route[next_stop_index]["system"]}", route_size-next_stop_index)

        if self.debug_mode:
            end_time = time.perf_counter()
            self.update_metrics(end_time - start_time, len(self.rows))

    def update_rows(self):
        """Update row objects"""
        if self.debug_mode:
            start_time = time.perf_counter()
        canvas = self.canvas
        route_size = len(self.route)

        #size of the row pool
        pool_size = min(route_size, MAX_ROWS+1)
        #current top Y after scrolling
        top = canvas.canvasy(0)
        #calculate how many row is scrolled
        route_offset = int(top//self.row_height)
        #limit the offset to prevent list index out of bound
        route_offset = min(route_offset, route_size-pool_size)

        #rearrange row objects to reduce the update call
        if len(self.rows) > 0:
            #how many row should rearrange
            delta = self.rows[0].get_index() - (route_offset+1)
            if delta != 0 and abs(delta) < len(self.rows):
                for _ in range(abs(delta)):
                    #pop the first if scroll down else last
                    pop_index = 0 if delta < 0 else -1
                    temp = self.rows.pop(pop_index)
                    if delta < 0:
                        self.rows.append(temp) #first to last
                    else: self.rows.insert(0, temp) #last ot first

        #loop through route list
        for row_index in range(pool_size):
            route_index = row_index + route_offset
            row_pos_offset = self.row_height*(route_index) + self.bar_height
            system = self.route[route_index]
            system["distance"] = get_distance(self.current_pos, system["pos"])

            if row_index >= len(self.rows):
                row = FancyRow(self, 0, row_pos_offset, self.size, self.row_height, route_index+1, system)
                row.draw()
                self.rows.append(row)
            else:
                row = self.rows[row_index]
                row.set_width(self.size)
                row.set_pos(0, row_pos_offset)
                row.set_index(route_index+1)
                row.set_system(system)
                row.update()
            #if not bottom
            not_bottom = route_index+1 < route_size
            row.show_bottom_line(not_bottom)

        if self.debug_mode:
            end_time = time.perf_counter()
            self.update_metrics(end_time - start_time, len(self.rows))

    #def update_theme(self):
        #super().update_theme()

    def update_info_bar_position(self):
        """Stick the info bar to the canvas top after scrolling"""
        x = self.canvas.canvasx(0)
        y = self.canvas.canvasy(0)
        self.info_bar.move_to(x, y, True)

    def on_canvas_scroll(self, event: tk.Event):
        super().on_canvas_scroll(event)
        if len(self.rows) > MAX_ROWS:
            self.update_info_bar_position()
            self.update_rows()

    def show_hints(self, x: float, y: float, text: str):
        """Show hints(tooltips)"""
        canvas = self.canvas
        self.hints_var.set(text)
        # Reset the anchor before measuring
        canvas.itemconfig("hints", state=tk.NORMAL, anchor=tk.S)

        canvas.coords("hints", x, y)

        #force bbox to update
        canvas.update_idletasks()

        bbox = canvas.bbox("hints") # (x1, y1, x2, y2)
        x_offset = 0
        #check if y1 off-screen
        if bbox[1] < 0:
            #flip the anchor
            canvas.itemconfig("hints", anchor=tk.N)
            #move it below logo
            canvas.coords("hints", x, y+self.to_pix("20p"))
            #force bbox to update
            canvas.update_idletasks()
            bbox = canvas.bbox("hints") # (x1, y1, x2, y2)

        #check if x1 and x2 off-screen
        if bbox[0] < 0: # Left edge
            x_offset = -bbox[0]
        elif bbox[2] > self.size: # Right edge
            x_offset = self.size - bbox[2]

        canvas.move("hints", x_offset, 0)

    def hide_hints(self):
        """Hide hint(tooltips)"""
        self.hints_var.set("")
        self.canvas.itemconfig("hints", state=tk.HIDDEN)

class FancyRow(BaseRow):
    """Row widget for FancyBoard"""

    def __init__(self, board, x, y, width, height, index, system):
        self.board: FancyBoard
        super().__init__(board, x, y, width, height, index, system)

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
            hints_text = ""
            if reminder_logo == DANGER_LOGO:
                hints_text = DANGER_STR
                styles["reminder"]["options"]["fill"] = DANGER_COLOR
            elif reminder_logo == FUELSTAR_LOGO:
                hints_text = FUELSTAR_STR
            styles["reminder"]["event"] = {"<Enter>": lambda event, text=hints_text: self.on_logo_enter(event, "", "reminder", text), "<Leave>": self.on_logo_leave}
        else:
            #clear event
            styles["reminder"]["event"] = {"<Enter>": "", "<Leave>": ""}

        #setup edsm logo event
        if edsm_logo:
            styles["edsm_logo"]["event"] = {"<Button-1>": self.on_edsm_click, "<Enter>": lambda event: self.on_logo_enter(event, "hand2", "edsm_logo", OPENEDSM_STR), "<Leave>": self.on_logo_leave}
        else:
            #clear event
            styles["edsm_logo"]["event"] = {"<Button-1>": "", "<Enter>": "", "<Leave>": ""}

        #setup thargoid logo
        if thargoid_logo:
            styles["thargoid_logo"]["options"]["fill"] = THARGOID_COLORS[self.get_thargoid_state()]
            styles["thargoid_logo"]["event"] = {"<Enter>": lambda event, text=f"{THARGOID_STR} {self.get_thargoid_state()}": self.on_logo_enter(event, "", "thargoid_logo", text), "<Leave>": self.on_logo_leave}
        else:
            #clear event
            styles["thargoid_logo"]["event"] = {"<Enter>": "", "<Leave>": ""}

    def draw(self):
        super().draw()
        self.resize_canvas_text()

    def update(self, to_top=False):
        if super().update():
            self.resize_canvas_text()

    def on_logo_enter(self, event: tk.Event, cursor="", obj_name="", text=""):
        """Change the cursor and show hints(tooltips)"""
        super().on_logo_enter(event, cursor)
        if obj_name in self.objs:
            bbox = self.canvas.bbox(self.objs[obj_name])
            x = (bbox[0]+bbox[2])/2 #(x1-x2)/2
            y = bbox[1] #y1
        else:
            x = self.canvas.canvasx(event.x)
            gap = to_pix(self.canvas, "5p")
            y = self.canvas.canvasy(event.y)-gap
        self.board.show_hints(x, y, text)

    def on_logo_leave(self, event: tk.Event):
        """Change back the cursor to default and hide hints(tooltips)"""
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

class FancyBar(BaseWidget):
    """FancyBar widget"""
    def __init__(self, board, x, y, width, height):
        self.board: FancyBoard
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
