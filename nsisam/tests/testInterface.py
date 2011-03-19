import unittest
from nsisam.interfaces.auth import IAuth
from nsisam.interfaces.http import IHttp
from nsisam.auth import Authentication
from nsisam.http import HttpHandler

class TestInterface(unittest.TestCase):
    
    def test_auth(self):
        self.assertEquals(IAuth.implementedBy(Authentication), True)
        self.assertEquals(sorted(IAuth.names()), ['add_user',
                                                'authenticate',
                                                'del_user'])
    
    def test_handler(self):
        self.assertEquals(IHttp.implementedBy(HttpHandler), True)
        self.assertEquals(sorted(IHttp.names()), ['delete',
                                                'get',
                                                'get_current_user',
                                                'post',
                                                'put',])

if __name__ == "__main__":
    unittest.main()
