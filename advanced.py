#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx
import  wx.lib.newevent

SomeNewEvent, EVT_SOME_NEW_EVENT = wx.lib.newevent.NewEvent()
SomeNewCommandEvent, EVT_SOME_NEW_COMMAND_EVENT = wx.lib.newevent.NewCommandEvent()


class Example(wx.Frame):

    def __init__(self, parent, title):
        super(Example, self).__init__(parent, title=title)

        self.Bind(EVT_SOME_NEW_EVENT, self.handler)

        self.InitUI()
        self.Centre()
        self.Layout()
        self.Fit()
        self.Show()

    def handler(self, evt):
        # given the above constructed event, the following is true
        #evt.attr1 == "hello"
        #evt.attr2 == 654
        pass

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

        def geometryBox():
            sb = wx.StaticBox(panel, label="Geometry")
            boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)

            hbox = wx.BoxSizer(wx.HORIZONTAL)

            tc1 = wx.TextCtrl(panel)
            tc2 = wx.TextCtrl(panel)
            tc3 = wx.TextCtrl(panel)
            tc4 = wx.TextCtrl(panel)

            hbox.Add(wx.StaticText(panel, label="X"), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
            hbox.Add(tc1, 1, flag=wx.EXPAND)
            hbox.Add(wx.StaticText(panel, label="Y"), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
            hbox.Add(tc2, 1, flag=wx.EXPAND)
            hbox.Add(wx.StaticText(panel, label="W"), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
            hbox.Add(tc3, 1, flag=wx.EXPAND)
            hbox.Add(wx.StaticText(panel, label="H"), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
            hbox.Add(tc4, 1, flag=wx.EXPAND)

            boxsizer.Add(hbox, flag=wx.LEFT | wx.TOP | wx.EXPAND, border=5)

            hbox = wx.BoxSizer(wx.HORIZONTAL)
            button1 = wx.Button(panel, label="Select Area")
            hbox.Add(button1, 1, flag=wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT, border=15)
            button1 = wx.Button(panel, label="Full Screen")
            hbox.Add(button1, 1, flag=wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT, border=15)
            boxsizer.Add(hbox, flag=wx.LEFT | wx.TOP | wx.EXPAND, border=5)

            return boxsizer

        def videoBox():
            sb = wx.StaticBox(panel, label="Video")
            boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
            fgs = wx.FlexGridSizer(3, 2, 5, 25)

            tc1 = wx.TextCtrl(panel)
            tc2 = wx.TextCtrl(panel)

            fgs.AddMany([(wx.StaticText(panel, label="input")), (tc1, 1, wx.EXPAND),
                        (wx.StaticText(panel, label="output")), (tc2, 1, wx.EXPAND)])

            fgs.AddGrowableCol(1, 1)
            boxsizer.Add(fgs, flag=wx.LEFT | wx.TOP | wx.EXPAND, border=5)
            return boxsizer

        def audioBox():
            sb = wx.StaticBox(panel, label="Audio")
            boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
            fgs = wx.FlexGridSizer(3, 2, 5, 25)

            tc1 = wx.TextCtrl(panel)
            tc2 = wx.TextCtrl(panel)

            fgs.AddMany([(wx.StaticText(panel, label="input")), (tc1, 1, wx.EXPAND),
                        (wx.StaticText(panel, label="output")), (tc2, 1, wx.EXPAND)])

            fgs.AddGrowableCol(1, 1)
            boxsizer.Add(fgs, flag=wx.LEFT | wx.TOP | wx.EXPAND, border=5)
            return boxsizer

        def actionBox():
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            button1 = wx.Button(panel, label="Streaming")
            hbox.Add(button1, 1, flag=wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT, border=15)
            return hbox

        panel = self
        vbox = wx.BoxSizer(wx.VERTICAL)

        vbox.Add(titleBox(), 0, wx.ALL, 0)
        vbox.Add(geometryBox(), 0, flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=10)
        vbox.Add(videoBox(), 0, flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=10)
        vbox.Add(audioBox(), 0, flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=10)
        vbox.Add(actionBox(), 1, flag=wx.EXPAND | wx.ALL, border=10)

        #sb = wx.StaticBox(panel, label="Optional Attributes")
        #boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
        #boxsizer.Add(wx.CheckBox(panel, label="Public"), flag=wx.LEFT | wx.TOP,
        #             border=5)
        #boxsizer.Add(wx.CheckBox(panel, label="Generate Default Constructor"),
        #             flag=wx.LEFT, border=5)
        #boxsizer.Add(wx.CheckBox(panel, label="Generate Main Method"),
        #             flag=wx.LEFT | wx.BOTTOM, border=5)
        #vbox.Add(boxsizer, 1, flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=10)

        panel.SetAutoLayout(True)
        panel.SetSizer(vbox)
        #sizer = wx.GridBagSizer(5, 5)

        #icon = wx.StaticBitmap(panel, bitmap=wx.Bitmap('exec.png'))
        #sizer.Add(icon, pos=(0, 4), flag=wx.TOP | wx.RIGHT | wx.ALIGN_RIGHT,
        #          border=5)

        #line = wx.StaticLine(panel)
        #sizer.Add(line, pos=(1, 0), span=(1, 5), flag=wx.EXPAND | wx.BOTTOM,
        #          border=10)

        #text2 = wx.StaticText(panel, label="Name")
        #sizer.Add(text2, pos=(2, 0), flag=wx.LEFT, border=10)

        #tc1 = wx.TextCtrl(panel)
        #sizer.Add(tc1, pos=(2, 1), span=(1, 3), flag=wx.TOP | wx.EXPAND)

        #text3 = wx.StaticText(panel, label="Package")
        #sizer.Add(text3, pos=(3, 0), flag=wx.LEFT | wx.TOP, border=10)

        #tc2 = wx.TextCtrl(panel)
        #sizer.Add(tc2, pos=(3, 1), span=(1, 3), flag=wx.TOP | wx.EXPAND,
        #          border=5)

        #button1 = wx.Button(panel, label="Browse...")
        #sizer.Add(button1, pos=(3, 4), flag=wx.TOP | wx.RIGHT, border=5)

        #text4 = wx.StaticText(panel, label="Extends")
        #sizer.Add(text4, pos=(4, 0), flag=wx.TOP | wx.LEFT, border=10)

        #combo = wx.ComboBox(panel)
        #sizer.Add(combo, pos=(4, 1), span=(1, 3), flag=wx.TOP | wx.EXPAND,
        #          border=5)

        #button2 = wx.Button(panel, label="Browse...")
        #sizer.Add(button2, pos=(4, 4), flag=wx.TOP | wx.RIGHT, border=5)

        #sb = wx.StaticBox(panel, label="Optional Attributes")

        #button3 = wx.Button(panel, label='Help')
        #sizer.Add(button3, pos=(7, 0), flag=wx.LEFT, border=10)

        #button4 = wx.Button(panel, label="Ok")
        #sizer.Add(button4, pos=(7, 3))

        #button5 = wx.Button(panel, label="Cancel")
        #sizer.Add(button5, pos=(7, 4), span=(1, 1), flag=wx.BOTTOM | wx.RIGHT,
        #          border=5)

        #sizer.AddGrowableCol(2)


class Core(object):
    def StartStreaming(self):
        pass

    def StopStreaming(self):
        pass

    def MediaConnectionLisener(self):
        pass

    def AvahiListener(self):
        #create the event
        evt = SomeNewEvent(attr1="hello", attr2=654)
        #post the event
        wx.PostEvent(target, evt)


if __name__ == '__main__':

    app = wx.App()
    Example(None, title="Desktop Mirror - Advanced")
    app.MainLoop()
