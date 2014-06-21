#!/usr/bin/python2
portnum = 8000


from twisted.internet import ssl, reactor
from twisted.internet.protocol import Factory, Protocol
from twisted.web.server import Site
from twisted.web.static import File
from twisted.web.resource import Resource

import cgi		#Allows for sending posts to and fro
import sqlite3	#All website info is stored in a sqlite database
import hashlib	#For sending hashed IPs as identifiers
import json		#For wrapping up the sent data in json format
import uuid

"""
Database setup - the database is created if none exists and is initialized to be
ready for use
"""
db = None

try:	#Check for existence of the database
    db = open('./database.db','r')
    db.close()
    db = sqlite3.connect('./database.db')
    cur = db.cursor()
    cur.execute("DELETE FROM auth")
    cur.close()
except:
    #The database does not exist
    print "CREATING DATABASE"
    db = sqlite3.connect('./database.db')
    cur = db.cursor()
    cur.execute('CREATE TABLE users (email text, password text, salt text)')
    cur.execute('CREATE TABLE auth (user text, token text, session text)')
    cur.execute('CREATE TABLE data (user text, label text, value text, time text)')
    cur.execute('CREATE TABLE categories (user text, label text, number integer, time text)')
    cur.execute("INSERT INTO users VALUES ('daniel@dkumor.com','675ed75f53f30ccc543a204182fe847daf1b8d51fe205341d5d43ad156d7427c9ee77466a12bd61fc7ae4bce7e79e7696f5b7f9ad28b665408277076c20a9beb','f9c16b026cd5404cb8ee78bfd4146736')")
    db.commit()
    cur.close()

def auth(sid,token):
    global db
    c = db.cursor()
    c.execute('SELECT user FROM auth WHERE (token=? AND session=?)',(token,sid))
    usr = c.fetchone()
    c.close()
    if (usr):
        return usr[0]
    print "AUTH FAIL:",token
    return None

class Login(Resource):
    def render_GET(self,request):
        print request.args
        return "LOL"
    def render_POST(self,request):
        global db
        c = db.cursor()
        c.execute('SELECT * FROM users WHERE (email=?)',(request.args["user"][0],))
        row = c.fetchone()
        if (row):
            if (row[1]==hashlib.sha512(request.args["password"][0]+ row[2]).hexdigest()):
                key = str(uuid.uuid4())
                sesh = str(request.getSession().uid)
                c.execute("INSERT INTO auth VALUES (?,?,?)",(request.args["user"][0],key,sesh))
                print request.args["user"][0],": login"
                return key
            print "AUTH FAIL:",request.args["user"][0]
            return ""
        else:
            print "UNKNOWN USER:",request.args["user"][0]
            return ""

class Query(Resource):
    def render_GET(self,request):
        global db
        usr = auth(request.getSession().uid,request.args["key"][0])
        if (usr):
            c = db.cursor()
            result = c.execute("SELECT time,label,value FROM data WHERE (user=?) ORDER BY time DESC LIMIT ?",(usr,10))
            points = []
            for row in result:
                points.append({"time": row[0], "label": row[1], "value": row[2]})
            result = c.execute("SELECT label FROM categories WHERE (user=?) ORDER BY number DESC LIMIT ?",(usr,5))
            labels = []
            for row in result:
                labels.append(row[0])
            print usr,": GETQ"
            return json.dumps({"points": points, "labels": labels})
        return ""
    def render_POST(self,request):
        global db
        usr = auth(request.getSession().uid,request.args["key"][0])
        if (usr):
            label = None
            value = None
            try:
                label = request.args["label"][0]
                value = request.args["value"][0]
            except:
                print usr,": Malformed expression:",request.args
                return ""
            c = db.cursor()
            #Insert the datapoint
            c.execute("INSERT INTO data VALUES (?,?,?,CURRENT_TIMESTAMP)",(usr,label,value))
            #Update the categories
            num = c.execute("SELECT number FROM categories WHERE (user=? AND label=?)",(usr,label)).fetchone()
            if (num):
                c.execute("UPDATE categories SET number=?,time=CURRENT_TIMESTAMP WHERE (user=? AND label=?)",(int(num[0])+1,usr,label))
            else:
                c.execute("INSERT INTO categories VALUES (?,?,?,CURRENT_TIMESTAMP)",(usr,label,1))
            c.close()
            db.commit()
            print usr,": add ",label,value
            return "OK"
        return ""

if __name__ == '__main__':
    meDB = File('./www')
    
    meDB.putChild("mksession",Login())
    meDB.putChild("q",Query())
    reactor.listenSSL(8000, Site(meDB),
                      ssl.DefaultOpenSSLContextFactory(
            'keys/server.key', 'keys/server.crt'))
    print "READY"
    reactor.run()
    db.commit()
    print "Cleanly finished"
