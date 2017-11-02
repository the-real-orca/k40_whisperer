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
		self.unit = ""
		self.scale = 0
		self.x = False
		self.y = False
		self.nano = False

	def init(self, unit, verbose=False):
		# set unit
		if unit == "in" or unit == "inch":
			self.unit = "in"
			self.scale = 1000
		else:
			self.unit = "mm"
			self.scale = 1000 / 25.4
			
		# connect and init laser main board
		self.release()
		self.nano = K40_CLASS()
		self.nano.initialize_device(verbose)
		self.x = False
		self.y = False

	def isInit(self):
		return ( self.nano != False )
		
	def release(self):
		if not( self.isInit() ): return
		self.unlock()
		time.sleep(0.5)
		self.nano.release_usb()
		time.sleep(0.5)
		self.nano = False
		

	def unlock(self):
		if not( self.isInit() ): return
		self.nano.unlock_rail()
		
	def read_data(self):
		if not( self.isInit() ): return
		return self.nano.read_data()
				
	
	def home(self):
		if not( self.isInit() ): return
		self.nano.home_position()
		self.x = 0
		self.y = 0

	# move relative to current position
	def move(self, dx, dy, speed):
		if not( self.isInit() ): return
# TODO check movement area
		dxmils = round(dx*self.scale)
		dymils = round(dy*self.scale)
		self.nano.rapid_move(dxmils, dymils)
		self.x += dxmils/self.scale
		self.y += dymils/self.scale
		
	# go to absolute position
	def goto(self, x, y):
		if not( self.isInit() ): return
# TODO check movement area
		dxmils = round( (x-self.x) *self.scale)
		dymils = round( (y-self.y) *self.scale)
		self.nano.rapid_move(dxmils, dymils)
		self.x += dxmils/self.scale
		self.y += dymils/self.scale
	
	def stop(self):
		if not( self.isInit() ): return
		self.nano.e_stop();

