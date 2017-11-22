
class Workspace:
	def __init__(self, width=100, height=100, originOffset=[0,0]):
		self.drawings = dict()
		self.size = [width, height]
		self.originOffset = originOffset
		self.drawingsOrigin = originOffset[:]

	def update(self):
		print("workspace has been updated -> reload")
		# TODO

	def add(self, drawing):
		self.drawings[drawing.id] = drawing
		self.update()

	def remove(self, id):
		del self.drawings[id]
		if len(self.drawings):
			self.drawingsOrigin = self.originOffset[:]
		self.update()

	def clear(self):
		self.drawings.clear()
		self.drawingsOrigin = self.originOffset[:]
		self.update()

	def setParams(self, params):
		id = params.get('id', None)
		if not(id): return

		# find task by id
		drawing = self.drawings.get(id, None)
		if not(drawing): return

		# set drawing params
#TODO		drawing.color = params.get('color', design.BLACK)
		drawing.position = [float(params.get('x', 0)), float(params.get('y', 0))]
