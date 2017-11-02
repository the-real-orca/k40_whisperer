#!/usr/bin/env python

# import system tools
import sys
import os

# import laser communication
import k40_wrapper

# import web framework
from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit

	
# init laser
laser=k40_wrapper.LASER_CLASS()
print("init laser")
try:
#TODO	laser.init("mm");
	laser.home();
except StandardError as e:
	error_text = "%s" %(e)
	if "BACKEND" in error_text.upper():
		error_text = error_text + " (libUSB driver not installed)"
	print ("Error: %s" %(error_text))
	sys.exit()
except:
	print("Unknown USB Error")
	sys.exit()
	
# application	
app = Flask(__name__, static_url_path='', static_folder='HTML')
socketio = SocketIO(app)

# routing table
@app.route('/')
def index():
	return app.send_static_file('index.html')

@socketio.on('message')
def handleWebSocket(data):
	print("Data: ", data)
	
@socketio.on('json')
def handle_json(data):
	
	# move laser
	if "move" in data:
		print("Move " + str(data["move"]["dx"]) + "," + str(data["move"]["dy"]))
		# laser.move(data["move"]["dx"], data["move"]["dy"]);
		
	# change anchor position
	if "anchor" in data:
		print("setAnchor: " + data["anchor"])
		# TODO handle anchor change
	
	# send status
	payload = {
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
		}
	}
	send(payload, json=True, broadcast=True)

	
	
if __name__ == '__main__':
	socketio.run(app, host='0.0.0.0', port='8080', debug=False)

	