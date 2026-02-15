"""Base widget"""
from abc import ABC, abstractmethod
import copy
import webbrowser
from typing import cast

import tkinter as tk

import logging

from theme import theme
from config import appname, config

from nextstop.ui.constant import (SIZE, FUELSTAR_LOGO, DANGER_LOGO,
                                  NORMAL_STR, CURRENT_STR,
                                  BROWN_DWARFS, WOLF_RAYET, WHITE_DWARFS,
                                  SCOOPABLE_STARS, DANGER_STARS)

logger = logging.getLogger(f"{appname}.EDMC-NextStop")

class BaseBoard(ABC):
    """BaseBoard widget"""
    def __init__(self, frame: tk.Frame):
        self.route = []
        self.thargoid_systems= {}
        self.current_index = -1
        self.current_pos = [0.0, 0.0, 0.0]
        self.size = frame.winfo_fpixels(SIZE)
        self.styles = {}
        self.rows: list[BaseRow] = []
        #create canvas
        self.canvas = tk.Canvas(frame, width=self.size, height=0, bd=0, highlightthickness=0)
        self.canvas.grid()
        #make canvas scrollable (1 scroll in Windows equal 120)
        self.canvas.bind('<MouseWheel>', self.on_canvas_scroll)

        #try resize canvas when plugin frame changing size
        frame.bind('<Configure>', self.on_frame_resize)
        #for stopping old event
        self.resize_event_id = ""

        #debug
        self.debug_var = tk.StringVar()
        self.debug_label = tk.Label(frame,
            fg="#00FF00", bg="#000000",
            font=("Consolas", 9, "bold"),
            textvariable=self.debug_var,
            anchor=tk.W, justify=tk.LEFT
        )
        self.update_debug_state()

    def update_debug_state(self):
        """Update the debug mode flag and label"""
        self.debug_mode = debug = config.get_int('nextStop_DebugMode') == 1
        if debug:
            self.debug_label.place(x=0, y=0)
        else:
            self.debug_label.place_forget()

    def update_metrics(self, duration, row_count):
        """Update the metrics text"""
        if not self.debug_mode:
            return
        self.update_debug_state()

        ms = duration*1000
        fps = 1.0/duration if duration > 0 else 0

        text = f"FPS: {fps:.0f}\nROW: {row_count}\n{ms:.1f}ms"
        self.debug_var.set(text)

    def set_route(self, route):
        """Route setter"""
        self.route = copy.deepcopy(route)

    def get_route(self):
        """Route getter"""
        return copy.deepcopy(self.route)

    def set_thargoid_systems(self, thargoid_systems):
        """Thargoid system list setter"""
        self.thargoid_systems = copy.deepcopy(thargoid_systems)

    def get_thargoid_systems(self):
        """Thargoid system list getter"""
        return copy.deepcopy(self.thargoid_systems)

    def set_current_pos(self, current_pos):
        """Current pos setter"""
        self.current_pos = copy.deepcopy(list(current_pos))

    def get_current_pos(self):
        """Current pos getter"""
        return copy.deepcopy(self.current_pos)

    def get_system_pos(self, index):
        """System pos getter"""
        return copy.deepcopy(self.route[index]["pos"])

    def update_current_index(self):
        """Update the current route index by searching the route"""
        #no route
        if len(self.route) <= 0:
            self.current_index = -1
            return

        current_pos = self.get_current_pos()
        current_index = max(self.current_index, 0)
        #set it to 0 or current value
        if self.route[current_index]["pos"] == current_pos:
            self.current_index = current_index
            return

        for i in range(1, 4):
            #look down
            if current_index+i < len(self.route):
                if self.route[current_index+i]["pos"] == current_pos:
                    self.current_index = current_index+i
                    return
            #look up
            if current_index-i >= 0:
                if self.route[current_index-i]["pos"] == current_pos:
                    self.current_index = current_index-i
                    return

        #look in route
        for i, system in enumerate(self.route):
            if system["pos"] == current_pos:
                self.current_index = i
                return

        #not found
        self.current_index = -1

    def on_canvas_scroll(self, event: tk.Event):
        """Canvas scroll event"""
        self.canvas.yview_scroll(int(-1*(event.delta/120)), tk.UNITS)

    def on_frame_resize(self, event: tk.Event):
        """Frame resize event"""
        #return if not parent
        if event.widget != self.canvas.master:
            return
        current_size = self.canvas.winfo_width()
        #return if same size
        if event.width == current_size:
            return
        #cancel resize before starting a new one
        if self.resize_event_id:
            self.canvas.after_cancel(self.resize_event_id)
            #delay longer when user dragging the window size
            delay = 500
        else:
            delay = 100
        min_size = self.to_pix(SIZE)
        self.size = event.width if event.width > min_size else min_size
        self.resize_event_id = self.canvas.after(delay, lambda: self.update_canvas(False))

    def resize_canvas(self, bbox, top_offset=0, move_y=True):
        """Resize and scroll the canvas"""
        self.resize_event_id = ""
        scroll_area = (bbox[0], bbox[1], bbox[2], bbox[3]+top_offset)
        self.canvas.config(scrollregion=scroll_area)
        fixed_size = self.to_pix(SIZE) + top_offset
        new_height = fixed_size if scroll_area[3] >= fixed_size else scroll_area[3]
        #change canvas height
        self.canvas.config(height=new_height)
        #change plugin frame height
        frame = cast(tk.Frame, self.canvas.master)
        frame.config(height=new_height)
        #change canvas widths
        self.canvas.config(width=self.size)
        if not move_y or self.current_index < 0:
            return
        if len(self.route) <= 0:
            self.canvas.yview_moveto(0)
        else:
            fraction = bbox[3]/scroll_area[3] * (self.current_index/len(self.route))
            self.canvas.yview_moveto(fraction)

    @abstractmethod
    def update_canvas(self, move_y=True):
        """Update everything inside the canvas"""

    def update_theme(self):
        """Update the theme"""
        theme.update(self.canvas)

    def destroy(self):
        """Destroy the canvas"""
        self.canvas.destroy()

    def to_pix(self, distance):
        """Convert the distance to pixel"""
        try:
            return self.canvas.winfo_fpixels(distance)
        except Exception as e:
            logger.error("Failed to get number of pixels! %s", e)
            return 0.0

