#!/bin/sh

chmod +x /app/src/main.py
sync 

cd /app/src
exec python3 main.py
