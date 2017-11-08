#!/usr/bin/env python

import utils

class TaskManager:
	def __init__(self, laser):
		self.laser = laser


	def run(self, params):
		# TODO process data
		# list of lines (dx, dy, polygon index)
		polylines = [ \
			utils.PolyLine(points=[[0,0], [10,0], [10,-10], [0,-10], [0,0]]), \
			utils.PolyLine(points=[[20,0], [30,0], [20,-10], [20,0]]) \
			]

		polylines = utils.optimizeLines(polylines)

		feedRate = 50
		self.laser.processVector(polylines, feedRate) #TODO additional params
