from task_manager import Task
import design_utils as design

config = {
		'workspace': {
					'homePos': [-150,100],
					'size': [300, 200]
				},
		'tasks': [
					{'id': "engrave", "colors": [design.BLUE], "speed": 100, "type": Task.VECTOR},
					{'id': "cut", "colors": [design.BLACK, design.RED], "speed": 50, "type": Task.VECTOR}
				]
		}

def configTasks(taskmanager):
	try:
		del taskmanager.tasks[:]
		for task in config['tasks']:
			taskmanager.tasks.append( Task(id=task['id'], colors=task['colors'], speed=task['speed'], type=task['type']) )
	except:
		print("task config error")

def configWorkspace(workspace):
	try:
		workspace.homePos = config['workspace']['homePos']
		workspace.size = config['workspace']['size']
		workspace.update()
	except:
		print("workspace config error")
