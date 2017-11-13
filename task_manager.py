#!/usr/bin/env python

import utils

class TaskManager:
	def __init__(self, laser, workspace):
		self.laser = laser
		self.workspace = workspace

	def run(self, params = None):
	
		#TODO default params
		params = {
			feedRate: 50
			}
			
		drawings = self.workspace.drawings
		drawingPolylines = [drawings[k].polylines for k in drawings] 

		#TODO for selected tasks ...
		colors = [utils.BLACK, utils.RED]
		
		# filter polylines by task color
		polylines = list(filter(lambda p: p.color in colors, drawingPolylines))

		# connect segmented polylines and
		# TODO reorder from inner to outer
		polylines = utils.optimizeLines(polylines)

		# send polylines to laser
		self.laser.processVector(polylines, params.feedRate) #TODO additional params
		
