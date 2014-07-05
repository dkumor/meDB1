import sqlite3
import os
import sys
import Queue

from auth import *

from module_data import *
from module_ratings import *
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
        
        for i in self.objects:
            self.objects[i].close()
        
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
        session.addObject(ratingAdder)
        session.addObject(dataAdder)
        session.addObject(dataTable)
        session.addObject(ratingTable)
        session.addObject(ratingCreator)
        
        
        
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
    
    

