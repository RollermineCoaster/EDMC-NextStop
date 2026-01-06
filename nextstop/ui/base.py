from nextstop.ui.constant import *

import tkinter as tk
from theme import theme

from abc import ABC, abstractmethod
import copy
import webbrowser

from config import appname, config
import logging
logger = logging.getLogger(f"{appname}.EDMC-NextStop")

class BaseBoard(ABC):

    def __init__(self, frame: tk.Frame):
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
        self.canvas.bind('<MouseWheel>', self.onCanvasScroll)

        #try resize canvas when plugin frame changing size
        frame.bind('<Configure>', self.onFrameResize)
        #for stopping old event
        self.resizeEventID = ""

        #debug
        self.debugVar = tk.StringVar()
        self.debugLabel = tk.Label(frame, fg="#00FF00", bg="#000000", font=("Consolas", 9, "bold"), textvariable=self.debugVar, anchor=tk.W, justify=tk.LEFT)
        self.updateDebugObject()

    def updateDebugObject(self):
        self.debugMode = debug = config.get_int('nextStop_DebugMode') == 1
        if debug:
            self.debugLabel.place(x=0, y=0)
        else:
            self.debugLabel.place_forget()

    def updateMetrics(self, duration, rowCount):
        if not self.debugMode: return
        self.updateDebugObject()
        
        ms = duration*1000
        fps = 1.0/duration if duration > 0 else 0

        text = f"FPS: {fps:.0f}\nROW: {rowCount}\n{ms:.1f}ms"
        self.debugVar.set(text)

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

    def onCanvasScroll(self, event: tk.Event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), tk.UNITS)

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

    def resizeCanvas(self, bbox, topOffset=0, moveY=True):
        self.resizeEventID = ""
        scrollArea = (bbox[0], bbox[1], bbox[2], bbox[3]+topOffset)
        self.canvas.config(scrollregion=scrollArea)
        fixedSize = self.toPix(SIZE) + topOffset
        newHeight = fixedSize if scrollArea[3] >= fixedSize else scrollArea[3]
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
            fraction = bbox[3]/scrollArea[3] * (self.currentIndex/len(self.route))
            self.canvas.yview_moveto(fraction)

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

class BaseWidget(ABC):

    def __init__(self, board: BaseBoard, canvas: tk.Canvas, x, y, width, height):
        self.board = board
        self.canvas = canvas
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.objs = {}
        self.styles = {}

    def setWidth(self, width): self.width = width
    def setHeight(self, height): self.height = height

    @abstractmethod
    def setupStyle(self): pass

    def draw(self):
        self.setupStyle()
        canvas = self.canvas
        if len(self.objs) > 0: self.clear()
        for k, v in self.styles.items():
            match v["type"]:
                case "text":
                    obj = canvas.create_text(self.x+v["x"], self.y+v["y"], **v["options"])
                case "line":
                    obj = canvas.create_line(self.x+v["x0"], self.y+v["y0"], self.x+v["x1"], self.y+v["y1"], **v["options"])
                case "rect":
                    obj = canvas.create_rectangle(self.x+v["x0"], self.y+v["y0"], self.x+v["x1"], self.y+v["y1"], **v["options"])
                case _:
                    logger.error(f"Unknown object type! {k}: {v}")
                    return
            self.objs[k] = obj
            if "event" in v:
                for name, event in v["event"].items():
                    canvas.tag_bind(obj, name, event)

    def update(self, toTop=False):
        if len(self.objs) <= 0: return self.draw()
        self.setupStyle()
        canvas = self.canvas
        for k, v in self.styles.items():
            obj = self.objs[k]
            match v["type"]:
                case "text":
                    canvas.coords(obj, self.x+v["x"], self.y+v["y"])
                case "line" | "rect":
                    canvas.coords(obj, self.x+v["x0"], self.y+v["y0"], self.x+v["x1"], self.y+v["y1"])
            canvas.itemconfig(obj, **v["options"])
            if "event" in v:
                for name, event in v["event"].items():
                    canvas.tag_bind(obj, name, event)
            if toTop:
                canvas.tag_raise(obj)

    def moveTo(self, x, y):
        self.x = x
        self.y = y
        self.update()

    def updateObj(self, objName, **options):
        if objName in self.objs:
            self.canvas.itemconfig(objName, **options)
        else:
            logger.error(f"Object ({objName}) not found!")

    def clear(self):
        for id in self.objs.values():
            self.canvas.delete(id)
        self.objs.clear()

class BaseRow(BaseWidget):

    def __init__(self, board, canvas, x, y, width, height, index, system):
        super().__init__(board, canvas, x, y, width, height)
        self.setIndex(index)
        self.setSystem(system)

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

    def showBottomLine(self, show):
        state = tk.NORMAL if show else tk.HIDDEN
        self.canvas.itemconfig(self.objs["bottomLine"], state=state)

    def onEDSMClick(self, event): webbrowser.open(self.getEDSMUrl())
    def onLogoEnter(self, event, cursor=""): self.canvas.config(cursor=cursor)
    def onLogoLeave(self, event): self.canvas.config(cursor="")