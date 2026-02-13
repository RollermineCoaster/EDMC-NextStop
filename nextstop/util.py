"""Utility function"""
import math
import logging
from config import appname

logger = logging.getLogger(f"{appname}.EDMC-NextStop")

def get_distance(pos1, pos2):
    """Get distance between pos1 and pos2"""
    return math.sqrt((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2 + (pos1[2]-pos2[2])**2)

def get_canvas_obj_height(canvas, obj_id):
    """Get canvas object height"""
    _, y1, _, y2 = canvas.bbox(obj_id)
    return abs(y2-y1)

def get_canvas_obj_width(canvas, obj_id):
    """Get canvas object width"""
    x1, _, x2, _ = canvas.bbox(obj_id)
    return abs(x2-x1)

def resize_canvas_text(canvas, obj_id, width):
    """Reduce font size to fit the width"""
    #remove the width limit of the object
    canvas.itemconfigure(obj_id, width=0)
    if isinstance(width, str):
        width = canvas.winfo_fpixels(width)
    #make system name resize dynamically
    text_height = get_canvas_obj_height(canvas, obj_id)
    text_font, text_size = canvas.itemcget(obj_id, "font").split()
    text_size = int(text_size)
    #limit the width of the object
    canvas.itemconfigure(obj_id, width=width)
    #while text size > 1pt and current text height > old text height
    while text_size > 1 and get_canvas_obj_height(canvas, obj_id) > text_height:
        text_size -= 1
        canvas.itemconfigure(obj_id, font=(text_font, text_size))

def to_pix(canvas, distance):
    """Convert the distance to pixel"""
    try:
        return canvas.winfo_fpixels(distance)
    except Exception as e:
        logger.error("Failed to get number of pixels! %s", e)
    return 0.0

def format_text(value, unit, units, placeholder=""):
    """Format the text with unit/units or show placeholder text if value < 0"""
    if not placeholder: 
        placeholder = f"{value}"
    output = placeholder if value <= 0 else str(value)
    output += f" {unit}" if value <= 1 else f" {units}"
    return output

def get_time(seconds):
    """Get the hour, minute, and second based on the given second."""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return h, m, s