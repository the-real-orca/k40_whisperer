import numpy as np
import matplotlib.path as path
import svgutils.transform as sg
from lxml import etree


BLACK = "black"		#(0, 0, 0)
WHITE = "white"		#(255, 255, 255)
RED = "red"			#(255, 0, 0)
GREEN = "green"		#(0, 255, 0)
BLUE = "blue"			#(0, 0, 255)
YELLOW = "yellow"	#(255, 255, 0)
CYAN = "cyan"			#(0, 255, 255)
MAGENTA = "magenta"	#(255, 0, 255)


class PolyLine:
	def __init__(self, points = [], color = BLACK):
		self.color = color
		self.path = path.Path(np.array(points))

	def getVertices()
		return self.path.vertices
		
	def encode(self):
		data = {
			"color": self.color,
			"points": []
			}
		for p in self.points:
			data.points.append(p)
		return data

	def appendPolyLine(self, polyline):
		self.path.make_compound_path(polyline.path)

	def appendPoint(self, p):
		self.path.vertices = np.concatenate((self.path.vertices,[p]), axis=0)

	def append(self, p):
		if isinstance(p, PolyLine):
			self.appendPolyLine(p)
		else:
			self.appendPoint(p)

	def reverse(self):
		self.path.vertices = self.path.vertices[::-1]

	def contains(self, polyline):
		return self.path.contains_path(polyline)

					 
class Drawing:
	def __init__(self, id, polylines, url=""):
		self.id = id
		self.polylines = polylines
		self.url = url

	def saveSVG(self, filePath)
		# compute canvas size
		strokeWidth = 0.5
		xMin=[]; xMax=[]
		yMin=[]; yMax=[]
		#for line in polylines:
		#	xMin.append( min(line.points[:,0]) )
		#	xMax.append( max(line.points[:,0]) )
		#	yMin.append( min(line.points[:,1]) )
		#	yMax.append( max(line.points[:,1]) )
		xPoints = [line.getVertices()[:,0] for line in polylines]
		xMin = min(xPoints); xMax = max(xPoints)
		yPoints = [line.getVertices()[:,1] for line in polylines]
		yMin = min(yPoints); yMax = max(yPoints)
		width = xMax - xMin
		height = yMax - yMin

		# create SVG
		svg = sg.SVGFigure(str(width)+"mm", str(height)+"mm")
		svg.root.set("viewBox", "%s %s %s %s" % (xMin, yMin, width, height))
		svgLines = []
		for line in polylines:
			# custom path creation
			points = line.getVertices()
			linedata = "M{} {} ".format(*points[0])
			linedata += " ".join(map(lambda x: "L{} {}".format(*x), points[1:]))
			linedata = etree.Element(sg.SVG+"path",
							   {"d": linedata, "stroke-width": str(strokeWidth), "stroke": line.color, "fill": "none"})
			svgLines.append( sg.FigureElement(linedata) )
		g = sg.GroupElement(svgLines)
		g.moveto(-xMin, -yMin) # move the drawing to be in viewBox
		svg.append(g)

		# save generated SVG files
		svg.save(filePath)

	def optimize(self, ignoreColor=False):
		self.combineLines(ignoreColor)
		self.reorderInnerToOuter()

	def combineLines(self, ignoreColor=False):

		# combine polyline segments
		i = 0
		while i < len(self.polylines):	# cannot use enumerate() since we change the list on-the-fly
			j = 0
			while j < len(self.polylines):
				b = self.polylines[j]
				connectedEndStart = equal(a.points[-1], b.points[0], dim=2)		# compare x,y end point with start point of segments
				connectedEndEnd = equal(a.points[-1], b.points[-1], dim=2)		# compare x,y end point with end point of segments
				if i != j and (connectedEndStart or connectedEndEnd) and \ 
					(a.color == b. color or ignoreColor):
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
			
		# reorder: inner -> outer regions
		return self.reorderInnerToOuter()

		
	def reorderInnerToOuter(self)
		# build polyline tree
		class Node(object):
			def __init__(self, data):
				self.data = data
				self.children = []
				
		if len(self.polylines) < 2:
			return polylines

		root = []
		for polyline in self.polylines:
			group = root
			# recursively test if polyline is inside any element of the current group
			while ( group != None):
				for node in group:
					# test if current polyline is inside of nodes polyline
					if node.data.contains(polyline):
						# dive recursively into node
						group = node.children
						break

					# test if nodes polyline is inside of current polyline
					if polyline.contains(node.data):
						# created node for current polyline and wrap surronded nodes
						node = Node(polyline)
						node.children = [x for x in group if polyline.contains(x.data)]
						# remove wrapped nodes from group (in-place manipulation!)
						for x in node.children:
							group.remove(x)
						# exit
						group = None
						break
				else:
					# add new element to group
					group.append( Node(polyline) )
					group = None
					break
		
		# walk through tree bottom->up
		polylines = []
		node = root
		childIndex = 0
		stack = []
		while node:
			# append polyline if all children have been processed 
			if len(node.children) >= childIndex:
				polylines.append(node.data)
				node, childIndex = stack.pop()
				continue
			
			# dive into next child
			next = node.children[childIndex]
			stack.append(node, childIndex+1)
			childIndex = 0
			node = next

		self.polylines = polylines
		return polylines
		
		
def equal(a, b, tol=0.001, dim=False):
	# use max distance for comparing
	d = abs(np.array(a)-np.array(b))
	if dim:
		d = d[:dim]
	if max(d) > tol:
		return False
	else:
		return True


def makePolyLines(lines, scale=1, color=BLACK):
	polylines=[]
	old = [0,0,0,0]
	p = PolyLine([], color)
	for line in lines:
		coords = np.array(line)*scale
		# check and see if we need to move to a new discontinuous start point
		if not(equal(old[2:4], coords[0:2])):
			if len(p.points):
				polylines.append(p)
			p = PolyLine([], color)
			p.append([coords[0], coords[1]]) # add start point
		p.append([coords[2], coords[3]]) # add end point
		old = coords
	# finalize polylines list
	polylines.append(p)

	return polylines

