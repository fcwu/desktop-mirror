#!/usr/bin/env python
import wx

class MyFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title,
                style=wx.RESIZE_BORDER | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR |
                wx.RESIZE_BORDER | wx.CLIP_CHILDREN)

        self.rootPanel = wx.Panel(self)

        innerPanel = wx.Panel(self.rootPanel,-1, size=(150,150), style=wx.ALIGN_CENTER)
        innerPanel.SetBackgroundColour(wx.Colour(128, 128, 0))
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        vbox = wx.BoxSizer(wx.VERTICAL)
        innerBox = wx.BoxSizer(wx.VERTICAL)

        # I want this line visible in the CENTRE of the inner panel
        txt = wx.StaticText(innerPanel, id=-1, label="TEXT HERE",style=wx.ALIGN_CENTER, name="")
        innerBox.AddSpacer((150,75))
        innerBox.Add(txt, 0, wx.CENTER)
        innerBox.AddSpacer((0,75))
        innerPanel.SetSizer(innerBox)

        hbox.Add(innerPanel, 0, wx.ALL|wx.ALIGN_CENTER)
        vbox.Add(hbox, 1, wx.ALL|wx.ALIGN_CENTER, 5)

        self.rootPanel.SetSizer(vbox)
        vbox.Fit(self)

        self.Bind(wx.EVT_SIZE, self.OnSize)
        #self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseEvents)
        #self.Bind(wx.EVT_MOTION, self.OnMouseMotion )
        self.rootPanel.Bind(wx.EVT_LEFT_DOWN, self.OnMouseEvents)
        self.rootPanel.Bind(wx.EVT_LEFT_UP, self.OnMouseEvents)
        #wx.MOUSE_BTN_LEFT

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update_title)
        self.timer.Start(40)  # in miliseconds
        self.mouse_pos = None
        self.in_window = False
        self.is_moving = False
        self.is_down = False
        #wx.SetCursor(wx.StockCursor(wx.CURSOR_SIZING))
        #wx.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
        #wx.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
        self.step = 0

    def update_title(self, event):
        if wx.GetMouseState().LeftDown():
            if self.is_down:
                return
            self.step += 1
            self.is_down = True
            return
        elif self.is_down:
            self.is_down = False
        else:
            return
        if self.step == 1:
            pos = wx.GetMousePosition()
            self.SetPosition(pos)
            self.mouse_pos = pos
        if self.step == 2:
            pos = wx.GetMousePosition()
            offset = (pos.x - self.mouse_pos.x, pos.y - self.mouse_pos.y)
            self.SetSize(offset)
            self.step = 0
        #if not self.is_moving:
        #    if wx.GetMouseState().LeftDown():
        #        pos = wx.GetMousePosition()
        #        self.SetPosition(pos)
        #        self.is_moving = True
        #        self.mouse_pos = pos
        #    return
        #if not wx.GetMouseState().LeftDown():
        #    self.is_moving = False
        #    return
        #pos = wx.GetMousePosition()
        #offset = (pos.x - self.mouse_pos.x, pos.y - self.mouse_pos.y)
        #self.mouse_pos = pos
        #self.SetTitle("Your mouse is at (%s, %s)" % (pos.x, pos.y))
        #panel_pos = self.rootPanel.ScreenToClient(wx.GetMousePosition())
        #print("Your mouse is at client (%s, %s)" % (panel_pos.x, panel_pos.y))
        #win_pos = self.GetPosition()
        #self.SetPosition((win_pos.x + offset[0], win_pos.y + offset[1]))

    def OnSize(self, event):
        print 'size: {}'.format(event.GetSize())
        event.Skip()

    def OnMouseEvents(self,e):
        print "Mouse event"
        #print dir(e)
        self.in_window = True
        if e.Entering():
            print "Hover"
        elif e.Leaving():
            print "Leaving Hover"
            self.in_window = False
            self.is_moving = False
        if e.LeftDown():
            print 'left down'
            self.mouse_pos = wx.GetMousePosition()
            self.is_moving = True
        else:
            print 'left up'
            self.is_moving = False
        e.Skip()

    def OnMouseMotion(self, event):
        frameClientPos = event.GetPosition()
        desktopPos = self.ClientToScreen( frameClientPos )  # Current cursor desktop coord
        print '----  MyFrame::OnMouseMotion()     mouse is at: ', desktopPos
    #end OnMouseMotion def

class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, -1, 'wxBoxSizer.py')
        frame.Show(True)
        frame.Center()
        frame.SetTransparent(200)
        return True

app = MyApp(0)
app.MainLoop()
