import design_utils as design

import time
def idle():
	time.sleep(0.1)

class Task:
	VECTOR = "vector"
	RASTER = "raster"

	def __init__(self, id, name="", colors=[design.BLACK], speed=100, intensity=0, type=VECTOR, repeat=1):
		self.id = id
		self.name = name
		self.colors = colors
		self.speed = speed
		self.intensity = intensity
		self.type = type
		self.repeat = repeat
		self.status = "---"
		self.progress = 0.0

class Profile:
	def __init__(self, id, name="", tasks=[]):
		self.id = id
		self.name = name
		self.tasks = []
		self.setTasks(tasks)

	def setTasks(self, tasks):
		self.tasks = []
		for task in tasks:
			self.tasks.append(Task(id=task['id'], name=task.get('name', ""), colors=task.get('colors', [design.BLACK]), speed=task.get('speed', 0), type=task.get('type', None),
		                              repeat=task.get('repeat', 1)))

	def toJson(self):
		return {
			'id': self.id,
			'name': self.name,
			'tasks': self.tasksToJson()
		}

	def tasksToJson(self):
		list = []
		for task in self.tasks:
			json = {
				'id': task.id,
				'name': task.name,
				'colors': task.colors,
				'speed': task.speed,
				'intensity': task.intensity,
				'type': task.type,
				'repeat': task.repeat,
				'status': task.status,
				'progress': task.progress
			}
			list.append(json)
		return list

class TaskManager:
	def __init__(self, laser, workspace):
		self.laser = laser
		self.workspace = workspace
		self.profiles = {}
		self._activeProfile = None
		self._activeTask = None

	def toJson(self):
		json = {}

		# update status and progress of active task
		if self._activeProfile:
			for task in self._activeProfile.tasks:
				if task == self._activeTask:
					task.status = self.laser.mode
					task.progress = self.laser.progress

		# add profiles list
		json['profiles'] = []
		for key in self.profiles:
			profile = self.profiles[key]
			json['profiles'].append(profile.toJson())

		# active profile
		if self._activeProfile:
			json['active'] = self._activeProfile.toJson()
		else:
			json['active'] = None
		return json


	def update(self):
		# reset tasks
		self._activeTask = None
		if self._activeProfile:
			for task in self._activeProfile.tasks:
				task.status = "---"
				task.progress = 0.0


	def setActiveProfile(self, params):
		id = params.get('id', None)
		if not(id): return

		# update profile
		if id not in self.profiles:
			profile = Profile(id, name=params.get('name', ""), tasks=params.get('tasks', []))
			self.profiles[id] = profile
		else:
			profile = self.profiles[id]
			profile.name = params.get('name', profile.name)
			if 'tasks' in params:
				profile.setTasks(params.get('tasks', profile.tasks))

		self._activeProfile = profile
		self._activeTask = None
		self.update()


	def removeProfile(self, id):
		del self.profiles[id]
		if id == self._activeProfile.id:
			# removed active profile -> switch to another profile
			for key in self.profiles:
				self._activeProfile = self.profiles[key]
				break
			else:
				self._activeProfile = None
				self._activeTask = None
		self.update()


	def run(self, id = None):
		profile = self._activeProfile
		if self.laser.isActive() or not(profile):
			return

		if id is None:
			# process all tasks
			tasks = profile.tasks
		else:
			# find task by id
			for task in profile.tasks:
				if task.id == id:
					tasks = [task]
					break
			else:
				# id not found
				return

		for task in profile.tasks:
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


