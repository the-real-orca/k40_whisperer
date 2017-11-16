#!/usr/bin/env python

import utils

class TaskManager:
	def __init__(self, laser, workspace):
		self.laser = laser
		self.workspace = workspace

	def runVectorTask(self, params = None):
	
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

		# connect segmented polylines and reorder from inner to outer
		draw = utils.Drawing(self.task.name, polylines)
		draw.optimize()
		draw.saveSVG("HTML/images/cut.svg")
		
		# send polylines to laser
		self.laser.processVector(draw.polylines, params.feedRate) #TODO additional params
		
