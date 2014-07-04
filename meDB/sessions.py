import sqlite3
import os
import sys
import Queue
from auth import *

class Session():
    sessions = {}
    
    def __init__(self,sid,usr):
        self.user = None
        self.id = sid
        self.socket = None
        self.q = Queue.Queue()
        self.objects = {}
        
        if not (usr in User.users):
            User.users[usr] = User(usr)
        self.user = User.users[usr]
        
        self.user.addSession(self)
        
    def addSocket(self,s):
        print self.user.user,":",self.id,"Adding Socket"
        self.socket = s     #There can be only one connected socket at a time
    def remSocket(self):
        print self.user.user,":",self.id,"Close Socket"
        self.socket = None
    def push(self,obj,data):
        self.q.put({"i": obj,"d": data})
    def pop(self):
        if (self.socket):
            self.socket.send(self.makeMessage())
            
    def send(self,obj,data):
        self.push(obj,data)
        self.pop()
            
    def receive(self,msg):
        
        i = msg["i"]
        if (i=="@"):
            self.user.receive(msg["d"],self)
        else:
            if (i in self.objects):
                self.objects[i].receive(msg["d"])
        
    def makeMessage(self):
        msg = []
        while not self.q.empty():
            msg.append(self.q.get())
        return msg
        
    def postResponse(self,msg):
        self.receive(msg)
        return self.makeMessage()
        
    def addObject(self,obj):
        oid =str(uuid.uuid4().hex)
        
        obj.setSession(oid,self)
        
        self.objects[oid] = obj
        
        self.push("@",{"c":({"i": oid, "t": obj.module(),"o": obj.init()},)})
        return oid
        
    def delObject(self,obj):
        self.push("@",{"d":(oid,)})
        del self.objects[obj]
    def close(self,dologout=False):
        if (dologout):
            logout(self.id)
        else:
            delSession(self.id)
        del self.sessions[self.id]
    
class User():
    users = {}
    def __init__(self,user):
        self.user = user
        self.session = []
        self.objects = {}
        print self.user,": ACTIVE"
    def addSession(self,session):
        self.session.append(session.id)
        print self.user,":",session.id," ADD SESSION"
        #Initialize stuff
        
        #Start websocket to speed up talking
        #session.push("@",{"ws": True})
    def receive(self,msg,session):
        print self.user,":",session.id,
        for i in msg:
            print i,
            if (i=="close"):
                print "!",
                session.close()
                self.session.remove(session.id)
                break
            if (i=="action"):
                #print msg[i],
                if (msg[i]=="logout"):
                    print "LOGOUT",
                    session.close(True)
                    self.session.remove(session.id)
                    session.push("@",{"j":"window.location.replace('/login');"})
                else:
                    print msg[i],"??"
            else:
                print "?",
        print "."
        

