from json import loads, dumps
from uuid import uuid4
from base64 import decodestring
from hashlib import sha1
from random import choice
from datetime import datetime
import functools
import cyclone.web
from twisted.internet import defer
from zope.interface import implements
from nsisam.interfaces.http import IHttp


def auth(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        auth_type, auth_data = self.request.headers.get('Authorization').split()
        if not auth_type == 'Basic':
            raise cyclone.web.HTTPAuthenticationRequired('Basic', realm='Restricted Access')
        user, password = decodestring(auth_data).split(':')
        # authentication itself
        if not self.settings.auth.authenticate(user, password):
            raise cyclone.web.HTTPError(401, 'Unauthorized')
        return method(self, *args, **kwargs)
    return wrapper


class HttpHandler(cyclone.web.RequestHandler):

    implements(IHttp)

    allowNone = True

    def _get_current_user(self):
        auth = self.request.headers.get('Authorization')
        if auth:
          return decodestring(auth.split(' ')[-1]).split(':')

    def _load_request_as_json(self):
        return loads(self.request.body)

    def _calculate_sha1_checksum(self, string):
        checksum_calculator = sha1()
        checksum_calculator.update(string)
        return checksum_calculator.hexdigest()

    @auth
    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def get(self):
        key = self._load_request_as_json().get('key')
        if not key:
            raise cyclone.web.HTTPError(400, 'Malformed request.')
        value = yield self.settings.db.get(key)
        if value:
            self.set_header('Content-Type', 'application/json')
            self.finish(value)
        else:
            raise cyclone.web.HTTPError(404, 'Key not found.')

    @auth
    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def put(self):
        self.set_header('Content-Type', 'application/json')
        key = str(uuid4())
        today = datetime.today().strftime(u'%d/%m/%y %H:%M')
        user = self._get_current_user()[0]
        value = self._load_request_as_json().get('value')
        if not value:
            raise cyclone.web.HTTPError(400, 'Malformed request.')
        data_dict = {u'data':value, u'date':today, u'from_user': user}
        result = yield self.settings.db.set(key, dumps(data_dict))
        checksum = self._calculate_sha1_checksum(dumps(data_dict))
        self.finish(cyclone.escape.json_encode({u'key':key, u'checksum':checksum}))

    @auth
    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def post(self):
        json_args = self._load_request_as_json()
        key = json_args.get('key')
        if not key:
            raise cyclobe.web.HTTPError(400, 'Malformed request.')
        exists = self.settings.db.exists(key)
        if exists:
            old_value_str = yield self.settings.db.get(key)
            value = json_args.get('value')
            today = datetime.today().strftime(u'%d/%m/%y %H:%M')
            user = self._get_current_user()[0]
            new_value = loads(old_value_str)
            new_value['data'] = value
            if not new_value.get(u'history'):
                new_value[u'history'] = list()
            new_value[u'history'].append({u'user':user, u'date':today})
            result = yield self.settings.db.set(key, dumps(new_value))
            checksum = self._calculate_sha1_checksum(dumps(new_value))
            self.set_header('Content-Type', 'application/json')
            self.finish(cyclone.escape.json_encode({u'key':key, u'checksum':checksum}))
        else:
            raise cyclone.web.HTTPError(404, 'Key not found.')

    @auth
    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def delete(self):
        key = yield self._load_request_as_json().get('key')
        if not key:
            raise cyclone.web.HTTPError(400, 'Malformed request.')
        exists = yield self.settings.db.exists(key)
        if exists and self.settings.db.delete(key):
            self.set_header('Content-Type', 'application/json')
            self.finish(cyclone.escape.json_encode({u'deleted':True}))
        else:
            raise cyclone.web.HTTPError(404, 'Key not found.')

