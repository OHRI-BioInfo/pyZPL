#!/usr/bin/env python

DPI = 203 #dots/inch
width = 4 #inches
height = 6 #inches
elementSpacing = 50 #dots
margin = 40 #dots

import xml.etree.ElementTree as ET
import sys
import re
import serial
import math
from bmpread import *
from pyZPL import *

labelWidth = DPI*width-margin*2
labelHeight = DPI*height-margin*2

dotswide = labelWidth
dotshigh = labelHeight

currentDown = margin

tree = ET.parse("/home/jbrooks/pyZPL/testlabel.xml")
root = tree.getroot()

fontHeight = 26
#fontWidth = int(math.ceil((4.0/5.0)*fontHeight))
fontWidth = 13

def findItem(itemList,ID):
    for item in itemList:
        if item.ID == ID:
            return item

def calculateTextDimensions(text,maxWidth):
    #Inter-character gap is 3 dots for font F
    textWidth = len(str(text))*fontWidth+3*len(str(text))
    lines = int(math.ceil(float(textWidth)/maxWidth))
    if textWidth > maxWidth:    #If the text is larger than max width, then it will be wrapped,
                                #so consider its width equal to max width
        return (maxWidth,lines)
    else:
        return (textWidth,lines)

def truncateText(text,maxWidth,maxHeight):
    dimensions = calculateTextDimensions(text,maxWidth)
    #maxHeight/(height of each text row, including gap)
    maxLines = int(math.ceil(maxHeight/(float(fontHeight)+dimensions[1]*3)))
    if dimensions[1] > maxLines: #If the text takes up more lines than it is allotted, truncate
        #(maxWidth*maxLines) = total allotted space, divided by
        #text size+gaps
        lineChars = int(math.floor(maxWidth*maxLines/(len(str(text))*float(fontWidth)+3*len(str(text)))))
        #Truncate to (chars in each line*allowed number of lines)
        return text[:int(lineChars*maxLines)]
    else:
        return text

#Go through elements recursively and make a tree structure by adding to the root node, and then
#to the child nodes
def processElements(root,customItems):
    global rowHeight,currentRow,currentRowElement,elementSpacing,remainingWidth,ZPLLayout

    for element in list(root.XMLElement):
        #The way this stuff works is, if the element has these defined (not None),
        #then they will be used. Otherwise, default values (mostly defined in the ZPLElement class) will be used
        height = element.get("height")
        width = element.get("width")

        top = element.get("top")
        bottom = element.get("bottom")
        left = element.get("left")
        right = element.get("right")

        elementID = element.get("id")
        newElement = ZPLElement()
        #Item is for custom items; ones that have user-definable variables.
        #Any element with an "id" attribute in the XML template is considered a custom item
        #Such elements will use the user-defined variables (passed in through a ZPLCustomItem object,
        #for example generated in web.py) instead of the data from the XML
        item = None
        if elementID is not None:
            item = findItem(customItems,elementID)
            if not bool(item.visible):
                continue
            newElement.ID = elementID
        newElement.type = element.tag
        newElement.XMLElement = element

        if element.tag == "Box":
            border = element.get("border")

            if border is not None:
                border = int(border)
            else:
                border = 10

            newElement.border = border

            if height is not None:
                newElement.height = int(height)
            if width is not None:
                newElement.width = int(width)
            newElement.ZPL = "^GBwidth,height,"+str(border)+"^FS"
            processElements(newElement,customItems)

        if element.tag == "Text":
            if height is not None:
                newElement.height = int(height)
            if width is not None:
                newElement.width = int(width)
            text = ""
            if elementID is not None:
                text = item.data
            else:
                text = element.text
            newElement.ZPL = "^FBwidth,lines^FDtext^FS"
            newElement.text = text

        if element.tag == "Image":
            imageFile = ""
            if elementID is not None:
                imageFile = item.data
            else:
                imageFile = element.text
            element.imageFile = imageFile

            if height is not None:
                newElement.height = int(height)
            if width is not None:
                newElement.width = int(width)
            newElement.image = getImg(imageFile,newElement.width,newElement.height)

            if height is None:
                newElement.height = newElement.image.height
            if width is None:
                newElement.width = newElement.image.width
            ZPLLayout = newElement.image.downloadCmd + ZPLLayout

        if top is not None:
            newElement.top = int(top)
        if bottom is not None:
            newElement.bottom = int(bottom)
        if left is not None:
            newElement.left = int(left)
        if right is not None:
            newElement.right = int(right)

        root.children.append(newElement)

#Generates the ZPL layout from all the objects
#It's recursive, because each container is considered separately
def generateLayout(parent):
    global ZPLLayout
    widthUsed = 0
    heightUsed = 0
    rowHeight = 0
    rowWidths = []

    rownum = 0
    firstElement = True

    for element in list(parent.children):
        absolute = False
        tooBig = False

        if element.width > parent.width or element.width == 0:
            element.width = parent.width-parent.border*2
            tooBig = True
        if element.height > parent.height or element.height == 0:
            element.height = parent.height-parent.border*2
            tooBig = True
        if tooBig and element.type == "Image":
            element.image = getImg(element.imageFile,element.width,element.height)
            element.ZPL = element.image.downloadCmd
        if element.type == "Text":
            element.text = truncateText(element.text,parent.width-parent.border*2,parent.height-parent.border*2)
            dimensions = calculateTextDimensions(element.text,parent.width-parent.border*2)
            element.width = dimensions[0]+1
            element.height = dimensions[1]*fontHeight

        if element.left is not None:
            element.x = parent.x+element.left+parent.border
            absolute = True
        elif element.right is not None:
            element.x = parent.x+parent.width-element.right-parent.border-element.width
            absolute = True

        if element.top is not None:
            element.y = parent.y+element.top+parent.border
            absolute = True
        elif element.bottom is not None:
            element.y = parent.y+parent.height-element.bottom-parent.border-element.height
            absolute = True

        if not absolute:
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
            element.y = heightUsed+margin+rownum*elementSpacing+parent.y
            element.x = widthUsed-element.width+parent.x

        if (element.x > parent.x+parent.width and not absoluteX) or (element.y > parent.y+parent.height and not absoluteY):
            element.ZPL = ""
        element.row = rownum

    rowWidths.append(widthUsed)

    for element in list(parent.children):
        if element.right is None and element.left is None:    element.x += (parent.width-rowWidths[element.row])/2
        element.ZPL = element.ZPL.replace("width",str(element.width))
        if element.type == "Text":
            element.ZPL = element.ZPL.replace("lines",str(element.height/fontHeight))
            element.ZPL = element.ZPL.replace("text",element.text)
        else:
            element.ZPL = element.ZPL.replace("height",str(element.height))
        if element.type == "Image":
            element.ZPL += "^XGR:SAMPLE.GRF,1,1^FS"
        ZPLLayout += "^FO"+str(element.x+margin)+","+str(element.y+margin)+element.ZPL
        if len(element.children) is not 0:
            generateLayout(element)

def printLabel(customItems):
    global ZPLLayout,rootElement,currentDown
    rootElement = ZPLElement()
    rootElement.width = labelWidth
    rootElement.height = labelHeight
    rootElement.border = 0
    rootElement.type = "Root"
    rootElement.XMLElement = root

    ZPLLayout = "^XA^CFF,"+str(fontHeight)
    currentDown = margin
    ser = serial.Serial(0)

    processElements(rootElement,customItems)
    generateLayout(rootElement)
    ZPLLayout += "^XZ"
    delImages = "^XA^IDR:*.*^FS^XZ"
    ser.write(delImages+ZPLLayout)
    ser.close()
    return ZPLLayout
