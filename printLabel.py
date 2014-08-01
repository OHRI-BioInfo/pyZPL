#!/usr/bin/env python

DPI = 203 #dots/inch
width = 4 #inches
height = 6 #inches
elementSpacing = 100 #dots

import xml.etree.ElementTree as ET
import sys
import re
from pyZPL import *

dotswide = DPI*width
dotshigh = DPI*height

remainingWidth = dotswide
remainingHeight = dotshigh

currentDown = 0
currentRow = 0
rowHeight = 0
currentRowElement = 0

tree = ET.parse("testlabel.xml")
root = tree.getroot()

rowBoxes = []
ZPLLayout = "^CF0,30,30^XA"

customIndex = 1

def newRow():
    global currentDown 
    global remainingHeight
    global remainingWidth
    global currentRow
    global rowHeight
    global ZPLLayout

    currentRight = 0
    for i in range(0,currentRowElement):
        ZPLLayout = ZPLLayout.replace("+row"+str(currentRow)+"Down",str(currentDown))
        ZPLLayout = ZPLLayout.replace("+row"+str(currentRow)+"Right"+str(i),str(currentRight))
        currentRight += int(rowBoxes[i].width) + elementSpacing

    currentDown += rowHeight + elementSpacing
    remainingHeight -= rowHeight + elementSpacing
    remainingWidth = dotswide
    rowHeight = 0
    currentRow += 1

for element in root.iter():
    if element.get("custom") is not None:
        if element.tag == "Image":
            if element.get("customtype") == "bool":
               if not bool(sys.argv[customIndex]):
                   element.find("..").remove(element)
        elif element.tag == "Text":
            if element.get("customtype") == "string":
                element.text = str(sys.argv[customIndex])
            elif element.get("customtype") == "bool":
                if not bool(sys.argv[customIndex]):
                    element.find("..").remove(element)
        customIndex += 1

for element in root.iter():
    if element.tag == "Box":
        boxWidth = element.get("width")
        boxHeight = element.get("height")
        border = element.get("border")

        if border is None:
            border = "10"
        
        newbox = ZPLBox()
        newbox.height = boxHeight
        newbox.width = boxWidth
        newbox.border = border
        rowBoxes.append(newbox)

        if int(boxHeight) > rowHeight:
            rowHeight = int(boxHeight)
        if remainingWidth is not dotswide:
            remainingWidth -= elementSpacing
            if remainingWidth < int(boxWidth)+int(border)*2:
                newRow()
        ZPLLayout += "^FO+row"+str(currentRow)+"Right"+str(currentRowElement)+",+row"+str(currentRow)+"Down"
        remainingWidth -= int(boxWidth)+int(border)*2

        ZPLLayout += "^GB"+boxWidth+","+boxHeight+","+border+"^FS"
        currentRowElement += 1
#        for boxchild in element.iter():
#            if element.tag == "Text":

newRow()

ZPLLayout += "^XZ"

print ZPLLayout
