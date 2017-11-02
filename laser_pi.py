#!/usr/bin/python


import sys
import traceback
import time
import k40_wrapper


laser=k40_wrapper.LASER_CLASS()

try:
    print ("INIT:"); laser.init("mm"); print ("OK")
	
    print ("HOME:"); laser.home(); print ("OK")
        
    print ("MOVE ABS: 100, -100"); laser.goto(100, -100); print ("OK")
    print ("MOVE REL: 50, 0"); laser.move(50, 0); print ("OK")
    print ("MOVE ABS: 0, 0"); laser.goto(0, 0); print ("OK")

    print ("UNLOCK:"); laser.unlock(); print ("OK")
    print ("RELEASE:"); laser.release(); print ("OK")

except StandardError as e:
    error_text = "%s" %(e)
    if "BACKEND" in error_text.upper():
        error_text = error_text + " (libUSB driver not installed)"
    print ("USB Error: %s" %(error_text))
    print (traceback.format_exc())
    sys.exit()

except:
    print("Unknown USB Error")
    sys.exit()
                

print ("DONE")
