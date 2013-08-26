#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import wx
import wx.lib.newevent
from threading import Thread, Lock
import signal
import logging
from argparse import ArgumentParser, SUPPRESS
from ConfigParser import ConfigParser

# local libraries
from common import APPNAME
from log import LoggingConfiguration
from command import Command
from crossplatform import CrossPlatform
from avahiservice import AvahiService
from streamserver import StreamServer

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

        self.InitUI()
        self.ConfigLoad()
        self.Centre()
        self.Show()

    def ConfigLoad(self):
        filepath = CrossPlatform.get().user_config_path('ui.ini')
        if not os.path.exists(filepath):
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

    def handler(self, evt):
        def avahi(data):
            self._input['address'].Clear()
            targets = self._core.targets
            widget = self._input['address']
            for f in targets:
                for service in targets[f]:
                    widget.Append('{} - {} - {}'.format(service['host'],
                                                        service['service'],
                                                        service['port']))

        def selection(data):
            self._input['x'].SetValue(data[0])
            self._input['y'].SetValue(data[1])
            self._input['w'].SetValue(data[2])
            self._input['h'].SetValue(data[3])

        logging.debug('UI event {0}: {1}'.format(evt.attr1, evt.attr2))
        dispatch = {'avahi': avahi, 'selection': selection}
        if evt.attr1 in dispatch:
            dispatch[evt.attr1](evt.attr2)

    def InitUI(self):
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
            hbox.Add(wx.StaticText(panel, label="Target"), flag=wx.ALL,
                     border=15)
            cb = wx.ComboBox(panel, 500, "127.0.0.1:12345",
                             style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER
                             )
            button1 = wx.Button(panel, label="Streaming")
            hbox.Add(cb, 1, flag=wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT,
                     border=15)
            hbox.Add(button1, 0, flag=wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT,
                     border=15)
            self._input['address'] = cb

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

        panel.SetAutoLayout(True)
        panel.SetSizer(vbox)
        panel.Layout()
        panel.Fit()
        self.Fit()

    def OnCloseWindow(self, event):
        self.ConfigSave()
        self.Destroy()
        logging.debug('Quit UiAdvanced')

    def OnTargetChosen(self, evt):
        cb = evt.GetEventObject()
        data = cb.GetClientData(evt.GetSelection())
        logging.info('OnTargetChosen: {} ClientData: {}'.format(
                     evt.GetString(), data))

    def OnTargetKey(self, evt):
        logging.info('OnTargetKey: %s' % evt.GetString())
        evt.Skip()

    def OnTargetKeyEnter(self, evt):
        logging.info('OnTargetKeyEnter: %s' % evt.GetString())
        evt.Skip()

    def OnClickSelectionArea(self, evt):
        self._core.launch_selection_area_process()

    def OnClickStream(self, evt):
        core = self._core
        obj = evt.GetEventObject()
        inp = self._input
        if core.is_streaming():
            core.stream_server_stop()
            obj.SetLabel('Stream')
            return
        core.stream_server_start(video_input=inp['video_input'].GetValue(),
                                 audio_input=inp['audio_input'].GetValue(),
                                 video_output=inp['video_output'].GetValue(),
                                 audio_output=inp['audio_output'].GetValue(),
                                 x=inp['x'].GetValue(),
                                 y=inp['y'].GetValue(),
                                 w=inp['w'].GetValue(),
                                 h=inp['h'].GetValue())
        obj.SetLabel('Stop')

    def OnClickFullScreen(self, evt):
        geometry = wx.Display().GetGeometry()
        self._input['x'].SetValue(str(geometry[0]))
        self._input['y'].SetValue(str(geometry[1]))
        self._input['w'].SetValue(str(geometry[2]))
        self._input['h'].SetValue(str(geometry[3]))


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
        self._lock = Lock()
        self._args = args
        self._extra_args = extra_args
        self._threads = []
        self._listener = []
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
        self._stream_server = StreamServer(kargs, lambda data:
                                           self.process_event('server', data))
        self._stream_server.start()

    def stream_server_stop(self):
        if hasattr(self, '_stream_server') and self._stream_server is not None:
            self._stream_server.stop()
            self._stream_server = None

    @property
    def targets(self):
        if not hasattr(self, '_avahi_browse'):
            return dict()
        return self._avahi_browse.targets

    def run(self):
        self._avahi_browse = AvahiService(lambda data:
                                          self.process_event('avahi', data))
        self._threads.append(self._avahi_browse)

        for thread in self._threads:
            thread.start()
        for thread in self._threads:
            thread.join()

    def stop(self):
        for thread in self._threads:
            thread.stop()
        self.stream_server_stop()

    def launch_selection_area_process(self):
        SelectionArea(lambda data:
                      self.process_event('selection', data)).start()

    def register_listener(self, ui_window):
        if ui_window not in self._listener:
            self._listener.append(ui_window)

    @sync
    def process_event(self, obj_id, data):
        def event_avahi(data):
            evt = SomeNewEvent(attr1="avahi", attr2=data)
            for listener in self._listener:
                wx.PostEvent(listener, evt)

        def event_selection(data):
            evt = SomeNewEvent(attr1="selection", attr2=data)
            for listener in self._listener:
                wx.PostEvent(listener, evt)

        def event_server(data):
            evt = SomeNewEvent(attr1="server", attr2=data)
            for listener in self._listener:
                wx.PostEvent(listener, evt)

        dispatch_map = {'avahi': event_avahi,
                        'selection': event_selection,
                        'server': event_server}
        if obj_id in dispatch_map:
            dispatch_map[obj_id](data)
            return
        logging.error('event not process: ' + obj_id)

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


class SelectionArea(Thread):
    def __init__(self, callback):
        Thread.__init__(self)
        self._callback = callback

    def run(self):
        if os.path.isfile('xrectsel/xrectsel') and \
           os.access('xrectsel/xrectsel', os.X_OK):
            execution = 'xrectsel/xrectsel'
        else:
            execution = 'xrectsel'
        cmd = Command(execution + ' "%x %y %w %h"', True, True).run()
        line = cmd.stdout.split()
        self._callback(line[0:4])


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
        UiAdvanced(None, title="Desktop Mirror - Advanced", core=core)
        app.MainLoop()
    except KeyboardInterrupt:
        logging.info('^c')
    finally:
        core.stop()
        core.join()


if __name__ == '__main__':
    main()
