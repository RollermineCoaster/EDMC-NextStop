"""
NextStop EDMC Plugin
It shows information about every star system in your route.
"""

import logging
import tkinter as tk
from typing import Optional
from threading import Thread
import requests
import copy

from nextstop.util import getDistance
from nextstop.ui import *

import myNotebook as nb  # noqa: N813
from config import appname, config

# This **MUST** match the name of the folder the plugin is in.
PLUGIN_NAME = "EDMC-NextStop"

logger = logging.getLogger(f"{appname}.{PLUGIN_NAME}")

class NextStop:

    def __init__(self) -> None:
        #display mode
        self.MODES = ["Simple", "Fancy"]
        self.SIMPLEMODE = self.MODES[0]
        self.FANCYMODE = self.MODES[1]
        #max size of the canvas
        self.size = 300*config.get_int("ui_scale")/100
        #default simple mode
        if config.get_str('nextStop_Mode') == None:
            config.set('nextStop_Mode', self.MODES[0])
        #config variable
        self.mode = tk.StringVar(value=config.get_str('nextStop_Mode'))
        #init module
        self.ui = None
        self.frame = None
        logger.debug("Config: nextStop_Mode = "+self.mode.get())
        logger.info("NextStop instantiated")

    def getRoute(self):
        if self.ui == None:
            logger.info("Failed to getRoute! UI module is None.")
        else:
            return self.ui.getRoute()

    def setRoute(self, route):
        if self.ui == None:
            logger.info("Failed to setRoute! UI module is None.")
        else:
            self.ui.setRoute(route)

    def getCurrentPos(self):
        if self.ui == None:
            logger.info("Failed to getCurrentPos! UI module is None.")
        else:
            return self.ui.getCurrentPos()

    def setCurrentPos(self, currentPos):
        if self.ui == None:
            logger.info("Failed to setCurrentPos! UI module is None.")
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
        self.on_preferences_closed("", False)  # Save our prefs

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
            logger.info("Removing old board.")
            route = self.getRoute()
            currentPos = self.getCurrentPos()
            self.ui.destroy()
            self.createBoard()
            self.setRoute(route)
            self.setCurrentPos(currentPos)
            self.ui.updateCanvas()
            self.ui.updateTheme()

    def setup_main_ui(self, parent: tk.Frame) -> tk.Frame:
        """
        Create our entry on the main EDMC UI.
        This is called by plugin_app below.
        :param parent: EDMC main window Tk
        :return: Our frame
        """
        logger.info("Setting up UI")
        #plugin frame
        self.frame = tk.Frame(parent)
        #bing a custom event to canvas for updateCanvas
        self.frame.bind_all('<<EDSMUpdate>>', lambda event : self.ui.updateCanvas())
        self.createBoard()
        return self.frame

    def createBoard(self):
        if self.mode.get() == self.SIMPLEMODE:
            logger.info("Display in simple mode")
            self.ui = SimpleBoard(self.frame, self.size)
        elif self.mode.get() == self.FANCYMODE:
            logger.info("Display in fancy mode")
            self.ui = FancyBoard(self.frame, self.size)

    def onEvent(self, cmdr: str, is_beta: bool, system: str, station: str, entry: dict, state: dict) -> Optional[str]:
        if entry["event"] == "StartUp" and state["NavRoute"]["event"] == "NavRoute" or entry["event"] == "NavRoute":
            logger.debug("Plot route.")
            #clear route list
            route = []
            #loop through the route
            for dest in state["NavRoute"]["Route"]:
                temp = {}
                temp["system"] = dest["StarSystem"]
                temp["pos"] = dest["StarPos"]
                #need EDSM to check
                temp["starTypeName"] = ""
                temp["starClass"] = dest["StarClass"]
                route.append(temp)
            logger.debug("Route: "+str(route))
            logger.debug('Starting worker thread...')
            self.setRoute(route)
            self.setCurrentPos(state["StarPos"])
            self.ui.updateCanvas()
            #get info from EDSM using thread
            thread = Thread(target=worker, name='EDSM worker')
            thread.daemon = True
            thread.start()
            logger.debug('Done.')
        elif entry["event"] == "NavRouteClear":
            logger.debug("Route clear.")
            #clear route list
            self.setRoute([])
            self.ui.updateCanvas()
        elif entry["event"] == "FSDJump":
            logger.debug("Jump end.")
            #update current pos
            self.setCurrentPos(entry["StarPos"])
            self.ui.updateCanvas()

def worker() -> None:
    try:
        logger.debug("Worker starting.")
        url = "https://www.edsm.net/api-v1/systems"
        logger.debug("URL: "+url)
        param = {"showPrimaryStar":1, "systemName":[]}
        #if no route
        if len(app.getRoute()) <= 0:
            logger.debug("No route! Worker end!")
            return
        #copy the route list
        route = copy.deepcopy(app.getRoute())
        #list of the route using SystemName as key and index as value
        routeIDs = {}
        for i in range(len(route)):
            systemName = route[i]["system"]
            param["systemName"].append(systemName)
            routeIDs[systemName] = i
        logger.debug("Param: "+str(param))
        #get info using the url above
        req = requests.post(url, json=param)
        if not req.status_code == requests.codes.ok:
            logger.error("Request not ok! Code: "+str(req.status_code))
        data = req.json()
        logger.debug("Data: "+str(data))
        for row in data:
            routeID = routeIDs[row["name"]]
            route[routeID]["starTypeName"] = row["primaryStar"]["type"] if "type" in row["primaryStar"] else ""
        logger.debug("Route after update: "+str(route))
        app.setRoute(route)
        app.frame.event_generate('<<EDSMUpdate>>', when="tail")
    except Exception as e:
        logger.error(type(e).__name__+e.args)

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
