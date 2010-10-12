#!/usr/bin/env python
# coding: utf-8

import txredisapi
import cyclone.web
from twisted.application import service, internet
from nsisam.xmlrpc import XmlrpcHandler
from nsisam.auth import Authentication

CONF_FILE = "./sam.conf"

def get_storage(conf):
    return [txredisapi.lazyRedisConnectionPool("localhost", 6973),
        txredisapi.lazyRedisConnectionPool("localhost", 6974)]

def get_authenticator(conf):
    return Authentication("./passwd.db")

class SAM(cyclone.web.Application):
    
    def __init__(self):
        handlers = [
            (r"/xmlrpc", XmlrpcHandler),
        ]

        settings = {
            "db_list": get_storage(CONF_FILE),
            "auth": get_authenticator(CONF_FILE),
        }

        cyclone.web.Application.__init__(self, handlers, **settings)


application = service.Application("SAM")
srv = internet.TCPServer(8888, SAM(), interface="127.0.0.1")
srv.setServiceParent(application)
