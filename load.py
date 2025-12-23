"""
NextStop EDMC Plugin
It shows information about every star system in your route.
"""

import logging
import tkinter as tk
from typing import Optional
from threading import Thread, RLock, Event
import time
import requests
import copy
import json
from os import path

from nextstop.util import getDistance
from nextstop.ui import *

import myNotebook as nb  # noqa: N813
from config import appname, config

# This **MUST** match the name of the folder the plugin is in.
PLUGIN_NAME = "EDMC-NextStop"

CACHE_LIMIT = 2000

logger = logging.getLogger(f"{appname}.{PLUGIN_NAME}")

class NextStop:

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
        #init module
        self.ui = None
        self.frame = None
        logger.debug("Config: nextStop_Mode = "+self.mode.get())
        #get info from DCoH using thread
        thread = Thread(target=DCoHWorker, name='DCoH worker')
        thread.daemon = True
        thread.start()
        #thread lock for cache
        self.cacheLock = RLock()
        #kill switch for worker
        self.stopWorker = Event()
        #cache
        pluginDir = path.join(config.plugin_dir, PLUGIN_NAME)
        self.cachePath = path.join(pluginDir, "system_cache.json")
        self.systemCache = {}
        self.loadCache()
        logger.info("NextStop instantiated")

    def getFromCache(self, id64):
        with self.cacheLock:
            starType = self.systemCache.get(str(id64), "")
            if starType:
                self.updateCache(id64, starType)
            return starType

    def updateCache(self, id64, starType):
        with self.cacheLock:
            key = str(id64)
            self.systemCache.pop(key, "")
            self.systemCache[key] = starType
            if len(self.systemCache) > 0 and len(self.systemCache) > CACHE_LIMIT:
                firstKey = next(iter(self.systemCache))
                del self.systemCache[firstKey]

    def loadCache(self):
        try:
            if path.exists(self.cachePath):
                with open(self.cachePath, "r") as file:
                    self.systemCache = json.load(file)
        except Exception as e:
            logger.error(f"Failed to load system cache! {e}")

    def saveCache(self):
        try:
            with self.cacheLock:
                with open(self.cachePath, "w") as file:
                    json.dump(self.systemCache, file)
        except Exception as e:
            logger.error(f"Failed to save system cache! {e}")

    def getRoute(self):
        if not self.ui:
            logger.error("Failed to getRoute! UI module is None.")
        else:
            return self.ui.getRoute()

    def setRoute(self, route):
        if not self.ui:
            logger.error("Failed to setRoute! UI module is None.")
        else:
            self.ui.setRoute(route)

    def getThargoidSystems(self):
        if not self.ui:
            logger.error("Failed to getThargoidSystems! UI module is None.")
        else:
            return self.ui.getThargoidSystems()

    def setThargoidSystems(self, thargoidSystems):
        if not self.ui:
            logger.error("Failed to setThargoidSystems! UI module is None.")
        else:
            self.ui.setThargoidSystems(thargoidSystems)

    def getCurrentPos(self):
        if not self.ui:
            logger.error("Failed to getCurrentPos! UI module is None.")
        else:
            return self.ui.getCurrentPos()

    def setCurrentPos(self, currentPos):
        if not self.ui:
            logger.error("Failed to setCurrentPos! UI module is None.")
        else:
            self.ui.setCurrentPos(currentPos)

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
        self.stopWorker.set() #stop all EDSM worker
        self.on_preferences_closed("", False)  # Save our prefs
        self.saveCache()

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
        nb.Label(frame, text='Mode: ').grid(row=current_row)
        nb.OptionMenu(frame, self.mode, self.mode.get(), *self.MODES).grid(row=current_row, column=1)
        current_row += 1  # Always increment our row counter, makes for far easier tkinter design.
        return frame

    def on_preferences_closed(self, cmdr: str, is_beta: bool) -> None:
        """
        on_preferences_closed is called by prefs_changed below.
        It is called when the preferences dialog is dismissed by the user.
        :param cmdr: The current ED Commander
        :param is_beta: Whether or not EDMC is currently marked as in beta mode
        """
        mode = self.mode.get()
        config.set('nextStop_Mode', mode)
        if mode == self.SIMPLEMODE and not isinstance(self.ui, SimpleBoard) or mode == self.FANCYMODE and not isinstance(self.ui, FancyBoard):
            logger.info("Updating board with new settings.")
            #get route, current pos and thargoid systems from old board
            route = self.getRoute()
            currentPos = self.getCurrentPos()
            thargoidSystems = self.getThargoidSystems()
            #destory old board
            self.ui.destroy()
            #make a new board
            self.createBoard()
            self.setRoute(route)
            self.setCurrentPos(currentPos)
            self.setThargoidSystems(thargoidSystems)
            self.ui.updateCanvas()
        self.ui.updateTheme()

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
        #bing a custom event to canvas for updateCanvas
        frame.bind('<<EDSMUpdate>>', lambda event : self.ui.updateCanvas())
        self.createBoard()
        return frame

    def createBoard(self):
        if self.mode.get() == self.SIMPLEMODE:
            logger.info("Display in simple mode.")
            self.ui = SimpleBoard(self.frame)
        elif self.mode.get() == self.FANCYMODE:
            logger.info("Display in fancy mode.")
            self.ui = FancyBoard(self.frame)

    def onEvent(self, cmdr: str, is_beta: bool, system: str, station: str, entry: dict, state: dict) -> Optional[str]:
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
            logger.debug("Route: "+str(route))
            self.setRoute(route)
            self.setCurrentPos(state["StarPos"])
            self.ui.updateCanvas()
            #stop all EDSM worker
            self.stopWorker.set()
            self.stopWorker.clear()
            #get info from EDSM using thread
            logger.info('Starting worker thread.')
            thread = Thread(target=EDSMworker, name='EDSM worker')
            thread.daemon = True
            thread.start()
            logger.debug('NavRoute event handled.')
        elif entry["event"] == "NavRouteClear":
            logger.info("Route clear! Updating UI.")
            if not self.ui.jumping:
                #clear route list
                self.setRoute([])
                self.ui.updateCanvas()
        elif entry["event"] == "StartJump" and entry["JumpType"] == "Hyperspace":
            logger.info("Jumping to another system.")
            self.ui.jumping = True
        elif entry["event"] == "FSDJump":
            logger.info("Arrived at another system. Updating current position.")
            self.ui.jumping = False
            #update current pos
            self.setCurrentPos(entry["StarPos"])
            self.ui.updateCanvas()

