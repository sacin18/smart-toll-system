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

def isLoginValid(uname,pword):
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                        port=stored_val['db_port'],
                        database=stored_val['db'],
                        user=stored_val['db_user'],
                        password=stored_val['db_password'])
        cursor=connection.cursor()
        pword=hashlib.sha256(pword).hexdigest()
        sql_query = "SELECT * FROM users where username='"+uname+"' and password='"+pword+"'"
        cursor.execute(sql_query)
        result=cursor.fetchall()
        if(len(result)==0):
            connection.close()
            return False
        connection.close()
        return True
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    print("login failed")
    return False    

def getCarid(uname):
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                        port=stored_val['db_port'],
                        database=stored_val['db'],
                        user=stored_val['db_user'],
                        password=stored_val['db_password'])
        cursor=connection.cursor()
        sql_query = "SELECT carid FROM users where username='"+uname+"')"
        cursor.execute(sql_query)
        result=cursor.fetchall()
        if(len(result)==0):
            connection.close()
            return -1
        connection.close()
        return result[0][0]
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return -1

def genTollToken():
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                        port=stored_val['db_port'],
                        database=stored_val['db'],
                        user=stored_val['db_user'],
                        password=stored_val['db_password'])
        cursor=connection.cursor()
        toka=hashlib.sha256(str(random.random()).encode('ascii')).hexdigest()
        tokb=hashlib.sha256(str(random.random()).encode('ascii')).hexdigest()
        sql_query = "insert into tokens values(null,'"+toka+"','"+tokb+"')"
        cursor.execute(sql_query)
        if(cursor.rowcount()==0):
            connection.close()
            return -1
        sql_query = "select count(*) from tokens"
        cursor.execute(sql_query)
        result=cursor.fetchall()
        if(len(result)==0):
            connection.close()
            return -1
        connection.close()
        tokenid=result[0][0]
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return -1

def getPriviledge(username):
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                        port=stored_val['db_port'],
                        database=stored_val['db'],
                        user=stored_val['db_user'],
                        password=stored_val['db_password'])
        cursor=connection.cursor()
        sql_query = "SELECT user_prividelige FROM users where username='"+username+"')"
        cursor.execute(sql_query)
        result=cursor.fetchall()
        if(len(result)==0):
            connection.close()
            return -1
        connection.close()
        return result[0][0]
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return -1

@app.route('/test', methods=['GET'])
@cross_origin()
def test():
    return "hello"

@app.route('/isPaymentDone', methods=['GET'])
@cross_origin()
def isPaymentDone():
    print("isPaymentDone")
    if(flask.request.authorization==None):
        return "basic authorization required",400
    username=flask.request.authorization['username']
    password=flask.request.authorization['password']
    if(username.strip()=="" or password.strip()==""):
        return "invalid authorization arguments",400
    if(not isLoginValid(username,password)):
        return "incorrect credentials",401
    invoice_id=flask.request.args.get('invoice_id')
    if(invoice_id==None or invoice_id.strip()==""):
        return "invoice_id not provided",400
    username=stored_val['razorpay_user']
    password=stored_val['razorpay_password']
    response = requests.get('https://api.razorpay.com/v1/invoices/'+str(invoice_id),
        auth=HTTPBasicAuth(username,password),verify=False)
    if(response.status_code==200):
        out=dict()
        resp=json.loads(response.json())
        if(resp['status']=="paid"):
            out["status"]="paid"
            out["amount_paid"]=resp["amount_paid"]
            return out,200
        else:
            out["status"]="not paid"
            out["amount_paid"]=0
            return out,402
    return "request failed",response.status_code

@app.route('/isTokenReady', methods=['POST'])
@cross_origin()
def isTokenReady():
    print("isTokenReady")
    if(flask.request.authorization==None):
        return "basic authorization required",400
    username=flask.request.authorization['username']
    password=flask.request.authorization['password']
    if(username.strip()=="" or password.strip()==""):
        return "invalid authorization arguments",400
    if(not isLoginValid(username,password)):
        return "incorrect credentials",401
    tollid=flask.request.form['tollid']
    if(tollid==None or tollid==""):
        return "tollid not provided",400
    now=datetime.now()
    now=now+relativedelta(minutes=30)
    schedule = now.strftime('%Y-%m-%d %H:%M:%S')
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                        port=stored_val['db_port'],
                        database=stored_val['db'],
                        user=stored_val['db_user'],
                        password=stored_val['db_password'])
        cursor=connection.cursor()
        sql_query = "select tokenid from token_dist where tollid="+str(tollid)+\
                " and carid in (select carid from users where username='"+username+"')"\
                " and schedule<'"+schedule+"'"
        cursor.execute(sql_query)
        result=cursor.fetchall()
        if(len(result)==0):
            connection.close()
            return "tokenid not found",404
        connection.close()
        return result[0][0],200
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return "failed",500
    

