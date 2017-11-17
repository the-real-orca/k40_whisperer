
class Workspace:
	def __init__(self, width=100, height=100, originOffset=[0,0]):
		self.drawings = dict()
		self.size = [width, height]
		self.originOffset = originOffset

	def update(self):
		print("workspace has been updated -> reload")
		# TODO

	def add(self, drawing, url):
		self.drawings[drawing.id] = [drawing, url]
		self.update()

	def remove(self, id):
		del self.drawings[id]
		self.update()

