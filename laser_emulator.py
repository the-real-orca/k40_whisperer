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


	""" go to absolute position """
	def moveTo(self, x, y):
		if not( self.isInit() ): return
		print("LASER_CLASS moveTo", x, y)


	def stop(self):
		if not( self.isInit() ): return
		print("LASER_CLASS stop")

		
	def processVector(self, polylines, feedRate, originX = 0, originY = 0, repeat = 1):
		if not( self.isInit() ): return
		print("LASER_CLASS processVector")
		path = "HTML/emulator"
		mkpath(path)
		filename = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S.txt")
		filename = "testcut.txt" # TODO
		path = os.path.join(path, filename)
		print("file", path)

		# save to file
		file = open(path,"w") 

		with open(path, 'a') as file:
			file.write("Origin: ({:.2f}, {:.2f})\n".format(originX, originY))
			for line in polylines:
				points = "\t".join(map(lambda x: "({:.2f}, {:.2f})".format(x[0], x[1]), line.getPoints()))
			file.write(points + "\n") 


	def processRaster(self, raster, feedRate, originX = 0, originY = 0, repeat = 1):
		if not( self.isInit() ): return
		print("LASER_CLASS processRaster")
		#TODO
		print("!!!!!!!!! NOT IMPLEMENTED !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
