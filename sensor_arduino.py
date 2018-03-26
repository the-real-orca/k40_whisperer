import logging

try:
	import serial
except ImportError:
	logging.warning("pyserial Module not found -> disable Sensors")

class Monitored:
	def __init__(self, name, val=0.0, alert=False, map={}):
		self.name = name
		self.val = val
		self.alert = alert
		self.map = map

	def __str__(self):
		return "Value: " + str(self.val) + " Alert: " + str(self.alert)

	def updateWith(self, data):
		if 'val' in self.map:
			self.val = data[ self.map['val'] ]
		if 'alert' in self.map:
			self.alert = bool(data[ self.map['alert'] ])

class Sensor:
	def __init__(self, port, baud, indexMap={}):
		try:
			self._ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=10)
		except:
			self._ser = None
		self._buf = ""
		self.general = Monitored('general', map=indexMap.get('general', {}))
		self.airAssist = Monitored('airAssist', map=indexMap.get('airAssist', {}))
		self.waterFlow = Monitored('waterFlow', map=indexMap.get('waterFlow', {}))
		self.waterTemp = Monitored('waterTemp', map=indexMap.get('waterTemp', {}))
		self.PSUTemp = Monitored('PSUTemp', map=indexMap.get('PSUTemp', {}))


	def update(self):
		if self._ser and self._ser.is_open:
			n = self._ser.in_waiting
			if n > 0:
				self._buf += self._ser.read(n)
				found = self._buf.rfind('\n')
				if found >= 0:
					lines = self._buf.split('\n')
					l = len(lines)
					line = lines[l-2]
					self._buf = lines[l-1]
					# update sensors
					vals = map(float, line.split())
					self.general.updateWith(vals)
					self.waterFlow.updateWith(vals)
					self.waterTemp.updateWith(vals)
					self.PSUTemp.updateWith(vals)

