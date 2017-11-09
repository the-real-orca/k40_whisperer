import os
from dxf import DXF_CLASS
import utils


class FileManager:

	def openDXF(self, path):
		dxf_import=DXF_CLASS()
		try:
			fd = open(path)
			dxf_import.GET_DXF_DATA(fd, tol_deg=1)
			fd.close()
		except StandardError as e:
			print("DXF Load Failed:", e)
			traceback.format_exc()
			return False
		except:
			print("Unable To open Drawing Exchange File (DXF) file.")
			traceback.format_exc()
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

		polylines = utils.makeLines(dxf_lines, scale=dxf_scale, color=utils.RED)
		polylines = utils.optimizeLines(polylines)
		return polylines


	def open(self, path):
		# open by filetype
		ext = os.path.splitext(path.lower())[1]
		if ext==".dxf":
			return self.openDXF(path)
		else:
			return False
