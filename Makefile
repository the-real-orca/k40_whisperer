#
# This makefile was added by the DSL K40 project and is not part of
# the original k40 whisperer code
#

all:
	@echo No default target
	@false

build-dep:
	apt install flake8 python-coverage

dep:
	apt install python-lxml python-pil python-tk python-usb

# Perform all known to work tests
test:   test.units

# Test just the code style - note: known to fail on this code base
test.style:
	flake8 ./*.py

test.units:
	./run_tests.py

# run the unit tests and additionally produce a test coverage report
cover:
	./run_tests.py cover

clean:
	rm -f htmlcov .coverage

