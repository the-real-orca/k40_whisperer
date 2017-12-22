#!/usr/bin/env python

# import system tools
import sys
import os
import time
from distutils.dir_util import mkpath

# import application tools
from config_manager import *
import design_utils as design
from task_manager import TaskManager, Task
from file_manager import FileManager
from workspace import Workspace

# import web framework
from flask import Flask, request, redirect, json
from werkzeug.utils import secure_filename

# web server configuration
HTML_FOLDER = 'HTML'
UPLOAD_FOLDER = HTML_FOLDER + '/uploads'
COMPUTED_FOLDER = HTML_FOLDER + '/computed'
ALLOWED_EXTENSIONS = set(['dxf']) # TODO set(['svg', 'dxf', 'png', 'jpg', 'jpeg'])
MAX_CONTENT_LENGTH = 64 * 1024 * 1024

def NullFunc():
	return
	
# application
print("init application")
mkpath(UPLOAD_FOLDER)
app = Flask(__name__, static_url_path='', static_folder=HTML_FOLDER)
app.app_context()
#app.config['HTML_FOLDER'] = HTML_FOLDER
#app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
seqNr = 1

# init laser
laser = configLaser()

# setup periodic laser check
def laser_thread():
	global app
	if not( laser.isInit() ):
		try:
			print("init laser")
			laser.init("mm")
			laser.home()
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
filemanager = FileManager(rootPath = COMPUTED_FOLDER, webRootPath = HTML_FOLDER)

# init workspace
workspace = Workspace(filemanager = filemanager)
configWorkspace(workspace)

# init task manager
taskmanager = TaskManager(laser, workspace)
configTasks(taskmanager)

# routing table
@app.route('/')
def handleRoot():
	return app.send_static_file('index.html')

@app.route('/upload', methods=['POST'])
def handleUpload():
	# check if the post request has the file part
	if 'file' not in request.files:
		return redirect("#")
	file = request.files['file']
	# if user does not select file, browser also submit a empty part without filename
	if not(file) or file.filename == '':
		return redirect("#")
	filename = secure_filename(file.filename)
	path = os.path.join(UPLOAD_FOLDER, filename)
	file.save(path)
	drawing = filemanager.open(path)
	if drawing:
		workspace.add(drawing)
	return ""

@app.route('/status')
def handleStatus():
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
			"usb": not (laser.isInit()),
			"airassist": False,
			"waterTemp": False,
			"waterFlow": False
		},
		"pos": {
			"x": laser.x,
			"y": laser.y
		},
		"workspace": workspace.toJson(),
		"tasks": []
	}
	for task in taskmanager.tasks:
		payload["tasks"].append({
			"id": task.id,
			"name": task.id,
			"colors": task.colors,
			"speed": task.speed,
			"intensity": task.intensity,
			"type": task.type,
			"repeat": task.repeat
		})
	return json.jsonify(payload)

@app.route('/command', methods=['POST'])
def handleCommand():
	data = json.loads( next(iter( request.form )) )
	try:
		global seqNr
		# check request sequence
		if data.get("seqNr", False) != seqNr:
			# sqeuence error -> ignore request and resend status
			print("ignore request\n")
			raise ValueError("sqeuence error -> ignore request and resend status")

		# increment sequence
		seqNr += 1

		# handle command
		commands = {
			"status": NullFunc,
			"init": laser.init,
			"release": laser.release,
			"home": laser.home,
			"unlock": laser.unlock,
			"stop": laser.stop,
			"move": lambda params: laser.move( float(params.get("dx",0)), float(params.get("dy",0)) ),
			"moveTo": lambda params: laser.moveTo( float(params.get("dx",0)), float(params.get("dy",0)) ),
			"workspace.clear": workspace.clear,
			"workspace.remove": workspace.remove,
			"workspace.set": workspace.setParams,
			"item.set": workspace.setParams,
			"task.set": taskmanager.setParams,
			"task.run": taskmanager.run
		}
		if "multiple" in data:
			cmdList = data.get("multiple", [])
		else:
			cmdList = [data]
		for cmd in cmdList:
			if "cmd" in cmd:
				try:
					# execute command
					cmdName = str(cmd.get("cmd")).lower()
					params = cmd.get("params", None)
					print(cmdName, params)
					if params is None:
						commands[cmdName]()
					else:
						commands[cmdName](params)
				except Exception as e:
					print("Exception", e)
	finally:
		# send status
		return handleStatus()

print("start webserver")
if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8080)
	print("SHUTDOWN")
