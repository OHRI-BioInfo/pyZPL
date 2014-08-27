#!/usr/bin/env python

DPI = 203 #dots/inch
width = 4 #inches
height = 6 #inches
elementSpacing = 20 #dots
margin = 40 #dots

import xml.etree.ElementTree as ET
import sys
import re
import serial
import math
import io
import shutil
import tempfile
from bmpread import *
from pyZPL import *

labelWidth = DPI*width-margin*2
labelHeight = DPI*height-margin*2

dotswide = labelWidth
dotshigh = labelHeight

currentDown = margin

dn = os.path.dirname(os.path.realpath(__file__))+"/"
tree = ET.parse(dn+"pace.xml")
root = tree.getroot()

defaultFontHeight = 18
defaultFontWidth = 10
fontHeight = defaultFontHeight
#fontWidth = int(math.ceil((4.0/5.0)*fontHeight))
fontWidth = defaultFontWidth

images = []
ser = None
tempdir = ""

def getStoredImages():
    global ser
    ser.write("^XA^HWR:*.*^XZ")
    ser.flush()
    output = ""
    EOT = False
    while not EOT:
        readchar = ser.read(1)
        #3 is ASCII end-of-transmission character
        if ord(readchar) == 3:
            EOT = True
        output += readchar
    lines = output.split('\n')
    stored = []
    for line in lines:
        #Takes the image name out of a line like this:
        #* R:C5SVJ64.GRF    1320
        regex = re.compile(r'.*?\* R\:([A-Z0-9]+)')
        match = regex.match(line)
        print line
        if match is None: #Ignore lines that don't match this format
            continue
        stored.append(match.group(1))
    return stored

def downloadImages():
    global images,ser
    storedImages = getStoredImages()
    for i,image in enumerate(images):
        if image.downloadName in storedImages:
            print image.downloadName+" already downloaded, skipping ("+str(i+1)+"/"+str(len(images))+")"
            continue
        print "Downloading "+image.downloadName+" to printer ("+str(i+1)+"/"+str(len(images))+")"
        ser.write(image.downloadCmd)

def findItem(itemList,ID):
    for item in itemList:
        if item.ID == ID:
            return item

def calculateTextDimensions(text,maxWidth,fscale):
    lines = 0
    widest = 0
    #Inter-character gap is 2 dots for font D
    splitForcedLines = text.split(r"\&")
    for line in splitForcedLines:
        textWidth = (len(line)+1.0)*fontWidth+fscale*2.0*len(line)
        if widest < textWidth:
            widest = textWidth
        lines += int(math.ceil(textWidth/maxWidth))
    print text+str(lines)+","+str(textWidth)+","+str(maxWidth)
    if textWidth > maxWidth:    #If the text is larger than max width, then it will be wrapped,
                                #so consider its width equal to max width
        return (maxWidth,lines)
    else:
        return (int(widest),lines)

