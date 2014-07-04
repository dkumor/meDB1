#!/usr/bin/python2

port = 8000

from meDB.siteHandlers import *
from meDB.auth import *

import random
import json

import tornado.httpserver
import tornado.websocket
import tornado.httpserver
import tornado.ioloop


path= os.path.join(os.path.dirname(os.path.realpath(__file__)), 'www')
application = tornado.web.Application([
    ("/",MainHandler),
    ("/login",LoginHandler),
    ("/ws/(.*)", QuerySocket),
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
