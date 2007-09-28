"""
Chula apache handler
"""

import re

from mod_python import apache as APACHE

from chula import error, collection, config as CONFIG

def _handler(req, config):
    regexp = (r'^/'
              r'(?P<module>[_a-zA-Z]+)/'
              r'(?P<method>[_a-zA-Z]+)(?:\.py)?'
              r'(?:\?)?(?P<args>.*)')

    # Create the route which will map to a Python object
    route = {'module':'home', 'method':'index'}

    # Update any parts we should use based on the url
    parts = re.match(regexp, req.unparsed_uri)
    if not parts is None:
        route.update(parts.groupdict())

    # The first letter of a class is always uppercase (PEP8)
    route['class'] = route['module'].capitalize()

    if False:
        req.content_type = 'text/html'
        req.write(str(route))
        return APACHE.OK

    # Check to make sure the config is available
    if config.classpath == CONFIG.Config.UNSET:
        msg = ('[cfg.classpath] must be specified in your apache handler. '
               'See documentation for help on how to set this.')
        raise error.UnsupportedConfigError(msg)

    # Import the controller module
    classpath = '%s.' % config.classpath
    module =  __import__(classpath + route['module'],
                         globals(),
                         locals(),
                         [route['class']])

    # Instantiate the controller class from the module
    controller = getattr(module, route['class'], None)
    if controller is None:
        msg = """
        The %s module needs to have a class named %s!
        """ % (route['module'], route['class'])
        raise NameError, msg

    controller = controller(req, config)

    # Set the Apache content type
    req.content_type = controller.content_type

    # Lookup the requested method to make sure it exists
    method = getattr(controller, route['method'], None)
    if method is None:
        msg = '%s.%s()' % (route['class'], route['method'])
        raise error.ControllerMethodNotFoundError(msg)

    # Execute the method and write the returned string to request object.
    # We're manually casting the return as a string because Cheetah
    # templates seem to require it.
    req.write(str(method()))

    # Persist session
    controller.session.persist()

    # If we got here, all is well
    return APACHE.OK

def handler(fcn):
    def wrapper(req):
        config = fcn()
        return _handler(req, config)

    return wrapper

