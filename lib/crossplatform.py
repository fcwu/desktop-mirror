#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import wx
import wx.lib.newevent

APPNAME = 'desktop-mirror'


class CrossPlatform(object):
    @classmethod
    def get(cls):
        if hasattr(cls, 'sigleton'):
            return cls.singleton
        if sys.platform.find('linux') >= 0:
            cls.singleton = CrossPlatformUbuntu()
        else:
            cls.singleton = CrossPlatformWindows()
        return cls.singleton

    def user_config_path(self, filename):
        filepath = os.path.join(wx.StandardPaths_Get().GetUserDataDir(),
                                filename)
        if not os.path.exists(os.path.dirname(filepath)):
            os.mkdir(os.path.dirname(filepath))
        return filepath

    def system_config_path(self):
        pass

    def is_linux(self):
        if sys.platform.find('linux') >= 0:
            return True
        return False

    def is_windows(self):
        if sys.platform.find('win') >= 0:
            return True
        return False


class CrossPlatformWindows(CrossPlatform):
    def system_config_path(self):
        path = os.path.join('share', 'default.ini')
        if os.path.exists(path):
            return path
        return os.path.join(wx.StandardPaths_Get().GetInstallPrefix(),
                            'share', 'default.ini')

    def share_path(self, filename):
        return os.path.join(wx.StandardPaths_Get().GetInstallPrefix(),
                            'share', filename)


class CrossPlatformUbuntu(CrossPlatform):
    def system_config_path(self):
        path = os.path.join('share', 'default.ini')
        if os.path.exists(path):
            return path
        return '/usr/share/' + APPNAME + '/default.ini'

    def share_path(self, filename):
        return '/usr/share/' + APPNAME + '/' + filename
