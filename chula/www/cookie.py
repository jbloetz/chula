"""
Cookie reads and writes cookies
"""

from mod_python import Cookie as Apache
from chula import guid
import time

class Cookie(object):
    def __init__(self, req, name, encryption_key, timeout):
        """
        @param req: Apache request object
        @type raq: mod_python.request
        """

        self.req = req
        self.name = name
        self.HMAC = encryption_key
        self.timeout = timeout
        self.cookies = Apache.get_cookies(self.req,
                                          Apache.MarshalCookie,
                                          secret=self.HMAC)

        # Create the reqeuested cookie if it doesn't exist
        if self.name not in self.cookies:
            self.persist(guid.guid())

    def exists(self):
        """
        Does the named cookie exist or not.
        @return: True/False
        """
        
        if self.cookies.has_key(self.name):
            return True
        else:
            return False
    
    def destroy(self):
        """
        Destroy cookie by saving the expire date to the past
        """
        
        c = Apache.MarshalCookie(self.name, '', self.HMAC)
        c.expires = time.time() - 60 * 1000
        c.path = '/' # /foo/bar would restrict the cookie to a directory
        Apache.add_cookie(self.req, c)

    def persist(self, value=None, path='/'):
        """
        Persist cookie to browser,
        @param value: Data to be saved in the cookie
        @type value: Dictionary, list, integer, string
        """
        if value is None:
            raise ValueError, "Please pass the value to be persisted"

        c = Apache.MarshalCookie(self.name, value, self.HMAC)
        if self.timeout > 0:
            c.expires = time.time() + 60 * self.timeout
        c.path = path # /foo/bar would restrict the cookie to a directory
        Apache.add_cookie(self.req, c)
        self.cookies[self.name] = c

    def value(self):
        """
        Return the value of the named cookie.
        @return: Dictionary, list, integer, string
        """
        
        try:
            value = self.cookies[self.name].value
            return value
        except KeyError, ex:
            msg = 'Requested cookie does not exist: %s' % self.name
            raise KeyError, msg

