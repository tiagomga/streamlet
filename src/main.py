import sys
import socket
import logging
import multiprocessing
from server import Server

HOST = "127.0.0.1"
PORT = 10000

SERVERS_CONFIGURATION = {
    0: (HOST, PORT, socket.socket(socket.AF_INET, socket.SOCK_STREAM)),
    1: (HOST, PORT+1, socket.socket(socket.AF_INET, socket.SOCK_STREAM)),
    2: (HOST, PORT+2, socket.socket(socket.AF_INET, socket.SOCK_STREAM)),
    3: (HOST, PORT+3, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
}

def main():
    if len(sys.argv) != 2:
        logging.error("Usage: python3 main.py <server_id>")
        sys.exit(1)
    try:
        server_id = int(sys.argv[1])
    except ValueError:
        sys.exit(1)
    server = Server(SERVERS_CONFIGURATION, server_id)
    server.run()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    multiprocessing.set_start_method("fork")
    try:
        main()
    except KeyboardInterrupt:
        logging.error("Aborted execution.")