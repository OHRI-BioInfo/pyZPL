from flask import *
from pyZPL import *

app = Flask(__name__)

testItem = ZPLCustomItem()
testItem.fixed = "readonly"
testItem.data = "testdata"
testItem.ID = "the_ID"
testItem.type = "Text"

items = []
items.append(testItem)

@app.route('/')
def root():
    return render_template("index.html",items=items)

if __name__ == '__main__':
    app.debug = True
    app.run()
