#!/usr/bin/env python

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



from distutils.core import setup
import pybonjour


# Grab the description from the package's doc string
desc = pybonjour.__doc__.strip().split('\n\n')


setup(
    name = 'pybonjour',
    version = pybonjour.__version__,
    author = 'Christopher Stawarz',
    author_email = 'cstawarz@csail.mit.edu',
    url = 'http://o2s.csail.mit.edu/o2s-wiki/pybonjour',
    description = desc[0].strip(),
    long_description = desc[1].strip(),
    download_url = 'http://o2s.csail.mit.edu/download/pybonjour/',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: System :: Distributed Computing',
        'Topic :: System :: Networking',
        ],
    py_modules = ['pybonjour'],
    )
