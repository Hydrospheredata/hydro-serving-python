PYTHON_EXEC=python

.PHONY: python-all
python-all: python-3.4 python-3.5 python-3.6

.PHONY: python
python: python-latest

.PHONY: python-%
python-%:
	$(eval RUNTIME_NAME = hydrosphere/serving-runtime-python-$*)
	docker build --no-cache --build-arg PYTHON_IMAGE_VERSION=$* --build-arg SIDECAR_VERSION=$(SIDECAR_VERSION) -t $(RUNTIME_NAME):latest .

run:
	${PYTHON_EXEC} src/main.py

.PHONY: test
test: test-runtime

test-runtime:
	cd test && $(PYTHON_EXEC) test.py

clean: clean-pyc

clean-pyc:
	find . -name "*.pyc" -type f -delete
	find . -name "*.pyo" -type f -delete

