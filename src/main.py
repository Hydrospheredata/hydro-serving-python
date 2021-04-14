import os
import time
import logging

from src.grpc_server import GRPCServer

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
PORT = os.getenv("APP_PORT", "9090")

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    logger = logging.getLogger("main")
    logger.info("Reading the model...")
    runtime = GRPCServer("/model")
    logger.info("Runtime is ready to serve...")
    runtime.start(port=PORT)
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        runtime.stop()
