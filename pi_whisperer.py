#!/usr/bin/env python

# import system tools
import sys
import os
import time
import thread

# import laser communication
import k40_wrapper

# import web framework
from flask import g, Flask, request, redirect, url_for
from flask_socketio import SocketIO, send, emit
from werkzeug.utils import secure_filename

# configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = set(['svg', 'dxf', 'png', 'jpg', 'jpeg'])
MAX_CONTENT_LENGTH = 64 * 1024 * 1024

# application
print("init application")
app = Flask(__name__, static_url_path='', static_folder='HTML')
app.app_context()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
socketio = SocketIO(app)
seqNr = 1


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
		}
	}
	send(payload, json=True, broadcast=broadcast)

# init laser
laser=k40_wrapper.LASER_CLASS()

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

# upload tools
def allowed_file(filename):
	return '.' in filename and \
		   filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
	file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	return redirect("#")

@socketio.on('connect')
def handleConnect():
	sendStatus(broadcast=False)

@socketio.on('message')
def handleData(data):
	global seqNr
	print("sequence:" + str(seqNr)); print(data)

	# check request sequence
	if data["seqNr"] != seqNr:
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
			"stop": laser.stop
		}
		try:
			# execute command
			commands[ str(data["cmd"]).lower() ]()
		except:
			pass

	# send status
	sendStatus()
	print("")


print("start webserver")
if __name__ == '__main__':
	socketio.run(app, host='0.0.0.0', port='8080', debug=True)
	print("SHUTDOWN")

