################################################################################
#
# Copyright (c) 2007-2008 Christopher J. Stawarz
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
################################################################################



import select
import threading
import time
import unittest

from pybonjour import *


class TestPyBonjour(unittest.TestCase):

    service_name = 'TestService'
    regtype = '_test._tcp.'
    port = 1111
    fullname = 'TestService._test._tcp.local.'
    timeout = 2

    def test_construct_fullname(self):
        # Check error handling
        self.assertRaises(ValueError, DNSServiceConstructFullName, None,
                          None)
        self.assertRaises(ctypes.ArgumentError, DNSServiceConstructFullName,
                          None, None, None)
        self.assertRaises(BonjourError, DNSServiceConstructFullName, None,
                          'foo', 'local.')

        fullname = DNSServiceConstructFullName(self.service_name,
                                               self.regtype, 'local.')

        self.assert_(isinstance(fullname, unicode))
        if not fullname.endswith(u'.'):
            fullname += u'.'
        self.assertEqual(fullname, self.fullname)

    def wait_on_event(self, sdRef, event):
        while not event.isSet():
            ready = select.select([sdRef], [], [], self.timeout)
            self.assert_(sdRef in ready[0], 'operation timed out')
            DNSServiceProcessResult(sdRef)

    def test_enumerate_domains(self):
        done = threading.Event()

        def cb(_sdRef, flags, interfaceIndex, errorCode, replyDomain):
            self.assertEqual(errorCode, kDNSServiceErr_NoError)
            self.assertEqual(_sdRef, sdRef)
            self.assert_(isinstance(replyDomain, unicode))
            if not (flags & kDNSServiceFlagsMoreComing):
                done.set()

        sdRef = \
            DNSServiceEnumerateDomains(kDNSServiceFlagsRegistrationDomains,
                                       callBack=cb)

        try:
            self.wait_on_event(sdRef, done)
        finally:
            sdRef.close()

    def register_record(self):
        done = threading.Event()

        def cb(_sdRef, flags, errorCode, name, regtype, domain):
            self.assertEqual(errorCode, kDNSServiceErr_NoError)
            self.assertEqual(_sdRef, sdRef)
            self.assert_(isinstance(name, unicode))
            self.assertEqual(name, self.service_name)
            self.assert_(isinstance(regtype, unicode))
            self.assertEqual(regtype, self.regtype)
            self.assert_(isinstance(domain, unicode))
            done.set()

        txt = TXTRecord()
        txt['foo'] = 'foobar'

        sdRef = DNSServiceRegister(name=self.service_name,
                                   regtype=self.regtype,
                                   port=self.port,
                                   txtRecord=txt,
                                   callBack=cb)

        return done, sdRef

    def test_register_browse_resolve(self):
        browse_done = threading.Event()
        resolve_done = threading.Event()

        def browse_cb(sdRef, flags, interfaceIndex, errorCode, serviceName,
                      regtype, replyDomain):
            self.assertEqual(errorCode, kDNSServiceErr_NoError)
            self.assertEqual(sdRef, browse_sdRef)
            self.assert_(flags & kDNSServiceFlagsAdd)
            self.assert_(isinstance(serviceName, unicode))
            self.assertEqual(serviceName, self.service_name)
            self.assert_(isinstance(regtype, unicode))
            self.assertEqual(regtype, self.regtype)
            self.assert_(isinstance(replyDomain, unicode))

            def resolve_cb(sdRef, flags, interfaceIndex, errorCode,
                           fullname, hosttarget, port, txtRecord):
                self.assertEqual(errorCode, kDNSServiceErr_NoError)
                self.assertEqual(sdRef, resolve_sdRef)
                self.assert_(isinstance(fullname, unicode))
                self.assertEqual(fullname, self.fullname)
                self.assert_(isinstance(hosttarget, unicode))
                self.assertEqual(port, self.port)
                self.assert_(isinstance(txtRecord, str))
                txt = TXTRecord.parse(txtRecord)
                self.assertEqual(txt['foo'], 'foobar')
                self.assert_(len(txtRecord) > 0)
                resolve_done.set()

            resolve_sdRef = DNSServiceResolve(0, interfaceIndex,
                                              serviceName, regtype,
                                              replyDomain, resolve_cb)

            try:
                self.wait_on_event(resolve_sdRef, resolve_done)
            finally:
                resolve_sdRef.close()

            browse_done.set()

        register_done, register_sdRef = self.register_record()

        try:
            self.wait_on_event(register_sdRef, register_done)

            browse_sdRef = DNSServiceBrowse(regtype=self.regtype,
                                            callBack=browse_cb)

            try:
                self.wait_on_event(browse_sdRef, browse_done)
            finally:
                browse_sdRef.close()
        finally:
            register_sdRef.close()

    def query_record(self, rrtype, rdata):
        # Give record time to be updated...
        time.sleep(5)

        done = threading.Event()

        def cb(_sdRef, flags, interfaceIndex, errorCode, fullname, _rrtype,
               rrclass, _rdata, ttl):
            self.assertEqual(errorCode, kDNSServiceErr_NoError)
            self.assertEqual(_sdRef, sdRef)
            self.assert_(isinstance(fullname, unicode))
            self.assertEqual(fullname, self.fullname)
            self.assertEqual(_rrtype, rrtype)
            self.assertEqual(rrclass, kDNSServiceClass_IN)
            self.assert_(isinstance(_rdata, str))
            self.assertEqual(_rdata, rdata)
            done.set()

        sdRef = DNSServiceQueryRecord(fullname=self.fullname,
                                      rrtype=rrtype,
                                      callBack=cb)

        try:
            self.wait_on_event(sdRef, done)
        finally:
            sdRef.close()

    def test_addrecord_updaterecord_removerecord(self):
        done, sdRef = self.register_record()

        try:
            self.wait_on_event(sdRef, done)

            RecordRef = DNSServiceAddRecord(sdRef,
                                            rrtype=kDNSServiceType_SINK,
                                            rdata='foo')
            self.assert_(RecordRef.value is not None)
            self.query_record(kDNSServiceType_SINK, 'foo')

            DNSServiceUpdateRecord(sdRef, RecordRef, rdata='bar')
            self.query_record(kDNSServiceType_SINK, 'bar')

            DNSServiceRemoveRecord(sdRef, RecordRef)
        finally:
            sdRef.close()

        self.assert_(RecordRef.value is None)

    def test_createconnection_registerrecord_reconfirmrecord(self):
        done = threading.Event()

        def cb(_sdRef, _RecordRef, flags, errorCode):
            self.assertEqual(errorCode, kDNSServiceErr_NoError)
            self.assertEqual(_sdRef, sdRef)
            self.assertEqual(_RecordRef, RecordRef)
            done.set()

        sdRef = DNSServiceCreateConnection()

        try:
            RecordRef = \
                DNSServiceRegisterRecord(sdRef,
                                         kDNSServiceFlagsUnique,
                                         fullname=self.fullname,
                                         rrtype=kDNSServiceType_SINK,
                                         rdata='blah',
                                         callBack=cb)
            self.assert_(RecordRef.value is not None)

            self.wait_on_event(sdRef, done)

            self.query_record(kDNSServiceType_SINK, 'blah')

            DNSServiceReconfirmRecord(fullname=self.fullname,
                                      rrtype=kDNSServiceType_SINK,
                                      rdata='blah')
        finally:
            sdRef.close()

        self.assert_(RecordRef.value is None)

    def test_txtrecord(self):
        txt = TXTRecord()
        self.assertEqual(len(txt), 0)
        self.assert_(not txt)
        self.assertEqual(str(txt), '\0')

        txt = TXTRecord({'foo': 'bar',
                         'baz': u'buzz',
                         'none': None,
                         'empty': ''})
        self.assertEqual(txt['foo'], 'bar')
        self.assertEqual(txt['BaZ'], 'buzz')
        self.assert_(txt['none'] is None)
        self.assertEqual(txt['empty'], '')

        self.assertEqual(len(txt), 4)
        self.assert_(txt)
        self.assertEqual(str(txt), str(TXTRecord.parse(str(txt))))

        txt['baZ'] = 'fuzz'
        self.assertEqual(txt['baz'], 'fuzz')
        self.assertEqual(len(txt), 4)

        self.assert_('foo' in txt)
        del txt['foo']
        self.assert_('foo' not in txt)

        self.assertRaises(KeyError, txt.__getitem__, 'not_a_key')
        self.assertRaises(KeyError, txt.__delitem__, 'not_a_key')
        self.assertRaises(ValueError, txt.__setitem__, 'foo\0', 'bar')
        self.assertRaises(ValueError, txt.__setitem__, '', 'bar')
        self.assertRaises(ValueError, txt.__setitem__, 'foo', 252 * 'b')

        # Example from
        # http://files.dns-sd.org/draft-cheshire-dnsext-dns-sd.txt
        data = '\x0Aname=value\x08paper=A4\x0EDNS-SD Is Cool'
        txt = TXTRecord.parse(data)
        self.assertEqual(str(txt), data)
        self.assert_(txt['DNS-SD Is Cool'] is None)

        data = '\x04bar=\nfoo=foobar\nfoo=barfoo\n=foofoobar'
        txt = TXTRecord.parse(data)
        self.assertEqual(len(txt), 2)
        self.assertEqual(txt['bar'], '')
        self.assertEqual(str(txt), '\x04bar=\nfoo=foobar')

        value = 254 * 'y'
        self.assertRaises(ValueError, TXTRecord().__setitem__, 'x', value)
        txt = TXTRecord(strict=False)
        txt['x'] = value
        self.assertEqual(len(str(txt)), 256)


if __name__ == '__main__':
    unittest.main()
