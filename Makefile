SHELL := /bin/bash

install:
	pip3 install -r catan-spectator/requirements.txt

test:
	python3 catan-spectator/main.py

clean:
	@:
