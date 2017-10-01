#!/usr/bin/env python

# pin configuration
POWER = 17 		# GPIO pin
FOCUS_UP = 7 	# GPIO pin
FOCUS_DOWN = 8	# GPIO pin

# web server
WWW_DIR = "/usr/share/laser/HTML"	# root dir of web server

# camera config
MIN_THRESHOLD = 250	# brightness threshold value
MIN_SIZE = 4	# minimal number of pixels of focus blob

#upload image
BUF_SIZE = 1024 * 10		# 10kB
MAX_SIZE = BUF_SIZE * 1000	# 10MB


#import system tools
import serial
import time
import thread
import os
import errno
import io
import argparse
from subprocess import call

# import bottle web framework
from bottle import get, put, post, route, request
from bottle import response
from bottle import static_file
from bottle import run

#import json tools
import json

# import opencv 
import cv2 
import numpy as np
from PIL import Image, ImageStat

# import Raspberry Pi GPIO
import RPi.GPIO as GPIO

# handle arguments
parser = argparse.ArgumentParser()
parser.add_argument("--dir", help="webserver root directory", type=str)
args = parser.parse_args()
if args.dir:
	WWW_DIR = os.path.abspath(args.dir)

print "WWW_DIR      ", WWW_DIR

# init GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(POWER, GPIO.OUT)
GPIO.output(POWER, GPIO.HIGH)
GPIO.setup([FOCUS_UP, FOCUS_DOWN], GPIO.OUT)
GPIO.output([FOCUS_UP, FOCUS_DOWN], GPIO.LOW)

# global variables
ser = None
ser_lock = thread.allocate_lock()
preview = None
intensity = 10
status = "off"
buffer_lock = thread.allocate_lock()
pixel_count = 0
focus = 0
focus_hist = np.zeros(6)
autofocus_mode = 0
autofocus_cnt = 0
autofocus_val = 0
BUFFER_COUNT = 4
img_buffer = ["", "", "", ""]
active_img_buffer = 0
json_buffer = ["{}", "{}", "{}", "{}"]
active_json_buffer = 0
pos = [0,0]
pos_count = 0
pos_lock = thread.allocate_lock()
start_time = 0
	
def resetStatus():
	global pos, pos_count
	global start_time, timeLeft
	global status
	pos_lock.acquire(); pos = [0,0]; pos_count = 0; pos_lock.release()
	if powerStatus() :
		status = "stopped"
	else :
		status = "off"

		
def sendIntensity(val):
	burnTime = int(int(val) * 2.4)	# convert percentage to burn time 1 - 240
	if ser and ( burnTime > 0 ) and ( burnTime <= 240 ) :
		ser_lock.acquire()
		ser.write(chr(burnTime))
		ser_lock.release()
		return val
	else :
		global intensity
		return intensity
		
		
def sendLaserImage():
	print "convert to B/W"
	mask = Image.open(WWW_DIR + "/uploads/mask.png")
	stat = ImageStat.Stat(mask)
	global pixel_count
	pixel_count = (stat.count[0] - stat.sum[0]/255)
	mask = mask.convert('1')
	# insert into 512x512 image
	img_laser = Image.new('1', (512, 512), 0xFF)
	img_laser.paste(mask, (0, 12))
	
	# write raw data buffer
	raw_stream = io.BytesIO()
	img_laser.save(raw_stream, format='BMP')
	raw_data = raw_stream.getvalue()
	
	# send to laser
	global intensity
	sendIntensity(intensity)
	time.sleep(0.1)
	ser_lock.acquire()
	ser.write(b"\xFE\xFE\xFE\xFE\xFE\xFE\xFE\xFE")
	time.sleep(3)
	print "send image to laser..."
	ret = ser.write( raw_data )
	time.sleep(1)
	ser_lock.release()

	
