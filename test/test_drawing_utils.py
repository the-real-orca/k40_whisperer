import unittest
import drawing_utils
import numpy as np
import Polygon, Polygon.IO, Polygon.Utils  # https://pypi.org/project/Polygon2/
import math

class Test_combineLines(unittest.TestCase):
	def setUp(self):
		self.lines = []
		self.expected = []

	def tearDown(self):
		drawing = drawing_utils.Drawing(self.lines)
		drawing.combineLines()
		self.assertEqual( 1,  len(drawing.polylines) )
		computed = drawing.polylines[0]
		expected = drawing_utils.Polyline(self.expected)
		self.assertTrue( expected.equals(computed),
		                 self._testMethodName +
		                 "\nExpected: " + str(expected.encode()) +
		                 "\nActual: " + str(computed.encode()) )

	def test_end_to_start(self):
		self.lines = [ [[0,0], [1,0], [2,0]],
		          [[2,0], [3,0], [4,0]] ]
		self.expected = [[0,0], [1,0], [2,0], [3,0], [4,0]]

	def test_start_to_end(self):
		self.lines = [ [[2,0], [1,0], [0,0]],
		          [[4,0], [3,0], [2,0]] ]
		self.expected = [[0,0], [1,0], [2,0], [3,0], [4,0]]

	def test_end_to_end(self):
		self.lines = [ [[0,0], [1,0], [2,0]],
		          [[4,0], [3,0], [2,0]] ]
		self.expected = [[0,0], [1,0], [2,0], [3,0], [4,0]]

	def test_start_to_start(self):
		self.lines = [ [[2,0], [1,0], [0,0]],
		          [[2,0], [3,0], [4,0]] ]
		self.expected = [[0,0], [1,0], [2,0], [3,0], [4,0]]


	def test_tripple(self):
		self.lines = [ [[0,0], [1,0]],
		               [[1,0], [2,0]],
		               [[2,0], [3,0]] ]
		self.expected = [[0,0], [1,0], [2,0], [3,0]]

	def test_tripple_reordered(self):
		self.lines = [ [[0,0], [1,0]],
		               [[2,0], [3,0]],
		               [[1,0], [2,0]] ]
		self.expected = [[3,0], [2,0], [1,0], [0,0]]

	def test_sparse_reordered(self):
		self.lines = [ [[0,0], [1,0]],
		               [[2,0], [3,0]],
		               [[4,0], [5,0]],
		               [[2,0], [1,0]],
		               [[4,0], [3,0]] ]
		self.expected = [[5, 0], [4, 0], [3, 0], [2, 0], [1, 0], [0, 0]]

	def test_square(self):
		self.lines = [ [[0,0], [1,0]],
		               [[1,0], [1,1]],
		               [[1,1], [0,1]],
		               [[0,1], [0,0]] ]
		self.expected = [[0,0], [1, 0], [1, 1], [0,1], [0,0]]

class Test_reorderInnerToOuter(unittest.TestCase):
	def setUp(self):
		self.lines = []
		self.expected = []

	def tearDown(self):
		drawing = drawing_utils.Drawing(self.lines)
		drawing.reorderInnerToOuter()
		self.assertEqual( len(self.expected),  len(drawing.polylines))
		for i, computed in enumerate(drawing.polylines):
			expected = drawing_utils.Polyline(self.expected[i])
			self.assertTrue( expected.equals(computed),
			                 self._testMethodName + " #" + str(i) +
			                 "\nExpected: " + str(expected.encode()) +
			                 "\nActual: " + str(computed.encode()) )

	def test_simple_square(self):
		self.lines = [ [[-2, -2], [2, -2], [2, 2], [-2, 2], [-2, -2]],
		               [[-1,-1], [1, -1], [1, 1], [-1,1], [-1,-1]] ]
		self.expected = [ [[-1,-1], [1, -1], [1, 1], [-1,1], [-1,-1]],
		               [[-2, -2], [2, -2], [2, 2], [-2, 2], [-2, -2]] ]

'''
	def test_hash_square(self):
		self.lines = [ [[-10, 2], [10, 2]], [[-10, -2], [10, -2]],
		               [[-2, -10], [-2, 10]], [[2, -10], [2, 10]],
		               [[-1,-1], [1, -1], [1, 1], [-1,1], [-1,-1]] ]
		self.expected = [ [[-1,-1], [1, -1], [1, 1], [-1,1], [-1,-1]],
		                  [[-10, 2], [10, 2]], [[-10, -2], [10, -2]],
		                  [[-2, -10], [-2, 10]], [[2, -10], [2, 10]] ]
'''

def pointDist(q, p):
	return math.sqrt( (p[0]-q[0])**2 + (p[1]-q[1])**2 )

def makePolygon(polyline):
	ub = []; lb = []
	poly = Polygon.Polygon()
	q = np.array(polyline[0])
	dd = [0,0]
	for p in polyline[1:]:
		p = np.array(p)
		l = pointDist(q,p)
		n = np.array([p[1]-q[1], -p[0]+q[0]]) / l
		d = n * 2
		print d
		print q-d, p-d, p, q
		poly = poly + Polygon.Polygon([q-d, p-d, p+d, q+d])
		poly = poly + Polygon.Polygon([q-dd, q+dd, q+d, q-d])
		q = p; dd = d
	return poly


class Test_polygon(unittest.TestCase):
	def test_polygon(self):
		p = makePolygon([[-10, 2], [10, 2], [20,20]])
#		p = p + makePolygon([[-10, -2], [10, -2]])
#		p = p + makePolygon([[2, -10], [2, 10]])
#		p = p + makePolygon([[-2, -10], [-2, 10]])

		#p = Polygon.Utils.convexHull(p)
#		p = Polygon.Utils.fillHoles(p)
		print p.contour(0)
		Polygon.IO.writeSVG('test.svg', (p))


if __name__ == '__main__':
	unittest.main();