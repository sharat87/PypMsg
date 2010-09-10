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

import conf
import socket as sk
from pickle import dumps, loads
from thread import start_new_thread
#import pickle as pk
import os

class Client:
	#def __init__(self, server1):
	def __init__(self, reportAttachment):
		self.atchs = [] #LIST OF (UID, FILENAME) TUPLES. FILENAME DOES NOT CONTAIN ANY PATH INFORMATION
		self.atchPaths = {} #LIST OF UID: FILEPATH ITEMS. FILEPATH CONTAINS THE (ABSOLUTE) PATH WITH NATIVE FILE-SEPS
		self.memberList = [] #LIST OF IP ADDRS OF ONLINE USERS
		#self.server = server1
		self.reportAttachment = reportAttachment
		#start_new_thread(self.scan, ())
	
	def scan(self):
		print 'Broadcasting...'
		self.memberList = []
		caster = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
		caster.setsockopt(sk.SOL_SOCKET, sk.SO_BROADCAST, 1)
		caster.sendto('PING', (conf.BROADCAST, conf.PORT))
		#start_new_thread(self.timeoutAdvisor, ())
		while True:
			msg, address = caster.recvfrom(1024)
			if msg == 'PACK':
				print 'received PACK signal from', address
				if address[0] not in self.memberList:
					print 'adding to list'
					self.memberList.append(address[0])
					self.memNotify()
				print 'memberlist now:', self.memberList
			#elif msg == 'TOUT': # SCANNING TIMEOUT
			#	print 'scanning timeout'
			#	break
			else:
				print 'unidentified signal (client-side):', msg, 'from', address, '-> IGNORED'
		caster.close()
	
	def sendMsg(self, host, message):
		if not host: host = '127.0.0.1'
		self.clientSocket = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
		print 'host:', host
		print 'port:', conf.PORT
		self.clientSocket.connect((str(host), conf.PORT))
		dict = {}
		dict['MODE'] = 'MSG'
		dict['MSG'] = message
		dict['atchs'] = self.atchs
		dict['USER'] = conf.USERNAME
		#dict['fils'] = [(i, atch) for i, atch in self.attachments['fils'] if os.path.exists(atch) and not os.path.isdir(atch)]
		#dict['dirs'] = [(i, atch) for i, atch in self.attachments['dirs'] if os.path.exists(atch) and os.path.isdir(atch)]
		#self.server.sentAttachments[host] = self.atchPaths
		#self.atchQueue.put(tuple([host, self.atchPaths]))
		self.reportAttachment(tuple([host, self.atchPaths]))
		data = dumps(dict, conf.PK_PROTOCOL)
		print 'sending data...',
		self.clientSocket.send(data)
		print 'done'
		print 'recieving ack...',
		res = self.clientSocket.recv(conf.BULK_METADATA)
		print 'done'
		if res == conf.ACK:
			print 'ACK successful'
		else:
			print 'PypMsg Error: "', res, '"'
		print 'closing connection'
		self.clientSocket.close()
		del self.clientSocket
	
	def addAttachment(self, path):
		if not path:
			return 'Please enter a valid path of the attachment.'
		if not os.path.exists(path):
			return 'The path entered does not exist.'
		uid = str(conf.get_uuid())
		if not os.path.isdir(path):
			self.atchs.append(tuple(['FIL' + uid, os.path.split(path)[1]]))
			self.atchPaths['FIL' + uid] = path
			return 'Success: Attached File.'
		else:
			self.atchs.append(tuple(['DIR' + uid, os.path.split(path)[1]]))
			self.atchPaths['DIR' + uid] = path
			return 'Success: Attached Folder.'
	
	def remAttachment(self, path):
		muid = ''
		for uid, filepath in self.atchPaths.items():
			if os.path.abspath(filepath) == os.path.abspath(path):
				self.atchPaths.pop(uid)
				muid = uid
		for uid, filename in self.atchs:
			if uid == muid:
				self.atchs.remove(tuple([uid, filename]))
				return 'Successfully removed attachment'
		return 'There is no such attachment.'