@app.route('/login', methods=['POST'])
@cross_origin()
def login():
    print("login")
    if(flask.request.form==None):
        return "basic authorization required",400
    username=flask.request.form['username']
    password=flask.request.form['password']
    if(username.strip()=="" or password.strip()==""):
        return "invalid authorization arguments",400
    if(not isLoginValid(username,password)):
        return "incorrect credentials",401
    return "login successful",200

@app.route('/blacklistCar', methods=['POST'])
@cross_origin()
def blacklistCar():
    print("blacklistCar")
    if(flask.request.authorization==None):
        return "basic authorization required",400
    username=flask.request.authorization['username']
    password=flask.request.authorization['password']
    if(username.strip()=="" or password.strip()==""):
        return "invalid authorization arguments",400
    if(not isLoginValid(username,password)):
        return "incorrect credentials",401
    if(getPriviledge(username)!='t'):
        return "unauthorized to perform token fetch",401
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                        port=stored_val['db_port'],
                        database=stored_val['db'],
                        user=stored_val['db_user'],
                        password=stored_val['db_password'])
        cursor=connection.cursor()
        pword=hashlib.sha256(pword).hexdigest()
        sql_query = "update users set user_prividelige='b' where username='"+str(username)+"' and user_prividelige='d'"
        cursor.execute(sql_query)
        result=cursor.rowcount()
        if(result==0):
            connection.close()
            return "blacklisting failed",400
        connection.close()
        return "blacklisting successful",200
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return "blacklisting failed",500

@app.route('/carWrtToll', methods=['GET'])
@cross_origin()
def carWrtToll():
    print("carWrtToll")
    tollid=flask.request.args.get('tollid')
    if(tollid==None or tollid==""):
        return "tollid not provided",400
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                        port=stored_val['db_port'],
                        database=stored_val['db'],
                        user=stored_val['db_user'],
                        password=stored_val['db_password'])
        cursor=connection.cursor()
        sql_query = "select carid,license_no,make,model from cars where carid in (select carid from transit where tollid="+str(tollid)+")"
        cursor.execute(sql_query)
        result=cursor.fetchall()
        out=[]
        if(len(result)==0):
            connection.close()
            return flask.jsonify(out),200
        for row in result:
            tmp=dict()
            tmp['carid']=row[0]
            tmp['license_no']=row[1]
            tmp['make']=row[2]
            tmp['model']=row[3]
            out.append(tmp)
        connection.close()
        return flask.jsonify(out),200
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return flask.jsonify([]),500

@app.route('/scheduleLater', methods=['POST'])
@cross_origin()
def scheduleLater():
    print("scheduleLater")
    if(flask.request.authorization==None):
        return "basic authorization required",400
    username=flask.request.authorization['username']
    password=flask.request.authorization['password']
    if(username.strip()=="" or password.strip()==""):
        return "invalid authorization arguments",400
    if(not isLoginValid(username,password)):
        return "incorrect credentials",401
    if(flask.request.form==None):
        return "form arguements not passes",400
    tollid=flask.request.form["tollid"]
    if(tollid==None or tollid==""):
        return "tollid not provided",400
    schedule=flask.request.form["schedule"]
    if(schedule==None or schedule==""):
        return "schedule not provided",400
    carid=getCarid(username)
    if(carid==-1):
        return "carid not found associated with user",404
    tokenid=genTollToken()
    if(tokenid==-1):
        return "tokenid generation failed",500
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                        port=stored_val['db_port'],
                        database=stored_val['db'],
                        user=stored_val['db_user'],
                        password=stored_val['db_password'])
        cursor=connection.cursor()
        sql_query = "insert into token_dist values('"+tollid+"','"+carid+"','"+tokenid+"','"+schedule+"')"
        #tollid int,carid int,tokenid int,schedule timestamp
        cursor.execute(sql_query)
        if(cursor.rowcount()==0):
            connection.close()
            return "scheduling failed",500
        connection.close()
        return "successfully scheduled",200
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return "scheduling failed",500

