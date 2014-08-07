#!/usr/bin/env python

DPI = 203 #dots/inch
width = 4 #inches
height = 6 #inches
elementSpacing = 50 #dots
margin = 40 #dots

import xml.etree.ElementTree as ET
import sys
import re
import json
from pyZPL import *

labelWidth = DPI*width-margin*2
labelHeight = DPI*height-margin*2

dotswide = labelWidth
dotshigh = labelHeight

currentDown = margin

tree = ET.parse("/home/jbrooks/pyZPL/testlabel.xml")
root = tree.getroot()
rootElement = ZPLElement()
rootElement.width = labelWidth
rootElement.height = labelHeight
rootElement.type = "Root"
rootElement.XMLElement = root

#jsonFile = open("testJSON.json")
#jsonData = sys.argv[1]
jsonData = '{"sample_text":{"data":"This is text. The text is nice.","visible":true},"title":{"data":"","visible":false},"poison":{"data":"SymbolD1_sm","visible":false}}'
jsonObject = json.loads(jsonData)

ZPLLayout = "^XA^CF0,30,30"

customIndex = 1

def processElements(root,nested):
    global rowHeight,currentRow,currentRowElement,elementSpacing,remainingWidth,ZPLLayout

    for element in list(root.XMLElement):
        height = element.get("height")
        width = element.get("width")
        elementID = element.get("id")
        newElement = ZPLElement()
        if elementID is not None:
            elementID = elementID.replace(" ","_")
            if not bool(jsonObject[elementID]['visible']):
                continue
            newElement.id = elementID
        newElement.type = element.tag
        newElement.XMLElement = element
                
        if element.tag == "Box":
            border = element.get("border")

            if border is not None:
                border = int(border)
            else:
                border = 10

            if height is not None:
                newElement.height = int(height)
            if width is not None:
                newElement.width = int(width)
            newElement.ZPL = "^GBwidth,height,"+str(border)+"^FS"
            processElements(newElement,True)

        if element.tag == "Text":
            if height is not None:
                newElement.height = int(height)
            if width is not None:
                newElement.width = int(width)
            text = ""
            if elementID is not None:
                text = jsonObject[elementID]['data']
            else:
                text = element.text
            newElement.ZPL = "^FBwidth,lines^FD"+text+"^FS"
        
        root.children.append(newElement)

def generateLayout(parent):
    global ZPLLayout
    widthUsed = 0
    heightUsed = 0
    rowHeight = 0
    rowWidths = []
    
    rownum = 0
    firstElement = True

    for element in list(parent.children):
        if element.width > parent.width or element.width == 0:
            element.width = parent.width
        if element.height > parent.height or element.height == 0:
            element.height = parent.height
        widthUsed += element.width
        if rowHeight < element.height:
            rowHeight = element.height
        if widthUsed > parent.width:
            heightUsed += rowHeight
            rowHeight = 0
            rowWidths.append(widthUsed-element.width)
            widthUsed = element.width
            rownum += 1
            firstElement = True
            
        if not firstElement:
            widthUsed += elementSpacing
        firstElement = False

        element.x = widthUsed-element.width+parent.x
        element.y = heightUsed+margin+rownum*elementSpacing+parent.y
        element.row = rownum
    
    rowWidths.append(widthUsed)
    print rowWidths

    for element in list(parent.children):
        element.x += (parent.width-rowWidths[element.row])/2
        element.ZPL = element.ZPL.replace("width",str(element.width))
        if element.type == "Text":
            element.ZPL = element.ZPL.replace("lines",str(element.height/30))
        else:
            element.ZPL = element.ZPL.replace("height",str(element.height))
        ZPLLayout += "^FO"+str(element.x+margin)+","+str(element.y+margin)+element.ZPL
        if len(element.children) is not 0:
            generateLayout(element)

processElements(rootElement,False)
generateLayout(rootElement)
ZPLLayout += "^XZ"

print ZPLLayout
