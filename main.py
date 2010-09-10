import os
import wx
import conf
from ui.server_ui import ServerWin

app = wx.App(0)

serverWin = ServerWin(None, show=True)

app.SetTopWindow(serverWin)
app.MainLoop()
