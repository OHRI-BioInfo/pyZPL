class ZPLElement:
    def __init__(self):
        self.children = []
    width = 0
    height = 0
    pwidth = 0 #percentage width
    pheight = 0 #percentage height
    x = 0
    y = 0
    type = ""
    ZPL = ""
    row = 0
    
    top = None
    bottom = None
    left = None
    right = None

class ZPLCustomItem:
    fixed = ""
    data = ""
    ID = ""
    type = ""
    visible = False

class ZPLImage:
    width = 0
    height = 0
    downloadCmd = ""
    uploadName = "" #File name as uploaded; see bmpread.py for how this is generated

class ZPLRow:
    def __init__(self):
        self.rowElements = []
    width = 0
    height = 0