def EDSMworker() -> None:
    try:
        logger.debug("Worker starting.")
        url = "https://www.edsm.net/api-v1/systems"
        logger.debug("URL: "+url)
        param = {"showId":1, "showPrimaryStar":1, "systemName":[]}
        appRoute = app.getRoute()
        #if no route
        if len(appRoute) <= 0:
            logger.info("No route! Worker end!")
            return
        #copy the route list
        route = copy.deepcopy(appRoute)
        #list of the route using SystemName as key and index as value
        routeIndexs = {}
        queryCount = 0
        for i in range(len(route)):
            if app.stopWorker.is_set(): return
            id64 = route[i]["id64"]
            starType = app.getFromCache(id64)
            if not starType:
                systemName = route[i]["system"]
                param["systemName"].append(systemName)
                routeIndexs[systemName] = i
                queryCount+=1
            else:
                route[i]["starTypeName"] = starType
                route[i]["edsmUrl"] = f"https://www.edsm.net/en/system?systemID64={id64}"
        logger.debug(f"{len(route)-queryCount} cached, query {queryCount}")
        while queryCount > 0:
            if app.stopWorker.is_set(): return
            logger.debug("Param: "+str(param))
            #get info using the url above
            req = requests.post(url, json=param, timeout=(5, 30))
            limitReset = int(req.headers.get('X-Rate-Limit-Reset', "") or -1)
            match req.status_code:
                case requests.codes.ok:
                    data = req.json()
                    logger.debug("Data: "+str(data))
                    for row in data:
                        if app.stopWorker.is_set(): return
                        systemName = row.get("name", "")
                        routeIndex = routeIndexs.get(systemName, -1)
                        if routeIndex < 0:
                            continue
                        id64 = route[routeIndex]["id64"]
                        if id64 == row.get("id64", 0):
                            starType = row.get("primaryStar", {}).get("type", "")
                            route[routeIndex]["starTypeName"] = starType
                            route[routeIndex]["edsmUrl"] = f"https://www.edsm.net/en/system?systemID64={id64}"
                            app.updateCache(id64, starType)
                    break
                case 429:
                    logger.error(f"Too Many Requests! Try again in {limitReset} sec!")
                    if limitReset > 0:
                        waitSec = limitReset - int(time.time()) if limitReset > 1000000000 else limitReset
                        if app.stopWorker.wait(timeout=waitSec): return
                        continue
                    else:
                        logger.error("Invalid X-Rate-Limit-Reset value!")
            logger.error("Request not ok! Code: "+str(req.status_code))
            return
        logger.debug("Route after update: "+str(route))
        app.setRoute(route)
        app.frame.event_generate('<<EDSMUpdate>>', when="tail")
        app.saveCache()
    except Exception as e:
        logger.error(f"{type(e).__name__}{e}")

def DCoHWorker() -> None:
    try:
        logger.debug("DCoHWorker starting.")
        url = "https://dcoh.watch/api/v1/overwatch/systems"
        logger.debug("URL: "+url)
        #get info using the url above
        req = requests.get(url)
        if not req.status_code == requests.codes.ok:
            logger.error("Request not ok! Code: "+str(req.status_code))
        data = req.json()
        #logger.debug("Data: "+str(data))
        thargoidSystems = {}
        for row in data["systems"]:
            thargoidSystems[row["systemAddress"]] = row["thargoidLevel"]["name"]
        logger.debug("Thargoid systems: "+str(thargoidSystems))
        app.setThargoidSystems(thargoidSystems)
        app.frame.event_generate('<<EDSMUpdate>>', when="tail")
    except Exception as e:
        logger.error(f"{type(e).__name__}{e}")

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
    return app.onEvent(cmdr, is_beta, system, station, entry, state)
