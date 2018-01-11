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
	def __init__(self, width=100, height=100, home='top-left', homeOff=[0,0], defaultOrigin='center', filemanager = None, laser = None):
		self._drawings = dict()
		self.laser = laser
		self.size = [width, height]
		self.home = home
		self.homeOff = homeOff
		self.filemanager = filemanager
		self.defaultOrigin = defaultOrigin
		self.indicator = False
		self.indicatorOff = [0,0]
		self.reset()

	def reset(self):
		if self.home == 'top-left':
			self.homePos = [ 0, self.size[1] ]
		elif self.home == 'top-right':
			self.homePos = [ self.size[0], self.size[1] ]
		elif self.home == 'bottom-left':
			self.homePos = [ 0, 0 ]
		elif self.home == 'bottom-right':
			self.homePos = [ self.size[0], 0 ]
		else: # unknown
			self.home = [ self.size[0]/2, self.size[1]/2 ]
			print("ERROR: unknown home location")
		self.homePos[0] += self.homeOff[0]
		self.homePos[1] += self.homeOff[1]
			
		if self.defaultOrigin == 'top-left':
			self.workspaceOrigin = [ 0, self.size[1] ]
		elif self.defaultOrigin == 'top-right':
			self.workspaceOrigin = [ self.size[0], self.size[1] ]
		elif self.defaultOrigin == 'bottom-left':
			self.workspaceOrigin = [ 0, 0 ]
		elif self.defaultOrigin == 'bottom-right':
			self.workspaceOrigin = [ self.size[0], 0 ]
		else: # center
			self.workspaceOrigin = [ self.size[0]/2, self.size[1]/2 ]
		self.workspaceOrigin[0] -= self.homePos[0]
		self.workspaceOrigin[1] -= self.homePos[1]

		self.indicator = False

	def update(self):
		print("workspace has been updated -> reload")
		if len(self._drawings) > 0:
			boundingBoxes = []
			for id in self._drawings:
				boundingBoxes.append(self._drawings[id].getBoundingBox())
			boundingBox = product = reduce(
				(lambda x, y: [min(x[0], y[0]), min(x[1], y[1]), max(x[2], y[2]), max(x[3], y[3])]), boundingBoxes)
		else:
			boundingBox = [0, 0, 0, 0]
		if self.indicator == 'top-left':
			dx = boundingBox[0]
			dy = boundingBox[3]
		elif self.indicator == 'top-right':
			dx = boundingBox[2]
			dy = boundingBox[3]
		elif self.indicator == 'bottom-left':
			dx = boundingBox[0]
			dy = boundingBox[1]
		elif self.indicator == 'bottom-right':
			dx = boundingBox[2]
			dy = boundingBox[1]
		else:
			dx = 0
			dy = 0
		self.indicatorOff = [dx,dy]

			
	def add(self, drawing):
		# create SVG image for displaying
		filename = drawing.name + "-" + str(drawing.id)
		self.filemanager.saveSVG(drawing, filename)
		drawing.url = urlForceReload(drawing.url)

		# auto align drawing
		if self.defaultOrigin == 'top-left':
			drawing.alignRightOfAxis()
			drawing.alignUnderAxis()
		elif self.defaultOrigin == 'top-right':
			drawing.alignLeftOfAxis()
			drawing.alignUnderAxis()
		elif self.defaultOrigin == 'bottom-left':
			drawing.alignRightOfAxis()
			drawing.alignAboveOfAxis()
		elif self.defaultOrigin == 'bottom-right':
			drawing.alignLeftOfAxis()
			drawing.alignAboveOfAxis()
		else:  # unknown
			# do nothing
			pass

		# add to workspace
		self._drawings[drawing.id] = drawing
		self.update()

	def load(self, path):
		drawing = self.filemanager.open(path)
		if drawing:
			self.add(drawing)

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
			"indicator": self.indicator if (self.workspaceOrigin[0]+self.indicatorOff[0])==self.laser.x and
											(self.workspaceOrigin[1]++self.indicatorOff[1])==self.laser.y
											else False,
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
				itemJson['color'] = design.COLOR_MIXED
			json["items"].append(itemJson)
		
		return json
				
	def setParams(self, params):

		# update indicator
		indicator = params.get('indicator', self.indicator)
		if indicator:
			self.setIndicator( indicator )

		# update workspace origin
		self.setWorkspaceOrigin( params.get('workspaceOrigin', self.workspaceOrigin) )

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

	def setIndicator(self, params):
		# update indicator location
		if params:
			self.indicator = params
			self.update()
			self.setWorkspaceOrigin(self.workspaceOrigin)

	def setWorkspaceOrigin(self, params):
		# update workspace origin
		self.workspaceOrigin = params

		# move laser to indicator position
		if self.indicator and self.laser:
			self.laser.moveTo(self.workspaceOrigin[0]+self.indicatorOff[0], self.workspaceOrigin[1]+self.indicatorOff[1])
