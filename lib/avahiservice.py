#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import logging.handlers
import platform
import socket
from select import select
from threading import Thread, Timer, Lock

# local libraries
import pybonjour


class AvahiService(Thread):
    TIMEOUT = 5

    def __init__(self, callback):
        Thread.__init__(self)
        self._callback = callback
        self._stoped = True
        self._targets = dict()
        self._hosts = dict()
        self._input = []
        self._lock = Lock()
        self._queried = []
        self._resolved = []

    @property
    def targets(self):
        return self._targets

    def query_callback(self, sdRef, flags, interfaceIndex, errorCode,
                       fullname, rrtype, rrclass, rdata, ttl):
        #self.remove_sd(sdRef)
        if errorCode != pybonjour.kDNSServiceErr_NoError:
            logging.error('AvahiService: query_callback: error={}'.
                          format(errorCode))
            return

        self._queried.append(True)
        ip = socket.inet_ntoa(rdata)
        logging.debug('Queryed service:: fullname={}, IP={}'.
                      format(fullname, ip))
        if fullname not in self._hosts:
            self._hosts[fullname] = []
        if ip in self._hosts[fullname]:
            return
        self._hosts[fullname].append(ip)

    def resolve_callback(self, sdRef, flags, interfaceIndex, errorCode,
                         fullname, hosttarget, port, txtRecord):
        if errorCode != pybonjour.kDNSServiceErr_NoError:
            logging.error('AvahiService: resolve_callback: error={}'.
                          format(errorCode))
            return

        logging.debug('Resolved service: {}; {}; {}'.format(fullname,
                                                            hosttarget,
                                                            port))
        if fullname not in self._targets:
            self._targets[fullname] = []
        host = hosttarget[:-7]
        if host != platform.node():
            service = fullname[fullname.find('.') + 1:-7]
            target = {'host': host, 'port': port, 'service': service}
            self._targets[fullname].append(target)
        self.fire_event()

        self._lock.acquire()
        sd = pybonjour.DNSServiceQueryRecord(interfaceIndex=interfaceIndex,
                                             fullname=hosttarget,
                                             rrtype=pybonjour.kDNSServiceType_A,
                                             callBack=self.query_callback)
        old_input = self._input
        self._input = (sd,)
        self._lock.release()

        while not self._stoped and not self._queried:
            R, W, E = select(self._input, [], [], self.TIMEOUT)
            if self._stoped:
                break
            if not (R, W, E):
                break
            for sd in R:
                pybonjour.DNSServiceProcessResult(sd)
        else:
            self._queried.pop()

        self.remove_input()
        self._lock.acquire()
        self._input = old_input
        self._lock.release()

        self._resolved.append(True)

    def browse_callback(self, sdRef, flags, interfaceIndex, errorCode,
                        serviceName, regtype, replyDomain):
        if errorCode != pybonjour.kDNSServiceErr_NoError:
            logging.error('AvahiService: browse_callback: error={}'.
                          format(errorCode))
            return

        fullname = '{}.{}{}'.format(serviceName, regtype, replyDomain)
        if not (flags & pybonjour.kDNSServiceFlagsAdd):
            if fullname in self._targets:
                self.fire_event()
                del self._targets[fullname]
            if fullname in self._hosts:
                del self._hosts[fullname]
            logging.info('Service removed: {}'.format(fullname))
            return

        logging.debug('Service added {}; resolving'.format(fullname))
        self._lock.acquire()
        old_input = self._input
        sd = pybonjour.DNSServiceResolve(0,
                                         interfaceIndex,
                                         serviceName,
                                         regtype,
                                         replyDomain,
                                         self.resolve_callback)
        self._input = (sd,)
        self._lock.release()

        while not self._stoped and not self._resolved:
            R, W, E = select(self._input, [], [], self.TIMEOUT)
            if self._stoped:
                break
            if not (R, W, E):
                break
            for sd in R:
                pybonjour.DNSServiceProcessResult(sd)
        else:
            self._resolved.pop()

        self.remove_input()
        self._lock.acquire()
        self._input = old_input
        self._lock.release()

    def run(self):
        self._stoped = False

        self.register_service(platform.node(), '_desktop-mirror._tcp', 47767)
        self.listen_browse(('_xbmc-jsonrpc._tcp', '_asustor-boxee._tcp',
                            '_desktop-mirror._tcp'), self.browse_callback)

        self._stoped = True

    def register_service(self, name, regtype, port):
        def register_callback(sdRef, flags, errorCode, name, regtype,
                              domain):
            if errorCode == pybonjour.kDNSServiceErr_NoError:
                logging.info('Registered service:')
                logging.info('  name    = ' + name)
                logging.info('  regtype = ' + regtype)
                logging.info('  domain  = ' + domain)
            else:
                logging.error('Failed to register service: {}'.
                              format(errorCode))
            #logging.debug('remove sd in sub: ' + str(sdRef))
            self._done = True

        self._done = False
        self._lock.acquire()
        sd = pybonjour.DNSServiceRegister(name=name,
                                          regtype=regtype,
                                          port=port,
                                          callBack=register_callback)
        self._input.append(sd)
        self._lock.release()

        while not self._stoped and not self._done:
            R, W, E = select(self._input, [], [], self.TIMEOUT)
            if self._stoped:
                break
            if not (R, W, E):
                # timeout
                continue
            for sd in R:
                pybonjour.DNSServiceProcessResult(sd)

        self._lock.acquire()
        self._input = []
        self._lock.release()


    def listen_browse(self, services, cb):
        for regtype in services:
            sd = pybonjour.DNSServiceBrowse(regtype=regtype,
                                            callBack=cb)
            self._input.append(sd)

        try:
            while not self._stoped:
                R, W, E = select(self._input, [], [], self.TIMEOUT)
                if not (R, W, E):
                    continue
                for sd in R:
                    pybonjour.DNSServiceProcessResult(sd)
        except Exception as e:
            logging.warn(str(e))
        finally:
            self.remove_input()

    def stop(self):
        self.remove_input()
        self._resolved.append(True)
        self._queried.append(True)
        self._stoped = True
        if hasattr(self, '_fire_timer') and self._fire_timer is not None:
            self._fire_timer.cancel()
        self.join()

    def fire_event(self):
        def callback():
            self._callback(None)
        if hasattr(self, '_fire_timer') and self._fire_timer is not None:
            self._fire_timer.cancel()
        self._fire_timer = Timer(1.0, lambda: callback())
        self._fire_timer.start()

    def remove_input(self):
        self._lock.acquire()
        for sd in self._input:
            sd.close()
        self._input = []
        self._lock.release()
