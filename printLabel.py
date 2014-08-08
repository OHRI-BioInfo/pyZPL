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
rootElement = ZPLElement()
rootElement.width = labelWidth
rootElement.height = labelHeight
rootElement.type = "Root"
rootElement.XMLElement = root

#jsonFile = open("testJSON.json")
#jsonData = sys.argv[1]
jsonData = '{"sample_text":{"data":"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Praesent hendrerit lectus quam, ut vestibulum dolor consectetur a. Sed urna erat, congue ornare justo non, posuere gravida neque. Maecenas convallis augue at odio lobortis, ut interdum mauris luctus. Maecenas eu nibh elit. Vestibulum id vulputate diam. Etiam facilisis elit sit amet metus commodo imperdiet. Donec ornare placerat gravida. Nulla a bibendum neque.","visible":true},"title":{"data":"","visible":false},"poison":{"data":"SymbolD1_sm.bmp","visible":true}}'
jsonObject = json.loads(jsonData)

ser = serial.Serial(0)
print ser.name

fontHeight = 30
fontWidth = int(math.ceil((4.0/5.0)*fontHeight))
ZPLLayout = "^XA^CF0,"+str(fontHeight)

customIndex = 1

def calculateTextDimensions(text,maxWidth):
    lines = int(math.ceil(len(str(text))*float(fontWidth)/maxWidth))
    cols = len(str(text))*fontWidth
    if cols > maxWidth:
        cols = maxWidth
    return (cols,lines)
    
def truncateText(text,maxWidth,maxHeight):
    dimensions = calculateTextDimensions(text,maxWidth)
    maxLines = int(math.ceil(maxHeight/float(fontHeight)))
    if dimensions[1] > maxLines:
        return text[:int(math.ceil(dimensions[0]/float(fontWidth)))*maxLines]
    else:
        return text

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
            newElement.ZPL = "^FBwidth,lines^FDtext^FS"
            newElement.text = text
            
        if element.tag == "Image":
            imageFile = ""
            if elementID is not None:
                imageFile = jsonObject[elementID]['data']
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
        tooBig = False
        if element.width > parent.width or element.width == 0:
            element.width = parent.width
            tooBig = True
        if element.height > parent.height or element.height == 0:
            element.height = parent.height
            tooBig = True
        if tooBig and element.type == "Image":
            element.image = getImg(element.imageFile,element.width,element.height)
            element.ZPL = element.image.downloadCmd
        if element.type == "Text":
            element.text = truncateText(element.text,parent.width,parent.height)
            dimensions = calculateTextDimensions(element.text,parent.width)
            element.width = dimensions[0]
            element.height = dimensions[1]*fontHeight
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
        if element.x > parent.x+parent.width or element.y > parent.y+parent.height:
            element.ZPL = ""
        element.row = rownum
    
    rowWidths.append(widthUsed)
    print rowWidths

    for element in list(parent.children):
        element.x += (parent.width-rowWidths[element.row])/2
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

processElements(rootElement,False)
generateLayout(rootElement)
ZPLLayout += "^XZ"

print ZPLLayout
#ser.write(ZPLLayout)
ser.close()
