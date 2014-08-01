#!/usr/bin/env python

import xml.etree.ElementTree as ET
import sys
from pyZPL import *

tree = ET.parse("testlabel.xml")
root = tree.getroot()

boxes = []

customIndex = 1

for element in root.iter():
    if element.get("custom") is not None:
        if element.tag == "Image":
            print "Images not yet implemented"
        elif element.tag == "Text":
            element.text = str(sys.argv[customIndex])
        customIndex += 1

#for box in root.findall("Box"):
#    newbox = ZPLBox()
#    newbox.width = int(box.get("width"))
#    newbox.height = int(box.get("height"))
#    boxes.append(newbox)
