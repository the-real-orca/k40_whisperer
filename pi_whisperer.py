#!/usr/bin/env python

# import system tools
import sys
import os

# import laser communication
import k40_wrapper

# import web framework
from flask import Flask, request, redirect, url_for
from flask_socketio import SocketIO, send, emit
from werkzeug.utils import secure_filename

	
# init laser
laser=k40_wrapper.LASER_CLASS()
print("init laser")
try:
#TODO	laser.init("mm");
	laser.home();
except StandardError as e:
	error_text = "%s" %(e)
	if "NOT FOUND" in error_text.upper():
		error_text = error_text + "\nconnect laser cutter and power on"
	if "BACKEND" in error_text.upper():
		error_text = error_text + " (libUSB driver not installed)"
	print ("Error: %s" %(error_text))
	sys.exit()
except:
	print("Unknown USB Error")
	sys.exit()

# upload tools	
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = set(['svg', 'dxf', 'png', 'jpg', 'jpeg'])
MAX_CONTENT_LENGTH = 64 * 1024 * 1024

def allowed_file(filename):
	return '.' in filename and \
		   filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# communication helpers		   
def sendStatus():
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
			"x": 1.2345, # TODO laser.x,
			"y": 0 # TODO laser.y
		}
	}
	send(payload, json=True, broadcast=True)

		   
# application	
print("init application")
app = Flask(__name__, static_url_path='', static_folder='HTML')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
socketio = SocketIO(app)
seqNr = 1


# routing table
@app.route('/')
def index():
	return app.send_static_file('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
	# check if the post request has the file part
	if 'file' not in request.files:
		return redirect(request.url)
	file = request.files['file']
	# if user does not select file, browser also submit a empty part without filename
	if not(file) or file.filename == '':
		return redirect(request.url)
	filename = secure_filename(file.filename)
	file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	return redirect('/')
	
@socketio.on('message')
def handle_json(data):
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
	if "goto" in data:
		laser.goto( float(data["goto"]["x"]), float(data["goto"]["y"]) );
		
	# change anchor position
	if "anchor" in data:
		print("setAnchor: " + data["anchor"])
		# TODO handle anchor change
	
	# send status
	sendStatus()
	print("")

	
print("start webserver")	
if __name__ == '__main__':
	socketio.run(app, host='0.0.0.0', port='8080', debug=True)

	