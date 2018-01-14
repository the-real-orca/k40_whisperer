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
import re as regex

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
		self.endstopPos = [0,0]
		self.msg = ""
		self.active = False
		self.repeat = 0
		self.mode = ""
		self.progress = 0
		self.nano = K40_CLASS()
		self.nano.n_timeouts = 10
		self.nano.timeout = 1000   # Time in milliseconds
		self.board_name = board_name
		self._stop_flag = [True]

		# response codes
		self.OK = 206
		self.COMPLETED = 236
		self.HOMED = 238

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
		self._stop_flag[0] = False
		self.release()
		idle()
		self.nano.initialize_device(verbose)
		idle()
		if self.nano.say_hello() != self.OK:
			self.release()
			return
		self.home()

	def setEndstopPos(self, endstopPos):
		self.endstopPos = endstopPos


	def isInit(self):
		return ( self.nano.dev != None )

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
			self.mode = ""
			print("self.nano.dev", self.nano.dev)



	def unlock(self):
		if not( self.isInit() ) or self.isActive(): return
		print("unlock")
		self.x = False
		self.y = False
		self.nano.unlock_rail()
		self.mode = "unlocked"

	def _internalHome(self):
		print("home")
		self.x = self.endstopPos[0]
		self.y = self.endstopPos[1]
		self._stop_flag[0] = False
		self.nano.home_position()
		self._waitForHome()
		self.moveTo(0,0)


	def home(self):
		if not( self.isInit() ) or self.isActive(): return
		self._internalHome()


	""" move relative to current position """
	def move(self, dx, dy):
		if not( self.isInit() ) or self.isActive(): return
		if self.x is False or self.y is False: return
		if dx == 0 and dy == 0: return
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
		if x == self.x and y == self.y: return
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
		self.nano.e_stop()
		self.mode = "stopped"

	def enable(self):
		if not( self.isInit() ): return
		print("enable")
		self._stop_flag[0] = False
		self.mode = "enable"

	def _updateCallback(self, msg = ""):
		if msg:
			self.msg = msg
			m = regex.match("(\w+) \D*([\d.]+)%", msg)
			if m:
				f = float(m.group(2))
				if m.group(1) == "Generating":
					self.mode = "prepare"
					# self.progress = f
				if m.group(1) == "Sending":
					self.mode = "running"
					self.progress = f
		idle()

	def _waitWhileBussy(self, timeout = 20):
		DELAY = 0.1
		status=0
		while status != self.COMPLETED:
			time.sleep(DELAY)
			status = self.nano.say_hello()
			timeout -= DELAY
			if ( timeout < 0):
				return False
		return True

	def _waitForHome(self, timeout = 20):
		DELAY = 0.1
		status=0
		while status != self.HOMED:
			time.sleep(DELAY)
			status = self.nano.say_hello()
			timeout -= DELAY
			if ( timeout < 0):
				return False
		return True


	def processVector(self, polylines, feedRate, originX = 0, originY = 0, repeat = 1):
		if not( self.isInit() ) or self.isActive(): return
		try:
			self.msg = "prepare data..."
			self.mode = "prepare"
			print("processVector")
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

			if len(ecoords)==0:
				raise StandardError("no ecoords")

	# TODO check movement area

			# generate data for K40 controller board
			data=[]
			egv_inst = egv(target=lambda s:data.append(s))
			egv_inst.make_egv_data(
				ecoords,								\
				startX = -(originX-self.endstopPos[0]),					\
				startY = -(originY-self.endstopPos[1]),					\
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

			# run laser
			self.mode = "running"
			self._internalHome()
			idle()
			self.nano.send_data(data, self._updateCallback, self._stop_flag, repeat, False)

			# wait for laser to finish and data buffer is empty
			self._waitWhileBussy(60)
			print("laser finished")
			self.progress = 100
			self.mode = "finished"

		except Exception as e:
			self.msg = str(e)
			if self._stop_flag[0]:
				self.mode = "stopped"
			else:
				self.mode = "error"
		finally:
			self.active = False

	def processRaster(self, raster, feedRate, originX = 0, originY = 0, repeat = 1):
		return

