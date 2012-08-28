from json import loads, dumps
from uuid import uuid4
from base64 import decodestring, encodestring
from hashlib import sha512
from random import choice
from datetime import datetime
from os.path import join
import functools
import cyclone.web
from twisted.internet import defer
from twisted.python import log
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
            log.msg("Authentication failed.")
            log.msg("User '%s' and password '%s' not known." % (user, password))
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
        checksum_calculator = sha512()
        checksum_calculator.update(string)
        digest = checksum_calculator.hexdigest()
        del checksum_calculator
        return digest

    @auth
    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def get(self):
        key = self._load_request_as_json().get('key')
        if not key:
            log.msg("GET failed!")
            log.msg("Request didn't have a key to find.")
            raise cyclone.web.HTTPError(400, 'Malformed request.')
        value = yield self.settings.db.get(key)
        if value:
            value_json = loads(value)
            file_in_fs = value_json.get('file_in_fs')
            if file_in_fs:
                value_json['data']['file'] = encodestring(open(join(self.settings.file_path, key)).read())
                value = dumps(value_json)
            log.msg("Found the value for the key %s" % key)
            self.set_header('Content-Type', 'application/json')
            self.finish(value)
        else:
            log.msg("GET failed!")
            log.msg("Couldn't find any value for the key: %s" % key)
            raise cyclone.web.HTTPError(404, 'Key not found.')

    @auth
    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def put(self):
        self.set_header('Content-Type', 'application/json')
        key = yield str(uuid4())
        today = datetime.today().strftime(u'%d/%m/%y %H:%M')
        user = self._get_current_user()[0]
        value = self._load_request_as_json().get('value')
        if not value:
            log.msg("PUT failed!")
            log.msg("Request didn't have a value to store.")
            raise cyclone.web.HTTPError(400, 'Malformed request.')
        if isinstance(value, dict) and value.get('filename') and value.get('file') and value['filename'].endswith('.ogv'):
            self._store_file_in_fs(value['file'], key)
            del value['file']
            data_dict = {u'date':today, u'from_user': user, u'file_in_fs':True, u'data':value}
        else:
            data_dict = {u'data':value, u'date':today, u'from_user': user}
        json_dict = dumps(data_dict)
        del data_dict
        result = self.settings.db.set(key, json_dict)
        checksum = self._calculate_sha1_checksum(json_dict)
        del json_dict
        log.msg("Value stored at key %s." % key)
        self.finish(cyclone.escape.json_encode({u'key':key, u'checksum':checksum}))

    def _store_file_in_fs(self, content, key):
        file_ = open(join(self.settings.file_path, key), 'w+')
        file_.write(decodestring(content))

    @auth
    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def post(self):
        json_args = self._load_request_as_json()
        key = json_args.get('key')
        if not key:
            log.msg("POST failed!")
            log.msg("Request didn't have a key to update.")
            raise cyclobe.web.HTTPError(400, 'Malformed request.')
        exists = yield self.settings.db.exists(key)
        if exists:
            old_value_str = yield self.settings.db.get(key)
            value = json_args.get('value')
            if not value:
                log.msg("POST failed!")
                log.msg("Request didn't have a new value to store.")
                raise cyclone.web.HTTPError(400, 'Malformed request.')
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
            log.msg("Value updated at key %s." % key)
            self.finish(cyclone.escape.json_encode({u'key':key, u'checksum':checksum}))
        else:
            log.msg("POST failed!")
            log.msg("Couldn't find any value for the key: %s" % key)
            raise cyclone.web.HTTPError(404, 'Key not found.')

    @auth
    @defer.inlineCallbacks
    @cyclone.web.asynchronous
    def delete(self):
        key = yield self._load_request_as_json().get('key')
        if not key:
            log.msg("DELETE failed!")
            log.msg("Request didn't have a key to delete.")
            raise cyclone.web.HTTPError(400, 'Malformed request.')
        exists = yield self.settings.db.exists(key)
        if exists and self.settings.db.delete(key):
            self.set_header('Content-Type', 'application/json')
            log.msg("Key %s and its value deleted." % key)
            self.finish(cyclone.escape.json_encode({u'deleted':True}))
        else:
            log.msg("DELETE failed!")
            log.msg("Couldn't find any value for the key: %s" % key)
            raise cyclone.web.HTTPError(404, 'Key not found.')

