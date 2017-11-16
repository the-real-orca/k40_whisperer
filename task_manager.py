#!/usr/bin/env python

import utils

class Task:
	VECTOR = "vector"
	RASTER = "raster"

	def __init__(self, id, colors=[utils.BLACK], speed=100, intensity=1, type=VECTOR):
		self.id = id
		self.name = id
		self.colors = colors
		self.speed = speed
		self.intensity = intensity
		self.type = type
	

class TaskManager:
	def __init__(self, laser, workspace):
		self.laser = laser
		self.workspace = workspace
		self.tasks = [ Task("cut", [utils.BLACK, utils.RED], 50, 10) ]

	def run(self, params = None):
		# TODO
			
		self.runVectorTask(self.tasks[0])
		
	def runVectorTask(self, task):
		# get polylines from all drawings in workspace	
		drawings = self.workspace.drawings
		drawingPolylines = [drawings[k].polylines for k in drawings] 
		
		# filter polylines by task color
		polylines = list(filter(lambda p: p.color in task.colors, drawingPolylines))

		# connect segmented polylines and reorder from inner to outer
		draw = utils.Drawing(task.id, polylines)
		draw.optimize()
		draw.saveSVG("HTML/images/cut.svg")
		
		# send polylines to laser
		self.laser.processVector(draw.polylines, task.speed) #TODO intensity
		

		