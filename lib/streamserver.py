#!/usr/bin/env python
# -*- coding: utf-8 -*-

from threading import Thread
import logging
import subprocess
import shlex
from select import select
from crossplatform import CrossPlatform


class StreamServer(Thread):
    S_STOPPED = 0
    S_STARTING = 1
    S_STARTED = 2
    S_STOPPING = 3

    def __init__(self, args, callback):
        Thread.__init__(self)
        self._args = args
        self._callback = callback

    def prepare_ffmpeg_process(self):
        args = self._args
        logging.debug('args: {}'.format(args))
        params = (args['video_input'] +
                  ' {video_output}'
                  ' tcp://127.0.0.1:9999'
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
        params = (CrossPlatform.get().share_path('crtmpserver.lua'),)
        cmdline = ['crtmpserver'] + shlex.split(params)
        logging.info('stream server start: ' + ' '.join(cmdline))
        return subprocess.Popen(cmdline,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

    def run(self):
        self._callback(self.S_STARTING)
        self.p_server = self.prepare_server_process()
        self.p_ffmpeg = self.prepare_ffmpeg_process()
        procs = (self.p_ffmpeg, self.p_server)
        logging.info('StreamServer Start')
        self._callback(self.S_STARTED)
        try:
            inputs = []
            for p in procs:
                inputs.extend((p.stdout, p.stderr))
            while self.p_ffmpeg.returncode is None:
                R, W, E = select(inputs, [], [])
                for p in procs:
                    p.poll()
                    if p.returncode is not None:
                        break
                for fd in R:
                    prefix = ''
                    if fd in (self.p_ffmpeg.stdout, self.p_ffmpeg.stderr):
                        prefix = 'FFMPEG: '
                    if fd in (self.p_server.stdout, self.p_server.stderr):
                        prefix = 'SERVER: '
                    logging.debug(prefix + fd.readline().strip())
                    logging.debug(prefix + fd.readline().strip())
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
        self._callback(self.S_STOPPING)
        map(kill_and_wait, (self.p_ffmpeg, self.p_server))
        logging.info('StreamServer stop')
        self._callback(self.S_STOPPED)
