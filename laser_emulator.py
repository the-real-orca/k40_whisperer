import datetime
import os
from distutils.dir_util import mkpath


class LASER_CLASS:
	def __init__(self):
		print ("LASER_CLASS __init__")
		self.x = False
		self.y = False
		self._init = True

	def __del__(self):
		print ("LASER_CLASS __del__")
		self.release()

	""" connect to laser controller board """
	def init(self, unit="mm"):
		print("LASER_CLASS init")
		self._init = True

	def isInit(self):
		return self._init

	def release(self):
		if not( self.isInit() ): return
		print("LASER_CLASS release")
		self._init = False
		self.x = False
		self.y = False		


	def unlock(self):
		if not( self.isInit() ): return
		print("LASER_CLASS unlock")
		self.x = False
		self.y = False		


	def home(self):
		if not( self.isInit() ): return
		print("LASER_CLASS home")
		self.x = 0
		self.y = 0

		
	""" move relative to current position """
	def move(self, dx, dy):
		if not( self.isInit() ): return
		print("LASER_CLASS move", dx, dy)
		self.x += dx
		self.y += dy


	""" go to absolute position """
	def moveTo(self, x, y):
		if not( self.isInit() ): return
		print("LASER_CLASS moveTo", x, y)
		self.x = x
		self.y = y


	def stop(self):
		if not( self.isInit() ): return
		print("LASER_CLASS stop")

		
	def processVector(self, polylines, feedRate, originX = 0, originY = 0, repeat = 1):
		if not( self.isInit() ): return
		print("LASER_CLASS processVector")
		path = "HTML/emulator"
		mkpath(path)
		filename = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S.txt")
		filename = "testcut.gcode" # TODO
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
					file.write("G0 X{:.2f} Y{:.2f}\n".format(p[0][0], p[0][1]))
					for x in p:
						file.write("G1 X{:.2f} Y{:.2f} E1\n".format(x[0], x[1]))


	def processRaster(self, raster, feedRate, originX = 0, originY = 0, repeat = 1):
		if not( self.isInit() ): return
		print("LASER_CLASS processRaster")
		#TODO
		print("!!!!!!!!! NOT IMPLEMENTED !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
