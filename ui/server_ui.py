import wx
from components import lists
from socket import error as sockError
from core.server import Server
from ui.client_ui import ClientWin
from core.scanner import Scanner
import Queue

class ServerWin(wx.Frame):
    def __init__(self, parent=None, id=-1, title='PypMsg: Main Window', show=False):
        self.clients = []
        #self.server = Server(self.reloadMessages)
        self.server = Server()
        self.scanner = Scanner(Scanner.SERVER)
        self.scanner.listen()
        self.atchQueue = Queue.Queue()

        wx.Frame.__init__(self, parent, id, title, size=(600,400))
        wx.EVT_CLOSE(self, self.OnClose)

        #panel = wx.Panel(self, -1)
        splitter = wx.SplitterWindow(self)
        leftPanel = wx.Panel(splitter)
        rightPanel = wx.Panel(splitter)

        self.msgList = lists.PListCtrl(leftPanel)
        self.msgList.InsertColumn(0, 'User Name', width = 100)
        self.msgList.InsertColumn(2, 'Message')
        self.msgList.InsertColumn(1, 'Address', width=80)
        self.msgList.Bind(wx.EVT_LIST_ITEM_SELECTED, self.showFileList)
        self.msgList.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.showMessage)

        #ipAddrCtrl = wx.StaticText(leftPanel, label='My IP Address: ')

        msgVbox = wx.BoxSizer(wx.VERTICAL)
        #msgVbox.Add(ipAddrCtrl, 0, wx.EXPAND)
        msgVbox.Add(self.msgList, 1, wx.EXPAND | wx.TOP, 10)

        self.filList = wx.ListCtrl(rightPanel, style=wx.LC_LIST)
        self.filList.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.downloadAttachment)
        msgBtn = wx.Button(rightPanel, label='&New Message')
        msgBtn.Bind(wx.EVT_BUTTON, self.newMessageWin)
        relBtn = wx.Button(rightPanel, label="&Refresh")
        relBtn.Bind(wx.EVT_BUTTON, self.reloadMessages)
        clrBtn = wx.Button(rightPanel, label="&Clear")
        clrBtn.Bind(wx.EVT_BUTTON, self.clearMessages)

        btnVbox = wx.BoxSizer(wx.VERTICAL)
        btnVbox.Add(wx.StaticText(rightPanel, label='Attachments:\n(Double-Click to download)'), 0, wx.TOP)
        btnVbox.Add(self.filList, 1, wx.EXPAND)
        btnVbox.Add(msgBtn, 0, wx.EXPAND | wx.TOP, 10)
        btnVbox.Add(relBtn, 0, wx.EXPAND | wx.TOP, 10)
        btnVbox.Add(clrBtn, 0, wx.EXPAND | wx.TOP, 10)

        leftPanel.SetSizer(msgVbox)
        rightPanel.SetSizer(btnVbox)

        splitter.SplitVertically(leftPanel, rightPanel, -150)

        if not self.server.startServing():
            wx.MessageDialog(None, 'An Instance of PypMsg is already running. Please close that before opening a new one. \
The current version of PypMsg does not support multiple-instances. Thank you.', 'Already Running',wx.OK | wx.ICON_ERROR | wx.CENTRE).ShowModal()
            raise SystemExit(1)

        self.reloadMessages()

        if show:
            self.Show()

    def addAttachment(self, atch):
        self.server.sentAttachments[atch[0]] = atch[1]

    def downloadAttachment(self, event):
        loc = wx.DirSelector(message = 'Select location to save attachment', parent = self)
        if not loc:
            return
        downloadStatus = self.server.downloadAttachment(self.msgList.GetNextSelected(-1), event.GetIndex(), loc, self.downloadComplete)

    def downloadComplete(self, atch, downloadStatus):
        if downloadStatus[:5] != 'ERROR':
            wx.MessageDialog(None, atch + ': ' + downloadStatus, 'Download', wx.OK | wx.ICON_INFORMATION | wx.CENTRE).ShowModal()
        else:
            self.server
            wx.MessageDialog(None, atch + ': ' + downloadStatus, 'Attachment', wx.OK | wx.ICON_ERROR | wx.CENTRE).ShowModal()

    def OnClose(self, event):
        self.server.stopServing()
        self.Destroy()

    def clearMessages(self, evt = None):
        self.msgList.DeleteAllItems()
        self.filList.DeleteAllItems()
        self.server.clearMessageQueue()

    def reloadMessages(self, evt = None):
        '''Currently removing all the messages in the list and repopulating it.
        This method gets really slow with large nos of messages.
        Remedy:
            1. Limit the no. of messages to may be 100?
            2. Handle large no. of messages through some kind of optimisations
            3. Eliminate this system, everytime reload is called, only the new
            messages shoule be appended to the list.
        '''
        self.filList.DeleteAllItems()
        self.msgList.DeleteAllItems()
        for (uname, addr, msg) in [(rec['USER'], rec['host'], rec['MSG']) for rec in self.server.msgQue]:
            self.msgList.Append([uname, addr, msg])
        #arch = self.server.msgQue[-1]
        #self.msgList.Append([arch['host'], arch['MSG']])
        print 'reloading messages done'

    def newMessageWin(self, event=None):
        self.clients.append(ClientWin(reportAttachment = self.addAttachment, parent=self, show=True))

    def showFileList(self, event=None):
        self.filList.DeleteAllItems()
        for uid, atch in self.server.msgQue[event.GetIndex()]['atchs']:
            self.filList.Append([atch])

    def showMessage(self, event = None):
        message = self.server.msgQue[event.GetIndex()]['MSG']
        display = '''From: %(USER)s
Address: %(host)s
Message:
%(MSG)s''' % self.server.msgQue[event.GetIndex()]
        wx.MessageDialog(None, display, "Details", wx.OK | wx.ICON_INFORMATION | wx.CENTRE).ShowModal()
        return
