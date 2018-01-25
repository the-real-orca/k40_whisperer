import datetime
import os
import logging
import time
from distutils.dir_util import mkpath
import messages as msg

def idle():
	time.sleep(0.1)

class LASER_CLASS:
	def __init__(self):
		self.x = False
		self.y = False
		self._init = False
		self.active = False
		self.progress = 0
		self.mode = ""

	def __del__(self):
		self.release()

	""" connect to laser controller board """
	def init(self):
		logging.info("LASER_CLASS init")
		msg.send('success', "Laser Emulator connected")
		self._init = True

	def setEndstopPos(self, endstopPos):
		pass

	def isInit(self):
		return self._init

	def isActive(self):
		return self.active

	def release(self):
		if not( self.isInit() ) or self.isActive(): return
		logging.info("LASER_CLASS release")
		msg.send('prime', "Laser Emulator released")
		self._init = False
		self.x = False
		self.y = False
		self.mode = ""


	def unlock(self):
		if not( self.isInit() ) or self.isActive(): return
		logging.info("LASER_CLASS unlock")
		self.x = False
		self.y = False
		self.mode = "unlocked"


	def home(self):
		if not( self.isInit() ) or self.active: return
		logging.info("LASER_CLASS home")
		time.sleep(2)
		self.x = 0
		self.y = 0

		
	""" move relative to current position """
	def move(self, dx, dy):
		if not( self.isInit() ) or self.active: return
		if dx == 0 and dy == 0: return
		logging.debug("move: " + str(dx) + "/" + str(dy) + " ...")
		time.sleep(1)
		self.x += dx
		self.y += dy


	""" go to absolute position """
	def moveTo(self, x, y):
		if not( self.isInit() ) or self.active: return
		if x == self.x and y == self.y: return
		logging.debug("move to: " + str(x) + "/" + str(y) + " ...")
		time.sleep(1)
		self.x = x
		self.y = y


	def stop(self):
		if not( self.isInit() ): return
		logging.info("LASER_CLASS stop")
		self.active = False
		self.mode = "stopped"

	def enable(self):
		if not( self.isInit() ): return
		logging.info("LASER_CLASS enable")
		self.mode = "enable"
		
	def processVector(self, polylines, feedRate, originX = 0, originY = 0, repeat = 1):
		if not( self.isInit() ) or self.active: return
		try:
			logging.info("LASER_CLASS processVector")
			self.active = True
			self.progress = 0
			self.mode = "prepare"
			path = "HTML/emulator"
			mkpath(path)
			filename = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S.gcode")
			logging.info("EMULATOR save to: " + filename)
			msg.send('prime', "EMULATOR save to: " + filename)
			path = os.path.join(path, filename)

			# save G-code
			file = open(path,"w")
			with open(path, 'a') as file:
				file.write("; use https://ncviewer.com/ or http://gcode.ws/ to analyze G-code\n")
				file.write("\n")
				file.write("; Origin: ({:.2f}, {:.2f})\n".format(originX, originY))
				file.write("; number of lines: {}\n".format(len(polylines)))
				file.write("\n")
				file.write("M452\t; set laser mode units to mm\n");
				file.write("G21\t; set units to mm\n");
				file.write("G90\t; absolute positioning\n");
				file.write("G28\t; home\n");
				file.write("G0 Z1 E0\t; WORKAROUND for G-Code Viewer\n");
				file.write("M83\t; E1 WORKAROUND for G-Code Viewer\n");
				for i, line in enumerate(polylines):
					p = line.getPoints()
					file.write("; polyline #{}\n".format(i))
					if len(p) > 1:
						if not self.active:
							raise RuntimeError("stopped")
						idle()
						file.write("G0 X{:.2f} Y{:.2f}\n".format(p[0][0], p[0][1]))
						for x in p:
							file.write("G1 X{:.2f} Y{:.2f} E1\n".format(x[0], x[1]))
			time.sleep(5)

			# simulate cutting time
			logging.debug("simulate cutting time ...")
			self.mode = "running"
			for i in range(0,10):
				self.progress = i*10
				time.sleep(1)
				if not self.active:
					raise RuntimeError("stopped")
				idle()
			self.progress = 100
			self.mode = "finished"
			logging.info("LASER_CLASS processVector finished")

		except Exception as e:
			if self.active:
				self.mode = "stopped"
			else:
				self.mode = "error"
				logging.error("LASER_CLASS processVector ERROR: " + str(e))
		finally:
			self.active = False



	def processRaster(self, raster, feedRate, originX = 0, originY = 0, repeat = 1):
		if not( self.isInit() ) or self.active: return
		logging.info("LASER_CLASS processRaster")
		#TODO
		logging.error("!!!!!!!!! NOT IMPLEMENTED !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
