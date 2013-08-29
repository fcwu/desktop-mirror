#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import BaseHTTPServer
import simplejson
from threading import Thread
from common import DEFAULT_PORT


class HttpHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        logging.debug('{}'.format(self.path))
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("OK")

    def do_HEAD(self):
        """Serve a HEAD request."""
        self.send_error(404, "No found")

    def do_POST(self):
        """Serve a POST request."""
        self.data_string = self.rfile.read(int(self.headers['Content-Length']))
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        data = simplejson.loads(self.data_string)
        logging.debug('HTTP: json = {}'.format(data))
        try:
            url = data['params']['item']['file']
            self.wfile.write('{"return": "ok"}')
            self.server.callback((StreamReceiver.EVENT_ASK_TO_PLAY, url))
        except:
            self.wfile.write('{"return": "format invalid"}')


class StreamReceiver(Thread):
    EVENT_ASK_TO_PLAY = 0

    def __init__(self, callback):
        Thread.__init__(self, name='StreamReceiver')
        self.callback = callback

    def run(self):
        logging.info('StreamReceiver started')
        self.httpd = BaseHTTPServer.HTTPServer(('0.0.0.0', DEFAULT_PORT), HttpHandler)
        self.httpd.callback = self.callback
        try:
            self.httpd.serve_forever()
        except Exception as e:
            logging.warn(str(e))
        self.httpd.server_close()
        logging.info('StreamReceiver stoped')

    def stop(self):
        try:
            self.httpd.server_close()
        except:
            pass
        self.join()