def powerOn():
	global ser, status
	# power on laser
	GPIO.output(POWER, GPIO.LOW)
	
	# try to connect
	time.sleep(0.2)
	ser_lock.acquire()
	try:
		#ser = serial.Serial("/dev/ttyUSB0", 57600)
		ser = serial.Serial("/dev/serial0", 57600, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, 1)
		if ser :
			count = ser.inWaiting()
			if count > 0 :
				ser.read(count) # clear serial buffer
			ser.write(b"\xF6")
			data = ser.read(1)
			if data == b"e" :
				data = ser.read(1)	# read second byte of hadshake
		else :
			data = 0
		if data == b"p" or data == b"y" :
			# successfully connected
			status = "stopped"
		else :
			# not connected -> power off
			if ser :
				ser.close()
			ser = False
			GPIO.output(POWER, GPIO.HIGH)
			status = "off"
	finally:
		ser_lock.release()

	return 0

	
def powerOff():
	global status
	global ser
	status = "off"
	ser_lock.acquire()
	if ser :
		ser.close()	
		ser = False
	ser_lock.release()
	# power off
	GPIO.output(POWER, GPIO.HIGH)
	GPIO.output([FOCUS_UP, FOCUS_DOWN], GPIO.LOW)
	return 0
	
def powerStatus():
	return GPIO.input(POWER) == GPIO.LOW


@get('/laser/status')
def getStatus():
	global start_time
	global pos, pos_count, pixel_count
	global status
	pos_lock.acquire(); x = pos[0]; y = pos[1]; count = pos_count; pos_lock.release()
	timestamp = int(round(time.time() * 1000))
	timeLeft = "-"
	if pixel_count > 0 :
		progress = int(round(count*100 / pixel_count))
		if progress > 5 and  progress < 100 :
			timeLeft = ( (timestamp - start_time) / progress * (100 - progress) / 1000 )
			timeLeft = (timeLeft + 45) / 60 # convert to minutes
		else :
			timeLeft = "?"
	else :
		progress = "---"
	if status == "off" or status == "stopped" :
		progress = "---"
	if status == "finished" :
		progress = 100
		
	return json.dumps({
		"timestamp": timestamp,
		"status": status,
		"power": powerStatus(),
		"intensity": intensity,
		"pos": { "x": x, "y": y},
		"timeLeft": timeLeft,
		"progress": progress
	})
	
	
@get('/laser/power')
def getPower():
	return json.dumps( powerStatus() )
@put('/laser/power')
def setPower():
	global status
	if request.json == 1 :
		powerOn()
	else :
		powerOff()
	return json.dumps(status)

	
@get('/laser/focus')
def getFocus():
	response.set_header('Content-type', 'application/json')
	global json_buffer, active_json_buffer, buffer_lock
	buffer_lock.acquire(); idx = active_json_buffer; buffer_lock.release()
	buf = json_buffer[idx]
	return buf
@put('/laser/focus')
def setFocus():
	driveFocue(request.json)
	return getFocus()
def driveFocue(val = False):
	global status
	if val == "auto" and (status == "stopped" or status == "finished") :
		# autofocus
		status = "autofocus"
		global autofocus_mode, autofocus_cnt, autofocus_val
		autofocus_mode = 1
		autofocus_cnt = 0
		autofocus_val = 0		
	elif val < 0 :
		# focus up
		GPIO.output([FOCUS_UP, FOCUS_DOWN], [GPIO.HIGH, GPIO.LOW])
	elif val > 0 :
		# focus down
		GPIO.output([FOCUS_UP, FOCUS_DOWN], [GPIO.LOW, GPIO.HIGH])
	else :
		# stop focus
		GPIO.output([FOCUS_UP, FOCUS_DOWN], GPIO.LOW)


	
@get('/laser/control')
def getControl():
	global status
	return json.dumps(status)
@put('/laser/control')
def setControl():
	global status
	global ser
	ser_lock.acquire()
	if ser :
		cmd = request.json
		if cmd == "start" :
			if status != "paused" :
				status = "printing"
				ser_lock.release()
				#sendLaserImage() TODO, need to resend on multi pass images
				resetStatus()
				global start_time
				start_time = int(round(time.time() * 1000))
				ser_lock.acquire()
			ser.write(b"\xF1")
			status = "printing"
		elif cmd == "pause" :
			if status == "printing" :
				ser.write(b"\xF2")
				status = "paused"
		elif cmd == "reset" :
			resetStatus()
			ser.write(b"\xF9")
			time.sleep(1)
		else :
			ser_lock.release()
			return "ERROR: unknown command (" + cmd + ")"
		ser_lock.release()
		return json.dumps(status)
	else :
		return "ERROR: NEJE Laser not connected"

		
