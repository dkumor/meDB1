from datetime import datetime
import sqlite3

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
        print self.usr.user,": add(\""+label,"\",\""+value+"\")"
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
    def close(self):
        self.db_data_obj.remove(self)
    def __del__(self):
        self.close()
        
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
            else:
                print i,msg[i]
    def init(self):
        return {"labels":self.db_data_getCategories(6)}
    def module(self):
        return "adder"
    def db_data_updated(self):
        self.session.send(self.id,{"labels":self.db_data_getCategories(6)})
            

