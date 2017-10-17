#!/usr/bin/python


import sys
import time
import k40_wrapper


laser=k40_wrapper.LASER_CLASS()
try:
    print ("INIT:")
    laser.init("mm")
	
    print ("HOME:"); laser.home(); time.sleep(3)
        
    print ("MOVE ABS: 100, -100"); laser.goto(100, -100); time.sleep(2)

    print ("MOVE REL: 50, 0"); laser.move(50, 0); time.sleep(2)
    print ("MOVE REL: -50, -50"); laser.move(-50, -50); time.sleep(2)

    print ("MOVE ABS: 0, 0"); laser.goto(0, 0); time.sleep(2)

    print ("UNLOCK:"); laser.unlock(); time.sleep(2)

    print ("RELEASE:"); laser.release()

except StandardError as e:
    error_text = "%s" %(e)
    if "BACKEND" in error_text.upper():
        error_text = error_text + " (libUSB driver not installed)"
    print ("USB Error: %s" %(error_text))
    sys.exit()

except:
    print("Unknown USB Error")
    sys.exit()
                

print ("DONE")
