from datetime import datetime
import sqlite3

class db_ratings(object):
    db_ratings_obj = []
    
    def __init__(self,usr,session,oid):
        self.usr = usr
        self.id = oid
        self.session = session
        self.db = self.usr.db
        self.db_ratings_obj.append(self)
        
        c = self.db.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ratings';")
        if (c.fetchone()==None):
            c.execute("CREATE TABLE ratings (label text, value integer, source text, notes text, time text)")
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ratings_categories';")
        if (c.fetchone()==None):
            c.execute("CREATE TABLE ratings_categories (label text, number integer, ratingsum integer)")
        self.db.commit()
    def db_ratings_add(self,label,value,notes="",source="",time=None):
        value = int(value)
        print self.usr.user,": ratings(\""+label,"\","+str(value)+")"
        if (time==None):
            time = datetime.utcnow()
        c = self.db.cursor()
        c.execute("INSERT INTO ratings VALUES (?,?,?,?,?)",(label,value,source,notes,time))
        #Update the categories
        num = c.execute("SELECT number,ratingsum FROM ratings_categories WHERE (label=?)",(label,)).fetchone()
        if (num!=None):
            c.execute("UPDATE ratings_categories SET number=?, ratingsum=? WHERE (label=?)",(int(num[0])+1,int(num[1])+int(value),label))
        else:
            c.execute("INSERT INTO ratings_categories VALUES (?,?,?)",(label,1,int(value)))
        self.db.commit()
        c.close()
        
        self.db_ratings_update()
        
    def db_ratings_get(self,num=10):
        c = self.db.cursor()
        result = c.execute("SELECT time,label,value,notes,source FROM ratings ORDER BY time DESC LIMIT ?",(num,))
        points = []
        for row in result:
            points.append({"time": row[0], "label": row[1], "value": row[2],"notes":row[3],"source":row[4]})
        return points
    def db_ratings_getCategories(self,num=5):
        labels = []
        c = self.db.cursor()
        result = c.execute("SELECT label,number,ratingsum FROM ratings_categories ORDER BY number DESC LIMIT ?",(num,))
        for row in result:
            labels.append(row)
        return labels
    def db_ratings_update(self):
        for i in self.db_ratings_obj:
            i.db_ratings_updated()
    def db_ratings_updated(self):
        pass
    def close(self):
        self.db_ratings_obj.remove(self)
    def __del__(self):
        self.close()

class ratingAdder(db_ratings):
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
                    self.db_ratings_add(label,value,notes,"web",t)
            else:
                print i,msg[i]
    def init(self):
        return {"data":self.db_ratings_getCategories(6)}
    def module(self):
        return "ratingdisplay"
    def db_ratings_updated(self):
        self.session.send(self.id,{"data":self.db_ratings_getCategories(6)})
    
class ratingCreator(db_ratings):
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
                    self.db_ratings_add(label,value,notes,"web",t)
                
            print i,msg[i]
    def init(self):
        return {"title": "Add Rating"}
    def module(self):
        return "adder"

class ratingTable(db_ratings):
        
    def receive(self,msg):
        print "TBLRatings",msg
        
    
    def init(self):
        return {"data": self.db_ratings_get(5),"title": "Recent Ratings"}
        
    def module(self):
        return "dtable"
    def db_ratings_updated(self):
        self.session.send(self.id,{"data":self.db_ratings_get()})
