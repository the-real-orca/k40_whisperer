import unittest
import drawing_utils
import numpy as np

class Test_combineLines(unittest.TestCase):
	def setUp(self):
		self.lines = []
		self.expected = []

	def tearDown(self):
		drawing = drawing_utils.Drawing(self.lines)
		drawing.combineLines()
		self.assertEqual( 1,  len(drawing.polylines))
		computed = drawing.polylines[0]
		expected = drawing_utils.Polyline(self.expected)
		self.assertTrue( expected.equals(computed),
		                 self._testMethodName +
		                 "\nExpected: " + np.array_str(expected.getPoints()) +
		                 "\nActual: " + np.array_str(computed.getPoints()) )

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

	def test_square(self):
		self.lines = [ [[0,0], [1,0]],
		               [[1,0], [1,1]],
		               [[1,1], [0,1]],
		               [[0,1], [0,0]] ]
		self.expected = [[0,0], [1, 0], [1, 1], [0,1], [0,0]]

if __name__ == '__main__':
	unittest.main();