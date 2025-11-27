#!/usr/bin/env python3
import os
import socket
import threading
import signal
import logging
import sys

bind_ip = os.getenv("C2_BIND_IP", "0.0.0.0")
port = int(os.getenv("C2_PORT", "9001"))

logging.basicConfig(level=logging.INFO)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    server.bind((bind_ip, port))
except Exception:
    logging.exception("Failed to bind to %s:%s", bind_ip, port)
    sys.exit(1)
server.listen(5)
logging.info("C2 server starting on %s:%s", bind_ip, port)


def handle_signal(signum, frame):
    logging.info("C2 server shutting down")
    server.close()
    sys.exit(0)


signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

def handle(client):
    client.send(b"Connected to C2\n")
    client.close()

while True:
    try:
        client, addr = server.accept()
    except Exception:
        logging.exception("Error accepting connection")
        break
    threading.Thread(target=handle, args=(client,), daemon=True).start()

server.close()
logging.info("C2 server stopped")
