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
import logging
import messages as msg


##############################################################################

from libs.k40_whisperer.nano_library import K40_CLASS
from libs.k40_whisperer.egv import egv

# [255, 206, 111, 8, 18, 0] -> busy / idle ?
# [255, 236, 111, 8, 2, 0] -> finished processing buffer
# [255, 206, 111, 8, 2, 0] -> before home
# [255, 238, 111, 8, 18, 0] -> home finished

def idle():
	time.sleep(0.1)

class LASER_CLASS:
	def __init__(self, board_name="LASER-M2"):
		self.unit = ""
		self.scale = 0
		self.x = False
		self.y = False
		self.endstopPos = [0,0]
		self.active = False
		self.repeat = 0
		self.mode = ""
		self.progress = 0
		self.nano = K40_CLASS()
		self.nano.n_timeouts = 30
		self.nano.timeout = 1000   # Time in milliseconds
		self.board_name = board_name
		self._stop_flag = [True]

		# response codes
		self.OK = 206
		self.COMPLETED = 236
		self.HOMED = 238

	def __del__(self):
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
		time.sleep(1)
		self.home()
		msg.send('success', "K40 Laser connected")

	def setEndstopPos(self, endstopPos):
		self.endstopPos = endstopPos


	def isInit(self):
		return ( self.nano.dev != None )

	def isActive(self):
		return self.active

	def release(self):
		if not( self.isInit() ): return
		try:
			self.stop()
			time.sleep(0.5)
			self.unlock()
			time.sleep(0.2)
		finally:
			try:
				self.nano.reset_usb()
				time.sleep(0.2)
			finally:
				try:
					self.nano.release_usb()
				finally:
					self.nano.dev = None
					self.mode = ""
					self.active = False
					logging.info("LASER_CLASS released")
					msg.send('prime', "K40 Laser released")



	def unlock(self):
		if not( self.isInit() ) or self.isActive(): return
		logging.info("LASER_CLASS unlock")
		self.x = False
		self.y = False
		self.nano.unlock_rail()
		self.mode = "unlocked"

	def _endStop(self):
		logging.debug("LASER_CLASS _endStop ...")
		self.x = self.endstopPos[0]
		self.y = self.endstopPos[1]
		self.nano.home_position()
		self._waitForEndstop()
		logging.debug("LASER_CLASS _endStop OK")


	def home(self):
		if not( self.isInit() ) or self.isActive(): return
		logging.debug("LASER_CLASS home ...")
		self.active = True
		self._stop_flag[0] = False
		self._endStop()
		self._internalMoveTo(0,0)
		self.active = False
		logging.debug("LASER_CLASS home OK")

	""" move relative to current position """
	def move(self, dx, dy):
		if not( self.isInit() ) or self.isActive(): return
		logging.debug("LASER_CLASS move ...")
		self.active = True
		self._internalMove(dx, dy)
		self.active = False
		logging.debug("LASER_CLASS move OK")

	""" move relative to current position """
	def _internalMove(self, dx, dy):
		if self.x is False or self.y is False: return
		if dx == 0 and dy == 0: return
		logging.debug("LASER_CLASS _internalMove: " + str(dx) + "/" + str(dy) + " ...")
# TODO check movement area
		dxmils = round(dx*self.scale)
		dymils = round(dy*self.scale)
		self.nano.rapid_move(dxmils, dymils)
		self.x += dxmils/self.scale
		self.y += dymils/self.scale
		idle()
		logging.debug("LASER_CLASS _internalMove OK")


	""" go to absolute position """
	def moveTo(self, x, y):
		if not (self.isInit()) or self.isActive(): return
		logging.debug("LASER_CLASS moveTo ...")
		self.active = True
		self._internalMoveTo(x, y)
		self.active = False
		logging.debug("LASER_CLASS moveTo OK")

	""" go to absolute position """
	def _internalMoveTo(self, x, y):
		logging.debug("LASER_CLASS _internalMoveTo: " + str(x) + "/" + str(y) + " ...")
		if self.x is False or self.y is False:
			self._endStop()
		if x == self.x and y == self.y: return
