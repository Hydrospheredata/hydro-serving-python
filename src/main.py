import os
from PythonRuntime import PythonRuntime
import time

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
PORT = os.getenv("APP_GRPC_PORT", "9090")

if __name__ == '__main__':
    print("Reading the model...")
    runtime = PythonRuntime("/model")
    print("Runtime is ready to serve...")
    runtime.start(port=PORT)
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        runtime.stop()
