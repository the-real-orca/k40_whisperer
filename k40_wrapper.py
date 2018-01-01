#!/usr/bin/env python
'''
This script is the comunicatin wrapper for the Laser Cutter.

Copyright (C) 2017 Stephan Veigl

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

import time
import numpy as np

##############################################################################

from nano_library import K40_CLASS
from egv import egv

# [255, 206, 111, 8, 18, 0] -> busy / idle ?
# [255, 236, 111, 8, 2, 0] -> finished processing buffer
# [255, 206, 111, 8, 2, 0] -> before home
# [255, 238, 111, 8, 18, 0] -> home finished

def idle():
	time.sleep(0.1)

class LASER_CLASS:
	def __init__(self, board_name="LASER-M2"):
		print ("LASER_CLASS __init__")
		self.unit = ""
		self.scale = 0
		self.x = False
		self.y = False
		self.active = False
		self.repeat = 0
		self.progress = 0
		self.nano = K40_CLASS()
		self.nano.n_timeouts = 10
		self.nano.timeout = 1000   # Time in milliseconds
		self.board_name = board_name
		self._stop_flag = [True]

		# response codes
		self.COMPLETED = 236
		self.CRC_FLAG = 1 << 0
		self.BUFFER_FULL_FLAG = 1 << 5

	def __del__(self):
		print ("LASER_CLASS __del__")
		self.release()

	""" connect to laser controller board """
	def init(self, unit="mm", verbose=False):
		# set unit
		if unit == "in" or unit == "inch":
			self.unit = "in"
			self.scale = 1000
		else:
			self.unit = "mm"
			self.scale = 1000 / 25.4

		# connect and init laser main board
		self.release()
		self.nano.initialize_device(verbose)
		self.nano.read_data()
		self.nano.say_hello()
		self._stop_flag[0] = False

	def isInit(self):
		return ( self.nano.dev != None )

	def getProgress(self):
		return self.progress

	def isActive(self):
		return self.active

	def release(self):
		if not( self.isInit() ) or self.isActive(): return
		print("LASER_CLASS released")
		try:
			self.unlock()
			time.sleep(0.1)
			self.nano.release_usb()
		finally:
			self.nano.dev = None
			print("self.nano.dev", self.nano.dev)


	def unlock(self):
		if not( self.isInit() ) or self.isActive(): return
		print("unlock")
		self.x = False
		self.y = False
		self.nano.unlock_rail()


	def home(self):
		if not( self.isInit() ) or self.isActive(): return
		print("home")
		self.nano.home_position()
		self.x = 0
		self.y = 0
		self._stop_flag[0] = False
		self._waitWhileBussy()


	""" move relative to current position """
	def move(self, dx, dy):
		if not( self.isInit() ) or self.isActive(): return
		if self.x is False or self.y is False: return
		print("move: " + str(dx) + "/" + str(dy))
# TODO check movement area
		dxmils = round(dx*self.scale)
		dymils = round(dy*self.scale)
		self.nano.rapid_move(dxmils, dymils)
		self.x += dxmils/self.scale
		self.y += dymils/self.scale


	""" go to absolute position """
	def moveTo(self, x, y):
		if not( self.isInit() ) or self.isActive(): return
		if self.x is False or self.y is False:
			self.home()
		print("goto: " + str(x) + "/" + str(y))
# TODO check movement area
		dxmils = round( (x-self.x) *self.scale)
		dymils = round( (y-self.y) *self.scale)
		self.nano.rapid_move(dxmils, dymils)
		self.x += dxmils/self.scale
		self.y += dymils/self.scale


	def stop(self):
		if not( self.isInit() ): return
		print("stop")
		self._stop_flag[0] = True
		self.nano.e_stop();

	def _updateCallback(self, msg = "", progress = None):
		if progress is not None:
			self.progress = progress / self.repeat
		print("updateCallback:", msg)
		idle()

	def _waitWhileBussy(self, timeout = 20):
		DELAY = 0.1
		status=0
		while not(status != self.COMPLETED):
			time.sleep(DELAY)
			status = self.nano.say_hello()
			timeout -= DELAY
			if ( timeout < 0):
				return False
		return True


	def processVector(self, polylines, feedRate, originX = 0, originY = 0, repeat = 1):
		if not( self.isInit() ) or self.isActive(): return
		try:
			print("processVector")
			print(polylines)
			self.active = True
			self.progress = 0
			self.repeat = repeat

			# convert polylines to ecoords
			ecoords=[]
			for loop, line in enumerate(polylines, start=1):
				if not(line): continue
				points = line.getPoints()
				x = np.zeros((len(points), 3))
				x[:,0:2] = points
				x[:,2] = loop
				ecoords.extend(x.tolist())
				if self._stop_flag[0]:
				   raise RuntimeError("stopped")
				idle()


			print("ecoords", ecoords, "#####################################################")
			if len(ecoords)==0:
				raise RuntimeError("no ecoords")

	# TODO check movement area

			# generate data for K40 controller board
			data=[]
			egv_inst = egv(target=lambda s:data.append(s))
			egv_inst.make_egv_data(
				ecoords,								\
				startX = -originX,					\
				startY = -originY,					\
				units = 'mm',							\
				Feed = feedRate ,					\
				board_name = self.board_name,	\
				Raster_step = 0,					\
				update_gui = self._updateCallback,	\
				stop_calc = self._stop_flag
			)

			if self._stop_flag[0]:
				raise  RuntimeError("stopped")
			idle()

			# send data to laser
			self.home()
			time.sleep(0.1)
			self.nano.send_data(data, self._updateCallback, self._stop_flag, repeat)

			# wait for laser to finish
			time.sleep(0.5)	# workaround TODO: make sure that laser data buffer is empty ????
			self._waitWhileBussy()
			print("laser finished")

			self.progress = 100
		finally:
			self.active = False

	def processRaster(self, raster, feedRate, originX = 0, originY = 0, repeat = 1):
		if not( self.isInit() ) or self.isActive(): return
		self.active = True
		data=[]
		egv_inst = egv(target=lambda s:data.append(s))

		# generate data for K40 controller board
		egv_inst.make_egv_data(
			raster,									\
			startX = -originX,					\
			startY = -originY,					\
			units = 'mm',							\
			Feed = feedRate ,					\
			board_name = self.board_name,	\
			Raster_step = 10,					\
			update_gui = self._updateCallback,	\
			stop_calc = self._stop_flag
		)

		while repeat > 0:
			# send data to laser
			self.home()
			self.nano.send_data(data, self._updateCallback, self._stop_flag)

			# wait for laser to finish
			self._waitWhileBussy()
			print("laser finished")

			# decrease repeat counter
			repeat -= 1

		self.active = False

