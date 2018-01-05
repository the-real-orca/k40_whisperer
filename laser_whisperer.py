#!/usr/bin/env python

# import gevent
from gevent import monkey; monkey.patch_all()
import gevent

import os
# import system tools
import sys
from distutils.dir_util import mkpath

# import web framework
from flask import Flask, request, redirect, json
from werkzeug.utils import secure_filename
import logging

# import laser application config and dispatcher
from config_manager import *
import dispatcher
	
# application
print("init application")
mkpath(UPLOAD_FOLDER)
server = Flask(__name__, static_url_path='', static_folder=HTML_FOLDER)
server.app_context()
seqNr = 1

# routing table
@server.route('/')
def handleRoot():
	return server.send_static_file('index.html')

@server.route('/upload', methods=['POST'])
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
	#dispatcher.dispatchCommand("workspace.load", path)
	gevent.spawn(dispatcher.dispatchCommand, "workspace.load", path)
	return ""

@server.route('/status')
def handleStatus():
	payload = dispatcher.getStatus()
	payload["seqNr"] = seqNr
	return json.jsonify( payload )

@server.route('/command', methods=['POST'])
def handleCommand():
	data = json.loads( next(iter( request.form )) )
	try:
		global seqNr
		# check request sequence
		if data.get("seqNr", False) != seqNr:
			# sqeuence error -> ignore request and resend status
			print("sqeuence error -> ignore request")
			raise ValueError("sqeuence error -> ignore request")

		# handle command
		if "multiple" in data:
			cmdList = data.get("multiple", [])
		else:
			cmdList = [data]
		for cmd in cmdList:
			#dispatcher.dispatchCommand(cmd.get("cmd"), cmd.get("params", None))
			gevent.spawn(dispatcher.dispatchCommand, cmd.get("cmd"), cmd.get("params", None))

		status = handleStatus()

		# increment sequence
		seqNr += 1

		# return status
		return status

	except StandardError as e:
		# return error
		return str(e), 500

print("start webserver")
if __name__ == '__main__':
	log = logging.getLogger('werkzeug')
	log.setLevel(logging.ERROR)
	server.debug=False
	server.run(host='0.0.0.0', port=8080)
	print("SHUTDOWN")
