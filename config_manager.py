from task_manager import Profile, Task
import design_utils as design
from distutils.dir_util import mkpath
import json as json_tools
import logging


# import laser communication
import k40_wrapper
import laser_emulator

# web server configuration
HTML_FOLDER = 'HTML'
UPLOAD_FOLDER = HTML_FOLDER + '/uploads'
COMPUTED_FOLDER = HTML_FOLDER + '/computed'
CONFIG_FOLDER = HTML_FOLDER + '/config'
ALLOWED_EXTENSIONS = set(['dxf']) # TODO set(['svg', 'dxf', 'png', 'jpg', 'jpeg'])
MAX_CONTENT_LENGTH = 64 * 1024 * 1024

config = {
		'workspace': {
			'home': 'top-left', # top-left, top-right, bottom-left, bottom-right, center
#			'home': 'center', # top-left, top-right, bottom-left, bottom-right, center
			'size': [300, 200]
		},
		# sample profiles
		'profiles': [
			{
				'id': "sample",
				'name': "sample profile",
				'tasks': [
					{'id': "engrave", 'name': "engrave", 'colors': [design.BLUE], 'speed': 30, 'type': Task.VECTOR},
					{'id': "cut", 'name': "cut", 'colors': [design.BLACK, design.RED], 'speed': 10, 'type': Task.VECTOR, 'repeat': 1}
				]
			}
		],
		'laser': {
					'endstopPos': [0,5],
#					'type': k40_wrapper		# K40 China Laser
					'type': laser_emulator	# Simulated Laser for Testing
				},
		'sensor': {
			'config': {
				'port': "/dev/ttyUSB0",
				'baud': 115200,
			},
            'indexMap': {
				'waterFlow': { 'val': 0, 'alert': 1 },
				'waterTemp': {'val': 2, 'alert': 3},
				'PSUTemp': {'val': 4, 'alert': 5},
				'general': {'alert': 6}
			}
		}
}

def configLaser():
	laser = config['laser']['type'].LASER_CLASS()
	laser.setEndstopPos(config['laser']['endstopPos'])
	return laser
		
def configFileManager(filemanager):
	# nothing to do
	pass

def loadProfiles(taskmanager):
	try:
		logging.info("loadProfiles from: " + CONFIG_FOLDER)
		with open(CONFIG_FOLDER+"/profiles.json") as f:
			data = json_tools.load(f)
		taskmanager.profiles.clear()
		for profile in data:
			taskmanager.setActiveProfile( profile )
	except IOError as e:
		# init with sample profiles
		for profile in config['profiles']:
			taskmanager.setActiveProfile(profile)
	except Exception as e:
		logging.error("load profiles error: " + str(e))

def saveProfiles(taskmanager):
	try:
		logging.info("saveProfiles to: " + CONFIG_FOLDER)
		mkpath(CONFIG_FOLDER)
		data = taskmanager.toJson()['profiles']
		with open(CONFIG_FOLDER+"/profiles.json", 'wt') as f:
			json_tools.dump(data, f, sort_keys=True, indent=2)
	except Exception as e:
		logging.error("load profiles error: " + str(e))

def configWorkspace(workspace):
	try:
		workspace.home = config['workspace']['home']
		workspace.size = config['workspace']['size']
		workspace.defaultOrigin = config['workspace']['home']
		workspace.reset()
	except Exception as e:
		logging.error("workspace config error: " + str(e))


