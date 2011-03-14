from json import loads
from uuid import uuid4
from base64 import decodestring
from random import choice
from datetime import datetime
import cyclone.web
from twisted.internet import defer
from zope.interface import implements
from nsisam.interfaces.http import IHttp

class HttpHandler(cyclone.web.RequestHandler):

    implements(IHttp)

    allowNone = True

    def _get_current_user(self):
        auth = self.request.headers.get("Authorization")
        if auth:
          return auth.split(" ")[-1].split(":")

    @defer.inlineCallbacks
    def _check_auth(self):
        if not self.settings.auth.authenticate(*self._get_current_user()):
            defer.returnValue("Authorization Failed!")
            
    def _load_request_as_json(self):
        return loads(self.request.body)

    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def get(self):
#        self._check_auth()
        self.set_header('Content-Type', 'application/json')
        for db in iter(self.settings.db_list):
            key = self._load_request_as_json().get('key')
            value = yield db.get(key)
            if value:
                value = eval(value)
                self.finish(cyclone.escape.json_encode(value))
        else:
            raise cyclone.web.HTTPError(404, "Key not found.")

    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def put(self):
#        self._check_auth()
        self.set_header('Content-Type', 'application/json')
        key = str(uuid4())
        db = choice(self.settings.db_list)
        today = datetime.today().strftime("%d/%m/%y %H:%M")
#        user = self._get_current_user()[0]
        value = self._load_request_as_json().get('value')
        data_dict = {"data":value, "size":len(value), "date":today}#, "from_user": user}
        result = yield db.set(key, data_dict)
        self.finish(cyclone.escape.json_encode({"key":key}))

    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def post(self):
#        self._check_auth()
        self.set_header('Content-Type', 'application/json')
        json_args = self._load_request_as_json()
        key = json_args.get('key')
        for db in self.settings.db_list:
            exists = yield db.exists(key)
            if exists:
                value = json_args.get('value')
                today = datetime.today().strftime("%d/%m/%y %H:%M")
 #               user = self._get_current_user()[0]
                data_dict = {"data":value, "size":len(value), "date":today}#, "from_user": user}
                result = yield db.set(key, data_dict)
                self.finish(cyclone.escape.json_encode({'key':key}))
            else:
                raise cyclone.web.HTTPError(404, "Key not found.")

    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def delete(self):
#        self._check_auth()
        self.set_header('Content-Type', 'application/json')
        for db in self.settings.db_list:
            key = self._load_request_as_json().get('key')
            exists = yield db.exists(key)
            if exists:
              result = yield db.delete(key)
              if result:
                  self.finish(cyclone.escape.json_encode({'deleted':True}))
        self.finish(cyclone.escape.json_encode({'deleted':False}))
