# hydro-serving-python
Python runtime for [Hydrosphere Serving](https://github.com/Hydrospheredata/hydro-serving).
Provides a GRPC API for Python scripts.

Supported versions are: python-3.7 python-3.8 

## Build commands
- `make test`
- `make python-${VERSION}` - build docker runtime with python:${VERSION}-alpine base image
- `make clean` - clean repository from temp files

## Usage

This runtime uses `src/func_main.py` script as an entry point.
You may create any arbitrary Python application within,
just keep in mind that the entry point of your script has to be located in
   `src/func_main.py`.
 

Example of a `func_main.py`:

```python
import pandas as pd
from joblib import load

# Load an ML model during runtime initialisation
clf = load('/model/files/classification_model.joblib')

# This function is called on each request
# Input and output must comply with your model's signature 
def predict(**kwargs):
    # kwargs is a dict with Numpy arrays or scalars you've specified in a signature
    x = pd.DataFrame.from_dict({"request": kwargs}).T
    predicted = clf.predict(x)
    return {"income": int(predicted)}
```

or if you wish to work with proto messages:
```python
    return {"income": TensorProto(int_val=[int(predicted)],
                                  dtype=DT_INT32,
                                  tensor_shape=TensorShapeProto())}
```
