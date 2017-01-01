#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Handle network IO
"""

import json
import urllib.parse
import urllib.request

from orderedattrdict import AttrDict


class NetworkException(Exception):
    pass


class RequestWithMethod(urllib.request.Request):
    """
    Helper class, to implement HTTP GET, POST, PUT, DELETE
    """
    def __init__(self, *args, **kwargs):
        self._method = kwargs.pop('method', None)
        urllib.request.Request.__init__(self, *args, **kwargs)

    def get_method(self):
        return self._method if self._method else super(RequestWithMethod, self).get_method()


def request(method='GET', url=None, param=None, data=None, decode=False):
    '''
    Do a REST call
    '''
    respdata = None
    if param:
        url += "?" + urllib.parse.urlencode(param)
    req = RequestWithMethod(url, method=method)
#     if self.dbconf.username is not None:
#         auth = '%s:%s' % (self.dbconf.username, self.dbconf.password)
#         auth = auth.encode("utf-8")
#         req.add_header(b"Authorization", b"Basic " + base64.b64encode(auth))
    # print("url", url)
    try:
        if data:
            resp = urllib.request.urlopen(req, urllib.parse.urlencode(data, encoding="utf-8").encode("ascii") )
        else:
            resp = urllib.request.urlopen(req)
    except urllib.error.URLError as err:
        raise NetworkException(err)

    if decode:
        encoding = resp.headers.get_content_charset()
        if encoding is None:
            encoding = "utf-8"
        tmp = resp.read().decode(encoding)
        resp.close()
        respdata = json.loads(tmp)
        if "data" in respdata:
            respdata = respdata["data"]
            # print("Reencoding http response")
            for ix in range(0, len(respdata)):
                respdata[ix] = AttrDict(respdata[ix])

    return respdata, resp
