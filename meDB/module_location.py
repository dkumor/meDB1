from module_ratings import *
from module_data import *

from datetime import datetime
import sqlite3

class db_location(object):
    db_location_obj = []
    
    def __init__(self,usr,session,oid):
        self.usr = usr
        self.id = oid
        self.session = session
        self.db = self.usr.db
        self.db_location_obj.append(self)
        
        c = self.db.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='location';")
        if (c.fetchone()==None):
            c.execute("CREATE TABLE location (source text, lat real, long real, accuracy real, notes text, time text)")
        
        self.db.commit()
    def db_location_add(self,latitude,longitude,accuracy=float('NaN'),notes="",source="",time=None):
        latitude = float(latitude)
        longitude = float(longitude)
        print self.usr.user,": location("+str(latitude),","+str(longitude)+")"
        if (time==None):
            time = datetime.utcnow()
        c = self.db.cursor()
        c.execute("INSERT INTO location VALUES (?,?,?,?,?,?)",(source,latitude,longitude,accuracy,notes,time))
        
        self.db.commit()
        c.close()
        
        self.db_location_update()
        
    def db_location_get(self,num=1):
        c = self.db.cursor()
        result = c.execute("SELECT time,lat,long,notes,source,accuracy FROM location ORDER BY time DESC LIMIT ?",(num,))
        points = []
        for row in result:
            points.append({"time": row[0], "latitude": row[1], "longitude": row[2],"notes":row[3],"source":row[4],"accuracy":row[5]})
        return points
    
    def db_location_update(self):
        for i in self.db_location_obj:
            i.db_location_updated()
    def db_location_updated(self):
        pass
    def close(self):
        self.db_location_obj.remove(self)
    def __del__(self):
        self.close()

class locator(db_location,db_data,db_ratings):
    def __init__(self,usr,session,oid):
        db_location.__init__(self,usr,session,oid)
        db_data.__init__(self,usr,session,oid)
        db_ratings.__init__(self,usr,session,oid)
    def receive(self,msg):
        for i in msg:
            if (i=='a'):
                for pt in msg[i]:
                    latitude = pt["lat"]
                    longitude = pt["long"]
                    accuracy = float("NaN")
                    if ("accuracy" in pt):
                        accuracy = pt["accuracy"]
                    notes = ""
                    if ("n" in pt):
                        notes = pt["n"]
                    t = None
                    if ("t" in pt):
                        t = pt["t"]
                    self.db_location_add(latitude,longitude,accuracy,notes,"web",t)
            else:
                print i,msg[i]
    def init(self):
        return {}
    def module(self):
        return "locator"
    def db_ratings_updated(self):
        self.requestLoc()
    def db_data_updated(self):
        self.requestLoc()
    def requestLoc(self):
        self.session.send(self.id,{"locate":""})
    def close(self):
        db_location.close(self)
        db_data.close(self)
        db_ratings.close(self)
    #def db_location_updated(self):
    #    self.session.send(self.id,{"data":self.db_ratings_getCategories(6)})
    
