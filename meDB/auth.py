import sqlite3
import uuid
import hashlib
auth = None
auth_loc = './db/auth.db'
try:
    auth = open(auth_loc,'r')
    auth.close()
    auth = sqlite3.connect(auth_loc)
    cur = auth.cursor()
    cur.execute("DELETE FROM auth")
    cur.close()
except:
    print "Creating Database"
    auth = sqlite3.connect(auth_loc)
    cur = auth.cursor()
    cur.execute('CREATE TABLE users (user text, password text, salt text,database text)')
    cur.execute('CREATE TABLE auth (user text, session text, skey text)')
    cur.execute('CREATE TABLE sessions (user text, session text,keepalive integer)')
    
     #Create the user DANIEL
    cur.execute("INSERT INTO users VALUES ('daniel@gmail.com','79e7696f5b7f9ad28b665408277076c20a9beb','f9c16b026cd5404cb8ee7fd4146736','188acfa4c342b881cadd7006ea47f8')")
    
    
    auth.commit()
    cur.close()

def getDB(user):
    c = auth.cursor()
    c.execute('SELECT database FROM users WHERE (user=?)',(user,))
    return c.fetchone()[0]
    
def setDB(user,db):
    c = auth.cursor()
    c.execute('UPDATE users SET database=? WHERE (user=?)',(db,user))
    db.commit()

def addUser(user,pwd):
    salt = str(uuid.uuid4().hex)
    db = str(uuid.uuid4().hex)
    ps = hashlib.sha512(pwd + salt)
    c = auth.cursor()
    c.execute("INSERT INTO users VALUES (?,?,?,?)",(user,ps,salt,db))
    db.commit()
    
def authUser(sesh):
    global auth
    if (sesh):
        c = auth.cursor()
        c.execute('SELECT user FROM sessions WHERE (session=?)',(sesh,))
        usr = c.fetchone()
        if (usr):
            return usr[0]
        
    return None

def hasSession(sesh,sid):
    global auth
    if (sesh and sid):
        c = auth.cursor()
        c.execute('SELECT user FROM auth WHERE (session=? AND skey=?)',(sesh,sid))
        usr = c.fetchone()
        if (usr):
            return usr[0]
        
    return None

def checkUser(usr,pwd):
    c = auth.cursor()
    c.execute('SELECT * FROM users WHERE (user=?)',(usr,))
    row = c.fetchone()
    if (row):
        if (row[1]==hashlib.sha512(pwd+ row[2]).hexdigest()):
            #Authentication successful
            return True
    return False

def makeSession(usr,session,keepalive=1):
    c = auth.cursor()
    skey = str(uuid.uuid4().hex)
    c.execute("INSERT INTO auth VALUES (?,?,?)",(usr,session,skey))
    if (authUser(session)==None):
        c.execute("INSERT INTO sessions VALUES (?,?,?)",(usr,session,keepalive))
    auth.commit()
    return skey
def delSession(skey):
    c = auth.cursor()
    c.execute("SELECT session FROM auth WHERE (skey=?)",(skey,))
    session = c.fetchone()[0]
    c.execute("DELETE FROM auth WHERE (skey=?)",(skey,))
    c.execute("SELECT COUNT(*) FROM auth WHERE (session=?)",(session,))
    if (c.fetchone()[0]==0):
        print "No sessions left, checking keepalive"
        c.execute("SELECT keepalive FROM sessions WHERE (session=?)",(session,))
        if (c.fetchone()[0]==0):
            print "DELETING SESSION"
            c.execute("DELETE FROM sessions WHERE (session=?)",(session,))
    auth.commit()
    
def logout(skey):
    c = auth.cursor()
    c.execute("SELECT session FROM auth WHERE (skey=?)",(skey,))
    session = c.fetchone()[0]
    c.execute("DELETE FROM auth WHERE (session=?)",(session,))
    c.execute("DELETE FROM sessions WHERE (session=?)",(session,))
    auth.commit()

def logoutUser(usr):
    c = auth.cursor()
    c.execute("DELETE FROM auth WHERE (user=?)",(usr,))
    c.execute("DELETE FROM sessions WHERE (user=?)",(usr,))
    auth.commit()
    auth.commit()
