import flask
#from flask_oauth import OAuth
from flask_cors import CORS, cross_origin
import mysql.connector
from mysql.connector import Error
import binascii,hashlib
import subprocess
import json
from OpenSSL import SSL
import requests, urllib
import threading, time
from requests.auth import HTTPBasicAuth
from datetime import datetime
from dateutil.relativedelta import relativedelta
import random
context = ('token_server.crt','token_server.key')

app = flask.Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

stored_val = json.load(open("storage.json"))

@app.route('/updateEntry', methods=['POST'])
@cross_origin()
def updateEntry():
    print("updateEntry")
    if(flask.request.form==None):
        return "form arguements not passed",400
    data=json.loads(flask.request.form["data"])
    for tokens in data["data"]:
        print("[ carid :",tokens["carid"],", tokena :",tokens["tokena"],", tokenb :",tokens["tokenb"])

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=9021,ssl_context=context)
