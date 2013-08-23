#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import logging
from datetime import datetime


class CommandException(Exception):
    def __init__(self, code, msg='Unknown'):
        self.code = code
        self.msg = msg

    def __str__(self):
        return 'Error ({0}): {1}'.format(self.code, self.msg)


class Command(object):
    """Simple subprocess. Popen wrapper to run shell commands and log their
       output
    """
    def __init__(self, command_str, silent=False, verbose=False):
        self.command_str = command_str
        self.silent = silent
        self.verbose = verbose

        self.process = None
        self.stdout = None
        self.stderr = None
        self.time = None

    def run(self):
        """Execute shell command and return output and status
        """
        logging.debug('Executing: {0!r}...'.format(self.command_str))

        self.process = subprocess.Popen(self.command_str,
                                        shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        start = datetime.now()
        result = self.process.communicate()
        end = datetime.now()
        self.time = end - start

        self.returncode = self.process.returncode
        if self.returncode != 0 or self.verbose:
            stdout, stderr = result
            message = ['Output:'
                       '- returncode:\n{0}'.format(self.returncode)]
            if stdout:
                if type(stdout) is bytes:
                    stdout = stdout.decode()
                message.append('- stdout:\n{0}'.format(stdout))
            if stderr:
                if type(stderr) is bytes:
                    stderr = stderr.decode()
                message.append('- stderr:\n{0}'.format(stderr))
            if not self.silent:
                logging.debug('\n'.join(message))

            self.stdout = stdout
            self.stderr = stderr

        if self.returncode != 0:
            raise CommandException(self.returncode,
                                   '{0}: {1}'.format(self.command_str,
                                                     self.stderr))

        return self
