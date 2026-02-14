"""
NextStop EDMC Plugin
It shows information about every star system in your route.
"""

import logging
import tkinter as tk
from typing import Optional
from threading import Thread, RLock, Event
import time
import copy
import json
from os import path

import ctypes
from ctypes.wintypes import DWORD, LPCVOID, LPCWSTR
AddFontResourceEx = ctypes.windll.gdi32.AddFontResourceExW
AddFontResourceEx.restypes = [LPCWSTR, DWORD, LPCVOID]  # type: ignore
FR_PRIVATE = 0x10
AddFontResourceEx(path.join(path.dirname(__file__), 'nextstop/assets/nextstop-logo.ttf'), FR_PRIVATE, 0)

import requests

import myNotebook as nb
from config import appname, config

from nextstop.ui.modes import SimpleBoard, FancyBoard

# This **MUST** match the name of the folder the plugin is in.
PLUGIN_NAME = "EDMC-NextStop"

CACHE_LIMIT = 2000

logger = logging.getLogger(f"{appname}.{PLUGIN_NAME}")

class NextStop:
    """NextStop plugin class"""
    def __init__(self) -> None:
        #display mode
        self.MODES = ["Simple", "Fancy"]
        self.SIMPLEMODE = self.MODES[0]
        self.FANCYMODE = self.MODES[1]
        #default simple mode
        if not config.get_str('nextStop_Mode'):
            config.set('nextStop_Mode', self.MODES[0])
        #config variable
        self.mode = tk.StringVar(value=config.get_str('nextStop_Mode'))
        self.debug_mode = tk.IntVar(value=config.get_int('nextStop_DebugMode'))
        #init module
        self.ui: SimpleBoard | FancyBoard
        self.frame: tk.Frame
        logger.debug("Config: nextStop_Mode = %s, nextStop_DebugMode = %s", self.mode.get(), self.debug_mode.get())
        #get info from DCoH using thread
        thread = Thread(target=dcoh_worker, name='DCoH worker')
        thread.daemon = True
        thread.start()
        #thread lock for cache
        self.cache_lock = RLock()
        #kill switch for worker
        self.stop_worker = Event()
        #cache
        plugin_dir = path.join(config.plugin_dir, PLUGIN_NAME)
        self.cache_path = path.join(plugin_dir, "system_cache.json")
        self.system_cache = {}
        self.load_cache()
        logger.info("NextStop instantiated")

    def get_from_cache(self, id64):
        """Get system data from cache using id64"""
        with self.cache_lock:
            star_type = self.system_cache.get(str(id64), "")
            if star_type:
                self.update_cache(id64, star_type)
            return star_type

    def update_cache(self, id64, star_type):
        """Update system data in cache using id64"""
        with self.cache_lock:
            key = str(id64)
            self.system_cache.pop(key, "")
            self.system_cache[key] = star_type
            if len(self.system_cache) > 0 and len(self.system_cache) > CACHE_LIMIT:
                first_key = next(iter(self.system_cache))
                del self.system_cache[first_key]

    def load_cache(self):
        """Load system cache from disk"""
        try:
            if path.exists(self.cache_path):
                with open(self.cache_path, "r", encoding="utf-8") as file:
                    self.system_cache = json.load(file)
        except Exception as e:
            logger.error("Failed to load system cache! %s", e)

    def save_cache(self):
        """Save system cache to disk"""
        try:
            with self.cache_lock:
                with open(self.cache_path, "w", encoding="utf-8") as file:
                    json.dump(self.system_cache, file)
        except Exception as e:
            logger.error("Failed to save system cache! %s", e)

    def get_route(self):
        """Get current route from board class"""
        if not self.ui:
            logger.error("Failed to get_route! UI module is None.")
            return []
        else:
            return self.ui.get_route()

    def set_route(self, route):
        """Set route"""
        if not self.ui:
            logger.error("Failed to set_route! UI module is None.")
        else:
            self.ui.set_route(route)

    def get_thargoid_systems(self):
        """Get current thargoid system list"""
        if not self.ui:
            logger.error("Failed to get_thargoid_systems! UI module is None.")
        else:
            return self.ui.get_thargoid_systems()

    def set_thargoid_systems(self, thargoid_systems):
        """Set thargoid system list"""
        if not self.ui:
            logger.error("Failed to set_thargoid_systems! UI module is None.")
        else:
            self.ui.set_thargoid_systems(thargoid_systems)

    def get_current_pos(self):
        """Get current position from board class"""
        if not self.ui:
            logger.error("Failed to get_current_pos! UI module is None.")
        else:
            return self.ui.get_current_pos()

    def set_current_pos(self, current_pos):
        """Set current position"""
        if not self.ui:
            logger.error("Failed to set_current_pos! UI module is None.")
        else:
            self.ui.set_current_pos(current_pos)

    def on_load(self) -> str:
        """
        on_load is called by plugin_start3 below.
        It is the first point EDMC interacts with our code after loading our module.
        :return: The name of the plugin, which will be used by EDMC for logging and for the settings window
        """
        return PLUGIN_NAME

    def on_unload(self) -> None:
        """
        on_unload is called by plugin_stop below.
        It is the last thing called before EDMC shuts down. Note that blocking code here will hold the shutdown process.
        """
        self.stop_worker.set() #stop all EDSM worker
        self.on_preferences_closed("", False)  # Save our prefs
        self.save_cache()

    def setup_preferences(self, parent: nb.Notebook, cmdr: str, is_beta: bool) -> Optional[tk.Frame]:
        """
        setup_preferences is called by plugin_prefs below.
        It is where we can setup our own settings page in EDMC's settings window. Our tab is defined for us.
        :param parent: the tkinter parent that our returned Frame will want to inherit from
        :param cmdr: The current ED Commander
        :param is_beta: Whether or not EDMC is currently marked as in beta mode
        :return: The frame to add to the settings window
        """
        current_row = 0
        frame = nb.Frame(parent)

        # setup our config
        # mode
        nb.Label(frame, text='Mode: ').grid(row=current_row, column=0, sticky=tk.W)
        nb.OptionMenu(frame, self.mode, self.mode.get(), *self.MODES).grid(row=current_row, column=1, sticky=tk.W)
        current_row += 1  # Always increment our row counter, makes for far easier tkinter design.
        nb.Label(frame, text='Debug: ').grid(row=current_row, column=0, sticky=tk.W)
        nb.Checkbutton(frame, text='Show Performance Metrics', variable=self.debug_mode).grid(row=current_row, column=1, sticky=tk.W)
        return frame

    def on_preferences_closed(self, cmdr: str, is_beta: bool) -> None:
        """
        on_preferences_closed is called by prefs_changed below.
        It is called when the preferences dialog is dismissed by the user.
        :param cmdr: The current ED Commander
        :param is_beta: Whether or not EDMC is currently marked as in beta mode
        """
        config.set('nextStop_DebugMode', self.debug_mode.get())
        self.ui.update_debug_state()
        mode = self.mode.get()
        config.set('nextStop_Mode', mode)
        if mode == self.SIMPLEMODE and not isinstance(self.ui, SimpleBoard) or mode == self.FANCYMODE and not isinstance(self.ui, FancyBoard):
            logger.info("Updating board with new settings.")
            #get route, current pos and thargoid systems from old board
            route = self.get_route()
            current_pos = self.get_current_pos()
            thargoid_systems = self.get_thargoid_systems()
            #destory old board
            self.ui.destroy()
            #make a new board
            self.create_board()
            self.set_route(route)
            self.set_current_pos(current_pos)
            self.set_thargoid_systems(thargoid_systems)
            self.ui.update_canvas()
        self.ui.update_theme()

    def setup_main_ui(self, parent: tk.Frame) -> tk.Frame:
        """
        Create our entry on the main EDMC UI.
        This is called by plugin_app below.
        :param parent: EDMC main window Tk
        :return: Our frame
        """
        logger.info("Setting up UI.")
        #plugin frame
        self.frame = frame = tk.Frame(parent)
        frame.grid_propagate(False)
        #bing a custom event to canvas for update_canvas
        frame.bind('<<EDSMUpdate>>', lambda event : self.ui.update_canvas())
        self.create_board()
        self.ui.update_canvas()
        return frame

    def create_board(self):
        """Create the board class based on the current mode settings"""
        if self.mode.get() == self.SIMPLEMODE:
            logger.info("Display in simple mode.")
            self.ui = SimpleBoard(self.frame)
        elif self.mode.get() == self.FANCYMODE:
            logger.info("Display in fancy mode.")
            self.ui = FancyBoard(self.frame)

    def on_event(self, cmdr: str, is_beta: bool, system: str, station: str, entry: dict, state: dict) -> Optional[str]:
        """Update the board when journal update"""
        if entry["event"] == "StartUp" and state["NavRoute"]["event"] == "NavRoute" or entry["event"] == "NavRoute":
            logger.info("Route detected! Updating UI.")
            #clear route list
            route = []
            #loop through the route
            for dest in state["NavRoute"]["Route"]:
                temp = {}
                temp["system"] = dest["StarSystem"]
                temp["id64"] = dest["SystemAddress"]
                temp["pos"] = dest["StarPos"]
                #need EDSM to check
                temp["starTypeName"] = ""
                temp["edsmUrl"] = ""
                temp["starClass"] = dest["StarClass"]
                route.append(temp)
            logger.debug("Route: %s", str(route))
            self.set_route(route)
            self.set_current_pos(state["StarPos"])
            self.ui.current_index = 0
            self.ui.update_canvas()
            #stop all EDSM worker
            self.stop_worker.set()
            self.stop_worker.clear()
            #get info from EDSM using thread
            logger.info('Starting worker thread.')
            thread = Thread(target=edsm_worker, name='EDSM worker')
            thread.daemon = True
            thread.start()
            logger.debug('NavRoute event handled.')
        elif entry["event"] == "NavRouteClear":
            logger.info("Route clear! Updating UI.")
            if not self.ui.jumping:
                #clear route list
                self.set_route([])
                self.ui.update_canvas()
        elif entry["event"] == "StartJump" and entry["JumpType"] == "Hyperspace":
            logger.info("Jumping to another system.")
            self.ui.jumping = True
        elif entry["event"] == "FSDJump":
            logger.info("Arrived at another system. Updating current position.")
            self.ui.jumping = False
            #update current pos
            self.set_current_pos(entry["StarPos"])
            self.ui.update_canvas()

