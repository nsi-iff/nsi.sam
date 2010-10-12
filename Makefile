PYTHON=python

all: install run_unit_test

install_cyclone:
	@rm -Rf cyclone
	git clone git://github.com/fiorix/cyclone.git
	cd cyclone && $(PYTHON) setup.py install
	@rm -Rf cyclone

install: install_cyclone
	$(PYTHON) setup.py develop

run_unit_test:
	cd nsisam/tests && $(PYTHON) testInterface.py && $(PYTHON) testAuth.py