class BaseWidget(ABC):
    """Base widget"""
    def __init__(self, board: BaseBoard, x, y, width, height):
        self.board = board
        self.pos = {"x": x, "y": y}
        self.size = {"width": width, "height": height}
        self.objs = {}
        self.styles = {}
        self.changed = False

    def _setter(self, name, value):
        if getattr(self, name, None) == value:
            return
        setattr(self, name, value)
        self.changed = True

    def _dict_setter(self, dict_name, key, value):
        target = getattr(self, dict_name)
        if target[key] == value:
            return
        target[key] = value
        self.changed = True

    def set_width(self, width):
        """Set widget width"""
        self._dict_setter("size", "width", width)
    def set_height(self, height):
        """Set widget height"""
        self._dict_setter("size", "height", height)
    def set_pos(self, x, y):
        """Set widget position"""
        self._dict_setter("pos", "x", x)
        self._dict_setter("pos", "y", y)

    def get_canvas(self):
        """Get canvas from board"""
        return self.board.canvas

    @abstractmethod
    def setup_style(self):
        """Setup widget style"""

    def draw(self):
        """Draw canvas objects based on widget style"""
        self.setup_style()
        canvas = self.get_canvas()
        x = self.pos["x"]
        y = self.pos["y"]
        if len(self.objs) > 0:
            self.clear()
        for k, v in self.styles.items():
            match v["type"]:
                case "text":
                    obj = canvas.create_text(x+v["x"], y+v["y"], **v["options"])
                case "line":
                    obj = canvas.create_line(x+v["x0"], y+v["y0"],
                                             x+v["x1"], y+v["y1"], **v["options"])
                case "rect":
                    obj = canvas.create_rectangle(x+v["x0"], y+v["y0"],
                                                  x+v["x1"], y+v["y1"], **v["options"])
                case _:
                    logger.error("Unknown object type! %s: %s", k, v)
                    return False
            self.objs[k] = obj
            if "event" in v:
                for name, event in v["event"].items():
                    canvas.tag_bind(obj, name, event)
        return True

    def update(self, to_top=False):
        """Update canvas objects based on widget style"""
        if not self.changed:
            return False

        if len(self.objs) <= 0:
            return self.draw()

        self.setup_style()
        canvas = self.get_canvas()
        x = self.pos["x"]
        y = self.pos["y"]
        for k, v in self.styles.items():
            obj = self.objs[k]
            match v["type"]:
                case "text":
                    canvas.coords(obj, x+v["x"], y+v["y"])
                case "line" | "rect":
                    canvas.coords(obj, x+v["x0"], y+v["y0"], x+v["x1"], y+v["y1"])
            canvas.itemconfig(obj, **v["options"])
            if "event" in v:
                for name, event in v["event"].items():
                    canvas.tag_bind(obj, name, event)
            if to_top:
                canvas.tag_raise(obj)

        self.changed = False
        return True

    def move_to(self, x, y, to_top=False):
        """Move widget"""
        self.set_pos(x, y)
        self.update(to_top)

    def update_obj(self, obj_name, **options):
        """Update a specific canvas object with the object name"""
        if obj_name in self.objs:
            self.get_canvas().itemconfig(obj_name, **options)
        else:
            logger.error("Object (%s) not found!", obj_name)

    def clear(self):
        """Clear all canvas object"""
        for obj_id in self.objs.values():
            self.get_canvas().delete(obj_id)
        self.objs.clear()

