import unittest
import doctest
from chula import passwd
from chula.error import *

password = 'gitisbetterthancvs'
salt = 'git'
sha1 = 'gitda2250b53614f05ad5ec31a95ee1e0080ae22288'

class Test_passwd(unittest.TestCase):
    def test_new_password_with_known_hash(self):
        self.assertEquals(sha1, passwd.hash(password, salt=salt))

    def test_similar_passwords_are_unique_with_salt(self):
        self.assertNotEqual(passwd.hash(password, salt=salt),
                            passwd.hash('cookiemonseterMM', salt=salt))

    def test_similar_passwords_are_unique_without_salt(self):
        self.assertNotEqual(passwd.hash(password),
                            passwd.hash('cookiemonseterMM'))

    def test_malformed_password(self):
        self.assertRaises(MalformedPasswordError, passwd.hash, 'a')

    def test_new_matches_with_positive_match(self):
        self.assertTrue(passwd.matches(password, sha1))

    def test_new_matches_without_positive_match(self):
        self.assertFalse(passwd.matches('badpasswd', sha1))

def run_unittest():
    unittest.TextTestRunner(verbosity=2).run(get_tests())

def get_tests():
    tests = unittest.makeSuite(Test_passwd)
    tests.addTest(doctest.DocTestSuite(passwd))
    return tests

if __name__ == '__main__':
    run_unittest()