@app.route('/tollSearch', methods=['GET'])
@cross_origin()
def tollSearch():
    print("tollSearch")
    minDist=None
    out=dict()
    if(flask.request.form==None):
        return "form arguements not passed",400
    locn=flask.request.form["locn"]
    loce=flask.request.form["loce"]
    if(locn==None or locn=="" or loce==None or loce==""):
        return "enough arguements not passed",400
    try:
        locn=float(locn)
        loce=float(loce)
    except:
        return "float values expected for locn and loce",400
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                        port=stored_val['db_port'],
                        database=stored_val['db'],
                        user=stored_val['db_user'],
                        password=stored_val['db_password'])
        cursor=connection.cursor()
        sql_query = "select * from tolls"
        cursor.execute(sql_query)
        result=cursor.fetchall()
        for row in result:
            tmp=abs(float(row[1])-float(locn))+abs(float(row[2])-float(loce))
            if(minDist==None or minDist>tmp):
                out["tollid"]=row[0]
                out["locn"]=row[1]
                out["loce"]=row[2]
                out["no_of_lanes"]=row[3]
        connection.close()
        return out,200
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return "failed to connect to database",500

@app.route('/getTolls', methods=['GET'])
@cross_origin()
def getTolls():
    print("getTolls")
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                        port=stored_val['db_port'],
                        database=stored_val['db'],
                        user=stored_val['db_user'],
                        password=stored_val['db_password'])
        cursor=connection.cursor()
        sql_query = "select * from tolls"
        cursor.execute(sql_query)
        result=cursor.fetchall()
        out=[]
        for row in result:
            tmp=dict()
            tmp["tollid"]=row[0]
            tmp["locn"]=row[1]
            tmp["loce"]=row[2]
            tmp["no_of_lanes"]=row[3]
            out.append(tmp)
        connection.close()
        return flask.jsonify(out),200
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return "failed to fetch tolls",500

@app.route('/historyView', methods=['GET'])
@cross_origin()
def historyView():
    print("historyView")
    if(flask.request.authorization==None):
        return "basic authorization required",400
    username=flask.request.authorization['username']
    password=flask.request.authorization['password']
    if(username.strip()=="" or password.strip()==""):
        return "invalid authorization arguments",400
    if(not isLoginValid(username,password)):
        return "incorrect credentials",401
    carid=getCarid(username)
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                        port=stored_val['db_port'],
                        database=stored_val['db'],
                        user=stored_val['db_user'],
                        password=stored_val['db_password'])
        cursor=connection.cursor()
        sql_query = "select * from transit where carid='"+str(carid)+"'"
        cursor.execute(sql_query)
        result=cursor.fetchall()
        out=[]
        for row in result:
            tmp=dict()
            tmp["transid"]=row[0]
            tmp["time_local"]=row[2]
            tmp["time_server"]=row[3]
            tmp["tollid"]=row[4]
            tmp["laneid"]=row[5]
            out.append(tmp)
        connection.close()
        return flask.jsonify(out),200
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return "failed to fetch transaction history",500

@app.route('/scheduleNow', methods=['POST'])
@cross_origin()
def scheduleNow():
    print("scheduleNow")
    if(flask.request.authorization==None):
        return "basic authorization required",400
    username=flask.request.authorization['username']
    password=flask.request.authorization['password']
    if(username.strip()=="" or password.strip()==""):
        return "invalid authorization arguments",400
    if(not isLoginValid(username,password)):
        return "incorrect credentials",401
    if(flask.request.form==None):
        return "form arguements not passed",400
    tollid=flask.request.form["tollid"]
    if(tollid==None or tollid==""):
        return "tollid not provided",400
    now=datetime.now()
    schedule = now.strftime('%Y-%m-%d %H:%M:%S')
    carid=getCarid(username)
    if(carid==-1):
        return "carid not found associated with user",404
    tokenid=genTollToken()
    if(tokenid==-1):
        return "tokenid generation failed",500
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                        port=stored_val['db_port'],
                        database=stored_val['db'],
                        user=stored_val['db_user'],
                        password=stored_val['db_password'])
        cursor=connection.cursor()
        sql_query = "insert into token_dist values('"+tollid+"','"+carid+"','"+tokenid+"','"+schedule+"')"
        #tollid int,carid int,tokenid int,schedule timestamp
        cursor.execute(sql_query)
        if(cursor.rowcount()==0):
            connection.close()
            return "scheduling failed",500
        connection.close()
        return "successfully scheduled",200
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return "scheduling failed",500

