#!/bin/sh

chmod +x /app/src/main.py
sync 

cd /app/src
PYTHONPATH=/app:/app/src/ python3 main.py