def edsm_worker() -> None:
    """Get system data from EDSM"""
    try:
        logger.debug("Worker starting.")
        url = "https://www.edsm.net/api-v1/systems"
        logger.debug("URL: %s", url)
        param = {"showId":1, "showPrimaryStar":1, "systemName":[]}
        app_route = app.get_route()
        #if no route
        if len(app_route) <= 0:
            logger.info("No route! Worker end!")
            return
        #copy the route list
        route = copy.deepcopy(app_route)
        #list of the route using SystemName as key and index as value
        route_indexs = {}
        query_count = 0
        for i in range(len(route)):
            if app.stop_worker.is_set(): return
            id64 = route[i]["id64"]
            star_type = app.get_from_cache(id64)
            if not star_type:
                system_name = route[i]["system"]
                param["systemName"].append(system_name)
                route_indexs[system_name] = i
                query_count+=1
            else:
                route[i]["starTypeName"] = star_type
                route[i]["edsmUrl"] = f"https://www.edsm.net/en/system?systemID64={id64}"
        logger.debug("%s cached, query %s", len(route)-query_count, query_count)
        while query_count > 0:
            if app.stop_worker.is_set():
                return
            logger.debug("Param: %s", param)
            #get info using the url above
            req = requests.post(url, json=param, timeout=(5, 30))
            limit_reset = int(req.headers.get('X-Rate-Limit-Reset', "") or -1)
            match req.status_code:
                case requests.codes.ok:
                    data = req.json()
                    logger.debug("Data: %s", data)
                    for row in data:
                        if app.stop_worker.is_set():
                            return
                        system_name = row.get("name", "")
                        route_index = route_indexs.get(system_name, -1)
                        if route_index < 0:
                            continue
                        id64 = route[route_index]["id64"]
                        if id64 == row.get("id64", 0):
                            star_type = row.get("primaryStar", {}).get("type", "")
                            route[route_index]["starTypeName"] = star_type
                            route[route_index]["edsmUrl"] = f"https://www.edsm.net/en/system?systemID64={id64}"
                            app.update_cache(id64, star_type)
                    break
                case 429:
                    logger.error("Too Many Requests! Try again in %s sec!", limit_reset)
                    if limit_reset > 0:
                        wait_sec = limit_reset - int(time.time()) if limit_reset > 1000000000 else limit_reset
                        if app.stop_worker.wait(timeout=wait_sec):
                            return
                        continue
                    else:
                        logger.error("Invalid X-Rate-Limit-Reset value!")
            logger.error("Request not ok! Code: %s", req.status_code)
            return
        logger.debug("Route after update: %s", route)
        app.set_route(route)
        app.frame.event_generate('<<EDSMUpdate>>', when="tail")
        app.save_cache()
    except Exception as e:
        logger.error("%s: %s", type(e).__name__, e)