@app.route('/walletMoneyView', methods=['GET'])
@cross_origin()
def walletMoneyView():
    print("walletMoneyView")
    username=flask.request.args.get("username")
    if(username==None or username==""):
        return "username not passed",400
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                        port=stored_val['db_port'],
                        database=stored_val['db'],
                        user=stored_val['db_user'],
                        password=stored_val['db_password'])
        cursor=connection.cursor()
        sql_query = "select money from user where username='"+username+"'"
        cursor.execute(sql_query)
        result=cursor.fetchall()
        if(len(result)==0):
            connection.close()
            return "tokenid not found",404
        connection.close()
        return result[0][0],200
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return "failed to fetch wallet",500

@app.route('/addWalletMoney', methods=['GET'])
@cross_origin()
def addWalletMoney():
    print("addWalletMoney")
    money=flask.request.args.get("money")
    if(money==None or money==""):
        return "enough arguements not passed",400
    try:
        money=float(money)
    except:
        return "float values expected for money",400
    money=money*100
    username=stored_val['razorpay_user']
    password=stored_val['razorpay_password']
    data=dict()
    data["amount"]=int(money)
    data["type"]= "link"
    data["description"]="adding money to some user"
    response = requests.post('https://api.razorpay.com/v1/invoices',
        auth=HTTPBasicAuth(username,password),verify=False)
    if(response.status_code==200):
        out=dict()
        resp=json.loads(response.json())
        out["status"]="unpaid"
        out["link"]=resp["short_url"]
        out["inv_id"]=resp["id"]
        return out,200
    return "request to razorpay failed",response.status_code

@app.route('/updateWallet', methods=['GET'])
@cross_origin()
def updateWallet():
    print("updateWallet")
    invoice_id=flask.request.args.get('invoice_id')
    if(invoice_id==None or invoice_id.strip()==""):
        return "invoice_id not provided",400
    username=stored_val['razorpay_user']
    password=stored_val['razorpay_password']
    response = requests.get('https://api.razorpay.com/v1/invoices/'+str(invoice_id),
        auth=HTTPBasicAuth(username,password),verify=False)
    if(response.status_code==200):
        out=dict()
        resp=json.loads(response.json())
        if(resp['status']=="paid"):
            money_addition=int(float(resp["amount_paid"])/100)
            t=datetime.fromtimestamp(int(resp["paid_at"]))
            now=datetime.now()
            diff=now-t
            if(diff.days<0):
                diff=t-now
            if(diff.seconds>10*60):
                return "expired invoice",402
            try:
                connection = mysql.connector.connect(host=stored_val['db_host'],
                                port=stored_val['db_port'],
                                database=stored_val['db'],
                                user=stored_val['db_user'],
                                password=stored_val['db_password'])
                cursor=connection.cursor()
                sql_query = "select money from users where username='"+str(username)+"'"
                cursor.execute(sql_query)
                result=cursor.fetchall()
                if(len(result)==0):
                    connection.close()
                    return "user not found",404
                money=int(result[0][0])
                money+=money_addition
                sql_query = "update users set money="+str(money)+" where username='"+str(username)+"'"
                cursor.execute(sql_query)
                result=cursor.rowcount()
                if(result==0):
                    connection.close()
                    return "wallet update failed",500
                connection.close()
                return "wallet successfully updated",200
            except mysql.connector.Error as error:
                print("Failed to access mysql tables {}".format(error))
    return "request to razorpay failed",response.status_code

