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

##############################################################################

from nano_library import K40_CLASS

class LASER_CLASS:
	def __init__(self):
		print ("LASER_CLASS __init__")
		self.unit = ""
		self.scale = 0
		self.x = False
		self.y = False
		self.nano = K40_CLASS()

	def __del__(self):
		print ("LASER_CLASS __del__")
		self.release()

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

	def isInit(self):
		return ( self.nano.dev != None )

	def release(self):
		if not( self.isInit() ): return
		print("LASER_CLASS released")
		self.x = False
		self.y = False
		self.unlock()
		time.sleep(0.5)
		self.nano.release_usb()
		time.sleep(0.5)

	def unlock(self):
		if not( self.isInit() ): return
		print("unlock")
		self.x = False
		self.y = False
		self.nano.unlock_rail()

	def read_data(self):
		if not( self.isInit() ): return
		return self.nano.read_data()

	def home(self):
		if not( self.isInit() ): return
		print("home")
		self.nano.reset_usb()
		self.nano.home_position()
		self.x = 0
		self.y = 0

	# move relative to current position
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

	# go to absolute position
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
		self.nano.e_stop();

