PYTHON_EXEC=python
VERSION=dev

.PHONY: python-all
python-all: python-3.7 python-3.8.11

.PHONY: python-%
python-%:
	docker build --no-cache --build-arg PYTHON_IMAGE_VERSION=$* -t hydrosphere/serving-runtime-python-$*:${VERSION} .

run:
	${PYTHON_EXEC} src/main.py

.PHONY: test
test: test-runtime

test-runtime:
	pytest test	

clean: clean-pyc

clean-pyc:
	find . -name "*.pyc" -type f -delete
	find . -name "*.pyo" -type f -delete

