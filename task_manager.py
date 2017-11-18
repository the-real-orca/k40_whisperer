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
		# get polylines from all drawings in workspace and translate to laser coordinates
		drawings = self.workspace.drawings
		drawingPolylines = [ polyline.applyOffset(drawings[k].position) for k in drawings for polyline in drawings[k].polylines]
		print("drawingPolylines", drawingPolylines)

		# filter polylines by task color
		print("task.colors",task.colors)
		polylines = list(filter(lambda p: p.color in task.colors, drawingPolylines))

		# connect segmented polylines and reorder from inner to outer
		draw = utils.Drawing(task.id, polylines)
		draw.optimize(ignoreColor=True)
		draw.saveSVG("HTML/uploads/cut.svg")

		# send polylines to laser
		if self.laser:
			self.laser.processVector(draw.polylines, feedRate=task.speed) #TODO intensity


