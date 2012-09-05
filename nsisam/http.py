from json import loads, dumps
from uuid import uuid4
from base64 import decodestring, encodestring
from hashlib import sha512
from random import choice
from datetime import datetime
from os.path import join
from os import remove
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


class FileHandler(cyclone.web.RequestHandler):

    @cyclone.web.asynchronous
    def get(self, key):
        self.set_header('Content-Type', 'video/ogg')
        file_ = open(join(self.settings.file_path, key))
        self.write(file_.read())
        file_.close()
        del file_
        self.finish()


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
    def get(self):
        key = self._load_request_as_json().get('key')
        if not key:
            log.msg("GET failed!")
            log.msg("Request didn't have a key to find.")
            raise cyclone.web.HTTPError(400, 'Malformed request.')
        value = yield self.settings.db.get(key)
        if value:
            try:
                value_json = loads(value)
            except TypeError:
                sleep(1)
                try:
                    value_json = loads(value)
                except TypeError
                    raise cyclone.web.HTTPError(500)
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
    def put(self):
        self.set_header('Content-Type', 'application/json')
        key = yield str(uuid4())
        today = datetime.today().strftime(u'%d/%m/%y %H:%M')
        user = self._get_current_user()[0]
        request = self._load_request_as_json()
        value = request.get('value')
        expire = request.get('expire')
        if not value:
            log.msg("PUT failed!")
            log.msg("Request didn't have a value to store.")
            raise cyclone.web.HTTPError(400, 'Malformed request.')
        if self._is_file(value):
            self._store_file_in_fs(value, key)
            del value['file']
            data_dict = {u'date':today, u'from_user': user, u'file_in_fs':True, u'data':value}
        else:
            data_dict = {u'data':value, u'date':today, u'from_user': user}
        json_dict = dumps(data_dict)
        del data_dict
        result = yield self.settings.db.set(key, json_dict)
        checksum = self._calculate_sha1_checksum(json_dict)
        del json_dict
        log.msg("Value stored at key %s." % key)
        if expire:
            self.settings.db.expire(key, expire)
        self.finish(cyclone.escape.json_encode({u'key':key, u'checksum':checksum}))

    def _is_file(self, value):
        if isinstance(value, dict) and value.get('filename') and value.get('file') and value['filename'].endswith('.ogv'):
            return True
        return False

    def _store_file_in_fs(self, content, key, value):
        file_ = open(join(self.settings.file_path, key), 'w+')
        file_.write(decodestring(content))

    @auth
    @defer.inlineCallbacks
    def post(self):
        json_args = self._load_request_as_json()
        key = json_args.get('key')
        expire = json_args.get('expire')
        self._check_var_existence(key, 400, "Request didn't have a kew to update.",
                                  "Malformed request", "POST")
        exists = yield self.settings.db.exists(key)
        if exists:
            old_value_str = yield self.settings.db.get(key)
            value_to_store = json_args.get('value')
            self._check_var_existence(value_to_store, 400, "Request didn't have a new value to store.",
                                      "Malformed request", "POST")
            if self._is_file(value_to_store):
                    self._store_file_in_fs(value_to_store['file'], key)
                    del value_to_store['file']
            new_value = loads(old_value_str)
            del old_value_str
            new_value['data'] = value_to_store
            self._update_history(new_value)
            new_value_str = dumps(new_value)
            del new_value
            result = yield self.settings.db.set(key, new_value_str)
            checksum = self._calculate_sha1_checksum(new_value_str)
            del new_value_str
            if expire:
                self.settings.db.expire(key, expire)
            self.set_header('Content-Type', 'application/json')
            log.msg("Value updated at key %s." % key)
            self.finish(cyclone.escape.json_encode({u'key':key, u'checksum':checksum}))
        else:
            log.msg("POST failed!")
            log.msg("Couldn't find any value for the key: %s" % key)
            raise cyclone.web.HTTPError(404, 'Key not found.')

    def _check_var_existence(self, var, error_code, error_message, short_message, http_verb):
        if not var:
            log.msg("%s failed." % http_verb.upper())
            log.msg(error_message)
            raise cyclone.web.HTTPError(error_code, short_message)


    def _update_history(self, value):
        today = datetime.today().strftime(u'%d/%m/%y %H:%M')
        user = self._get_current_user()[0]
        if not value.get(u'history'):
            value[u'history'] = list()
        value[u'history'].append({u'user':user, u'date':today})

    @auth
    @defer.inlineCallbacks
    def delete(self):
        key = yield self._load_request_as_json().get('key')
        if not key:
            log.msg("DELETE failed!")
            log.msg("Request didn't have a key to delete.")
            raise cyclone.web.HTTPError(400, 'Malformed request.')
        exists = yield self.settings.db.exists(key)
        if exists and self.settings.db.delete(key):
            try:
                remove(join(self.settings.file_path, key))
            except OSError:
                pass
            self.set_header('Content-Type', 'application/json')
            log.msg("Key %s and its value deleted." % key)
            self.finish(cyclone.escape.json_encode({u'deleted':True}))
        else:
            log.msg("DELETE failed!")
            log.msg("Couldn't find any value for the key: %s" % key)
            raise cyclone.web.HTTPError(404, 'Key not found.')

