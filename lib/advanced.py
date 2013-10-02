#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import wx
import wx.lib.newevent
from threading import Thread, Lock
import signal
import logging
from argparse import ArgumentParser, SUPPRESS
from ConfigParser import ConfigParser
from subprocess import Popen
import subprocess as sb
# CoreEventHandler
import socket
import urllib2
import json
import re

# local libraries
from common import APPNAME
from common import DEFAULT_PORT
from log import LoggingConfiguration
from command import Command
from crossplatform import CrossPlatform
from avahiservice import AvahiService
from streamserver import StreamServer
from streamreceiver import StreamReceiver
from areachooser import FrmAreaChooser

SomeNewEvent, EVT_SOME_NEW_EVENT = wx.lib.newevent.NewEvent()


class UiAdvanced(wx.Frame):
    def __init__(self, parent, title, core):
        super(UiAdvanced, self).__init__(parent, title=title,
                                         size=wx.DefaultSize,
                                         style=wx.DEFAULT_FRAME_STYLE)

        self._core = core
        self._core.register_listener(self)
        self._input = dict()

        self.Bind(EVT_SOME_NEW_EVENT, self.handler)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        # ~/Downloads/png2ico/png2ico icon.ico
        # desktop-mirror-64.png desktop-mirror-32.png desktop-mirror-16.png
        self.SetIcon(wx.Icon(CrossPlatform.get().share_path('icon.ico'),
                             wx.BITMAP_TYPE_ICO))

        self.InitUI()
        self.ConfigLoad()
        self.OnClickFullScreen(None)
        self.Centre()
        self.Show()

    def ConfigLoad(self):
        #filepath = CrossPlatform.get().user_config_path('ui.ini')
        #if not os.path.exists(filepath):
        filepath = CrossPlatform.get().system_config_path()
        logging.info('Loading config from ' + filepath)
        config = ConfigParser()
        config.read(filepath)
        if not config.has_section('input'):
            config.add_section('input')
        else:
            for w in self._input:
                if config.has_option('input', w):
                    self._input[w].SetValue(config.get('input', w))
        self.config = config

    def ConfigSave(self):
        config = self.config
        for w in self._input:
            config.set('input', w, self._input[w].GetValue())
        filepath = CrossPlatform.get().user_config_path('ui.ini')
        logging.info('Saving config to ' + filepath)
        with open(filepath, 'w') as configfile:
            config.write(configfile)

    def OnAvahi(self, data):
        hosts = self._core.hosts
        unique = []
        targets = self._core.targets
        widget = self._input['address']
        val = widget.GetValue()
        widget.Clear()
        #logging.debug('val: {}'.format(val))
        #logging.debug('hosts: {}'.format(hosts))
        for f in targets:
            for service in targets[f]:
                key = service['host']
                if key in unique:
                    continue
                unique.append(key)
                t = {'host': service['host'],
                     'service': service['service'],
                     'port': service['port'],
                     'ip': hosts[service['host']][0]}
                logging.debug('Adding one {}'.format(t))
                widget.Append('{} - {}:{}'.format(t['host'],
                                                  t['ip'],
                                                  t['port']))
                widget.SetClientData(widget.GetCount() - 1, t)
        # After appending, widget value will be cleared
        widget.SetValue(val)

    def OnSelection(self, data):
        self._input['x'].SetValue(str(data[0]))
        self._input['y'].SetValue(str(data[1]))
        self._input['w'].SetValue(str(data[2]))
        self._input['h'].SetValue(str(data[3]))
        self._input_rb_area.SetLabel('Area ({}x{}+{}+{})'.format(
                                     data[2],
                                     data[3],
                                     data[0],
                                     data[1]))

    def OnStreamServer(self, data):
        #status_str = {StreamServer.S_STOPPED: 'Stopped',
        #              StreamServer.S_STARTING: 'Start...',
        #              StreamServer.S_STARTED: 'Started',
        #              StreamServer.S_STOPPING: 'Stop...'}
        #self.statusbar.SetStatusText(status_str[data])
        if StreamServer.S_STARTED != data:
            return
        try:
            self._core.playme(self._target['ip'],
                              self._target['port'],
                              self._target['service'])
        except OSError:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)
            logging.warn('{} {} {}'.format(exc_type,
                                           fname[1],
                                           exc_tb.tb_lineno))
            msg = ('Connection Error\n'
                   ' - IP: {}\n'
                   ' - Port: {}\n'
                   ' - Service: {}').format(self._target['ip'],
                                            self._target['port'],
                                            self._target['service'])
            wx.MessageBox(msg, APPNAME,
                          style=wx.OK | wx.CENTRE | wx.ICON_ERROR)

    def OnStreamReceiver(self, data):
        if data[0] != StreamReceiver.EVENT_ASK_TO_PLAY:
            logging.warn('Unknown event: {}'.format(data))
            return
        dlg = wx.MessageDialog(self,
                               ('Stream Request. Accept?'),
                               APPNAME,
                               wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            if CrossPlatform.get().is_linux():
                cmdline = ['ffplay', data[1]]
                Popen(cmdline)
            else:
                startupinfo = sb.STARTUPINFO()
                startupinfo.dwFlags |= sb.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0
                cmdline = ['ffplay', data[1]]
                Popen(cmdline, startupinfo=startupinfo)

    def handler(self, evt):
        logging.debug('UI event {0}: {1}'.format(evt.attr1, evt.attr2))
        dispatch = {'avahi': self.OnAvahi,
                    'selection': self.OnSelection,
                    'server': self.OnStreamServer,
                    'srx': self.OnStreamReceiver}
        if evt.attr1 in dispatch:
            dispatch[evt.attr1](evt.attr2)

    def InitUI(self):
        def titleBox(hide=True):
            font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
            font.SetPointSize(16)

            hbox = wx.BoxSizer(wx.HORIZONTAL)
            text1 = wx.StaticText(panel, label="Desktop Mirror")
            text1.SetFont(font)
            hbox.Add(text1, flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=15)
            #hbox = wx.BoxSizer(wx.HORIZONTAL)
            #line = wx.StaticLine(panel)
            #hbox.Add(line, 1, flag=wx.EXPAND | wx.ALL, border=10)
            #vbox.Add(hbox, 1, wx.ALL, 5)
            if hide:
                map(lambda w: w.Hide(),
                    [w.GetWindow() for w in hbox.GetChildren()
                     if w.GetWindow() is not None])
            return hbox

        def targetBox():
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            #hbox.Add(wx.StaticText(panel, label="Target"),
            #         flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
            cb = wx.ComboBox(panel, 500, "127.0.0.1",
                             style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER
                             )
            cb.SetMinSize((250, 0))
            button1 = wx.Button(panel, label="Streaming")
            hbox.Add(cb, 1, flag=wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT,
                     border=0)
            hbox.Add(button1, 0, flag=wx.EXPAND | wx.LEFT | wx.ALIGN_RIGHT,
                     border=5)
            self._input['address'] = cb
            self._input_stream = button1

            self.Bind(wx.EVT_COMBOBOX, self.OnTargetChosen, cb)
            self.Bind(wx.EVT_TEXT, self.OnTargetKey, cb)
            self.Bind(wx.EVT_TEXT_ENTER, self.OnTargetKeyEnter, cb)
            self.Bind(wx.EVT_BUTTON, self.OnClickStream, button1)

            return hbox

        def geometryBox(hide=True):
            sb = wx.StaticBox(panel, label="Geometry")
            boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)

            hbox = wx.BoxSizer(wx.HORIZONTAL)

            tc1 = wx.TextCtrl(panel)
            tc2 = wx.TextCtrl(panel)
            tc3 = wx.TextCtrl(panel)
            tc4 = wx.TextCtrl(panel)
            self._input['x'] = tc1
            self._input['y'] = tc2
            self._input['w'] = tc3
            self._input['h'] = tc4

            hbox.Add(wx.StaticText(panel, label="X"),
                     flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
            hbox.AddSpacer(5)
            hbox.Add(tc1, 1, flag=wx.EXPAND)
            hbox.AddSpacer(10)
            hbox.Add(wx.StaticText(panel, label="Y"),
                     flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
            hbox.AddSpacer(5)
            hbox.Add(tc2, 1, flag=wx.EXPAND)
            hbox.AddSpacer(10)
            hbox.Add(wx.StaticText(panel, label="W"),
                     flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
            hbox.AddSpacer(5)
            hbox.Add(tc3, 1, flag=wx.EXPAND)
            hbox.AddSpacer(10)
            hbox.Add(wx.StaticText(panel, label="H"),
                     flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
            hbox.AddSpacer(5)
            hbox.Add(tc4, 1, flag=wx.EXPAND)

            boxsizer.Add(hbox, flag=wx.LEFT | wx.TOP | wx.EXPAND, border=5)

            hbox2 = wx.BoxSizer(wx.HORIZONTAL)
            button1 = wx.Button(panel, label="Select Area")
            hbox2.Add(button1, 1,
                      flag=wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT, border=15)
            button2 = wx.Button(panel, label="Full Screen")
            hbox2.Add(button2, 1, flag=wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT,
                      border=15)
            boxsizer.Add(hbox2, flag=wx.LEFT | wx.TOP | wx.EXPAND, border=5)

            self.Bind(wx.EVT_BUTTON, self.OnClickSelectionArea, button1)
            self.Bind(wx.EVT_BUTTON, self.OnClickFullScreen, button2)

            if hide:
                map(lambda w: w.Hide(),
                    [w.GetWindow() for w in hbox.GetChildren()
                    if w.GetWindow() is not None])
                map(lambda w: w.Hide(),
                    [w.GetWindow() for w in hbox2.GetChildren()
                    if w.GetWindow() is not None])
                sb.Hide()

            return boxsizer

        def videoBox(hide=True):
            sb = wx.StaticBox(panel, label="Video")
            boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
            fgs = wx.FlexGridSizer(3, 2, 5, 25)

            tc1 = wx.TextCtrl(panel)
            tc2 = wx.TextCtrl(panel)
            self._input['video_input'] = tc1
            self._input['video_output'] = tc2

            fgs.AddMany([(wx.StaticText(panel, label="input")),
                         (tc1, 1, wx.EXPAND),
                         (wx.StaticText(panel, label="output")),
                         (tc2, 1, wx.EXPAND)])

            fgs.AddGrowableCol(1, 1)
            boxsizer.Add(fgs, flag=wx.LEFT | wx.TOP | wx.EXPAND, border=5)

            if hide:
                map(lambda w: w.Hide(),
                    [w.GetWindow() for w in fgs.GetChildren()
                    if w.GetWindow() is not None])
                sb.Hide()
            return boxsizer

        def audioBox(hide=True):
            sb = wx.StaticBox(panel, label="Audio")
            boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
            fgs = wx.FlexGridSizer(3, 2, 5, 25)

            tc1 = wx.TextCtrl(panel)
            tc2 = wx.TextCtrl(panel)
            self._input['audio_input'] = tc1
            self._input['audio_output'] = tc2

            fgs.AddMany([(wx.StaticText(panel, label="input")),
                         (tc1, 1, wx.EXPAND),
                         (wx.StaticText(panel, label="output")),
                         (tc2, 1, wx.EXPAND)])

            fgs.AddGrowableCol(1, 1)
            boxsizer.Add(fgs, flag=wx.LEFT | wx.TOP | wx.EXPAND, border=5)

            if hide:
                map(lambda w: w.Hide(),
                    [w.GetWindow() for w in fgs.GetChildren()
                    if w.GetWindow() is not None])
                sb.Hide()
            return boxsizer

        def fullareaBox(hide=True):
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            rb1 = wx.RadioButton(panel, -1, 'Fullscreen', style=wx.RB_GROUP)
            hbox.Add(rb1, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
            rb2 = wx.RadioButton(panel, -1, 'Area')
            hbox.Add(rb2, 1, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)

            self._input_rb_fullscreen = rb1
            self._input_rb_area = rb2
            self.Bind(wx.EVT_RADIOBUTTON, self.OnClickFullArea, id=rb1.GetId())
            self.Bind(wx.EVT_RADIOBUTTON, self.OnClickFullArea, id=rb2.GetId())

            return hbox

        panel = wx.Panel(self, -1)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        vboxL = wx.BoxSizer(wx.VERTICAL)
        vboxR = wx.BoxSizer(wx.VERTICAL)

        png = wx.Image(CrossPlatform.get().share_path('desktop-mirror-64.png'),
                       wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        image = wx.StaticBitmap(panel, -1, png, (0, 0),
                                (png.GetWidth(), png.GetHeight()))
        vboxL.Add(image)

        flags = wx.EXPAND
        #vboxR.Add(titleBox(), 0, wx.ALL, 0)
        vboxR.Add(targetBox(), 1, flag=flags | wx.TOP, border=10)
        vboxR.Add(fullareaBox(), 0, flag=flags, border=10)
        for fn in (titleBox, geometryBox, videoBox, audioBox):
            fn()
            #vboxR.Add(fn(), 0, flag=flags, border=10)

        hbox.Add(vboxL, 0, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER, 10)
        hbox.Add(vboxR, 1, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER, 10)
        #self.statusbar = self.CreateStatusBar()

        panel.SetAutoLayout(True)
        panel.SetSizer(hbox)
        panel.Layout()
        panel.Fit()
        self.Fit()

    def InitUIFull(self):
        def titleBox():
            font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
            font.SetPointSize(16)

            hbox = wx.BoxSizer(wx.HORIZONTAL)
            text1 = wx.StaticText(panel, label="Desktop Mirror")
            text1.SetFont(font)
            hbox.Add(text1, flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=15)
            #hbox = wx.BoxSizer(wx.HORIZONTAL)
            #line = wx.StaticLine(panel)
            #hbox.Add(line, 1, flag=wx.EXPAND | wx.ALL, border=10)
            #vbox.Add(hbox, 1, wx.ALL, 5)
            return hbox

        def targetBox():
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            hbox.Add(wx.StaticText(panel, label="Target"),
                     flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
            cb = wx.ComboBox(panel, 500, "127.0.0.1",
                             style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER
                             )
            button1 = wx.Button(panel, label="Streaming")
            hbox.Add(cb, 1, flag=wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT,
                     border=15)
            hbox.Add(button1, 0, flag=wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT,
                     border=15)
            self._input['address'] = cb
            self._input_stream = button1

            self.Bind(wx.EVT_COMBOBOX, self.OnTargetChosen, cb)
            self.Bind(wx.EVT_TEXT, self.OnTargetKey, cb)
            self.Bind(wx.EVT_TEXT_ENTER, self.OnTargetKeyEnter, cb)
            self.Bind(wx.EVT_BUTTON, self.OnClickStream, button1)

            return hbox

        def geometryBox():
            sb = wx.StaticBox(panel, label="Geometry")
            boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)

            hbox = wx.BoxSizer(wx.HORIZONTAL)

            tc1 = wx.TextCtrl(panel)
            tc2 = wx.TextCtrl(panel)
            tc3 = wx.TextCtrl(panel)
            tc4 = wx.TextCtrl(panel)
            self._input['x'] = tc1
            self._input['y'] = tc2
            self._input['w'] = tc3
            self._input['h'] = tc4

            hbox.Add(wx.StaticText(panel, label="X"),
                     flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
            hbox.AddSpacer(5)
            hbox.Add(tc1, 1, flag=wx.EXPAND)
            hbox.AddSpacer(10)
            hbox.Add(wx.StaticText(panel, label="Y"),
                     flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
            hbox.AddSpacer(5)
            hbox.Add(tc2, 1, flag=wx.EXPAND)
            hbox.AddSpacer(10)
            hbox.Add(wx.StaticText(panel, label="W"),
                     flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
            hbox.AddSpacer(5)
            hbox.Add(tc3, 1, flag=wx.EXPAND)
            hbox.AddSpacer(10)
            hbox.Add(wx.StaticText(panel, label="H"),
                     flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
            hbox.AddSpacer(5)
            hbox.Add(tc4, 1, flag=wx.EXPAND)

            boxsizer.Add(hbox, flag=wx.LEFT | wx.TOP | wx.EXPAND, border=5)

            hbox = wx.BoxSizer(wx.HORIZONTAL)
            button1 = wx.Button(panel, label="Select Area")
            hbox.Add(button1, 1,
                     flag=wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT, border=15)
            button2 = wx.Button(panel, label="Full Screen")
            hbox.Add(button2, 1, flag=wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT,
                     border=15)
            boxsizer.Add(hbox, flag=wx.LEFT | wx.TOP | wx.EXPAND, border=5)

            self.Bind(wx.EVT_BUTTON, self.OnClickSelectionArea, button1)
            self.Bind(wx.EVT_BUTTON, self.OnClickFullScreen, button2)

            return boxsizer

        def videoBox():
            sb = wx.StaticBox(panel, label="Video")
            boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
            fgs = wx.FlexGridSizer(3, 2, 5, 25)

            tc1 = wx.TextCtrl(panel)
            tc2 = wx.TextCtrl(panel)
            self._input['video_input'] = tc1
            self._input['video_output'] = tc2

            fgs.AddMany([(wx.StaticText(panel, label="input")),
                         (tc1, 1, wx.EXPAND),
                         (wx.StaticText(panel, label="output")),
                         (tc2, 1, wx.EXPAND)])

            fgs.AddGrowableCol(1, 1)
            boxsizer.Add(fgs, flag=wx.LEFT | wx.TOP | wx.EXPAND, border=5)
            #fgs.GetContainingWindow().Hide()
            map(lambda w: w.Hide(), [w.GetWindow() for w in fgs.GetChildren()
                if w.GetWindow() is not None])
            sb.Hide()
            return boxsizer

        def audioBox():
            sb = wx.StaticBox(panel, label="Audio")
            boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
            fgs = wx.FlexGridSizer(3, 2, 5, 25)

            tc1 = wx.TextCtrl(panel)
            tc2 = wx.TextCtrl(panel)
            self._input['audio_input'] = tc1
            self._input['audio_output'] = tc2

            fgs.AddMany([(wx.StaticText(panel, label="input")),
                         (tc1, 1, wx.EXPAND),
                         (wx.StaticText(panel, label="output")),
                         (tc2, 1, wx.EXPAND)])

            fgs.AddGrowableCol(1, 1)
            boxsizer.Add(fgs, flag=wx.LEFT | wx.TOP | wx.EXPAND, border=5)
            map(lambda w: w.Hide(), [w.GetWindow() for w in fgs.GetChildren()
                if w.GetWindow() is not None])
            sb.Hide()
            return boxsizer

        panel = wx.Panel(self, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)

        flags = wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT
        vbox.Add(titleBox(), 0, wx.ALL, 0)
        vbox.Add(targetBox(), 0, flag=flags, border=10)
        vbox.Add(geometryBox(), 0, flag=flags, border=10)
        vbox.Add(videoBox(), 0, flag=flags, border=10)
        vbox.Add(audioBox(), 0, flag=flags, border=10)
        vbox.AddSpacer(10)

        self.statusbar = self.CreateStatusBar()

        panel.SetAutoLayout(True)
        panel.SetSizer(vbox)
        panel.Layout()
        panel.Fit()
        self.Fit()

    def StartStreamServer(self):
        def guess_target():
            target = None
            cb = self._input['address']
            hostname = cb.GetValue()
            m = re.search('^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(:\d{1,5})?$',
                          hostname)
            if target is None and m is not None:
                port = DEFAULT_PORT + 1 if m.group(2) is None else m.group(2)
                return {'ip': m.group(1), 'port': port,
                        'service': 'desktop-mirror'}
            for i in xrange(0, cb.GetCount()):
                if hostname != cb.GetString(i):
                    continue
                data = cb.GetClientData(i)
                return {'ip': data['ip'],
                        'port': data['port'],
                        'service': data['service']}
            return target

        core = self._core
        if not hasattr(self, '_target') or self._target is None:
            self._target = guess_target()
        if self._target is None:
            return False
        inp = self._input
        core.stream_server_start(video_input=inp['video_input'].GetValue(),
                                 audio_input=inp['audio_input'].GetValue(),
                                 video_output=inp['video_output'].GetValue(),
                                 audio_output=inp['audio_output'].GetValue(),
                                 x=inp['x'].GetValue(),
                                 y=inp['y'].GetValue(),
                                 w=inp['w'].GetValue(),
                                 h=inp['h'].GetValue(),
                                 ip=self._target['ip'],
                                 port=self._target['port'],
                                 service=self._target['service'])
        return True

    def OnCloseWindow(self, event):
        self.ConfigSave()
        self.Destroy()
        logging.debug('Quit UiAdvanced')

    def OnTargetChosen(self, evt):
        cb = evt.GetEventObject()
        data = cb.GetClientData(evt.GetSelection())
        self._target = {'ip': data['ip'], 'port': data['port'],
                        'service': data['service']}
        logging.info('OnTargetChosen: {} ClientData: {}'.format(
                     evt.GetString(), data))
        self._target_chosen_cache = evt.GetString()
        self._input_stream.Enable(True)

    def OnTargetKey(self, evt):
        logging.info('OnTargetKey: %s' % evt.GetString())
        if hasattr(self, '_target_chosen_cache') and \
                self._target_chosen_cache == evt.GetString():
            return
        self._target = None
        m = re.search('^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(:\d{1,5})?$',
                      evt.GetString())
        if m is None:
            ## Not available in 2.8
            # evt.GetEventObject().SetBackgroundColour(wx.Colour(255, 0, 0,
            #128));
            self._input_stream.Enable(False)
        else:
            port = DEFAULT_PORT + 1 if m.group(2) is None else m.group(2)
            self._target = {'ip': m.group(1), 'port': port,
                            'service': '_desktop-mirror._tcp'}
            self._input_stream.Enable(True)
        evt.Skip()

    def OnTargetKeyEnter(self, evt):
        logging.info('OnTargetKeyEnter: %s' % evt.GetString())
        evt.Skip()

    def OnClickSelectionArea(self, evt):
        self._core.launch_selection_area_process()

    def OnClickStream(self, evt):
        core = self._core
        obj = evt.GetEventObject()
        if core.is_streaming():
            core.stream_server_stop()
            obj.SetLabel('Stream')
            return
        if self.StartStreamServer():
            obj.SetLabel('Stop')
        else:
            cb = self._input['address']
            wx.MessageBox('{} is down'.format(cb.GetValue()),
                          APPNAME,
                          style=wx.OK | wx.CENTRE | wx.ICON_ERROR)

    def OnClickFullScreen(self, evt):
        geometry = wx.Display().GetGeometry()
        self._input['x'].SetValue(str(geometry[0]))
        self._input['y'].SetValue(str(geometry[1]))
        self._input['w'].SetValue(str(geometry[2]))
        self._input['h'].SetValue(str(geometry[3]))

    def OnClickFullArea(self, evt):
        logging.debug('Event: {}'.format(evt.GetId()))
        if evt.GetId() == self._input_rb_fullscreen.GetId():
            self.OnClickFullScreen(evt)
        else:
            self.OnClickSelectionArea(evt)


def sync(func):
    def wrapper(*args, **kv):
        self = args[0]
        self._lock.acquire()
        try:
            return func(*args, **kv)
        finally:
            self._lock.release()
    return wrapper


class Core(Thread):
    def __init__(self, args, extra_args):
        Thread.__init__(self)
        self._args = args
        self._extra_args = extra_args
        self._threads = []
        self._event_handler = CoreEventHandler()
        if CrossPlatform.get().is_linux():
            signal.signal(signal.SIGCHLD, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def is_streaming(self):
        if hasattr(self, '_stream_server') and self._stream_server is not None:
            return True
        return False

    def stream_server_start(self, *args, **kargs):
        if self.is_streaming():
            return
        logging.info('StreamServer start: {}'.format(kargs))
        self._stream_server = StreamServer(kargs, lambda data:
                                           self.handler('server', data))
        self._stream_server.start()

    def stream_server_stop(self):
        if hasattr(self, '_stream_server') and self._stream_server is not None:
            self._stream_server.stop()
            self._stream_server = None

    def playme(self, remote_ip, remote_port, service):
        def myip(remote_ip):
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((remote_ip, 0))
            return s.getsockname()[0]

        def xbmc():
            stream_url = self._stream_server.url.format(ip=myip(remote_ip))
            url = 'http://{}:{}/xbmcCmds/xbmcHttp?command=PlayFile({})'.format(
                  remote_ip, remote_port, stream_url)
            req = urllib2.Request(url)
            logging.debug('url = {}'.format(url))
            response = urllib2.urlopen(req)
            result = response.read()
            logging.debug('result: {}'.format(result))

        def desktop_mirror():
            stream_url = self._stream_server.url.format(ip=myip(remote_ip))
            data_as_json = json.dumps({'method': 'Player.Open',
                                      'id': 1, 'jsonrpc': '2.0',
                                      'params': {'item': {'file': stream_url}}}
                                      )
            url = 'http://{}:{}/jsonrpc'.format(remote_ip, remote_port)
            logging.debug('url = {}'.format(url))
            logging.debug('  json = {}'.format(data_as_json))
            req = urllib2.Request(url, data_as_json,
                                  {'Content-Type': 'application/json'})
            response = urllib2.urlopen(req)
            result = response.read()
            #logging.debug('result: {}'.format(result))
            result = json.loads(result)
            ##switch back to json with pretty format
            logging.debug(json.dumps(result, indent=4))
        logging.info('Got streaming url: {}'.
                     format(self._stream_server.url))
        if service == '_desktop-mirror._tcp':
            desktop_mirror()
        else:
            xbmc()

    @property
    def targets(self):
        if not hasattr(self, '_avahi_browse'):
            return dict()
        return self._avahi_browse.targets

    @property
    def hosts(self):
        if not hasattr(self, '_avahi_browse'):
            return dict()
        return self._avahi_browse.hosts

    def run(self):
        self._avahi_browse = AvahiService(lambda data:
                                          self.handler('avahi', data))
        self._stream_recever = StreamReceiver(lambda data:
                                              self.handler('srx', data))
        self._threads.append(self._avahi_browse)
        self._threads.append(self._stream_recever)

        for thread in self._threads:
            thread.start()
        for thread in self._threads:
            thread.join()

    def stop(self):
        for thread in self._threads:
            logging.debug('Stopping thread - {}'.format(thread.name))
            thread.stop()
        self.stream_server_stop()

    def launch_selection_area_process(self):
        SelectionArea(lambda data:
                      self.handler('selection', data)).start()

    def register_listener(self, ui_window):
        self._event_handler.register_listener(ui_window)

    def on_event_relay(self, event_name, data):
        self._event_handler.on_event_relay(event_name, data)

    def on_event_stream_ready(self, event_name, data):
        self._event_handler.on_event_stream_ready(event_name, data)

    def handler(self, obj_id, data):
        self._event_handler.handler(obj_id, data)

    def signal_handler(self, signum, frame):
        logging.info('signal: ' + str(signum))
        if signal.SIGTERM == signum:
            self.send_form_destroy()
        try:
            if CrossPlatform.get().is_linux():
                if signal.SIGCHLD == signum:
                    os.waitpid(-1, os.WNOHANG)
        except OSError:
            pass


class CoreEventHandler(object):
    def __init__(self):
        self._lock = Lock()
        self._listener = []

    def register_listener(self, ui_window):
        if ui_window not in self._listener:
            self._listener.append(ui_window)

    def on_event_relay(self, event_name, data):
        evt = SomeNewEvent(attr1=event_name, attr2=data)
        for listener in self._listener:
            wx.PostEvent(listener, evt)

    def on_event_stream_ready(self, event_name, data):
        self.on_event_relay(event_name, data)

    @sync
    def handler(self, obj_id, data):
        dispatch_map = {'avahi': self.on_event_relay,
                        'selection': self.on_event_relay,
                        'server': self.on_event_stream_ready,
                        'srx': self.on_event_relay}
        if obj_id in dispatch_map:
            dispatch_map[obj_id](obj_id, data)
            return
        logging.error('event not process: ' + obj_id)


class SelectionAreaExternalProgram(Thread):
    def __init__(self, callback):
        Thread.__init__(self)
        self._callback = callback

    def run(self):
        if os.path.isfile('lib/areachooser.py') and \
           os.access('lib/areachooser.py', os.X_OK):
            execution = 'lib/areachooser.py'
        else:
            execution = 'areachooser.py'
        cmd = Command(execution + ' "%x %y %w %h"', True, True).run()
        line = cmd.stdout.split()
        self._callback(line[0:4])


class SelectionArea(object):
    def __init__(self, callback):
        #Thread.__init__(self)
        self._callback = callback

    def run(self):
        frame = FrmAreaChooser(None, -1, 'Live Area', self._callback)
        frame.Show(True)
        frame.SetTransparent(100)
        frame.Center()

    def start(self):
        self.run()


class MyArgumentParser(object):
    """Command-line argument parser
    """
    def __init__(self):
        """Create parser object
        """
        description = ('IBS command line interface. '
                       '')

        epilog = ('')
        parser = ArgumentParser(description=description, epilog=epilog)
        log_levels = ['notset', 'debug', 'info',
                      'warning', 'error', 'critical']
        parser.add_argument('--log-level', dest='log_level_str',
                            default='info', choices=log_levels,
                            help=('Log level. '
                                  'One of {0} or {1} (%(default)s by default)'
                                  .format(', '.join(log_levels[:-1]),
                                          log_levels[-1])))
        parser.add_argument('--log-dir', dest='log_dir',
                            default=os.path.join(wx.StandardPaths_Get().
                                                 GetTempDir()),
                            help=('Path to the directory to store log files'))
        parser.add_argument('-z', '--zsync-input', dest='zsync_file',
                            default=None,
                            help=('file path of zsync input path'))
        parser.add_argument('-g', '--osd', action='store_true', dest="osd",
                            default=False,
                            help=('show OSD notify during monitor'))
        # Append to log on subsequent startups
        parser.add_argument('--append', action='store_true',
                            default=False, help=SUPPRESS)

        self.parser = parser

    def parse(self):
        """Parse command-line arguments
        """
        args, extra_args = self.parser.parse_known_args()
        args.log_level = getattr(logging, args.log_level_str.upper())

        # Log filename shows clearly the type of test (pm_operation)
        # and the times it was repeated (repetitions)
        args.log_filename = os.path.join(args.log_dir,
                                         ('{0}.log'
                                          .format(APPNAME)))
        return args, extra_args


def main():
    app = wx.App(redirect=False)
    app.SetAppName(APPNAME)
    args, extra_args = MyArgumentParser().parse()

    LoggingConfiguration.set(args.log_level, args.log_filename, args.append)
    logging.debug('Arguments: {0!r}'.format(args))
    logging.debug('Extra Arguments: {0!r}'.format(extra_args))

    core = Core(args, extra_args)
    try:
        core.start()
        UiAdvanced(None, title="Desktop Mirror", core=core)
        app.MainLoop()
    except KeyboardInterrupt:
        logging.info('^c')
    finally:
        core.stop()
        core.join()


if __name__ == '__main__':
    main()
