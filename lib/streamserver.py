#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from threading import Thread
import logging
import shlex
from subprocess import Popen, PIPE, STDOUT
import subprocess as sb
#from select import select
from crossplatform import CrossPlatform
from common import DEFAULT_PORT
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

ON_POSIX = 'posix' in sys.builtin_module_names


class StreamIsNotAvailable(Exception):
    pass


class Process(object):
    def __init__(self, server, name):
        self._server = server
        if name is None:
            name = 'Unknown'
        self._name = name

    def run(self, args):
        cmdline = self.prepare(args)
        logging.info(self._name + ' start: ' + ' '.join(cmdline))
        if CrossPlatform.get().is_linux():
            p = Popen(cmdline, stdout=PIPE, stderr=STDOUT)
        else:
            startupinfo = sb.STARTUPINFO()
            startupinfo.dwFlags |= sb.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
            p = Popen(cmdline, stdout=PIPE, stderr=STDOUT,
                      startupinfo=startupinfo)
        self.p = p
        return self

    def fds(self):
        return (self.p.stdout, self.p.stderr)

    def kill_and_wait(self):
        try:
            self.p.kill()
        except OSError:
            # maybe already dead
            pass
        try:
            self.p.wait()
        except OSError:
            # maybe already recycled
            pass

    @property
    def name(self):
        return self._name

    @property
    def returncode(self):
        self.p.poll()
        return self.p.returncode

    @property
    def stdout(self):
        return self.p.stdout

    @property
    def stderr(self):
        return self.p.stderr

    def is_dead(self):
        self.p.poll()
        return self.p.returncode is not None


class FfmpegCrtmpProcess(Process):
    def __init__(self, server):
        super(FfmpegCrtmpProcess, self).__init__(server, 'ffmpeg')

    def prepare(self, args):
        params = (args['video_input'] +
                  ' {audio_input}'
                  ' {video_output}'
                  ' {audio_output}'
                  ' -f flv tcp://127.0.0.1:' + str(DEFAULT_PORT + 1)
                  ).format(video_input=args['video_input'],
                           video_output=args['video_output'],
                           audio_input=args['audio_input'],
                           audio_output=args['audio_output'],
                           x=args['x'],
                           y=args['y'],
                           w=args['w'],
                           h=args['h'])
        return ['avconv'] + shlex.split(params)

    def process(self, line):
        if not line.startswith(self.name):
            return


class FfmpegTcpProcess(Process):
    PORT_OFFSET = 0

    def __init__(self, server):
        super(FfmpegTcpProcess, self).__init__(server, 'ffmpeg')

    def prepare(self, args):
        port = self.__class__.PORT_OFFSET + DEFAULT_PORT + 1
        self.__class__.PORT_OFFSET += 1
        params = (args['video_input'] +
                  ' {audio_input}'
                  ' {video_output}'
                  ' {audio_output}'
                  ' -f mpegts tcp://0.0.0.0:' + str(port) +
                  '?listen'
                  ).format(video_input=args['video_input'],
                           video_output=args['video_output'],
                           audio_input=args['audio_input'],
                           audio_output=args['audio_output'],
                           x=args['x'],
                           y=args['y'],
                           w=args['w'],
                           h=args['h'])
        self._server._url = 'tcp://{ip}:' + str(port)
        return ['avconv'] + shlex.split(params)

    def process(self, line):
        if not line.startswith(self.name):
            return
        if line.startswith(self.name + ':     Stream #'):
            self._server.status = self._server.S_STARTED


class ServerProcess(Process):
    def __init__(self, server):
        super(ServerProcess, self).__init__(server, 'server')

    def prepare(self, args):
        # http://osdir.com/ml/python.py2exe/2006-01/msg00008.html
        # shlex has path problem on Windows 7 x86_64
        # such as share/crtmpserver.lua -> sharecrtmpserver.lua
        params = [CrossPlatform.get().share_path('crtmpserver.lua'), ]
        return ['crtmpserver'] + params

    def process(self, line):
        if not line.startswith(self.name):
            return
        if hasattr(self, '_url'):
            return
        index = line.find('Stream INLFLV(1) with name')
        if index < 0:
            return
        fields = line[index:].split('`', 2)
        if len(fields) != 3:
            logging.debug('server_process fields counts != 3: {}'.
                          format(fields))
            return
        self._server._url = "rtmp://{ip}:1936/flvplayback/" + fields[1]
        self._server.status = self._server.S_STARTED


class StreamServer(Thread):
    S_STOPPED = 0
    S_STARTING = 1
    S_STARTED = 2
    S_STOPPING = 3

    def __init__(self, args, callback):
        Thread.__init__(self)
        args['w'] = int(str(args['w']))
        args['w'] += args['w'] % 2
        args['h'] = int(str(args['h']))
        args['h'] += args['h'] % 2
        self._args = args
        self._callback = callback
        self._status = self.S_STOPPED
        self._processes = []

    def _start_processes(self):
        if self._args['service'] == '_desktop-mirror._tcp':
            self._processes.append(ServerProcess(self).run(self._args))
            self._processes.append(FfmpegCrtmpProcess(self).run(self._args))
        else:
            self._processes.append(FfmpegTcpProcess(self).run(self._args))

    def run(self):
        def enqueue_output(out, queue, prefix):
            for line in iter(out.readline, b''):
                queue.put(prefix + ': ' + line)
            out.close()

        def create_monitor_thread(p):
            t = Thread(target=enqueue_output, args=(p.stdout, q, p.name))
            t.daemon = True  # thread dies with the program
            t.start()

        class ProcessDead(Exception):
            pass

        logging.info('StreamServer Start')

        self.status = self.S_STARTING
        self._start_processes()
        q = Queue()
        map(create_monitor_thread, self._processes)

        is_dead = False
        while not is_dead:
            try:
                #line = q.get_nowait()
                line = q.get(timeout=.5)
                line = line.strip()
                logging.debug(line)
                map(lambda p: p.process(line), self._processes)
            except Empty:
                pass
                #print('no output yet')
            else:  # got line
                # ... do something with line
                pass
            for p in self._processes:
                if p.is_dead():
                    logging.info('{} is dead'.format(p.name))
                    is_dead = True

        self.stop()

    def stop(self):
        self.status = self.S_STOPPING
        map(lambda p: p.kill_and_wait(), self._processes)
        logging.info('StreamServer stop')
        self.status = self.S_STOPPED

    @property
    def args(self):
        return self._args

    @property
    def url(self):
        if not hasattr(self, '_url'):
            raise StreamIsNotAvailable
        return self._url

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        if self._status == status:
            return
        self._status = status
        try:
            self._callback(self._status)
        except:
            pass