# TODO check movement area
		dxmils = round( (x-self.x) *self.scale)
		dymils = round( (y-self.y) *self.scale)
		self.nano.rapid_move(dxmils, dymils)
		self.x += dxmils/self.scale
		self.y += dymils/self.scale
		logging.debug("LASER_CLASS _internalMoveTo: OK")


	def stop(self):
		if not( self.isInit() ): return
		logging.info("stop")
		self._stop_flag[0] = True
		self.nano.e_stop()
		self.mode = "stopped"

	def enable(self):
		if not( self.isInit() ): return
		self._stop_flag[0] = False
		self.mode = "enable"

	def _updateCallback(self, msg = ""):
		if msg:
			logging.debug("LASER_CLASS callback: " + msg)
			m = regex.match("(\w+) \D*([\d.]+)%", msg)
			if m:
				f = float(m.group(2))
				if m.group(1) == "Generating":
					self.mode = "prepare"
					self.progress = f
				if m.group(1) == "Sending":
					self.mode = "running"
					self.progress = f
		time.sleep(0.5)

	def _waitWhileBussy(self, timeout=0):
		logging.debug("LASER_CLASS _waitWhileBussy ...")
		DELAY = 0.05
		timeremaining = float(timeout)
		status = 0
		while status != self.COMPLETED:
			time.sleep(DELAY)
			status = self.nano.say_hello()
			if status != self.OK:
				logging.debug("LASER_CLASS _waitWhileBussy status: " + str(status))
			timeremaining -= DELAY
			if timeout and timeremaining < 0:
				logging.error("LASER_CLASS _waitWhileBussy TIMEOUT")
				return False
		logging.debug("LASER_CLASS _waitWhileBussy OK")
		return True

	def _waitForEndstop(self, timeout=0):
		logging.debug("LASER_CLASS _waitForEndstop ...")
		DELAY = 0.05
		timeremaining = float(timeout)
		status = 0
		while status != self.HOMED:
			time.sleep(DELAY)
			status = self.nano.say_hello()
			if status != self.OK:
				logging.debug("LASER_CLASS _waitForEndstop status" + str(status))
			timeremaining -= DELAY
			if timeout and timeremaining < 0:
				logging.error("LASER_CLASS _waitForEndstop TIMEOUT")
				return False
		logging.debug("LASER_CLASS _waitForEndstop OK")
		return True


	def processVector(self, polylines, feedRate, originX = 0, originY = 0, repeat = 1):
		if not( self.isInit() ) or self.isActive(): return
		try:
			self.mode = "prepare"
			logging.info("LASER_CLASS processVector ...")
			self.active = True
			self.progress = 0
			self.repeat = repeat

			# convert polylines to ecoords
			ecoords = []
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
			data = []
			egv_inst = egv(target=lambda s:data.append(s))
# TODO			startX = -(originX - self.endstopPos[0]),
# TODO			startY = -(originY - self.endstopPos[1]),
			egv_inst.make_egv_data(
				ecoords,
				startX=0,
				startY=0,
				units='mm',
				Feed=feedRate,
				board_name=self.board_name,
				Raster_step=0,
				update_gui=self._updateCallback,
				stop_calc=self._stop_flag
			)
			if self._stop_flag[0]:
				raise  RuntimeError("stopped")
			idle()
			# run laser
			self.mode = "running"
			while repeat > 0:
				if self._stop_flag[0]:
					raise  RuntimeError("stopped")
				idle()

				# send data to laser
				self._endStop()
				idle()
				logging.debug("goto origin: " + str(originX) + " / " + str(originY))
				self._internalMoveTo(originX, originY)
				idle()
				logging.debug("send_data ...")
				self.nano.send_data(data, self._updateCallback, self._stop_flag, passes=repeat, preprocess_crc=False)
				logging.debug("send_data finished")
				# wait for laser to finish
				self._waitWhileBussy()
				logging.debug("buffer empty")
				# decrease repeat counter
				repeat = 0 # TODOint(repeat) - 1

			self.progress = 100
			self.mode = "finished"
			logging.info("LASER_CLASS processVector finished")
# TODO			self._internalHome()

		except Exception as e:
			if self._stop_flag[0]:
				self.mode = "stopped"
			else:
				self.mode = "error"
				logging.error("processVector ERROR: " + str(e))
		finally:
			self.active = False


	def processRaster(self, raster, feedRate, originX = 0, originY = 0, repeat = 1):
		return

