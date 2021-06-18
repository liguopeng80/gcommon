#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2016-01-18

from twisted.python.components import proxyForInterface
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue, succeed
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer, IResponse

from zope.interface import implementer

from gcommon.utils.gjsonobj import JsonObject

import json

@implementer(IBodyProducer)
class StringProducer(object):

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass


class HTTPResponse(proxyForInterface(IResponse)):

    def __init__(self, original):
        self.original = original
        self.raw_body = None

    def raw_response(self):
        return self._original

    @inlineCallbacks
    def raw_content(self):
        if not self.raw_body:
            self.raw_body = yield readBody(self.original)
        returnValue(self.raw_body.decode('utf-8'))


class HTTPClient(object):
    Content_Type_XML = 'application/xml'
    Content_Type_Plain_Text = 'text/plain'
    Content_Type_JSON = 'application/json'
    Content_Type_URL_Encoded = 'application/x-www-form-urlencoded; charset=UTF-8'

    def __init__(self, agent, body_producer=StringProducer):
        self._agent = agent
        self._body_producer = body_producer

    def get(self, url, **kwargs):
        return self.request('GET', url, **kwargs)

    def post(self, url, data=None, **kwargs):
        return self.request('POST', url, data=data, **kwargs)
    
    def post_json(self, url, data, extra_headers=None, timeout=None):
        """data is a dict or list"""
        data = json.dumps(data).encode('utf-8')
        extra_headers = extra_headers or {}
        extra_headers.update({'content-type': self.Content_Type_JSON})
        if timeout:
            extra_headers.update({'timeout': timeout})
            
        return self.request('POST', url, data=data, **extra_headers)

    def put(self, url, data=None, **kwargs):
        return self.request('PUT', url, data=data, **kwargs)

    def delete(self, url, data=None, **kwargs):
        return self.request('DELETE', url, data=data, **kwargs)

    def request(self, method, url, **kwargs):
        # TODO: merge url params from kwargs['params']
        # TODO: parse headers from kwargs['header']
        headers = Headers({})
        for k, v in kwargs.items():
            if k != "data":
                headers.addRawHeader(str(k), str(v))

        # Get body producer for POST and PUT
        body_producer = None
        
        if isinstance(method, str):
            method = method.encode('utf-8')
            
        if isinstance(url, str):
            url = url.encode('utf-8')

        data = kwargs.get('data')
        if data:
            if isinstance(data, JsonObject):
                data = data.dumps()
            body_producer = self._body_producer(data)

        d = self._agent.request(method,
                                url,
                                headers=headers,
                                bodyProducer=body_producer) \
                       .addCallback(HTTPResponse)
        return d


# Test
if __name__ == "__main__":
    @inlineCallbacks
    def test():
        # response = yield HTTPClient(Agent(reactor)).get('https://www.baidu.com')
        response = yield HTTPClient(Agent(reactor)).post('http://127.0.0.1:9999')
        # response = yield HTTPClient(Agent(reactor)).post_json('http://127.0.0.1:9999', data=JsonObject({'a': 'b'}))
        response = yield response.raw_content()
        print(type(response))
        print(response)
        
    reactor.callLater(0, test)
    reactor.run()
    pass



