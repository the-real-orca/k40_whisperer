import re
import design_utils as design
import time

def urlForceReload(url):
	params = []
	parts=url.split('?')
	if len(parts) > 1:
		params = parts[1].split('&')
		params = list(filter(lambda x: not(x.startswith("reload=")), params))
	params.append( "reload=" + str(int(time.time()*10)) )
	url = parts[0] + "?" + "&".join(params)
	return url


class Workspace:
	def __init__(self, width=100, height=100, homePos=[0,0], filemanager = None):
		self._drawings = dict()
		self.size = [width, height]
		self.homePos = homePos
		self.filemanager = filemanager
		self.update()

	def update(self):
		self.workspaceOrigin = [ self.size[0]/2, self.size[1]/2 ]
		print("workspace has been updated -> reload")
		# TODO

	def add(self, drawing):
		# create SVG image for displaying
		filename = drawing.name + "-" + str(drawing.id)
		self.filemanager.saveSVG(drawing, filename)
		drawing.url = urlForceReload(drawing.url)

		# add to workspace
		self._drawings[drawing.id] = drawing
		self.update()

	def remove(self, id):
		del self._drawings[id]
		self.update()

	def getItems(self):
		return self._drawings

	def clear(self):
		self._drawings.clear()
		self.update()

	def toJson(self):
		json = {
			"width": self.size[0],
			"height": self.size[1],
			"homePos": self.homePos,
			"workspaceOrigin": self.workspaceOrigin,
			"viewBox": [-self.workspaceOrigin[0], -self.workspaceOrigin[1], self.size[0], self.size[1]],
			"items": []

		}
		for id in self._drawings:
			item = self._drawings[id]
			viewBox = item
			itemJson = {
				"id": item.id,
				"name": item.name,
				"x": item.position[0],
				"y": item.position[1],
				"width": item.size[0],
				"height": item.size[1],
				"viewBox": item.getViewBox(0)[0],
				"boundingBox": item.getBoundingBox(),
				"url": item.url
			}
			colors = map(lambda x: x.color, item.polylines)
			if len(set(colors)) == 1:
				itemJson['color'] = item.polylines[0].color
			else:
				itemJson['color'] = COLOR_MIXED
			json["items"].append(itemJson)
		
		return json
				
	def setParams(self, params):

		# find drawing by id
		id = params.get('id', None)
		if not(id): return
		drawing = self._drawings.get(id, None)
		if not(drawing): return

		# set drawing params
		changed = False
		
		# position
		x = params.get('x', drawing.position[0]); y = params.get('y', drawing.position[1])
		dx = params.get('dx', 0); dy = params.get('dy', 0)
		pos = [float(x) + float(dx), float(y) + float(dy)]
		if drawing.position != pos:
			drawing.position = pos
			changed = True
			
		# color
		color = params.get('color', None)
		if color and color != design.COLOR_MIXED:
			for line in drawing.polylines:
				if line.color != color:
					line.color = color
					line.update()
					changed = True
			drawing.update()
				
		# update drawing and workspace
		if changed:
			drawing.update()
			self.filemanager.saveSVG(drawing, drawing.path)
			drawing.url = urlForceReload(drawing.url)
			self.update()
				
		
		