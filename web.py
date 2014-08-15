from flask import *
from pyZPL import *
from printLabel import printLabel
import xml.etree.ElementTree as ET

app = Flask(__name__)


tree = ET.parse("/home/jbrooks/pyZPL/testlabel.xml")
customElements = tree.findall(".//*[@id]")

customItems = []
for element in customElements:
    newItem = ZPLCustomItem()
    newItem.ID = element.get("id")
    newItem.data = element.text
    newItem.type = element.tag
    if element.get("fixed"):
        newItem.fixed = "readonly"
    customItems.append(newItem)

@app.route('/')
def root():
    return render_template("index.html",items=customItems)
    
@app.route('/print', methods=['POST'])
def print_():
    customItemsModified = []
    if request.method == 'POST':
        for key,value in request.form.iteritems():
            newItem = ZPLCustomItem()
            split = key.split('_')
            newItem.type = split[len(split)-1]
            newItem.ID = str.join("_",split[:len(split)-1])
            print newItem.ID

            newItem.data = request.form[newItem.ID+"_string"]
            try:
                request.form[newItem.ID+"_bool"]
                newItem.visible = True
            except KeyError:
                newItem.visible = False
            customItemsModified.append(newItem)
        return printLabel(customItemsModified)
    else:
        return "can has post?"

if __name__ == '__main__':
    app.debug = True
    app.run()
