# hydro-serving-tensorflow
TensorFlow runtime for [ML-Lambda](https://github.com/Hydrospheredata/hydro-serving).
Provides GRPC API for a TensorFlow model saved with `SavedModelBuilder`.

## Build commands
- `make test`
- `make tf` - build docker runtime with tensorflow:latest-py3 base image
- `make tf-${VERSION}` - build docker runtime with tensorflow:${VERSION}-py3 base image
- `make clean` - clean repository from temp files