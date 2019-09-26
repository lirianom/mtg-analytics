from flask import Flask
from flask_cors import CORS
from bson.json_util import dumps
import sys
sys.path.insert(1, './utils/')
import db_functions as db

app = Flask(__name__)
CORS(app)

@app.route('/', methods = ['GET'])
def getAllCards() :
    return dumps(db.get_cards_api())

if __name__ == '__main__' :
    app.run(debug = True, port = 5000)
