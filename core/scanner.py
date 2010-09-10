import conf
import socket as sk
from thread import start_new_thread
from time import sleep
import Queue

MYIP = '172.16.3.85'

class Scanner:
	CLIENT, SERVER = False, True
	def __init__(self, mode = CLIENT):
		if type(mode) != type(True):
			raise TypeError('Please use Scanner.CLIENT or Scanner.SERVER to specify the second parameter.')
		self.memqueue = Queue.Queue()
		self.getMember = self.memqueue.get
	
	# TO BE CALLED BY SERVERS
	def listen(self):
		start_new_thread(self._listenPings, ())

	def _listenPings(self):
		resser = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
		resser.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
		resser.setsockopt(sk.SOL_SOCKET, sk.SO_BROADCAST, 1)
		
		resser.bind((conf.HOST, conf.PORT))
		resser.settimeout(None)
		
		while True:
			msg, address = resser.recvfrom(1024)
			if msg[:4] == 'STOP':
				break
			elif msg[:4] == 'PING':
				print 'received PING signal from', address
				resser.sendto('PACK' + conf.USERNAME, address)
			else:
				print 'unidentified signal (server-side):', msg, 'from', address, '-> IGNORED'
	
	# TO BE CALLED BY CLIENTS
	def scan(self, userHandler = lambda addr: None):
		start_new_thread(self._refreshMembersList, tuple([userHandler]))

	def _refreshMembersList(self, userHandler):
		print 'Broadcasting...'
		scannerSock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
		scannerSock.setsockopt(sk.SOL_SOCKET, sk.SO_BROADCAST, 1)
		scannerSock.settimeout(5)
		scannerSock.sendto('PING' + conf.USERNAME, (conf.BROADCAST, conf.PORT))
		while True:
			try:
				msg, address = scannerSock.recvfrom(1024)
			except sk.timeout:
				print 'scanner timeout'
				break
			if msg[:4] == 'PACK':
				print 'received PACK signal from', address, 'calling handler'
				userHandler(msg[4:], address[0])
			else:
				print 'unidentified signal (client-side):', msg, 'from', address, '-> IGNORED'
		scannerSock.close()
