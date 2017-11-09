import numpy as np

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)


class PolyLine:
	def __init__(self, points = [], color = BLACK):
		self.color = color
		self.points = np.array(points)

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


def equal(a, b, tol=0.001, dim=False):
	# use max distance for comparing
	d = abs(np.array(a)-np.array(b))
	if dim:
		d = d[:dim]
	if max(d) > tol:
		return False
	else:
		return True


def makeLines(lines, scale=1, color=BLACK):
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


def optimizeLines(polylines):

	# combine polyline segments
	i = 0
	while i < len(polylines):
		print("")
		a = polylines[i]
		j = 0
		while j < len(polylines):
			b = polylines[j]
			connectedEndStart = equal(a.points[-1], b.points[0], dim=2)		# compare x,y end point with start point of segments
			connectedEndEnd = equal(a.points[-1], b.points[-1], dim=2)		# compare x,y end point with end point of segments
			if i != j and a.color == b. color and (connectedEndStart or connectedEndEnd):
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
