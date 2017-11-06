#!/usr/bin/env python



class TaskManager:
	def __init__(self, laser):
		self.laser = laser


	def run(self, params):
		# TODO process data
		# list of lines (dx, dy, polygon index)
		lines = [ [0,0,0], [10,0,0], [10,-10,0], [0,-10,0], [0,0,0], \
		   [20,0,1], [30,0,1], [20,-10,1], [20,0,1] ] 	# simulate data
		print("lines", lines)
		#TODO lines = self.optimize_paths(lines)
		feedRate = 50
		self.laser.processVector(lines, feedRate) #TODO additional params
