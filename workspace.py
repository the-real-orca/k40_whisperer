import utils

class Drawing:
	def __init__(self, name, polylines)
		self.name = name
		self.polylines = polylines

class Workspace:
	def __init__(self, width=100, height=100, originOffset=[0,0]):
		self.drawings = []
		self.size = [width, height]
		self.originOffset = originOffset
		
	def update()
		print("workspace has been updated -> reload")
		# TODO
		
	def add(drawing):
		self.drawings.append(drawing)
		self.update()
	