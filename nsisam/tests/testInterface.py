import unittest
from nsisam.interfaces.auth import IAuth
from nsisam.interfaces.xmlrpc import IXmlrpc
from nsisam.auth import Authentication
from nsisam.xmlrpc import XmlrpcHandler

class TestInterface(unittest.TestCase):
    
    def test_auth(self):
        self.assertEquals(IAuth.implementedBy(Authentication), True)
        self.assertEquals(sorted(IAuth.names()), ['add_user',
                                                'authenticate',
                                                'del_user'])

    def test_handler(self):
        self.assertEquals(IXmlrpc.implementedBy(XmlrpcHandler), True)
        self.assertEquals(sorted(IXmlrpc.names()), ['get_current_user',
                                                'xmlrpc_delete',
                                                'xmlrpc_get',
                                                'xmlrpc_set',
                                                'xmlrpc_update'])
       
if __name__ == "__main__":
    unittest.main()
