#!/usr/bin/env python
# -*- coding: utf-8 -*-

from threading import Thread
import logging
import subprocess
import shlex
from select import select
from crossplatform import CrossPlatform


class StreamIsNotAvailable(Exception):
    pass


class StreamServer(Thread):
    S_STOPPED = 0
    S_STARTING = 1
    S_STARTED = 2
    S_STOPPING = 3

    def __init__(self, args, callback):
        Thread.__init__(self)
        self._args = args
        self._callback = callback
        self._status = self.S_STOPPED

    def prepare_ffmpeg_process(self):
        args = self._args
        logging.debug('args: {}'.format(args))
        params = (args['video_input'] +
                  ' {audio_input}'
                  ' {video_output}'
                  ' {audio_output}'
                  ' -map 0 -map 1 -f flv tcp://127.0.0.1:9999'
                  ).format(video_input=args['video_input'],
                           video_output=args['video_output'],
                           audio_input=args['audio_input'],
                           audio_output=args['audio_output'],
                           x=args['x'],
                           y=args['y'],
                           w=args['w'],
                           h=args['h'])
        cmdline = ['ffmpeg'] + shlex.split(params)
        logging.info('ffmpeg start: ' + ' '.join(cmdline))
        return subprocess.Popen(cmdline,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

    def prepare_server_process(self):
        args = self._args
        logging.debug('args: {}'.format(args))
        params = (CrossPlatform.get().share_path('crtmpserver.lua'))
        cmdline = ['crtmpserver'] + shlex.split(params)
        logging.info('stream server start: ' + ' '.join(cmdline))
        return subprocess.Popen(cmdline,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

    def run(self):
        def ffmpeg_process(fd):
            if fd not in (self.p_ffmpeg.stdout, self.p_ffmpeg.stderr):
                return
            logging.debug('FFMPEG: ' + fd.readline().strip())

        def server_process(fd):
            if fd not in (self.p_server.stdout, self.p_server.stderr):
                return
            line = fd.readline().strip()
            logging.debug('SERVER: ' + line)
            if hasattr(self, '_url'):
                return
            index = line.find('Stream INLFLV(1) with name')
            if index < 0:
                return
            fields = line[index:].split('`', 2)
            if len(fields) != 3:
                logging.debug('server_process fields counts != 3: ' + str(fields))
                return
            self._url = "rtmp://{ip}:1936/flvplayback/" + fields[1]
            self.status = self.S_STARTED

        self.status = self.S_STARTING
        self.p_server = self.prepare_server_process()
        self.p_ffmpeg = self.prepare_ffmpeg_process()
        procs = (self.p_ffmpeg, self.p_server)
        logging.info('StreamServer Start')
        try:
            inputs = []
            for p in procs:
                inputs.extend((p.stdout, p.stderr))
            go = True
            while True:
                R, W, E = select(inputs, [], [])
                for i, p in enumerate(procs):
                    p.poll()
                    if p.returncode is not None:
                        logging.info('{} dead'.format(i))
                        go = False
                        break
                if not go:
                    break
                for fd in R:
                    ffmpeg_process(fd)
                    server_process(fd)
        except:
            pass
        self.stop()

    def stop(self):
        def kill_and_wait(p):
            try:
                p.kill()
            except OSError:
                # maybe already dead
                pass
            try:
                p.wait()
            except OSError:
                # maybe already recycled
                pass
        self.status = self.S_STOPPING
        map(kill_and_wait, (self.p_ffmpeg, self.p_server))
        logging.info('StreamServer stop')
        self.status = self.S_STOPPED

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
