from flask import *
from pyZPL import *
import xml.etree.ElementTree as ET

app = Flask(__name__)


tree = ET.parse("/home/jbrooks/pyZPL/testlabel.xml")
customElements = tree.findall(".//*[@id]")

items = []
for element in customElements:
    newItem = ZPLCustomItem()
    newItem.ID = element.get("id")
    newItem.data = element.text
    newItem.type = element.tag
    if element.get("fixed"):
        newItem.fixed = "readonly"
    items.append(newItem)

@app.route('/')
def root():
    return render_template("index.html",items=items)

if __name__ == '__main__':
    app.debug = True
    app.run()
