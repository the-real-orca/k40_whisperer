
import time
import logging

class MessagePoolSingletone(object):
	class MessagePool(logging.Handler):
		def emit(self, record):
			log_entry = self.format(record)
			send(str(record.levelname).lower(), str(record.levelname).lower(), log_entry, timestamp=record.created)

	__instance = None
	def __new__(cls):
		if MessagePoolSingletone.__instance is None:
			MessagePoolSingletone.__instance = object.__new__(cls)
		return MessagePoolSingletone.__instance

	def __init__(self):
		self.list = []
		self.maxSize = 10
		# capture log messages
		logMessages = MessagePoolSingletone.MessagePool()
		logMessages.setLevel(logging.WARNING)
		logging.getLogger('').addHandler(logMessages)

	def append(self, type, header, text, timestamp=False):
		if len(self.list) >= self.maxSize:
			self.list.pop(0)
		if not (timestamp):
			timestamp = time.time()
		self.list.append({
			'type': type,
			'header': header,
			'text': text,
			'timestamp': int(timestamp * 1000)
		})
		self.cleanup()

	def cleanup(self):
		t = int( (time.time() - 60)*1000 )
		self.list = filter(lambda msg: (msg.get('timestamp', 0) > t), self.list)

# singeltone instance
_messagePool = MessagePoolSingletone()

def send(type='info', header="", text="", timestamp=False):
	_messagePool.append(type, header, text, timestamp)

def get_list():
	_messagePool.cleanup()
	return _messagePool.list

