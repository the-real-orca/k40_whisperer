import os
from dxf import DXF_CLASS
import design_utils as design


class FileManager:

	def openDXF(self, path):
		dxf_import=DXF_CLASS()
		try:
			fd = open(path)
			dxf_import.GET_DXF_DATA(fd, tol_deg=1)
			fd.close()
		except StandardError as e:
			print("DXF Load Failed:", e)
			return False
		except:
			print("Unable To open Drawing Exchange File (DXF) file.")
			return False

		dxf_lines=dxf_import.DXF_COORDS_GET(new_origin=False)
		if dxf_import.dxf_messages != "":
			print("DXF Import:",dxf_import.dxf_messages)

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
			print("DXF Import: unknown unit '%s'", dxf_units)
			return False

		polylines = design.makePolylines(dxf_lines, scale=dxf_scale, color=design.RED)

		# create drawings object
		name = os.path.basename(path).replace("_", " ")
		drawing = design.Drawing(name, polylines)
		drawing.flipY()	# DXF import is mirrored around the x-axis -> invert Y coordinates
		drawing.combineLines()

		# create SVG image for displaying
		path += ".svg";
		drawing.saveSVG(path)

		return drawing, path


	def open(self, path):
		# open by filetype
		ext = os.path.splitext(path.lower())[1]
		if ext==".dxf":
			return self.openDXF(path)
		else:
			return False