class BaseRow(BaseWidget):
    """Base row widget"""
    def __init__(self, board, x, y, width, height, index, system):
        super().__init__(board, x, y, width, height)
        self.index = index
        self.system = copy.deepcopy(system)

    def get_index(self):
        """Get system index"""
        return getattr(self, "index", 0)

    def set_index(self, index):
        """Set system index"""
        self._setter("index", index)

    def set_system(self, system):
        """Set system data"""
        self._setter("system", copy.deepcopy(system))

    def get_system_name(self):
        """Get system name"""
        return self.system["system"]

    def get_edsm_url(self):
        """Get EDSM url"""
        return self.system["edsmUrl"]

    def get_id64(self):
        """Get system id"""
        return self.system["id64"]

    def get_thargoid_state(self):
        """Get thargoid state"""
        if self.get_id64() not in self.board.thargoid_systems:
            return NORMAL_STR

        return self.board.thargoid_systems[self.get_id64()]

    def get_star_type_name(self):
        """Get star type name"""
        name = self.system["starTypeName"]
        if name != "":
            return name
        star_class: str = self.system["starClass"]
        match star_class:
            #* mean uncertain because NavRoute didn't have that info
            #Scoopable
            case "O": name = "O (Blue-White) Star"
            case "B": name = "B (Blue-White*) Star"
            case "A": name = "A (Blue-White*) Star"
            case "F": name = "F (White*) Star"
            case "G": name = "G (White-Yellow*) Star"
            case "K": name = "K (Yellow-Orange*) Star"
            case "M": name = "M (Red*) Star"

            #Brown Dwarfs
            case v if v in BROWN_DWARFS: name = f"{star_class} (Brown dwarf) Star"

            #Proto-stars
            case "TTS":  name = "T Tauri Star"
            case "AeBe": name = "Herbig Ae/Be Star"

            #Wolf-Rayet
            case v if v in WOLF_RAYET:
                text = star_class.replace("W", "Wolf-Rayet ").strip()
                name = f"{text} Star"

            #Rare
            case "MS" | "S": name = f"{star_class}-type Star"

            #White Dwarfs
            case v if v in WHITE_DWARFS:
                name = f"White Dwarf ({star_class}) Star"

            #Others
            case "N": name = "Neutron Star"
            case "H": name = "Black Hole"
            case "SupermassiveBlackHole":
                name = "Supermassive Black Hole"

            #Default
            case _: name = f"{star_class} Star"

        return name

    def get_distance_text(self):
        """Get distance text"""
        #get distance
        distance = self.system["distance"]
        #format the distance "xxx.xx Ly"
        return CURRENT_STR if distance <= 0 else f"{distance:.2f} Ly"

    def get_reminder_logo(self):
        """Get reminder logo"""
        match self.system["starClass"]:
            #if scoopable
            case v if v in SCOOPABLE_STARS:
                return FUELSTAR_LOGO
            #if danger
            case v if v in DANGER_STARS:
                return DANGER_LOGO
            case _:
                return ""

    def show_bottom_line(self, show):
        """Show/hide bottom line"""
        state = tk.NORMAL if show else tk.HIDDEN
        self.get_canvas().itemconfig(self.objs["bottomLine"], state=state)

    def on_edsm_click(self, event):
        """Open the EDSM link"""
        webbrowser.open(self.get_edsm_url())
    def on_logo_enter(self, event, cursor=""):
        """Change the cursor"""
        self.get_canvas().config(cursor=cursor)
    def on_logo_leave(self, event):
        """Change back the cursor to default"""
        self.get_canvas().config(cursor="")
