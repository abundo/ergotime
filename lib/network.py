#!/usr/bin/env python3

'''
Common network related utilities
'''

import urllib
import urllib.request
import json


class RequestWithMethod(urllib.request.Request):
    """
    Helper class, to implement HTTP GET, POST, PUT, DELETE
    """
    def __init__(self, *args, **kwargs):
        self._method = kwargs.pop('method', None)
        urllib.request.Request.__init__(self, *args, **kwargs)

    def get_method(self):
        return self._method if self._method else super(RequestWithMethod, self).get_method()


def request(method='GET', url=None, data=None, decode=False):
    '''
    Do a REST call
    '''
    respdata = None
    req = RequestWithMethod(url, method=method)
#     if self.dbconf.username is not None:
#         auth = '%s:%s' % (self.dbconf.username, self.dbconf.password)
#         auth = auth.encode("utf-8")
#         req.add_header(b"Authorization", b"Basic " + base64.b64encode(auth))
#    try:
    if data:
        resp = urllib.request.urlopen(req, urllib.parse.urlencode(data, encoding="utf-8").encode("ascii") )
    else:
        resp = urllib.request.urlopen(req)
#    except urllib.error.HTTPError as e:
#        raise bc.Error(1, "HTTPerror %s" % e)
#    except urllib.error.URLError as e:
#        raise bc.Error(1, "URLerror %s" % e)

    if decode:
        encoding = resp.headers.get_content_charset()
        if encoding is None:
            encoding = "utf-8"
#        try:
        tmp = resp.read().decode(encoding)
        respdata = json.loads(tmp)
        resp.close()
#        except ValueError:
#            raise bc.Error(1, "JSON ValueError for " + tmp)
#        except TypeError:
#            raise bc.Error(1, "JSON TypeError for " + tmp)

    return respdata, resp
