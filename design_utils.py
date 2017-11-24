import time
import numpy as np
import matplotlib.path as path



BLACK = "black"      #(0, 0, 0)
WHITE = "white"      #(255, 255, 255)
RED = "red"          #(255, 0, 0)
GREEN = "green"      #(0, 255, 0)
BLUE = "blue"        #(0, 0, 255)
ORANGE = "orange"    #(255, 165, 0)	~ yellow
CYAN = "darkcyan"    #(0, 140, 140) ~ cyan
MAGENTA = "magenta"  #(255, 0, 255)
COLOR_MIXED = "mix"

class Polyline:
	def __init__(self, points = [], color = BLACK):
		self.color = color
		self._points = np.array(points)

	def __repr__(self):
		str = "(" + self.color
		str += ": " + self._points[:2].__str__()
		if len(self._points) >= 2:
			str += "..."
		str += ")"
		str = str.replace("\n", ",")
		return str

	def __bool__(self):
		return len(self._points) > 0

	def update(self):
		pass

	def getPoint(self, index):
		if index >= len(self._points):
			return [0,0]
		else:
			return self._points[index]
		
	def getPoints(self):
		return self._points

	def applyOffset(self, off):
		return Polyline(self._points + np.array(off), self.color)

	def encode(self):
		return {
			"color": self.color,
			"points": self.getPoints()
			}

	def appendPolyline(self, polyline):
		points = polyline.getPoints()
		if len(points)==0:
				return
		if len(self._points)>0:
			if equal(points[0], self._points[-1]):
				s = 1
			else:
				s = 0
			self._points = np.concatenate((self._points, points[s:]), axis=0)
		else:
			self._points = np.array(points)
		return self

	def appendPoint(self, p):
		if len(self._points)>0:
			self._points = np.concatenate((self._points,[p]), axis=0)
		else:
			self._points = np.array([p])
		return self

	def append(self, p):
		if isinstance(p, Polyline):
			return self.appendPolyline(p)
		else:
			return self.appendPoint(p)

	def reverse(self):
		self._points = self._points[::-1]
		return self

	def contains(self, polyline):
		if len(self._points)==0 or not(isinstance(polyline, Polyline)) or len(polyline.getPoints())==0:
			return False
		p = path.Path(self._points, closed=True)
		return all(p.contains_points(polyline.getPoints()))

	def flipX(self):
		if len(self._points)>0:
			self._points[:,0] = -self._points[:,0]
		return self

	def flipY(self):
		if len(self._points)>0:
			self._points[:,1] = -self._points[:,1]
		return self


