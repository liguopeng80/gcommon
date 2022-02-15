#!/usr/bin/python
# -*- coding: utf-8 -*-
# created: 2014-12-02

"""Demo and test program to verify WS server."""

import sys

from autobahn.twisted.websocket import WebSocketClientFactory
from autobahn.twisted.websocket import WebSocketClientProtocol
from twisted.internet import reactor
from twisted.python import log


class MyClientProtocol(WebSocketClientProtocol):
    def onOpen(self):
        print("connected to server")
        self.sendMessage("Hello, world!".encode("utf8"))

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode("utf8")))

    def onClose(self, was_clean, code, reason):
        print("connection closed: ", was_clean, code, reason)
        reactor.stop()  # @UndefinedVariable


def main():
    log.startLogging(sys.stdout)

    factory = WebSocketClientFactory()
    factory.protocol = MyClientProtocol

    reactor.connectTCP("127.0.0.1", 10086, factory)  # @UndefinedVariable
    reactor.run()  # @UndefinedVariable


# Test Codes
if __name__ == "__main__":
    main()
    print("Done")
