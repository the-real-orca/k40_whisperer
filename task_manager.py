#!/usr/bin/env python

import utils

class Task:
	VECTOR = "vector"
	RASTER = "raster"

	def __init__(self, id, name=None, colors=[utils.BLACK], speed=100, intensity=0, type=VECTOR, repeat=1):
		self.id = id
		if name:
			self.name = name
		else:
			self.name = id
		self.colors = colors
		self.speed = speed
		self.intensity = intensity
		self.type = type
		self.repeat = repeat


class TaskManager:
	def __init__(self, laser, workspace):
		self.laser = laser
		self.workspace = workspace
		self.tasks = []

	def setParams(self, params):
		id = params.get('id', None)
		if not(id): return

		# find task by id
		for task in self.tasks:
			if task.id == id:
				break
		else:
			# create new task
			task = Task(id)
			self.tasks.append(task)

		# set task params
		task.id = params.get('id')
		task.name = params.get('name', task.id)
		task.colors = params.get('colors', [utils.BLACK])
		task.speed = float(params.get('speed', 100))
		task.intensity = float(params.get('intensity', 0))
		task.type = params.get('type', Task.VECTOR)
		task.repeat = int(params.get('repeat', 0))

	def run(self, id = None):
		if id is None:
			# process all tasks
			tasks = self.tasks
		else:
			# find task by id
			for task in self.tasks:
				if task.id == id:
					tasks = [task]
					break
			else:
				# id not found
				return
		for task in tasks:
			for i in range(task.repeat):
				if task.type == Task.VECTOR:
					self.runVectorTask(task)
				else:
					self.runRasterTask(task)

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
		self.laser.processVector(draw.polylines, feedRate=task.speed) #TODO intensity