@get('/laser/preview')
def getPreview():
	global preview
	return json.dumps(preview)
@put('/laser/preview')
def setPreview():
	global preview
	global ser
	if ser :
		ser_lock.acquire()
		set = request.json
		if set == "origin" :
			ser.write(b"\xF3")
			preview = "origin"
		elif set == "center" :
			ser.write(b"\xFB")
			preview = "center"
		elif set == "box" :
			ser.write(b"\xF4")
			preview = "box"
		else :
			ser_lock.release()
			return "ERROR: unknown position command (" + set + ")"
		ser_lock.release()			
		return json.dumps(preview)
	else :
		return "ERROR: NEJE Laser not connected"
	
@put('/laser/move/<coord>')
def setMove(coord):
	global ser
	if ser :
		ser_lock.acquire()
		dir = request.json
		if coord == "x" and dir < 0 :
			ser.write(b"\xF5\x03")
		elif coord == "x" and dir > 0 :
			ser.write(b"\xF5\x04")
		elif coord == "y" and dir < 0 :
			ser.write(b"\xF5\x01")
		elif coord == "y" and dir > 0 :
			ser.write(b"\xF5\x02")
		ser_lock.release()			
		return
	else :
		return "ERROR: NEJE Laser not connected"
	
	
@get('/laser/intensity')
def getIntensity():
	global intensity
	return json.dumps(intensity)
@put('/laser/intensity')
def setIntensity():
	global intensity
	global ser
	if ser :
		intensity = sendIntensity(request.json)
		return json.dumps(intensity)
	else :
		return "ERROR: NEJE Laser not connected"
	

@route('/')
def index():
    return static_file("index.html", root=WWW_DIR)

	
@route('/laser/image.jpg')
def data_image():
	response.set_header('Content-type', 'image/jpeg')
	global img_buffer, active_img_buffer, buffer_lock
	buffer_lock.acquire(); idx = active_img_buffer;	buffer_lock.release()
	
	ret, buf = cv2.imencode('.jpg', img_buffer[idx]) # TODO optimize to reuse encoded JPEG
	
	return buf.tostring()

	
