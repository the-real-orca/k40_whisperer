import os
from distutils.dir_util import mkpath
import re
from libs.k40_whisperer.dxf import DXF_CLASS
import svgutils.transform as sg
from lxml import etree
import design_utils as design
import logging

class FileManager:
	def __init__(self, rootPath = ".", webRootPath = "."):
		self.rootPath = rootPath
		self.webRootPath = webRootPath

	def pathToURL(self, path):
		return os.path.relpath(path, self.webRootPath)		
		
	def openDXF(self, path):
		dxf_import=DXF_CLASS()		
		try:
			with open(path) as fd:
				dxf_import.GET_DXF_DATA(fd, tol_deg=2)
#				dxf_import.GET_DXF_DATA(fd, tol_deg=1) #TODO
		except StandardError as e:
			logging.error("DXF Load Failed: " + str(e))
			return False
		except:
			logging.error("Unable To open Drawing Exchange File (DXF) file.")
			return False

#		dxf_lines=dxf_import.DXF_COORDS_GET(new_origin=False) # TODO
		dxf_lines=dxf_import.DXF_COORDS_GET_TYPE(new_origin=False, engrave=False)
		if dxf_import.dxf_messages != "":
			logging.info("DXF Import: " + str(dxf_import.dxf_messages))

		dxf_units = dxf_import.units
		if dxf_units=="Inches":
			dxf_scale = 25.4
		elif dxf_units=="Microinches":
			dxf_scale = 25.4/1000000.0
		elif dxf_units=="Mils":
			dxf_scale = 25.4/1000.0
		elif dxf_units=="Feet":
			dxf_scale = 304.8
		elif dxf_units=="Millimeters" or dxf_units=="Unitless":
			dxf_scale = 1
		elif dxf_units=="Centimeters":
			dxf_scale = 10
		elif dxf_units=="Meters":
			dxf_scale = 100
		else:
			logging.warning("DXF Import: unknown unit: " + str(dxf_units))
			return False

		color=design.RED
		polylines = design.makePolylines(dxf_lines, scale=dxf_scale, color=color)

		# create drawings object
		name = os.path.basename(path).replace("_", " ")
		drawing = design.Drawing(polylines, name=name)
		# optimice drawing object
		drawing.combineLines()

		return drawing


	def open(self, path):
		# open by filetype
		ext = os.path.splitext(path.lower())[1]
		if ext==".dxf":
			return self.openDXF(path)
		else:
			return False


	def saveSVG(self, drawing, filename=None, path=None):
		# compute canvas size
		[xMin, yMin, width, height], strokeWidth = drawing.getViewBox()

		# create SVG
		svg = sg.SVGFigure(str(width)+"mm", str(height)+"mm")
		svg.root.set("viewBox", "%s %s %s %s" % (xMin, yMin, width, height))
		svgLines = []
		for line in drawing.polylines:
			# custom path creation
			points = " ".join(map(lambda x: "{:.3f},{:.3f}".format(x[0], -x[1]), line.getPoints()))
			linedata = etree.Element(sg.SVG+"polyline", {
								   "points": points,
								   "stroke-width": str(strokeWidth),
								   "stroke-linecap": "square",
								   "stroke": line.color,
								   "fill": "none"})
			svgLines.append( sg.FigureElement(linedata) )
		g = sg.GroupElement(svgLines, {'id': "root"})
		svg.append(g)

		# save generated SVG files
		if not(path):
			path = self.rootPath
		if not(filename):
			filename = drawing.filename

		filename = re.sub(r"[^(a-zA-Z0-9\-_)]+", "_", filename)	# make sure that only safe characters are used for filename
		mkpath(path)
		filepath = os.path.join(path, filename)+".svg"
		drawing.filename = filename
		drawing.path = path
		drawing.url = self.pathToURL(filepath)
		logging.info("drawing.path: " + drawing.path)
		logging.info("drawing.url: " + drawing.url)
		svg.save(filepath)

		