def dcoh_worker() -> None:
    """Get thargoid systems list from DCoH"""
    try:
        logger.debug("dcoh_worker starting.")
        url = "https://dcoh.watch/api/v1/overwatch/systems"
        logger.debug("URL: %s", url)
        #get info using the url above
        req = requests.get(url)
        if not req.status_code == requests.codes.ok:
            logger.error("Request not ok! Code: %s", req.status_code)
        data = req.json()
        #logger.debug("Data: "+str(data))
        thargoid_systems = {}
        for row in data["maelstroms"]:
            thargoid_systems[row["systemAddress"]] = "Titan"
        for row in data["systems"]:
            thargoid_systems[row["systemAddress"]] = row["thargoidLevel"]["name"]
        logger.debug("Thargoid systems: %s", thargoid_systems)
        app.set_thargoid_systems(thargoid_systems)
        app.frame.event_generate('<<EDSMUpdate>>', when="tail")
    except Exception as e:
        logger.error("%s: %s", type(e).__name__, e)

app = NextStop()

# Note that all of these could be simply replaced with something like:
# plugin_start3 = cc.on_load
def plugin_start3(plugin_dir: str) -> str:
    """
    Handle start up of the plugin.
    See PLUGINS.md#startup
    """
    return app.on_load()


def plugin_stop() -> None:
    """
    Handle shutdown of the plugin.
    See PLUGINS.md#shutdown
    """
    return app.on_unload()


def plugin_prefs(parent: nb.Notebook, cmdr: str, is_beta: bool) -> Optional[tk.Frame]:
    """
    Handle preferences tab for the plugin.
    See PLUGINS.md#configuration
    """
    return app.setup_preferences(parent, cmdr, is_beta)


def prefs_changed(cmdr: str, is_beta: bool) -> None:
    """
    Handle any changed preferences for the plugin.
    See PLUGINS.md#configuration
    """
    return app.on_preferences_closed(cmdr, is_beta)


def plugin_app(parent: tk.Frame) -> Optional[tk.Frame]:
    """
    Set up the UI of the plugin.
    See PLUGINS.md#display
    """
    return app.setup_main_ui(parent)

def journal_entry(cmdr: str, is_beta: bool, system: str, station: str, entry: dict, state: dict) -> Optional[str]:
    """Trigger update for every journal update"""
    return app.on_event(cmdr, is_beta, system, station, entry, state)