@route('/laser/focus.jpg')
def focus_image():
	response.set_header('Content-type', 'image/jpeg')

	# get raw image
	global img_buffer, active_img_buffer, active_json_buffer, buffer_lock
	buffer_lock.acquire(); idx = active_img_buffer;	buffer_lock.release()
	img = img_buffer[idx]

	x_min = 40; x_max = 280
	y_min = 40; y_max = 200
	crop = img[y_min:y_max,x_min:x_max]

	#gray = img[y_min:y_max,x_min:x_max,0]	# use blue as gray channel
	#gray = img[y_min:y_max,x_min:x_max,1]	# use green as gray channel
	#gray = img[y_min:y_max,x_min:x_max,2]	# use red as gray channel
	gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
	
	# detect laser point sharpness
	global focus, focus_hist
	max = gray.max()
	sharpness  = cv2.Laplacian(gray, cv2.CV_64F).var() 
	val = sharpness / (1000 - max) * 1000
	val = val * 0.5 + focus * 0.5

	focus_update = np.append(focus_hist[1:], val)
	d = np.append(focus_update - focus_hist, [val - focus, val - focus])
	delta = np.mean( d[2:] )
	focus_hist = focus_update
	s = sorted(focus_update)
	focus = np.mean( s[1:-1] )
	if abs(delta) > 0.05 :
		focus += delta
	
	FOCUS_FACT = 0.995
	MAX_CNT = 50
	STABILIZE_CNT = 10
		
	# autofocus
	global autofocus_mode, autofocus_cnt, autofocus_val
	if autofocus_mode > 0 :
		autofocus_cnt = autofocus_cnt + 1
		# init
		if autofocus_mode == 0 :
			autofocus_val = focus
			autofocus_mode = 1
			autofocus_cnt = 0

		# 1. drive down until focus decreasng
		if autofocus_mode == 1 :
			print "autofocus #1 ", autofocus_val, focus
			if ((focus < autofocus_val * FOCUS_FACT) and ( autofocus_cnt > STABILIZE_CNT)) or ( autofocus_cnt > MAX_CNT) :
				# stop focus
				driveFocue(0);
				autofocus_mode = autofocus_mode + 1
				autofocus_cnt = 0
			else :
				# focus down
				if autofocus_val < focus :
					autofocus_val = focus
				driveFocue(1);

		# 2. wait to stabilize focus		
		elif autofocus_mode == 2 :
			autofocus_val = autofocus_val * 0.5 + focus * 0.5
			if ( autofocus_cnt > STABILIZE_CNT) :
				print "autofocus #2 ", autofocus_val, focus
				autofocus_mode = autofocus_mode + 1
				autofocus_cnt = 0

		# 3. drive up until focus point is increasng
		elif autofocus_mode == 3 :
			print "autofocus #3 ", autofocus_val, focus
			if ((focus < autofocus_val * FOCUS_FACT) and ( autofocus_cnt > STABILIZE_CNT)) or ( autofocus_cnt > MAX_CNT) :
				# stop focus
				driveFocue(0);
				autofocus_mode = autofocus_mode + 1
				autofocus_cnt = 0
			else :
				# focus up
				if autofocus_val < focus :
					autofocus_val = focus
				driveFocue(-1);

		# 4. wait to stabilize focus		
		elif autofocus_mode == 4 :
			autofocus_val = autofocus_val * 0.5 + focus * 0.5
			if ( autofocus_cnt > STABILIZE_CNT) :
				print "autofocus #4 ", autofocus_val, focus
				autofocus_mode = autofocus_mode + 1
				autofocus_cnt = 0

		# 5. drive back for 5 iterrations
		elif autofocus_mode == 5 :
			print "autofocus #5 ", autofocus_val, focus
			driveFocue(1);
			autofocus_mode = autofocus_mode + 1
			autofocus_cnt = 0

		# 6. wait to stabilize focus		
		elif autofocus_mode == 6 :
			print "autofocus #6 ", autofocus_val, focus
			if ( autofocus_cnt > 7) :
				driveFocue(0);
				autofocus_mode = autofocus_mode + 1
				autofocus_cnt = 0
			
		else :
			autofocus_mode = 0
			driveFocue(0);
			global status
			status = "stopped"

			
	# compose focus data
	data = json.dumps({
		"timestamp": round(time.time() * 1000, 0),
		"status": status,
		"focus": round(focus, 2)
	})

	# save JSON object
	buffer_lock.acquire();
	active_json_buffer = (active_json_buffer +1) % BUFFER_COUNT
	json_buffer[active_json_buffer] = data;	
	buffer_lock.release()
	
	# return focus image
	ret, buf = cv2.imencode('.jpg', crop) # TODO optimize to reuse encoded JPEG
	return buf.tostring()

	