class Drawing:
	def __init__(self, polylines, name=None, position=[0,0]):
		self.id = int(time.time()*10)
		self.name = name
		if len(polylines) > 0:
			for line in polylines:
				print("line", line)
				if not(isinstance(line, Polyline)):
					raise Exception("TYPE ERROR should be: Polyline, is: " + line.__class__.__name__)
		self.polylines = polylines
		self.position = position
		self._strokeWidth = 0.4
		self.update()

	def update(self):
		viewBox, strokeWidth = self.getViewBox(0)
		self.size = viewBox[2:4]
		return self

	def getViewBox(self, strokeWidth = None):
		if strokeWidth is None: strokeWidth = self._strokeWidth
		xMin=1e12; xMax=-1e12
		yMin=1e12; yMax=-1e12
		for line in self.polylines:
			points = line.getPoints()
			if len(points)==0:
				continue
			xMin = min( np.append(points[:,0], xMin) )
			xMax = max( np.append(points[:,0], xMax) )
			yMin = min( np.append(points[:,1], yMin) )
			yMax = max( np.append(points[:,1], yMax) )
		width = xMax - xMin +strokeWidth
		height = yMax - yMin +strokeWidth
		return [xMin -strokeWidth/2, yMin -strokeWidth/2, width, height], strokeWidth

	def flipX(self):
		for line in self.polylines:
			line.flipX()
		return self

	def flipY(self):
		for line in self.polylines:
			line.flipY()
		return self

	def optimize(self, ignoreColor=False):
		self.combineLines(ignoreColor)
		self.reorderInnerToOuter()
		return self

	def combineLines(self, ignoreColor=False):
		# combine polyline segments
		i = 0
		while i < len(self.polylines):    # cannot use enumerate() since we change the list on-the-fly
			j = 0
			a = self.polylines[i]
			pointsA = a.getPoints()
			if len(pointsA)==0:
				self.polylines.pop(i)
				continue
			while j < len(self.polylines):
				b = self.polylines[j]
				pointsB = b.getPoints()
				if len(pointsB)==0:
					j += 1
					continue
				connectedEndStart = equal(pointsA[-1], pointsB[0], dim=2)	# compare x,y end point with start point of segments
				connectedEndEnd = equal(pointsA[-1], pointsB[-1], dim=2)	# compare x,y end point with end point of segments
				if i != j and (connectedEndStart or connectedEndEnd) \
					and (a.color == b. color or ignoreColor):
					if connectedEndEnd:
						b.reverse()
					# connect segments
					a.append(b)
					# remove added segment from path and re-adjust indizes
					self.polylines.pop(j)
					if j < i: i -= 1
				else:
					j += 1
			i += 1
		return self


	def reorderInnerToOuter(self):
		# build polyline tree
		class Node(object):
			def __init__(self, data):
				self.data = data
				self.children = []

		if len(self.polylines) < 2:
			return self.polylines
		
		# sort polylines by X coordinate of start point
		self.polylines = sorted(self.polylines, key=lambda line: line.getPoint(0)[0])
			
		print("build polyline tree +++++++++++++++++++++++++++++++++++++++++++++++++++++++")
		baseGroup = []
		for polyline in self.polylines:
			group = baseGroup
			print("test", polyline,"-----------------------------------")
			# recursively test if polyline is inside any element of the current group
			while ( group != None):
				print("group", [a.data for a in group])
				for node in group:
					# test if current polyline is inside of nodes polyline
					if node.data.contains(polyline):
						# dive recursively into node
						print("dive into", node.data)
						group = node.children
						break

					# test if nodes polyline is inside of current polyline
					if polyline.contains(node.data):
						# created node for current polyline and wrap surronded nodes
						print("envelop", node.data)

						n = Node(polyline)
						n.children = [x for x in group if polyline.contains(x.data)]
						# remove wrapped nodes from group (in-place manipulation!)
						for x in n.children:
							group.remove(x)
						group.append(n)

						print("new group", [a.data for a in group])
						# exit
						group = None
						break
				else:
					# add new element to group
					group.append( Node(polyline) )
					print("append", polyline,"to", group[0].data)
					group = None
					break

		# walk through tree bottom->up
		polylines = []
		node = Node(None)
		node.children = baseGroup
		childIndex = 0
		stack = []
		print("walk through tree +++++++++++++++++++++++++++++++++++++++++++++++++++++++")
		while True:
			print("node", node.data, len(node.children), childIndex)
			# append polyline if all children have been processed
			if len(node.children) <= childIndex:
				if node.data:
					polylines.append(node.data)
				if len(stack) > 0:
					node, childIndex = stack.pop()
					continue
				else:
					break

			# dive into next child
			next = node.children[childIndex]
			stack.append([node, childIndex+1])
			childIndex = 0
			node = next

		print("optimized polylines")
		for p in polylines: print(p)
		self.polylines = polylines
		return self


def equal(a, b, tol=0.001, dim=False):
	# use max distance for comparing
	d = abs(np.array(a)-np.array(b))
	if dim:
		d = d[:dim]
	if max(d) > tol:
		return False
	else:
		return True


def makePolylines(lines, scale=1, color=BLACK):
	polylines=[]
	old = [0,0,0,0]
	p = Polyline([], color)
	for line in lines:
		coords = np.array(line)*scale
		# check and see if we need to move to a new discontinuous start point
		if not(equal(old[2:4], coords[0:2])):
			polylines.append(p)
			p = Polyline([], color)
			p.append([coords[0], coords[1]]) # add start point
		p.append([coords[2], coords[3]]) # add end point
		old = coords
	# finalize polylines list
	polylines.append(p)

	return polylines

