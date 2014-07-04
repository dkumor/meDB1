from auth import *
from sessions import *

import os
import stat
import mimetypes
import datetime
import time
import email

import json

import tornado.web
import tornado.websocket
from tornado.web import HTTPError


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return authUser(self.get_secure_cookie("session"))



class QuerySocket(tornado.websocket.WebSocketHandler):
    #This method is required so that the clients can send message
    def send(self,msg):
        self.write_message(json.dumps(msg))
        
    #Websocket connection stuff
    def open(self,skey):
        self.usr= hasSession(self.get_secure_cookie("session"),skey)
        if (self.usr==None):
            #If the user is not authenticated, force a re-login through injected javascript
            print "Websocket Auth Failure"
            self.sendMessage([{"i":"@","d":{"j":"window.location.replace('/login');"}}])
            self.close()
        else:
            if not (skey in Session.sessions):
                Session.sessions[skey] = Session(skey,self.usr)
            self.session = Session.sessions[skey]
            self.session.addSocket(self)
        
    
    def on_message(self,msg):
        if (self.session!=None):
            self.session.receive(json.loads(msg))
            
    def on_close(self):
        self.session.remSocket()
        print "Closing socket"


class MainHandler(BaseHandler):
    def initialize(self):
        self.webapp = open("./app/app.html","r").read()
        
    @tornado.web.authenticated
    def get(self):
        #Checks if the session keys match, and if they do, writes the webpage, if not, redirects towards login,
        #   which will create a session key
        if (len(self.get_arguments("session")) > 0):
            if (hasSession(self.get_secure_cookie("session"),self.get_argument("session"))):
                self.write(self.webapp)
                return
        self.redirect("/login")
    
    def post(self):
        #At this point, we read the message contents - we already know which web browser the message belongs to,
        #   we just need to make sure that the key is also valid. The key is assigned to
        skey = self.get_argument("session")
        usr = hasSession(self.get_secure_cookie("session"),skey)
        if (usr!=None):
            if not (skey in Session.sessions):
                Session.sessions[skey] = Session(skey,usr)
            self.write(json.dumps(Session.sessions[skey].postResponse(json.loads(self.get_argument("q")))))
            return
            
        #The session is unknown: Tell the app to go to the login screen
        self.write(json.dumps([{"i":"@","d":{"j":"window.location.replace('/login');"}}]))


class LoginHandler(BaseHandler):
    def initialize(self):
        self.loginpage = open("./app/login.html","r").read()
    def get(self):
        res = self.get_current_user()
        if (res):
            #If there is already an authenticated
            # session cookie, create another session ID so that the user
            #can have multiple tabs of different data open on the same web browser.
            skey = makeSession(res,self.get_secure_cookie("session"))
            self.redirect("/?session="+skey)
        else:
            self.set_secure_cookie("session",str(uuid.uuid4().hex))
            self.write(self.loginpage)
    def post(self):
        global auth
        
        if not (self.get_secure_cookie("session")):
            self.set_secure_cookie("session",str(uuid.uuid4().hex))
        
        usr = self.get_argument("user")
        pwd = self.get_argument("password")
        keepalive = self.get_argument("keepalive")
        
        if (checkUser(usr,pwd)):
            #Auth successful, create a session for the user
            skey = makeSession(usr,self.get_secure_cookie("session"),keepalive)
            self.write(skey)
            return
        print "AUTH FAIL:",usr

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
