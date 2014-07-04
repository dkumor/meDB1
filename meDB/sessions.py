import sqlite3
import os
import sys
import Queue
from datetime import datetime
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
        obj = obj(self.user,self,oid)
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
        self.obj = []
        #Open or create database for user
        dbname = "./db/"+getDB(self.user)+".db"
        self.db = sqlite3.connect(dbname)
                
        print self.user,": ACTIVE"
    def addSession(self,session):
        self.session.append(session.id)
        print self.user,":",session.id," ADD SESSION"
        
        #Initialize stuff
        session.addObject(dataAdder)
        session.addObject(dataTable)
        
        
        
        #Start websocket to speed up talking
        #session.push("@",{"ws": True})
        #OR, set refresh rate to 10 seconds
        #session.push("@",{"rr": 15000})
        
        
        
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
                    session.send("@",{"j":"window.location.replace('/login');"})
                else:
                    print msg[i],"??"
            else:
                print "?",
        print "."
    
    
class db_data(object):
    db_data_obj = []
    
    def __init__(self,usr,session,oid):
        self.usr = usr
        self.id = oid
        self.session = session
        self.db = self.usr.db
        self.db_data_obj.append(self)
        
        c = self.db.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='data';")
        if (c.fetchone()==None):
            c.execute("CREATE TABLE data (label text, value text, source text, notes text, time text)")
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='data_categories';")
        if (c.fetchone()==None):
            c.execute("CREATE TABLE data_categories (label text, number integer, type text)")
        self.db.commit()
    def db_data_add(self,label,value,notes="",source="",time=None):
        if (time==None):
            time = datetime.utcnow()
        c = self.db.cursor()
        c.execute("INSERT INTO data VALUES (?,?,?,?,?)",(label,value,source,notes,time))
        #Update the categories
        num = c.execute("SELECT number FROM data_categories WHERE (label=?)",(label,)).fetchone()
        if (num):
            c.execute("UPDATE data_categories SET number=? WHERE (label=?)",(int(num[0])+1,label))
        else:
            c.execute("INSERT INTO data_categories VALUES (?,?,'')",(label,1))
        self.db.commit()
        c.close()
        print self.usr.user,": add(\""+label,"\",\""+value+"\")"
        self.db_data_update()
        
    def db_data_get(self,num=10):
        c = self.db.cursor()
        result = c.execute("SELECT time,label,value,notes,source FROM data ORDER BY time DESC LIMIT ?",(num,))
        points = []
        for row in result:
            points.append({"time": row[0], "label": row[1], "value": row[2],"notes":row[3],"source":row[4]})
        return points
    def db_data_getCategories(self,num=5):
        labels = []
        c = self.db.cursor()
        result = c.execute("SELECT label FROM data_categories ORDER BY number DESC LIMIT ?",(num,))
        for row in result:
            labels.append(row[0])
        return labels
    def db_data_update(self):
        for i in self.db_data_obj:
            i.db_data_updated()
    def db_data_updated(self):
        pass
    
    def __del__(self):
        self.db_data_obj.remove(self)
        
class dataTable(db_data):
        
    def receive(self,msg):
        print "TBLDATA",msg
        
    
    def init(self):
        return {"data": self.db_data_get()}
        
    def module(self):
        return "dtable"
    def db_data_updated(self):
        self.session.send(self.id,{"data":self.db_data_get()})


class dataAdder(db_data):
    def receive(self,msg):
        for i in msg:
            if (i=='a'):
                for pt in msg[i]:
                    label = pt["l"]
                    value = pt["v"]
                    notes = ""
                    if ("n" in pt):
                        notes = pt["n"]
                    t = None
                    if ("t" in pt):
                        t = pt["t"]
                    self.db_data_add(label,value,notes,"web",t)
                
            print i,msg[i]
    def init(self):
        return {"labels":self.db_data_getCategories(6)}
    def module(self):
        return "adder"
    def db_data_updated(self):
        self.session.send(self.id,{"labels":self.db_data_getCategories(6)})
            