def truncateText(text,maxWidth,maxHeight,fscale):
    dimensions = calculateTextDimensions(text,maxWidth,fscale)
    #maxHeight/(height of each text row, including gap)
    maxLines = int(math.ceil(maxHeight/(float(fontHeight)+dimensions[1]*2)))
    if dimensions[1] > maxLines: #If the text takes up more lines than it is allotted, truncate
        #(maxWidth*maxLines) = total allotted space, divided by
        #text size+gaps
        lineChars = int(math.floor(maxWidth*maxLines/(len(str(text))*float(fontWidth)+2*len(str(text)))))
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
        #Usually when stuff is set to 0, the next stage of the program (generating the layout) will detect this
        #and act accordingly
        height = element.get("height")
        width = element.get("width")
        pheight = 0
        pwidth = 0

        if height is not None:
            if height[len(height)-1:] == "%":
                pheight = int(height[:len(height)-1])
                height = 0
            else:
                height = int(height)
        else:
            height = 0

        if width is not None:
            if width[len(width)-1:] == "%":
                pwidth = int(width[:len(width)-1])
                width = 0
            else:
                width = int(width)
        else:
            width = 0

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
        newElement.height = height
        newElement.width = width
        newElement.pheight = pheight
        newElement.pwidth = pwidth

        if element.tag == "Box":
            border = element.get("border")

            if border is not None:
                border = int(border)
            else:
                border = 10

            newElement.border = border

            newElement.ZPL = "^GBwidth,height,"+str(border)+"^FS"
            processElements(newElement,customItems)

        if element.tag == "Text":
            text = ""
            justify = "L"
            if elementID is not None:
                text = item.data
            else:
                text = element.text
            if element.get("fscale") is not None:
                newElement.fscale = int(element.get("fscale"))
            else:
                newElement.fscale = 1
            if element.get("justify") is not None:
                justify = element.get("justify")
                if justify == "justify":
                    justify = "J"
                elif justify == "right":
                    justify = "R"
                elif justify == "center":
                    justify = "C"

            newElement.ZPL = "^CFD"+","+str(defaultFontHeight*newElement.fscale)+","+\
            str(defaultFontWidth*newElement.fscale)+"^FBwidth,lines,,"+justify+"^FDtext^FS"
            newElement.text = text

        if element.tag == "Image":
            imageFile = ""
            if elementID is not None:
                imageFile = item.data
            else:
                imageFile = element.text
            element.imageFile = imageFile

            ispwidth = False
            ispheight = False
            mywidth = newElement.width
            myheight = newElement.height
            if pwidth != 0:
                mywidth = pwidth
                ispwidth = True
            if pheight != 0:
                myheight = pheight
                ispheight = True

            #If width and height were none, then newElement's width and height are zero,
            #and the image will not be resized
            newElement.image = getImg(imageFile,mywidth,myheight,ispwidth,ispheight,tempdir)

            #We still need a non-zero width and height for this element, so if it wasn't specified
            #then get it from the image we just read
            if height == 0 and pheight == 0:
                newElement.height = newElement.image.height
            if width == 0 and pwidth == 0:
                newElement.width = newElement.image.width
            images.append(newElement.image)

        if element.tag == "vspacer" or element.tag == "hspacer":
            if element.get("size") is not None:
                newElement.size = int(element.get("size"))
            else:
                newElement.size = 0

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
    global ZPLLayout,fontWidth,fontHeight
    widthUsed = 0
    heightUsed = 0
    rowHeight = 0
    rowWidths = []

    rownum = 0
    firstElement = True

    for element in list(parent.children):
        #Handle spacers
        if element.type == "vspacer":
            heightUsed += element.size
            continue
        if element.type == "hspacer":
            widthUsed += element.size
            continue

        absoluteX = False
        absoluteY = False
        tooBig = False

        if (element.width > parent.width or element.width == 0) and element.pwidth == 0:
            element.width = parent.width-parent.border*2
            tooBig = True
        if (element.height > parent.height or element.height == 0) and element.pheight == 0:
            element.height = parent.height-parent.border*2
            tooBig = True
        if element.pwidth != 0:
            element.width = int(round(element.pwidth/100.0*parent.width))
        if element.pheight != 0:
            element.height = int(round(element.pheight/100.0*parent.height))
        if tooBig and element.type == "Image":
            element.image = getImg(element.imageFile,element.width,element.height,tempdir)
            element.ZPL = element.image.downloadCmd
        if element.type == "Text":
            fontWidth = defaultFontWidth*element.fscale
            fontHeight = defaultFontHeight*element.fscale
            element.text = truncateText(element.text,parent.width-parent.border*2,parent.height-parent.border*2,element.fscale)
            dimensions = calculateTextDimensions(element.text,parent.width-parent.border*2,element.fscale)
            element.width = dimensions[0]
            element.height = dimensions[1]*fontHeight
            print "height:"+str(element.height)
            element.lines = dimensions[1]

        if element.left is not None:
            element.x = parent.x+element.left+parent.border
            absoluteX = True
        elif element.right is not None:
            element.x = parent.x+parent.width-element.right-parent.border-element.width
            absoluteX = True

        if element.top is not None:
            element.y = parent.y+element.top+parent.border
            absoluteY = True
        elif element.bottom is not None:
            element.y = parent.y+parent.height-element.bottom-parent.border-element.height
            absoluteY = True

        if not absoluteX:
            widthUsed += element.width
            if widthUsed > parent.width:
                heightUsed += rowHeight
                rowHeight = 0
                rowWidths.append(widthUsed-element.width)
                widthUsed = element.width
                rownum += 1
                firstElement = True
            if rowHeight < element.height and not absoluteY:
                rowHeight = element.height
            if not firstElement:
                widthUsed += elementSpacing
            firstElement = False
            if not absoluteY:
                element.y = heightUsed+rownum*elementSpacing+parent.y+parent.border
            element.x = widthUsed-element.width+parent.x

        if (element.x > parent.x+parent.width and not absoluteX) or (element.y > parent.y+parent.height and not absoluteY):
            element.ZPL = ""
        element.row = rownum

    rowWidths.append(widthUsed)

    for element in list(parent.children):
        if element.right is None and element.left is None: element.x += (parent.width-rowWidths[element.row])/2
        element.ZPL = element.ZPL.replace("width",str(element.width))
        if element.type == "Text":
            element.ZPL = element.ZPL.replace("lines",str(element.lines))
            element.ZPL = element.ZPL.replace("text",element.text)
        else:
            element.ZPL = element.ZPL.replace("height",str(element.height))
        if element.type == "Image":
            element.ZPL += "^XGR:"+element.image.downloadName+",1,1^FS"
        ZPLLayout += "^FO"+str(element.x)+","+str(element.y)+element.ZPL
        if len(element.children) is not 0:
            generateLayout(element)

def printLabel(customItems):
    global ZPLLayout,rootElement,currentDown,ser,images,tempdir
    tempdir = tempfile.mkdtemp()+"/"
    images = []
    rootElement = ZPLElement()
    rootElement.width = labelWidth
    rootElement.height = labelHeight
    rootElement.border = 0
    rootElement.type = "Root"
    rootElement.XMLElement = root
    rootElement.x = margin
    rootElement.y = margin

    ZPLLayout = "^XA"
    currentDown = margin
    ser = serial.Serial(0,9600,timeout=5)

    processElements(rootElement,customItems)
    generateLayout(rootElement)
    downloadImages()
    ZPLLayout += "^XZ"
    ser.write(ZPLLayout)
    ser.flush()
    ser.close()
    shutil.rmtree(tempdir)
    return ZPLLayout
