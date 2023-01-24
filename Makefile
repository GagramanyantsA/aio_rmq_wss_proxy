SHELL := /bin/bash

install_requirements:
	( \
	source venv/bin/activate; \
	pip3 install -r requirements.txt; \
	)

install:
	python3 -m venv venv
	make install_requirements


run_server:
	( \
	source venv/bin/activate; \
	PYTHONPATH=$(shell pwd) python3 _testing/public_sample/public_websocket_service.py; \
	)

run_client:
	( \
	source venv/bin/activate; \
	PYTHONPATH=$(shell pwd) python3 _testing/public_client_for_testing.py; \
	)