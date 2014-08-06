#!/usr/bin/env python

DPI = 203 #dots/inch
width = 4 #inches
height = 6 #inches
elementSpacing = 50 #dots
margin = 40 #dots

import xml.etree.ElementTree as ET
import sys
import re
from pyZPL import *

labelWidth = DPI*width-margin*2
labelHeight = DPI*height-margin*2

dotswide = labelWidth
dotshigh = labelHeight

currentDown = margin

tree = ET.parse("testlabel.xml")
root = tree.getroot()
rootElement = ZPLElement()
rootElement.width = labelWidth
rootElement.height = labelHeight
rootElement.type = "Root"
rootElement.XMLElement = root

ZPLLayout = "^CF0,30,30^XA"

customIndex = 1

for element in root.iter():
    if element.tag == "Image":
        root.remove(element) #Images not implemented yet
    if element.tag == "Text":
        if element.get("width") is None:
            element.set("width",dotswide)
        element.set("height",int(element.get("width"))/30)
    if element.tag == "Box":
        if element.get("border") is None:
            element.set("border","10")
    if element.get("custom") is not None:
        if element.tag == "Image":
            if element.get("customtype") == "bool":
               if not bool(sys.argv[customIndex]):
                   root.remove(element)
        elif element.tag == "Text":
            if element.get("customtype") == "string":
                element.text = str(sys.argv[customIndex])
            elif element.get("customtype") == "bool":
                if not bool(sys.argv[customIndex]):
                    element.find("..").remove(element)
        customIndex += 1

def processElements(root,nested):
    global rowHeight,currentRow,currentRowElement,elementSpacing,remainingWidth,ZPLLayout

    for element in list(root.XMLElement):
        newElement = ZPLElement()
        newElement.height = int(element.get("height"))
        newElement.width = int(element.get("width"))
        newElement.type = element.tag
        newElement.XMLElement = element
        
        #if nested:
            #dotswide = newElement.width-margin*2
            #dotshigh = newElement.height-margin*2
        #else:
            #dotswide = labelWidth
            #dotshigh = labelHeight
        
        #if int(element.get("height")) > rowHeight:
            #rowHeight = int(element.get("height"))
        #if remainingWidth is not dotswide:
            #if remainingWidth < int(element.get("width")) + elementSpacing:
                #newRow()
                #rowElements.append(newElement)
            #else:
                #remainingWidth -= elementSpacing
                
        if element.tag == "Box":
            border = int(element.get("border"))
            newElement.ZPL = "^GB"+str(newElement.width)+","+str(newElement.height)+","+str(border)+"^FS"
            processElements(newElement,True)
        #if element.tag == "Text":
        
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
        if element.width > parent.width:
            element.width = parent.width
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
        element.y = heightUsed+margin+rownum*elementSpacing#+parent.y
        element.row = rownum
    
    rowWidths.append(widthUsed)
    print rowWidths
    
    for element in list(parent.children):
        element.x += (parent.width-rowWidths[element.row])/2
        ZPLLayout += "^FO"+str(element.x+margin)+","+str(element.y+margin)+element.ZPL
        if len(element.children) is not 0:
            generateLayout(element)

processElements(rootElement,False)
generateLayout(rootElement)
ZPLLayout += "^XZ"

print ZPLLayout
