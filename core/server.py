from conf import *
import socket as sk
from pickle import dumps, loads
from thread import start_new_thread
import os

class Server:
	def __init__(self, newMessageNotify=lambda:None, newMemberNotify=lambda:None):
		self.msgQue = []
		self.sentAttachments = {}
		if callable(newMessageNotify):
			self.msgNotify = newMessageNotify
		else:
			raise TypeError('Message notifier not callable')
	
	def setMsgNotify(self, newMessageNotify=lambda:None):
		if callable(newMessageNotify):
			self.msgNotify = newMessageNotify
		else:
			raise TypeError('Message notifier not callable')
	
	def startServing(self):
		testSocket = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
		code = testSocket.connect_ex((prefs.get(sysSection, 'host'), prefs.getint(sysSection, 'port')))
		if code == 0:
			return False
		testSocket.close()
		start_new_thread(self.serve, ())
		#start_new_thread(self.cast, ())
		return True
	
	def cast(self):
		resser = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
		resser.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
		resser.setsockopt(sk.SOL_SOCKET, sk.SO_BROADCAST, 1)
		
		resser.bind((prefs.get(sysSection, 'host'), prefs.getint(sysSection, 'port')))
		
		while True:
			msg, address = resser.recvfrom(10)
			if msg == 'STOP':
				break
			elif msg == 'PING':
				print 'received PING signal from', address
				#if address[0] not in self.memberList:
				#	self.memberList.append(address[0])
				resser.sendto('PACK', address)
				#if address[0] == MYIP:
				#	self.tosk = resser
			else:
				print 'unidentified signal (server-side):', msg, 'from', address, '-> IGNORED'

	def serve(self):
		self.serverSocket = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
		self.serverSocket.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
		self.serverSocket.bind((prefs.get(sysSection, 'host'), prefs.getint(sysSection, 'port')))
		self.serverSocket.listen(5)
		print 'Server Started on %s:%s' % (prefs.get(sysSection, 'host'), prefs.getint(sysSection, 'port'))
		
		while True:
			clientSocket, address = self.serverSocket.accept()
			data = clientSocket.recv(prefs.getint(sysSection, 'bulk-metadata'))
			if not data:
				continue
			#print 'Bytes Recieved: ', len(data)
			dict = loads(data)
			if dict['MODE'] == 'EXT':
				clientSocket.send('EXIT SUCCESS')
				break
			elif dict['MODE'] == 'MSG':
				dict['host'] = str(address[0])
				self.msgQue.append(dict)
				self.msgNotify()
				clientSocket.send('ACK')
			else:
				start_new_thread(self.respondTo, (dict, clientSocket, address))
		
		self.serverSocket.close()
		del self.serverSocket
	
	def respondTo(self, dict, clientSocket, address):
		if dict['MODE'] == 'REQ':
			host = str(address[0])
			uid = dict['UID']
			atchPath = self.sentAttachments[host][uid]
			if not os.path.exists(atchPath):
				clientSocket.send('ERR: PATH DOES NOT EXIST\n')
			atchPath = os.path.abspath(atchPath)
			if os.path.isdir(atchPath):
				if dict['REQ'] == 'TREE':
					dirTree = [(dir.replace(atchPath, '/', 1).replace(os.sep, '/'), dirs, fils) for dir, dirs, fils in os.walk(atchPath)]
					clientSocket.send(dumps(dirTree, PK_PROTOCOL))
				elif dict['REQ'] == 'FILE':
					dirname = dict['DIR']
					filename = dict['FIL']
					reqPath = os.path.join(atchPath + dirname, filename)
					if os.path.exists(reqPath):
						clientSocket.send('OK')
						clientSocket.recv(prefs.getint(sysSection, 'bulk-metadata'))
						file = open(reqPath, 'rb')
						while True:
							data = file.read(prefs.getint(sysSection, 'bulk-filedata'))
							if not data: break
							clientSocket.send(data)
						file.close()
					else:
						clientSocket.send('ERR: DOES NOT EXIST')
			else:
				file = open(atchPath, 'rb')
				while True:
					data = file.read(prefs.getint(sysSection, 'bulk-filedata'))
					if not data: break
					clientSocket.send(data)
				file.close()
		elif dict['MODE'] == 'PNG':
			clientSocket.send(dumps(dict, PK_PROTOCOL))
		else:
			clientSocket.send(dumps({'MODE':'ERR', 'ERR':'UNKNOWN MODE:' + dict['MODE']}, PK_PROTOCOL))
		
		clientSocket.close()
	
	def downloadAttachment(self, msgIndex, atchIndex, location=prefs.get(sysSection, 'home-dir'), downloadComplete=lambda stat:None, replace=False):
		if not callable(downloadComplete):
			raise TypeError('Download Complete Handler is not callable')
		start_new_thread(self.downloader, (msgIndex, atchIndex, location, downloadComplete, replace))
	
	def downloader(self, msgIndex, atchIndex, location, downloadComplete, replace):
		archive = self.msgQue[msgIndex]; del msgIndex
		downloaderSocket = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
		downloaderSocket.connect((archive['host'], prefs.getint(sysSection, 'port')))
		uid, atch = archive['atchs'][atchIndex]
		dict = {'MODE':'REQ', 'UID':uid, 'REQ':'TREE'}
		downloaderSocket.send(dumps(dict, PK_PROTOCOL))
		status = ''
		os.chdir(location)
		if uid[:3] == 'FIL':
			while os.path.exists(atch):
				atch = atch[:: - 1].replace('.', '.mp~', 1)[:: - 1]
			file = open(atch, 'wb')
			while True:
				data = downloaderSocket.recv(prefs.getint(sysSection, 'bulk-filedata'))
				if not data: break
				file.write(data)
			file.close()
			status = 'Download Completed Successfully'
		elif uid[:3] == 'DIR':
			root_here = atch
			while os.path.exists(root_here):
				root_here = root_here + '~pm'
			os.mkdir(root_here)
			ppath = os.path.abspath(root_here)
			treeData = ''
			while True:
				data = downloaderSocket.recv(prefs.getint(sysSection, 'bulk-filedata'))
				if not data: break
				treeData += data
			tree = loads(treeData)
			for dirname, dirs, fils in tree:
				for dir in dirs:
					os.mkdir(os.path.join(ppath + dirname.replace('/', os.sep), dir))
				for fil in fils:
					dict['REQ'] = 'FILE'
					dict['DIR'] = dirname
					dict['FIL'] = fil
					dSocket = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
					dSocket.connect((archive['host'], prefs.getint(sysSection, 'port')))
					dSocket.send(dumps(dict, PK_PROTOCOL))
					res = dSocket.recv(prefs.getint(sysSection, 'bulk-metadata'))
					if res == 'OK':
						file = open(os.path.join(ppath + dirname.replace('/', os.sep), fil), 'wb')
						dSocket.send(ACK)
						while True:
							data = dSocket.recv(prefs.getint(sysSection, 'bulk-filedata'))
							if not data: break
							file.write(data)
						file.close()
			status = 'Download Completed Successfully'
		else:
			return 'ERROR: ' + 'UNRECOGNIZED UID'
		downloaderSocket.close()
		downloadComplete(atch, status)
	
	def clearMessageQueue(self):
		#TODO: USE CLEAR METHOD OF LISTS
		self.msgQue = []
	
	def stopServing(self):
		exitSock = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
		exitSock.connect((prefs.get(sysSection, 'exit-host'), prefs.getint(sysSection, 'port')))
		exitSock.send(dumps({'MODE':'EXT'}, PK_PROTOCOL))
		res = exitSock.recv(prefs.getint(sysSection, 'bulk-metadata'))
		exitSock.close()
		if res == 'EXIT SUCCESS':
			print 'Bye Bye!'
		else:
			print 'PypMsg Error: "', res, '"'
