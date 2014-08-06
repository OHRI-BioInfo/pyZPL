class ZPLElement:
    def __init__(self):
        self.children = []
    width = 0
    height = 0
    x = 0
    y = 0
    type = ""
    ZPL = ""
    row = 0

class ZPLRow:
    def __init__(self):
        self.rowElements = []
    width = 0
    height = 0