"""
class Session():
    sessions = {}
    def __init__(self,sender,usr):
        self.s = sender
        self.id = str(uuid.uuid4().hex)
        self.send([{"i":"@","d":{"i":self.id}}])
        self.sessions[self.id] = self
        if not (usr in User.users):
            self.usr = User(usr)
            User.users[usr] = self.usr
        else:
            self.usr = User.users[usr]
        self.unum = User.users[usr].addSession(self)
    def send(self,msg):
        self.s.sendMessage(msg)
    def recv(self,msg):
        self.usr.recv(msg,self.unum)


class dataAdder():
    def __init__(self,usr,oid,sid):
        self.usr = usr
        self.oid = oid
        self.sid = sid
    def recv(self,msg,snum):
        for i in msg:
            if (i=='a'):
                for pt in msg[i]:
                    label = pt["l"]
                    value = pt["v"]
                    self.usr.addData(label,value,"","web")
                self.usr.put(self.oid,self.init(),snum)
                
            print i,msg[i]
    def getTopCategories(self):
        labels = []
        c = self.usr.db.cursor()
        result = c.execute("SELECT label FROM data_categories ORDER BY number DESC LIMIT ?",(6,))
        for row in result:
            labels.append(row[0])
        return labels
    def init(self):
        return {"labels":self.getTopCategories()}
    def type(self):
        return "adder"
    
class dataTable():
    def __init__(self,usr,oid,sid):
        self.usr = usr
        self.oid = oid
        self.sid = sid
        self.usr.registerAdd(self.oid)
    def recv(self,msg):
        print "TBLDATA"
        for i in msg:
            print i,msg[i]
    def getData(self):
        c = self.usr.db.cursor()
        result = c.execute("SELECT time,label,value FROM data ORDER BY time DESC LIMIT ?",(10,))
        points = []
        for row in result:
            points.append({"time": row[0], "label": row[1], "value": row[2]})
        return points
    def init(self):
        print "INIT"
        return {"data":self.getData()}
    def type(self):
        return "dtable"
    def event(self,typ):
        if (typ=="add"):
            
            
        
class User():
    users = {}
    def __init__(self,usr):
        self.user = usr
        self.sessions = []
        self.objects = {}
        self.ordering = []
        self.initDB()
        
        self.addObject(dataAdder)
        self.addObject(dataTable)
    def registedAdd(self,oid)
    def addObject(self,clas):
        oid =str(uuid.uuid4().hex)
        i = clas(self,oid)
        self.objects[oid] = i
        self.ordering.append(oid)
        
    def addData(self,label,value,notes,source=""):
        c = self.db.cursor()
        c.execute("INSERT INTO data VALUES (?,?,?,?,CURRENT_TIMESTAMP)",(label,value,source,notes))
        #Update the categories
        num = c.execute("SELECT number FROM data_categories WHERE (label=?)",(label,)).fetchone()
        if (num):
            c.execute("UPDATE data_categories SET number=? WHERE (label=?)",(int(num[0])+1,label))
        else:
            c.execute("INSERT INTO data_categories VALUES (?,?,'')",(label,1))
        self.db.commit()
        c.close()
        print self.user,": add(\""+label,"\",\""+value+"\")"
        
        
    def initDB(self):
        #Open or create database for user
        dbname = "./db/"+getDB(self.user)+".db"
        
        try:
            self.db = open(dbname,'r')
            self.db.close()
            self.db = sqlite3.connect(dbname)
        except:
            print self.user,": Make Database"
            self.db = sqlite3.connect(dbname)
            cur = self.db.cursor()
            cur.execute("CREATE TABLE data (label text, value text, source text, notes text, time text)")
            cur.execute("CREATE TABLE data_categories (label text, number integer, type text)")
            cur.execute("CREATE TABLE ratings (label text, value integer, notes text, time text)")
            cur.execute("CREATE TABLE ratings_categories (label text, number integer)")
            self.db.commit()
            cur.close()
         
    
    def addSession(self,s):
        self.sessions.append(s)
        print self.user,":",len(self.sessions),"session(s) (ADD)"
        
        return len(self.sessions)-1
    def remSession(self,s):
        self.sessions.remove(s)
        print self.user,":",len(self.sessions),"session(s) (REM)"
    def send(self,msg,snum):
        self.sessions[snum].send(msg)
        print msg
    def put(self,oid,msg,snum):
        self.sessions[snum].send([{"i": oid,"d":msg}])
    def recv(self,msg,snum):
        print self.user,":",
        #try:
        if (msg["i"]=="@"):
            d = msg["d"]
            for i in d:
            
                if ('h'==i):
                    print "h",
                elif ('r'==i):
                    print "r",
                elif ('u'==i):
                    print "u",
                elif ('d'==i):
                    print "d",
                elif ('i'==i):
                    print "i",
                    if (d[i]==""):
                        #If the id is an empty string, initialize the contents
                        initializer= []
                        for i in range(len(self.ordering)):
                            o = self.objects[self.ordering[i]]
                            initializer.append({"i": self.ordering[i], "t": o.type(), "o": o.init(),"l": {"i": self.ordering[i],"a": "","v": True}})
                        self.send([{"i":"@","d":{"c":initializer}}],snum)
                elif ('f'==i):
                    print 'f',
                else:
                    print i+"?",
                
        else:
            if msg["i"] in self.objects:
                ret = self.objects[msg["i"]].recv(msg["d"],snum)
                if (ret!=None):
                    self.send({"i": msg.i,"d": ret},snum)
        print "."
        #except:
        #    print "ERROR:",msg
"""
