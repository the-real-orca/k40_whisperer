#!/usr/bin/env python

# import system tools
import sys
import os
import time
import thread

# import laser communication
import k40_wrapper
from task_manager import TaskManager
from file_manager import FileManager
from workspace import Workspace

# import file tools
from svg_reader import SVG_READER

# import web framework
from flask import g, Flask, request, redirect, url_for
from flask_socketio import SocketIO, send, emit
from werkzeug.utils import secure_filename

# configuration
HTML_FOLDER = 'HTML'
UPLOAD_FOLDER = HTML_FOLDER + '/uploads'
ALLOWED_EXTENSIONS = set(['svg', 'dxf', 'png', 'jpg', 'jpeg'])
MAX_CONTENT_LENGTH = 64 * 1024 * 1024
workspaceImg = ""

# application
print("init application")
app = Flask(__name__, static_url_path='', static_folder=HTML_FOLDER)
app.app_context()
app.config['HTML_FOLDER'] = HTML_FOLDER
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
socketio = SocketIO(app)
seqNr = 1

def pathToURL(path):
	return os.path.relpath(path, HTML_FOLDER)

# init laser
laser = k40_wrapper.LASER_CLASS()

# setup periodic laser check
def laser_thread():
	global app
	if not( laser.isInit() ):
		try:
			print("init laser")
			laser.init("mm");
			laser.home();
			print("laser init ok")
		except StandardError as e:
			error_text = "%s" %(e)
			if "BACKEND" in error_text.upper():
				error_text = error_text + " (libUSB driver not installed)"
			print ("Error: %s" %(error_text))
			if "NOT FOUND" not in error_text.upper():
				sys.exit()
		except:
			print("Unknown USB Error")
			sys.exit()
	#sendStatus()
#thread.start_new_thread(laser_thread, ())
#laser_thread()


# init file manager
filemanager = FileManager()

# init workspace
workspace = Workspace(originOffset=[10, 40])

# init task manager
taskmanager = TaskManager(laser, workspace)


# send laser status
def sendStatus(broadcast = True):
	payload = {
		"seqNr": seqNr,
		"status": {
			"laser": False,
			"usb": laser.isInit(),
			"airassist": 0,
			"waterTemp": 0,
			"waterFlow": 0,
		},
		"alert": {
			"laser": False,
			"usb": not(laser.isInit()),
			"airassist": False,
			"waterTemp": False,
			"waterFlow": False
		},
		"pos": {
			"x": laser.x,
			"y": laser.y
		},
		"workspace": {
			"width": workspace.size[0],
			"height": workspace.size[1],
			"originOffset": workspace.originOffset,
			"drawingsOrigin": workspace.drawingsOrigin,
			"drawings": []

		},
		"tasks": []
	}
	for k in workspace.drawings:
		draw = workspace.drawings[k]
		payload["workspace"]["drawings"].append({
			"id": draw.id,
			"name": draw.id,
			"x": draw.position[0],
			"y": draw.position[1],
			"width": draw.size[0],
			"height": draw.size[1],
			"url": draw.param.get("url", "")
		})
	for task in taskmanager.tasks:
		payload["tasks"].append({
			"id": task.id,
			"name": task.id,
			"colors": task.colors,
			"speed": task.speed,
			"intensity": task.intensity,
			"type": task.type
		})


	send(payload, json=True, broadcast=broadcast)


# routing table
@app.route('/')
def index():
	return app.send_static_file('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
	# check if the post request has the file part
	if 'file' not in request.files:
		return redirect("#")
	file = request.files['file']
	# if user does not select file, browser also submit a empty part without filename
	if not(file) or file.filename == '':
		return redirect("#")
	filename = secure_filename(file.filename)
	path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
	file.save(path)
	drawing, path = filemanager.open(path)
	if drawing:
		if len(workspace.drawings)==0:
			# set drawings origin for first drawing to fit to workspace
			viewBox, strokeWidth = drawing.getViewBox(strokeWidth=0)
			workspace.drawingsOrigin[0] = workspace.originOffset[0] - min(viewBox[0],0)
			workspace.drawingsOrigin[1] = workspace.originOffset[1] - min(viewBox[1],0)
		drawing.position = list(workspace.drawingsOrigin)
		drawing.param["url"] = pathToURL(path)
		workspace.add(drawing)
	return redirect("#")

@socketio.on('connect')
def handleConnect():
	sendStatus(broadcast=False)

@socketio.on('message')
def handleData(data):
	global seqNr
	print("sequence:" + str(seqNr)); print(data)

	try:
		# check request sequence
		if data.get("seqNr", False) != seqNr:
			# sqeuence error -> ignore request and resend status
			sendStatus()
			print("ignore request\n")
			return

		# increment sequence
		seqNr += 1

		# move laser
		if "move" in data:
			laser.move( float(data["move"]["dx"]), float(data["move"]["dy"]) );
		if "moveTo" in data:
			laser.moveTo( float(data["moveTo"]["x"]), float(data["moveTo"]["y"]) );

		# change anchor position
		if "anchor" in data:
			print("setAnchor: " + data["anchor"])
			# TODO handle anchor change

		# handle command
		if "cmd" in data:
			commands = {
				"init": laser.init,
				"release": laser.release,
				"home": laser.home,
				"unlock": laser.unlock,
				"stop": laser.stop,
				"workspace.clear": workspace.clear,
				"workspace.remove": workspace.remove,
				"task.run": taskmanager.run
			}
			try:
				# execute command
				cmdName = str(data["cmd"]).lower()
				params = data.get("params", None)
				print(cmdName, params)
				if params is None:
					commands[cmdName]()
				else:
					commands[cmdName](params)
			except Exception as e:
				print("Exception", e)
	finally:
		# send status
		sendStatus()
		print("status", data)


print("start webserver")
if __name__ == '__main__':
	socketio.run(app, host='0.0.0.0', port='8080', debug=True)
	print("SHUTDOWN")
