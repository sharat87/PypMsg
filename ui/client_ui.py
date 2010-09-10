'''
This file is part of PypMsg.

PypMsg is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

PypMsg is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with PypMsg.  If not, see <http://www.gnu.org/licenses/>.
'''

import wx
from components import lists
from core.scanner import Scanner
from core.client import Client
from thread import start_new_thread
import Queue

class ClientWin(wx.Frame):
	def __init__(self, reportAttachment=lambda atchs: None, parent=None, id=-1, title='PypMsg: New Message', show=False):
		self.scanner = Scanner(Scanner.CLIENT)
		self.client = Client(reportAttachment)
		self.userList = []
		
		wx.Frame.__init__(self, parent, id, title, size=(450,300))
		
		panel = wx.Panel(self, -1)
		
		#self.hostCtrl = wx.TextCtrl(panel)
		self.messCtrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.VSCROLL)
		
		fgs = wx.FlexGridSizer(rows = 2, cols = 2, vgap = 7, hgap = 15)
		fgs.AddMany([
		#			 (wx.StaticText(panel, label='Host IP')),
		#			 (self.hostCtrl, 1, wx.EXPAND),
					 (wx.StaticText(panel, label='Message')),
					 (self.messCtrl, 1, wx.EXPAND)
					 ])
		#fgs.AddGrowableRow(1, 1)
		fgs.AddGrowableCol(1, 1)
		
		self.atchList = wx.ListCtrl(panel, style=wx.LC_LIST)
		dp = AttachmentDropTarget(self.onDropFiles)
		self.atchList.SetDropTarget(dp)
		remAtchBtn = wx.Button(panel, label='&Remove')
		remAtchBtn.Bind(wx.EVT_BUTTON, self.remAttachment)
		sendBtn = wx.Button(panel, label='&Send')
		sendBtn.Bind(wx.EVT_BUTTON, self.sendMsg)
		refreshBtn = wx.Button(panel, label='Re&fresh')
		refreshBtn.Bind(wx.EVT_BUTTON, lambda event: self.reloadMembers())
		
		self.memList = lists.PListCtrl(panel)
		self.memList.InsertColumn(0, 'User Name')
		self.memList.InsertColumn(1, 'Address')
		
		vbox2 = wx.BoxSizer(wx.VERTICAL)
		vbox2.Add(self.memList, 1, wx.EXPAND)
		vbox2.Add(fgs, 0, wx.EXPAND | wx.TOP, 10)
		
		vbox1 = wx.BoxSizer(wx.VERTICAL)
		vbox1.Add(wx.StaticText(panel, label='Attachments:'), 0, wx.EXPAND | wx.BOTTOM, 5)
		vbox1.Add(self.atchList, 1, wx.EXPAND | wx.ALL)
		vbox1.Add(remAtchBtn, 0, wx.EXPAND | wx.TOP, 10)
		vbox1.Add(refreshBtn, 0, wx.EXPAND | wx.TOP, 10)
		vbox1.Add(sendBtn, 0, wx.EXPAND | wx.TOP, 10)
		
		hbox = wx.BoxSizer()
		hbox.Add(vbox2, 1, wx.EXPAND | wx.ALL, 15)
		hbox.Add(vbox1, .2, wx.EXPAND | wx.TOP | wx.BOTTOM | wx.RIGHT, 15)
		
		panel.SetSizer(hbox)
		
		if show:
			self.Show()
			self.reloadMembers()
	
	def sendMsg(self, event):
		if not self.memList.GetSelectedItemCount():
			wx.MessageDialog(None, 'Please select recipient user(s) from the user list',
							'Attachment', wx.OK | wx.ICON_EXCLAMATION | wx.CENTRE).ShowModal()
			return
		nextSel = self.memList.GetNextSelected(-1)
		while nextSel != -1:
			self.client.sendMsg(self.memList.GetItem(nextSel, col=1).GetText(), self.messCtrl.GetValue())
			nextSel = self.memList.GetNextSelected(nextSel)
		self.Close()
	
	def reloadMembers(self):
		print 'reloading members in the list'
		self.memList.DeleteAllItems()
		self.scanner.scan(self.userHandler)
	
	def onDropFiles(self, filenames):
		for file in filenames:
			self.addAttachment(file)
	
	def addAttachment(self, atch):
		atchStatus = self.client.addAttachment(atch)
		if 'Success' in atchStatus:
			self.atchList.Append([atch])
		else:
			wx.MessageDialog(None, atchStatus, 'Attachment',
							wx.OK | wx.ICON_EXCLAMATION | wx.CENTRE).ShowModal()
	
	def remAttachment(self, event):
		atch = self.atchList.GetNextSelected(-1)
		if not atch >= 0:
			wx.MessageDialog(None, 'Please select an attachment from the list to be removed.',
							'Attachment', wx.OK | wx.ICON_EXCLAMATION | wx.CENTRE).ShowModal()
			return
		remStatus = self.client.remAttachment(self.atchList.GetItemText(atch))
		if 'Success' in remStatus:
			self.atchList.DeleteItem(atch)
		else:
			wx.MessageDialog(None, remStatus, 'Attachment', wx.OK | wx.ICON_EXCLAMATION | wx.CENTRE).ShowModal()
	
	def userHandler(self, username, address):
		self.memList.Append([username, address])

class AttachmentDropTarget(wx.FileDropTarget):
	def __init__(self, onDropFiles):
		wx.FileDropTarget.__init__(self)
		self.onDropFiles = onDropFiles
	def OnDropFiles(self, x, y, filenames):
		self.onDropFiles(filenames)

if __name__ == '__main__':
	app=wx.App()
	clWin = ClientWin(show = True)
	app.MainLoop()
