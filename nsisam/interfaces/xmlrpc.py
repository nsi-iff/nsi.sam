from zope.interface import Interface

class IXmlrpc(Interface):

    def get_current_user():
        """Returns the user and password of request"""

    def xmlrpc_get(key):
        """ """

    def xmlrpc_set(key):
        """ """

    def xmlrpc_delete(key):
        """ """

    def xmlrpc_update(key, value):
        """ """

