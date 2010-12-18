from uuid import uuid4
from base64 import decodestring
from random import choice
from datetime import datetime
import cyclone.web
from twisted.internet import defer
from zope.interface import implements
from nsisam.interfaces.xmlrpc import IXmlrpc

class XmlrpcHandler(cyclone.web.XmlrpcRequestHandler):

    implements(IXmlrpc)

    allowNone = True

    def _get_current_user(self):
        auth = self.request.headers.get("Authorization")
        if auth:
          return decodestring(auth.split(" ")[-1]).split(":")

    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def xmlrpc_get(self, key):
        for db in iter(self.settings.db_list):
              value = yield db.get(key)
              if value:
                  defer.returnValue(value)
        else:
            defer.returnValue(False)

    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def xmlrpc_set(self, value):
        if not self.settings.auth.authenticate(*self._get_current_user()):
            defer.returnValue("Authorization Failed!")
        key = str(uuid4())
        db = choice(self.settings.db_list)
        today = datetime.today().strftime("%d/%m/%y %H:%M")
        user = self._get_current_user()[0]
        data_dict = {"data":value, "size":len(value), "date":today, "from_user": user}
        result = yield db.set(key, data_dict)
        defer.returnValue(key)

    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def xmlrpc_update(self, key, value):
        if not self.settings.auth.authenticate(*self._get_current_user()):
            defer.returnValue("Authorization Failed!")
        for db in self.settings.db_list:
            exists = yield db.exists(key)
            if exists:
                today = datetime.today().strftime("%d/%m/%y %H:%M")
                user = self._get_current_user()[0]
                data_dict = {"data":value, "size":len(value), "date":today, "from_user": user}
                result = yield db.set(key, data_dict)
                defer.returnValue(result)
        defer.returnValue(False)

    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def xmlrpc_delete(self, key):
        if not self.settings.auth.authenticate(*self._get_current_user()):
            defer.returnValue("Authorization Failed!")
        for db in self.settings.db_list:
            exists = yield db.exists(key)
            if exists:
              result = yield db.delete(key)
              if result:
                  defer.returnValue(True)
        defer.returnValue(False)

