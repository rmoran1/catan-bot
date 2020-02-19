SHELL := /bin/bash

install:
	pip3 install -r catan-spectator/requirements.txt

test:
	@sed -i 's/yurick/patrick/' catan-spectator/views.py
	@sed -i 's/josh/droid2/' catan-spectator/views.py
	@sed -i 's/zach/charlie/' catan-spectator/views.py
	@sed -i 's/ross/ralph/' catan-spectator/views.py
	python3 catan-spectator/main.py
	@sed -i 's/patrick/yurick/' catan-spectator/views.py
	@sed -i 's/droid2/josh/' catan-spectator/views.py
	@sed -i 's/charlie/zach/' catan-spectator/views.py
	@sed -i 's/ralph/ross/' catan-spectator/views.py

clean:
	@:
