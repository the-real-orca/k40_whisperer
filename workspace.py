import re
import drawing_utils
import time
import logging

def urlForceReload(url):
	params = []
	parts=url.split('?')
	logging.debug("urlForceReload: " + url)
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
			logging.error("ERROR: unknown home location")

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
		logging.info("workspace has been updated -> reload")
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

		# move laser to indicator position
		if self.indicator and self.laser:
			self.laser.moveTo(self.workspaceOrigin[0]+self.indicatorOff[0], self.workspaceOrigin[1]+self.indicatorOff[1])

			
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
		drawing.sortIndex = time.time()
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

		drawings = sorted(self._drawings.values(), key=lambda(item): item.sortIndex)
		for item in drawings:
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
				itemJson['color'] = drawing_utils.COLOR_MIXED
			json["items"].append(itemJson)

		return json
				
	def itemSetParams(self, params):
		changed = False

		# find drawing by id
		id = params.get('id', None)
		if not(id): return
		drawing = self._drawings.get(id, None)
		if not(drawing): return

		# position
		x = params.get('x', drawing.position[0]); y = params.get('y', drawing.position[1])
		dx = params.get('dx', 0); dy = params.get('dy', 0)
		pos = [float(x) + float(dx), float(y) + float(dy)]
		if drawing.position != pos:
			drawing.position = pos
			changed = True
			
		# color
		color = params.get('color', None)
		if color and color != drawing_utils.COLOR_MIXED:
			for line in drawing.polylines:
				if line.color != color:
					line.color = color
					line.update()
					changed = True
			drawing.update()
				
		# update drawing and workspace
		if changed:
			drawing.update()
			self.filemanager.saveSVG(drawing)
			drawing.url = urlForceReload(drawing.url)
			self.update()

	def itemRotate(self, params):
		changed = False

		# find drawing by id
		id = params.get('id', None)
		if not (id): return
		drawing = self._drawings.get(id, None)
		if not (drawing): return

		# rotate
		angle = params.get('angle', None)
		if angle == 90:
			drawing.rotateLeft()
			changed = True
		if angle == -90:
			drawing.rotateRight()
			changed = True

		# update drawing and workspace
		if changed:
			drawing.update()
			self.filemanager.saveSVG(drawing)
			drawing.url = urlForceReload(drawing.url)
			self.update()

	def itemMirror(self, params):
		changed = False

		# find drawing by id
		id = params.get('id', None)
		if not (id): return
		drawing = self._drawings.get(id, None)
		if not (drawing): return

		# rotate
		mirror = params.get('mirror', None)
		if mirror == "X":
			drawing.flipY()
			changed = True
		if mirror == "Y":
			drawing.flipX()
			changed = True

		# update drawing and workspace
		if changed:
			drawing.update()
			self.filemanager.saveSVG(drawing)
			drawing.url = urlForceReload(drawing.url)
			self.update()


	def setParams(self, params):
		changed = False

		# update indicator
		indicator = params.get('indicator', self.indicator)
		if indicator:
			self.setIndicator(indicator, False)
			changed = True

		# update workspace origin
		workspaceOrigin = params.get('workspaceOrigin')
		if workspaceOrigin:
			self.setWorkspaceOrigin(workspaceOrigin, False)
			changed = True

		# update drawing and workspace
		if changed:
			self.update()

	def setIndicator(self, params, update=True):
		# update indicator location
		if params:
			self.indicator = params

		if update:
			self.update()

	def setWorkspaceOrigin(self, params, update=True):
		# update workspace origin
		self.workspaceOrigin = params

		if update:
			self.update()