import sys
sys.path.append("C:/Users/Fung/AppData/Local/EDMarketConnector/plugins/EDMCOverlay")

from DotFont import DotFont
from edmcoverlay import Overlay
import time
import math

dot = DotFont(open("bigKMB.json"), "0", "1")

client = Overlay()

data = dot.getString("ABCDEFGHIJKLMNOP")

width = 8*16
height = 16*2
px = 3
#for y in range(height):
#    for x in range(width):
#        client.send_shape("sqx"+str(x)+"y"+str(y), "rect", "black", "yellow", 4*x, 4*y, 4, 4, 10)

for y in range(len(data)):
    print(data[y])
    for x in range(len(data[y])):
        if data[y][x]=="1":
        #if True:
            client.send_shape("1sqx"+str(x)+"y"+str(y), "rect", "black", "yellow", math.floor((1280-width*px)/2)+px*x,    px*y, px, px, 10)
            client.send_shape("2sqx"+str(x)+"y"+str(y), "rect", "black", "yellow", math.floor((1280-width*px)/2)+px*x, 16*px+px*y, px, px, 10)
            #client.send_message("row"+str(row), data[row], "yellow", 200, 200+row*14, 10)

time.sleep(10)