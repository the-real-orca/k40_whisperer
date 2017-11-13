import numpy as np
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
		self.points = np.array(points)

	def encode(self):
		data = {
			"color": self.color,
			"points": []
			}
		for p in self.points:
			data.points.append(p)
		return data

	def appendPolyLine(self, polyline):
		if equal(polyline.points[0], self.points[-1]):
			s = 1
		else:
			s = 0
		if len(self.points):
			self.points = np.concatenate((self.points, polyline.points[s:]), axis=0)
		else:
			self.points = np.array(polyline.points[s:])

	def appendPoint(self, p):
		if len(self.points):
			self.points = np.concatenate((self.points,[p]), axis=0)
		else:
			self.points = np.array([p])

	def append(self, p):
		if isinstance(p, PolyLine):
			self.appendPolyLine(p)
		else:
			self.appendPoint(p)

	def reverse(self):
		self.points = self.points[::-1]

class Drawing:
	def __init__(self, id, polylines, url):
		self.id = id
		self.polylines = polylines
		self.url = url


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


def optimizeLines(polylines, ignoreColor=False):

	# combine polyline segments
	i = 0
	while i < len(polylines):	# cannot use enumerate() since we change the list on-the-fly
		j = 0
		while j < len(polylines):
			b = polylines[j]
			connectedEndStart = equal(a.points[-1], b.points[0], dim=2)		# compare x,y end point with start point of segments
			connectedEndEnd = equal(a.points[-1], b.points[-1], dim=2)		# compare x,y end point with end point of segments
			if i != j and (connectedEndStart or connectedEndEnd) and \ 
				(a.color == b. color or ignoreColor):
				if connectedEndEnd:
					b.reverse()
				# connect segments
				a.append(b)
				# remove added segment from path and readjust indizes
				polylines.pop(j)
				if j < i: i -= 1
			else:
				j += 1
		i += 1
		
	# reorder: inner -> outer regions
	# TODO

	# combine segments
	return polylines

def reorderInnerToOuter(polylines)
	
	
def saveSVG(polylines, path):
	# compute canvas size
	strokeWidth = 0.5
	xMin=[]; xMax=[]
	yMin=[]; yMax=[]
	#for line in polylines:
	#	xMin.append( min(line.points[:,0]) )
	#	xMax.append( max(line.points[:,0]) )
	#	yMin.append( min(line.points[:,1]) )
	#	yMax.append( max(line.points[:,1]) )
	xPoints = [line.points[:,0] for line in polylines]
	xMin = min(xPoints); xMax = max(xPoints)
	yPoints = [line.points[:,1] for line in polylines]
	yMin = min(yPoints); yMax = max(yPoints)
	width = xMax - xMin
	height = yMax - yMin

	# create SVG
	svg = sg.SVGFigure(str(width)+"mm", str(height)+"mm")
	svg.root.set("viewBox", "%s %s %s %s" % (xMin, yMin, width, height))
	svgLines = []
	for line in polylines:
		# custom path creation
		linedata = "M{} {} ".format(*line.points[0])
		linedata += " ".join(map(lambda x: "L{} {}".format(*x), line.points[1:]))
		linedata = etree.Element(sg.SVG+"path",
						   {"d": linedata, "stroke-width": str(strokeWidth), "stroke": line.color, "fill": "none"})
		svgLines.append( sg.FigureElement(linedata) )
	g = sg.GroupElement(svgLines)
	g.moveto(-xMin, -yMin) # move the drawing to be in viewBox
	svg.append(g)

	# save generated SVG files
	svg.save(path)