@app.route('/tokenSend', methods=['GET'])
@cross_origin()
def tokenSend():
    print("tokenSend")
    if(flask.request.authorization==None):
        return "basic authorization required",400
    username=flask.request.authorization['username']
    password=flask.request.authorization['password']
    if(username.strip()=="" or password.strip()==""):
        return "invalid authorization arguments",400
    if(not isLoginValid(username,password)):
        return "incorrect credentials",401
    tokenid=flask.request.args.get("tokenid")
    if(tokenid==None or tokenid==""):
        return "tokenid not provided",400
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                        port=stored_val['db_port'],
                        database=stored_val['db'],
                        user=stored_val['db_user'],
                        password=stored_val['db_password'])
        cursor=connection.cursor()
        sql_query = "select tokena,tokenb from tokens where tokenid in (select tokenid from token_dist where carid in (select carid from users where username='"+username+"'))"
        cursor.execute(sql_query)
        result=cursor.fetchall()
        if(len(result)==0):
            connection.close()
            return "tokenid not found",404
        connection.close()
        out=dict()
        out["tokena"]=result[0][0]
        out["tokenb"]=result[0][1]
        return out,200
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return "failed to fetch tokens",500

@app.route('/tollOpened', methods=['POST'])
@cross_origin()
def tollOpened():
    print("tollOpened")
    if(flask.request.authorization==None):
        return "basic authorization required",400
    username=flask.request.authorization['username']
    password=flask.request.authorization['password']
    if(username.strip()=="" or password.strip()==""):
        return "invalid authorization arguments",400
    if(not isLoginValid(username,password)):
        return "incorrect credentials",401
    if(flask.request.form==None):
        return "form arguements not passed",400
    tollid=flask.request.form["tollid"]
    laneid=flask.request.form["laneid"]
    carid=flask.request.form["carid"]
    time_local=flask.request.form["time_local"]
    tmp=[tollid,laneid,carid,time_local]
    if((None in tmp) or ("" in tmp)):
        return "enough form arguements not passed",400
    time_local=datetime.fromtimestamp(float(time_local)).strftime('%Y-%m-%d %H:%M:%S')
    time_server=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                        port=stored_val['db_port'],
                        database=stored_val['db'],
                        user=stored_val['db_user'],
                        password=stored_val['db_password'])
        cursor=connection.cursor()
        sql_query = "insert into transit values(null,'"+carid+"','"+time_local+"','"+time_server+"','"+tollid+"','"+laneid+"')"
        cursor.execute(sql_query)
        if(cursor.rowcount()==0):
            connection.close()
            return "transaction entry failed",500
        connection.close()
        return "successfully enterd transaction",200
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return "transaction entry failed",500

@app.route('/getTokens', methods=['GET'])
@cross_origin()
def getTokens():
    print("getTokens")
    if(flask.request.authorization==None):
        return "basic authorization required",400
    username=flask.request.authorization['username']
    password=flask.request.authorization['password']
    if(username.strip()=="" or password.strip()==""):
        return "invalid authorization arguments",400
    if(not isLoginValid(username,password)):
        return "incorrect credentials",401
    if(getPriviledge(username)!='t'):
        return "unauthorized to perform token fetch",401
    if(flask.request.form==None):
        return "form arguements not passed",400
    tollid=flask.request.form["tollid"]
    if(tollid==None or tollid==""):
        return "enough form arguements not passed",400
    try:
        connection = mysql.connector.connect(host=stored_val['db_host'],
                        port=stored_val['db_port'],
                        database=stored_val['db'],
                        user=stored_val['db_user'],
                        password=stored_val['db_password'])
        cursor=connection.cursor()
        sql_query = "select token_dist.carid,tokens.tokena,tokens.tokenb from tokens,token_dist where tokens.tokenid=token_dist.tokenid and token_dist.tollid='"+str(tollid)+"'"
        cursor.execute(sql_query)
        results=cursor.fetchall()
        out=dict()
        if(len(results)==0):
            connection.close()
            return "tokens not found",404
        else:
            for row in results:
                tmp=dict()
                tmp["tokena"]=row[1]
                tmp["tokenb"]=row[2]
                out[row[0]]=tmp
        connection.close()
        return out,200
    except mysql.connector.Error as error:
        print("Failed to access mysql tables {}".format(error))
    return "fetching tokens failed",500


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=9020,ssl_context=context)
