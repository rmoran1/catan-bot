SHELL := /bin/bash

build:
	pip3 install -r catan/requirements.txt

install:
	pip3 install -r catan/requirements.txt

test:
	python3 catan-spectator/main.py

clean:
	@:
