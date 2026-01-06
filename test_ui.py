import sys
import tkinter as tk
from unittest.mock import MagicMock

# 1. Mock the EDMC 'config' module
mock_config = MagicMock()
# Define default return values for methods your code calls
mock_config.config.get_int.return_value = 1
mock_config.config.get_str.return_value = "Simple"
sys.modules["config"] = mock_config

# 2. Mock the 'theme' module (if you haven't already)
mock_theme = MagicMock()
sys.modules["theme"] = mock_theme

sys.modules["requests"] = MagicMock()

# Mock 'nb' if your config UI uses it
mock_nb = MagicMock()
mock_nb.Frame = tk.Frame
mock_nb.Label = tk.Label
mock_nb.OptionMenu = tk.OptionMenu
mock_nb.Checkbutton = tk.Checkbutton
sys.modules["myNotebook"] = mock_nb

from os import path
import ctypes
from ctypes.wintypes import DWORD, LPCVOID, LPCWSTR
AddFontResourceEx = ctypes.windll.gdi32.AddFontResourceExW
AddFontResourceEx.restypes = [LPCWSTR, DWORD, LPCVOID]  # type: ignore
FR_PRIVATE = 0x10
AddFontResourceEx(path.join(path.dirname(__file__), 'nextstop/assets/nextstop-logo.ttf'), FR_PRIVATE, 0)

# NOW you can import your UI classes
from nextstop.ui.boards import FancyBoard

# 1. Setup Mock Data
MOCK_ROUTE_5 = [
    {"system": "Sol", "starClass": "G", "starTypeName": "Yellow Dwarf", "pos": [0,0,0], "edsmUrl": "https://www.edsm.net/en/system/id/27/name/Sol", "id64": 1},
    {"system": "Alpha Centauri", "starClass": "M", "starTypeName": "", "pos": [0,0,4.3], "edsmUrl": "https://www.edsm.net/en/system/id/350/name/Alpha+Centauri", "id64": 2},
    {"system": "Barnard's Star", "starClass": "M", "starTypeName": "Red Dwarf", "pos": [-0.03, 5.8, 1.2], "edsmUrl": "", "id64": 3},
    {"system": "Wolf 359", "starClass": "M", "starTypeName": "", "pos": [5.1, 4.2, -5.3], "edsmUrl": "", "id64": 4},
    {"system": "Sirius", "starClass": "A", "starTypeName": "Main Sequence", "pos": [-4.1, -6.2, 5.1], "edsmUrl": "https://...", "id64": 5}
]

MOCK_ROUTE_12 = [
    {"system": "Maia", "starClass": "B", "starTypeName": "Blue-White Giant", "pos": [-81, -177, -345], "id64": 101, "edsmUrl": "https://..."},
    {"system": "Jackson's Lighthouse", "starClass": "N", "starTypeName": "Neutron Star", "pos": [174, -40, 48], "id64": 102, "edsmUrl": "https://..."},
    {"system": "Sagittarius A*", "starClass": "H", "starTypeName": "Supermassive Black Hole", "pos": [25, -11, 25899], "id64": 103, "edsmUrl": "https://..."},
    {"system": "Colonia", "starClass": "F", "starTypeName": "", "pos": [-1112, -47, 21330], "id64": 104, "edsmUrl": ""},
    {"system": "Eishia Phai AA-A h12", "starClass": "DA", "starTypeName": "White Dwarf", "pos": [1500, -200, 4000], "id64": 105, "edsmUrl": ""},
    {"system": "Dryau Awesomesauce", "starClass": "K", "starTypeName": "", "pos": [4500, 150, 8000], "id64": 106, "edsmUrl": ""},
    {"system": "LHS 3447", "starClass": "M", "starTypeName": "", "pos": [5, 2, -10], "id64": 107, "edsmUrl": ""},
    {"system": "Achenar", "starClass": "B", "starTypeName": "", "pos": [67, -33, -118], "id64": 108, "edsmUrl": ""},
    {"system": "Rhea", "starClass": "F", "starTypeName": "", "pos": [65, 18, 5], "id64": 109, "edsmUrl": ""},
    {"system": "Alioth", "starClass": "A", "starTypeName": "", "pos": [-33, 72, -47], "id64": 110, "edsmUrl": ""},
    {"system": "Shinrarta Dezhra", "starClass": "G", "starTypeName": "", "pos": [55, 17, 27], "id64": 111, "edsmUrl": ""},
    {"system": "Beagle Point", "starClass": "K", "starTypeName": "", "pos": [-1, 16, 65270], "id64": 112, "edsmUrl": ""}
]

# Insert this in your test_ui.py
def generate_stress_route(length=120):
    route = []
    classes = ["O", "B", "A", "F", "G", "K", "M", "N", "H", "DA"]
    for i in range(length):
        s_class = classes[i % len(classes)]
        route.append({
            "system": f"STRESS-TEST-SYSTEM-{i:03}",
            "starClass": s_class,
            "starTypeName": "Stress Test" if i % 10 == 0 else "",
            "pos": [0, 0, i * 50],  # Systems spaced 50Ly apart
            "edsmUrl": "https://www.edsm.net/" if i % 2 == 0 else "",
            "id64": 1000 + i
        })
    return route

MOCK_ROUTE_120 = generate_stress_route(120)

def run_test():
    root = tk.Tk()
    root.title("NextStop UI Test Bench")
    root.geometry("300x600")
    root.configure(bg="black")

    # Initialize your Board
    # You can switch between SimpleBoard and FancyBoard here to test both
    board = FancyBoard(root) 

    def next_jump():
        if board.currentIndex < len(board.route) - 1:
            # Mocking the ship moving to the next system's position
            target_pos = board.route[board.currentIndex+1]["pos"]
            board.setCurrentPos(target_pos)
            board.updateCanvas()

    def set_route(route):
        board.setRoute(route)
        reset_route()

    def clear_route(): set_route([])
    def set_route5(): set_route(MOCK_ROUTE_5)
    def set_route12(): set_route(MOCK_ROUTE_12)
    def set_route120(): set_route(MOCK_ROUTE_120)

    def reset_route():
        board.currentIndex = 0
        board.setCurrentPos([0, 0, 0])
        board.updateCanvas()

    # Create a dedicated frame for test controls
    ctrl_frame = tk.Frame(root)
    ctrl_frame.grid(row=1, column=0, sticky="ew")

    # Now you can use pack inside the frame because the frame has no other slaves yet!
    tk.Button(ctrl_frame, text="Simulate Next Jump", command=next_jump).grid(row=0, column=0)
    tk.Button(ctrl_frame, text="Reset Route", command=reset_route).grid(row=0, column=1)
    tk.Button(ctrl_frame, text="Clear Route", command=clear_route).grid(row=1, column=0)
    tk.Button(ctrl_frame, text="Set Route 5", command=set_route5).grid(row=2, column=0)
    tk.Button(ctrl_frame, text="Set Route 12", command=set_route12).grid(row=3, column=0)
    tk.Button(ctrl_frame, text="Set Route 120", command=set_route120).grid(row=4, column=0)

    from load import plugin_prefs
    option_frame = plugin_prefs(root, "FAKE_CMDR", False)
    option_frame.grid(row=2, column=0)

    # Trigger the Draw
    board.updateCanvas()

    print("Test UI Started. Close window to exit.")
    print(f"Debug: {board.debugMode}")
    root.mainloop()

if __name__ == "__main__":
    run_test()