#!/usr/bin/env python

# import system tools
import sys
import os
import time
import multiprocessing as thread # import Process, Queue, Pipe
import queue
from distutils.dir_util import mkpath

# import application tools
from config_manager import *
import design_utils as design
from task_manager import TaskManager, Task
from file_manager import FileManager
from workspace import Workspace

# import web framework
from flask import g, Flask, request, redirect, url_for
from flask_socketio import SocketIO, send, emit
from werkzeug.utils import secure_filename

# web server configuration
HTML_FOLDER = 'HTML'
UPLOAD_FOLDER = HTML_FOLDER + '/uploads'
COMPUTED_FOLDER = HTML_FOLDER + '/computed'
ALLOWED_EXTENSIONS = ['dxf'] # TODO set(['svg', 'dxf', 'png', 'jpg', 'jpeg'])
MAX_CONTENT_LENGTH = 64 * 1024 * 1024

LASER_CHECK_INTERVAL = 5
seqNr = 1

# run laser controller in separate thread
def controller_function(command_queue):
	def workspace_add(path):
		drawing = filemanager.open(path)
		if drawing:
			workspace.add(drawing)

	def compose_status(pipe):
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
		print("compose_status", payload)
		pipe.send(payload)

	# init laser
	laser = configLaser()

	# init file manager
	filemanager = FileManager(rootPath=COMPUTED_FOLDER, webRootPath=HTML_FOLDER)

	# init workspace
	workspace = Workspace(filemanager=filemanager)
	configWorkspace(workspace)

	# init task manager
	taskmanager = TaskManager(laser, workspace)
	configTasks(taskmanager)

	# map command to function
	commands = {
		"status": compose_status,
		"init": laser.init,
		"release": laser.release,
		"home": laser.home,
		"unlock": laser.unlock,
		"stop": laser.stop,
		"move": lambda data: laser.move(float(data.get("dx", 0)), float(data.get("dy", 0))),
		"moveTo": lambda data: laser.moveTo(float(data.get("dx", 0)), float(data.get("dy", 0))),
		"workspace.add": workspace_add,
		"workspace.clear": workspace.clear,
		"workspace.remove": workspace.remove,
		"workspace.set": workspace.setParams,
		"item.set": workspace.setParams,
		"task.set": taskmanager.setParams,
		"task.run": taskmanager.run
	}

	# start command loop
	while (True):
		try:
			cmd = command_queue.get(timeout=LASER_CHECK_INTERVAL)
#			if cmd is None:
#				break

			print("cmd", cmd)
			# handle command
			try:
				# execute command
				cmdName = str(cmd.get('cmd')).lower()
				params = cmd.get('params', None)
				print(cmdName, params)
				if params is None:
					commands[cmdName]()
				else:
					commands[cmdName](params)
			except Exception as e:
				print("Exception", e)
			finally:
				# sendStatus()
				command_queue.task_done()

		except queue.Empty:
			print("laser status %s #################################################" %laser.isInit())
			if not laser.isInit():
				laser.init()
			continue
		except:
			break

# send laser status
def sendStatus(broadcast = True):
	status_sender, status_receiver = thread.Pipe()
	global command_queue
	print("command_queue.put")
	command_queue.put({'cmd': "status", 'params': status_sender})

	return
	payload = status_receiver.recv()

	print("payload status:", payload['status'])
	send(payload, json=True, broadcast=broadcast)

print("setup application")
app = Flask(__name__, static_url_path='', static_folder=HTML_FOLDER)
app.app_context()
app.config['HTML_FOLDER'] = HTML_FOLDER
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
mkpath(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
socketio = SocketIO(app)

# routing table
@app.route('/')
def index():
	print("index.html")
	return app.send_static_file('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
	# check if the post request has the file part
	if 'file' not in request.files:
		return redirect("#")
	file = request.files['file']
	# if user does not select file, browser also submit a empty part without filename
	if not file or file.filename == '':
		return redirect("#")
	filename = secure_filename(file.filename)
	path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
	file.save(path)
	global command_queue
	command_queue.put({'cmd':"workspace.add", 'params': path})
	return ""

@socketio.on('connect')
def handleConnect():
	sendStatus(broadcast=False)

@socketio.on('message')
def handleData(data):
	try:
		global seqNr
		# check request sequence
		if data.get("seqNr", False) != seqNr:
			# sqeuence error -> ignore request and resend status
			sendStatus()
			print("ignore request\n")
			return

		# increment sequence
		seqNr += 1

		# handle command
		global command_queue
		if "multiple" in data:
			cmdList = data.get("multiple", [])
		else:
			cmdList = [data]
		for cmd in cmdList:
			command_queue.put(cmd)
	finally:
		# send status
		sendStatus()

# run application
if __name__ == '__main__':
	print("start application")
	command_queue = thread.Queue()
	controller_thread = thread.Process(target=controller_function, args=(command_queue,))
	controller_thread.start()

	socketio.run(app, host='0.0.0.0', port='8080', debug=False)
	print("SHUTDOWN")
