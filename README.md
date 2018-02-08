# hydro-serving-python
Python runtime for [ML-Lambda](https://github.com/Hydrospheredata/hydro-serving).
Provides GRPC API for a Python scripts.
Supported versions are: python-3.4 python-3.5 python-3.6

## Build commands
- `make test`
- `make python` - build docker runtime with python:latest-alpine base image
- `make python-${VERSION}` - build docker runtime with python:${VERSION}-alpine base image
- `make clean` - clean repository from temp files
