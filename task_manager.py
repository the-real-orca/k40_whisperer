import design_utils as design

import time
def idle():
	time.sleep(0.1)

class Task:
	VECTOR = "vector"
	RASTER = "raster"

	def __init__(self, id, name=None, colors=[design.BLACK], speed=100, intensity=0, type=VECTOR, repeat=1):
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
		self.status = "---"
		self.progress = 0.0


class TaskManager:
	def __init__(self, laser, workspace):
		self.laser = laser
		self.workspace = workspace
		self.tasks = []
		self._activeTask = None

	def toJson(self):
		json = []
		for task in self.tasks:
			if task == self._activeTask:
				task.status = self.laser.mode
				task.progress = self.laser.progress
			t = {
				"id": task.id,
				"name": task.id,
				"colors": task.colors,
				"speed": task.speed,
				"intensity": task.intensity,
				"type": task.type,
				"repeat": task.repeat,
				"status": task.status,
				"progress": task.progress
			}
			json.append(t)
		return json

	def updated(self):
		# reset tasks
		self._activeTask = None
		for t in self.tasks:
			t.status = "---"
			t.progress = 0.0
			print(t.id)

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
		task.colors = params.get('colors', [design.BLACK])
		task.speed = float(params.get('speed', 100))
		task.intensity = float(params.get('intensity', 0))
		task.type = params.get('type', Task.VECTOR)
		task.repeat = int(params.get('repeat', 0))

		self.updated()

	def run(self, id = None):
		if self.laser.isActive():
			return

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

		for task in self.tasks:
			task.status = "wait" if task in tasks else "---"
			task.progress = 0.0

		self.laser.enable()
		for task in tasks:
			self._activeTask = task
			if task.type == Task.VECTOR:
				self.runVectorTask(task)
			else:
				self.runRasterTask(task)
			# get final status of task
			idle()
			task.status = self.laser.mode
			task.progress = self.laser.progress
			if task.status == "error" or task.status == "stopped":
				break
		self.laser.home()

	def runVectorTask(self, task):
		try:
			# get polylines from all drawings in workspace and apply offset to drawing
			drawings = self.workspace.getItems()
			polylines = [ polyline.applyOffset(drawings[k].position) for k in drawings for polyline in drawings[k].polylines]
			print("drawingPolylines", polylines)

			# filter polylines by task color
			print("task.colors",task.colors)
			polylines = list(filter(lambda p: p.color in task.colors, polylines))
			if len(polylines) == 0:
				self.laser.mode = "empty"
				self.laser.progress = 100.0
				return

			# connect segmented polylines and reorder from inner to outer
			print("optimize polylines", polylines)
			draw = design.Drawing(polylines, name=task.name)
			draw.optimize(ignoreColor=True)

			# to laser
			print("send to laser")
			self.laser.processVector(draw.polylines,
				originX=self.workspace.homeOff[0]+self.workspace.workspaceOrigin[0],
				originY=self.workspace.homeOff[1]+self.workspace.workspaceOrigin[1],
				feedRate=task.speed,
				repeat=task.repeat) #TODO intensity
		finally:
			pass


