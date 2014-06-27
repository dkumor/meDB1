#!/usr/bin/python2

port = 8000
isTesting = True

import sqlite3
import uuid
import hashlib

import os
import stat
import mimetypes
import datetime
import time
import email

import tornado.httpserver
import tornado.websocket
import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.web import HTTPError

auth = None

try:
    auth = open('./auth.db','r')
    auth.close()
    auth = sqlite3.connect('./auth.db')
    cur = auth.cursor()
    cur.execute("DELETE FROM auth")
    cur.close()
except:
    print "Creating Database"
    auth = sqlite3.connect('./auth.db')
    cur = auth.cursor()
    cur.execute('CREATE TABLE users (email text, password text, salt text)')
    cur.execute('CREATE TABLE auth (user text, session text)')
    
     #Create the user DANIEL
    cur.execute("INSERT INTO users VALUES ('daniel@dkumor.com','675ed75f53f30ccc543a204182fe847daf1b8d51fe205341d5d43ad156d7427c9ee77466a12bd61fc7ae4bce7e79e7696f5b7f9ad28b665408277076c20a9beb','f9c16b026cd5404cb8ee78bfd4146736')")
    
    
    auth.commit()
    cur.close()
class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        if (isTesting): return "daniel@dkumor.com"
        global auth
        
        sesh = self.get_secure_cookie("session")
        if (sesh):
            c = auth.cursor()
            c.execute('SELECT user FROM auth WHERE (session=?)',(sesh,))
            usr = c.fetchone()
            if (usr):
                return usr[0]
            
        return None

class MainHandler(BaseHandler):
    def initialize(self):
        self.webapp = open("./app/app.html","r").read()
        
    @tornado.web.authenticated
    def get(self):
        self.write(self.webapp)
    
    @tornado.web.authenticated
    def post(self):
        self.write("POST is not available at this time")

class LoginHandler(BaseHandler):
    def initialize(self):
        self.loginpage = open("./app/login.html","r").read()
    def get(self):
        self.set_secure_cookie("session",str(uuid.uuid4()))
        self.write(self.loginpage)
    def post(self):
        global auth
        
        if not (self.get_secure_cookie("session")):
            self.set_secure_cookie("session",str(uuid.uuid4()))
        
        usr = self.get_argument("user")
        c = auth.cursor()
        c.execute('SELECT * FROM users WHERE (email=?)',(usr,))
        row = c.fetchone()
        if (row):
            if (row[1]==hashlib.sha512(self.get_argument("password")+ row[2]).hexdigest()):
                sesh = self.get_secure_cookie("session")
                c.execute("INSERT INTO auth VALUES (?,?)",(usr,sesh))
                print usr,": login"
                auth.commit()
                self.write("OK")
                return
            print "AUTH FAIL:",usr
            return
        else:
            print "UNKNOWN USER:",usr

class StaticHandler(tornado.web.RequestHandler):
    def initialize(self, path, default_filename=None):
        self.root = os.path.abspath(path) + os.path.sep
        self.default_filename = default_filename
        
    def head(self, path):
        self.get(path, include_body=False)
 
    def get(self, path, include_body=True):
        if os.path.sep != "/":
            path = path.replace("/", os.path.sep)
        abspath = os.path.abspath(os.path.join(self.root, path))
        # os.path.abspath strips a trailing /
        # it needs to be temporarily added back for requests to root/
        if not (abspath + os.path.sep).startswith(self.root):
            raise HTTPError(403, "%s is not valid", path)
        if os.path.isdir(abspath) and self.default_filename is not None:
            # need to look at the request.path here for when path is empty
            # but there is some prefix to the path that was already
            # trimmed by the routing
            if not self.request.path.endswith("/"):
                self.redirect(self.request.path + "/")
                return
            abspath = os.path.join(abspath, self.default_filename)
        if not os.path.exists(abspath):
            raise HTTPError(404)
        if not os.path.isfile(abspath):
            raise HTTPError(403, "%s is not a file", path)
 
        stat_result = os.stat(abspath)
        modified = datetime.datetime.fromtimestamp(stat_result[stat.ST_MTIME])
 
        self.set_header("Last-Modified", modified)
        self.set_header("Cache-Control", "public")
        mime_type, encoding = mimetypes.guess_type(abspath)
        if mime_type:
            self.set_header("Content-Type", mime_type)
 
        
 
        # Check the If-Modified-Since, and don't send the result if the
        # content has not been modified
        ims_value = self.request.headers.get("If-Modified-Since")
        if ims_value is not None:
            date_tuple = email.utils.parsedate(ims_value)
            if_since = datetime.datetime.fromtimestamp(time.mktime(date_tuple))
            if if_since >= modified:
                self.set_status(304)
                return
 
        if not include_body:
            return
        file = open(abspath, "rb")
        try:
            self.write(file.read())
        finally:
            file.close()
            

class QuerySocket(tornado.websocket.WebSocketHandler):
    #This method is required so that the clients can send message
    def sendMessage(self,msg):
        #self.write_message(json.dumps(msg))
        pass
        
    #Websocket connection stuff
    def open(self):
        print "Socket Open"
        
        pass
    
    def on_message(self,msg):
        print msg
    def on_close(self):
        print "socket Close"


path= os.path.join(os.path.dirname(os.path.realpath(__file__)), 'www')
application = tornado.web.Application([
    ("/",MainHandler),
    ("/login",LoginHandler),
    ("/q", QuerySocket),
    (r"/(.*)",StaticHandler,{"path": path})
],cookie_secret="u5ethsg36GDTy6w5rggtb45ywrgs/=wr",login_url="/login")

server = tornado.httpserver.HTTPServer(application,ssl_options = {
    "certfile": os.path.join("keys/server.crt"),
    "keyfile": os.path.join("keys/server.key")
})

server.listen(port)

print "Server is running on port %s" % port
try:
    tornado.ioloop.IOLoop.instance().start()
except KeyboardInterrupt:
    pass
print "\nShut Down Successfully\n"
