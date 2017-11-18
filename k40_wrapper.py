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

COMPLETED_FLAG = 1<<5

class LASER_CLASS:
	def __init__(self, board_name="LASER-M2"):
		print ("LASER_CLASS __init__")
		self.unit = ""
		self.scale = 0
		self.x = False
		self.y = False
		self.nano = K40_CLASS()
		self.board_name = board_name
		self._stop_flag = [True]


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


	def release(self):
		if not( self.isInit() ): return
		print("LASER_CLASS released")
		self.unlock()
		time.sleep(0.2)
		self.nano.release_usb()
		time.sleep(0.2)


	def unlock(self):
		if not( self.isInit() ): return
		print("unlock")
		self.x = False
		self.y = False
		self.nano.unlock_rail()


	def home(self):
		if not( self.isInit() ): return
		print("home")
		self.nano.reset_usb()
		self.nano.home_position()
		self._waitWhileBussy()
		self.x = 0
		self.y = 0
		self._stop_flag[0] = False


	""" move relative to current position """
	def move(self, dx, dy):
		if not( self.isInit() ): return
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
		if not( self.isInit() ): return
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
		self.nano.e_stop_flag();


	def _updateCallback(self, msg = ""):
		print(msg)


	def _waitWhileBussy(self, timeout = 600):
		status = self.nano.say_hello()[0]
		DELAY = 0.1
		while not(status[1] & COMPLETED_FLAG):
			time.sleep(DELAY)
			status = self.nano.say_hello()[0]
			timeout -= DELAY
			if ( timeout < 0):
				return False
		return True


	def processVector(self, polylines, feedRate, originX = 0, originY = 0, repeat = 1):
		if not( self.isInit() ): return

		# convert polylines to ecoords
		ecoords=[]
		for loop, line in enumerate(polylines, start=1):
			points = line.getPoints()
			x = np.zeros((len(points), 3))
			x[:,0:2] = points
			x[:,1] = -x[:,1]
			x[:,2] = loop
			ecoords.extend(x.tolist())

		print("ecoords", ecoords, "#####################################################")

		# generate data for K40 controller board
		data=[]
		egv_inst = egv(target=lambda s:data.append(s))
		egv_inst.make_egv_data(
			ecoords,									\
			startX = -originX,					\
			startY = -originY,					\
			units = 'mm',							\
			Feed = feedRate ,					\
			board_name = self.board_name,	\
			Raster_step = 0,					\
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


	def processRaster(self, raster, feedRate, originX = 0, originY = 0, repeat = 1):
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



