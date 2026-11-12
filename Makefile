PYTHON ?= python3

.PHONY: verify
verify:
	$(PYTHON) -B -m unittest discover -s tests -v
