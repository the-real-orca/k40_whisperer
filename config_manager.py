from task_manager import Profile, Task
import design_utils as design
from distutils.dir_util import mkpath
import json as json_tools

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
			'home': 'top-left', # top-left, top-right, bottom-left, bottom-right
			'homeOff': [0,0],
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
					'type': k40_wrapper		# K40 China Laser
#					'type': laser_emulator	# Simulated Laser for Testing
				}
}

def configLaser():
	laser = config['laser']['type'].LASER_CLASS()
	return laser
		
def configFileManager(filemanager):
	# nothing to do
	pass

def loadProfiles(taskmanager):
	try:
		with open(CONFIG_FOLDER+"/profiles.json") as f:
			data = json_tools.load(f)
		taskmanager.profiles.clear()
		for profile in data:
			taskmanager.setActiveProfile( profile )
	except IOError as e:
		# init with sample profiles
		for profile in config['profiles']:
			taskmanager.setActiveProfile(profile)
	except StandardError as e:
		print("load profiles error", e)

def saveProfiles(taskmanager):
	try:
		print("saveProfiles")
		mkpath(CONFIG_FOLDER)
		data = taskmanager.toJson()['profiles']
		with open(CONFIG_FOLDER+"/profiles.json", 'wt') as f:
			json_tools.dump(data, f, sort_keys=True, indent=2)
	except StandardError as e:
		print("save profiles error", e)

def configWorkspace(workspace):
	try:
		workspace.home = config['workspace']['home']
		workspace.homeOff = config['workspace']['homeOff']
		workspace.size = config['workspace']['size']
		workspace.defaultOrigin = config['workspace']['home']
		workspace.reset()
	except:
		print("workspace config error")


