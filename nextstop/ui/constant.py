"""
Constant
"""
SCOOPABLE_STARS = ["O","B","A","F","G","K","M"]
BROWN_DWARFS = ["L","T","Y"]
WOLF_RAYET = ["W","WN","WNC","WC","WO"]
WHITE_DWARFS = ["D","DA","DAB","DAO","DAZ","DAV","DB","DBV","DBZ","DC","DCV","DO","DOV","DQ","DX"]
#white dwarfs, neutron stars, black holes
DANGER_STARS = WHITE_DWARFS + ["N", "H", "SupermassiveBlackHole"]

#color
DANGER_COLOR = "#FF0000"
THEME_1933 = {
    "bg":        "#FFFFFF",
    "textMain":  "#000000",
    "textMinor": "#555555",
    "main":      "#FF0000",
    "minor1":    "#888888",
    "minor2":    "#BBBBBB"
}
THARGOID_COLORS = {
    "Alert":      "#FFD00F",
    "Invasion":   "#FF6F00",
    "Controlled": "#286300",
    "Titan":      "#990000",
    "Recovery":   "#9F1BFF"
}

#font
LOGO_FONT = "nextstop-logo"
FUELSTAR_LOGO =    "\uE800"
DANGER_LOGO =      "\uE801"
THARGOIDWAR_LOGO = "\uE810"
EDSM_LOGO =        "\uE820"
BULLET_BG =        "\uF111"
BULLET_FG =        "\uF10C"

#string
CURRENT_STR =   "CURRENT"
DANGER_STR =    "Danger"
FUELSTAR_STR =  "Fuel Star"
OPENEDSM_STR =  "Open EDSM"
NORMAL_STR =    "Normal"
THARGOID_STR =  "Thargoid"
NEXTSTOP_STR =  "Next stop:"
REMAINING_STR = "Remaining:"
JUMP_STR =      "Jump"
JUMPS_STR =      "Jumps"
HOUR_STR =      "Hour"
HOURS_STR =      "Hours"
MIN_STR =       "Min"
MINS_STR =       "Mins"
NOROUTE_STR = "No Route"
DASH6_STR = "-------"
NOROUTEFULL_STR = f"{DASH6_STR}{NOROUTE_STR}{DASH6_STR}"

SIZE = "225p"
MAX_ROWS = 6
