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

#for box in root.findall("Box"):
#    newbox = ZPLBox()
#    newbox.width = int(box.get("width"))
#    newbox.height = int(box.get("height"))
#    boxes.append(newbox)