@post('/upload')
def upload():
	global ser
	if not(ser) :
		print "ERROR: NEJE Laser not connected"
		return "ERROR: NEJE Laser not connected"

	upload = request.files.get('upload')
	name, ext = os.path.splitext(upload.filename)
	if ext.lower() not in ('.png','.jpg','.jpeg'):
		print 'File extension not allowed'
		return 'File extension not allowed'

	# read uploaded image
	global status
	status = "uploading"
	data_blocks = []
	byte_count = 0
	buf = upload.file.read(BUF_SIZE)
	while buf:
		byte_count += len(buf)
		if byte_count > MAX_SIZE:
			raise HTTPError(413, 'Request entity too large (max: {} bytes)'.format(MAX_SIZE))
		data_blocks.append(buf)
		buf = upload.file.read(BUF_SIZE)
	buf = "".join(data_blocks) # flatten data_blocks
	data = np.fromstring(buf, dtype='uint8') #use numpy to construct an array from the bytes
	
	# process uploaded image
	img = cv2.imdecode(data, cv2.cv.CV_LOAD_IMAGE_GRAYSCALE)
	# make sure that image is < 500x500
	w = img.shape[1]; h = img.shape[0]; ratio = w/h
	if w > 500 or h > 500 :
		if w > 500 :
			w = 500; h = int(w / ratio)
		if h > 500 :
			w = int(h * ratio); h = 500
		img = cv2.resize(img, (h, w))
		
	# create B/W image
	ret, mask = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)
	cv2.imwrite(WWW_DIR + "/uploads/mask.png", mask)
	
	# send new image to laser for preview
	sendLaserImage()

	resetStatus()
	return getStatus()

	
@route('/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root=WWW_DIR)

	
	
# do web cam processing in separate thread
def webcam_thread():
	# init web cam
	camera = cv2.VideoCapture(0)
	
	call(["v4l2-ctl", "-c", "exposure_auto=1"])
	call(["v4l2-ctl", "-c", "exposure_auto_priority=0"])
	call(["v4l2-ctl", "-c", "exposure_absolute=350"])

	#camera.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 352)
	#camera.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 288)
	camera.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 320)
	camera.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 240)
	#camera.set(cv2.cv.CV_CAP_PROP_FPS , 15)
	camera.set(cv2.cv.CV_CAP_PROP_BRIGHTNESS, 0.8)
	camera.set(cv2.cv.CV_CAP_PROP_CONTRAST, 1.0)
	
	print "FRAME_WIDTH  ", camera.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH);
	print "FRAME_HEIGHT ", camera.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT);
	
	while True :
	 
		# retrieve current image
		ret, img = camera.read()
		img = cv2.flip(img, -1) # rotate 180deg
		
		# remove red tint
		img[:,:,2] *= 0.8
		d = img[:,:,2] - img[:,:,1]
		delta = d.mean()

		img[:,:,2] -= delta

		# write to image buffer
		global img_buffer, json_buffer, active_img_buffer, buffer_lock
		idx = (active_img_buffer +1) % BUFFER_COUNT
		img_buffer[idx] = img
		buffer_lock.acquire(); active_img_buffer = idx; buffer_lock.release()
			
		time.sleep(0.1)

		
# read data from serial port
def serial_thread():
	global ser
	global status
	buf = []
	while True:
		time.sleep(0.2)

		ser_lock.acquire()
		if not(ser) :
			ser_lock.release()
			continue
		
		try:
			# append data from serial port to buffer
			count = ser.inWaiting()
			if count > 0 :
				buf.extend( ser.read(count) )
				
				while len(buf) > 0 :
					b = ord(buf[0])
					if b == 0xFF :
						# decode position of laser
						if ( len(buf) < 5 ):
							break	# wait for buffer to fill
						x = ord(buf[1]) * 100 + ord(buf[2])
						y = ord(buf[3]) * 100 + ord(buf[4])
						del buf[0:5]
						global pos_count
						pos_lock.acquire(); pos[0] = x; pos[1] = y; pos_count = pos_count + 1; pos_lock.release()
					elif b == 0x66 :
						status = "finished"
						del buf[0]
					elif b == 0x79 :
						# laser reseted
						status = "stopped"
						del buf[0]
					else :
						# ignore unknown byte
						print "unknown response: ", hex(ord((buf[0])))
						del buf[0]
		finally:
			ser_lock.release()
		

# init image data
tmp = Image.open(WWW_DIR + "/uploads/mask.png")
stat = ImageStat.Stat(tmp)
pixel_count = (stat.count[0] - stat.sum[0]/255)
tmp = 0
		
# start webcam thread
thread.start_new_thread(webcam_thread, ())

# start serial thread
thread.start_new_thread(serial_thread, ())


# start web server
run(host='0.0.0.0', port=8080, debug=False, quiet=True)
