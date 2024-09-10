import os
import sys
import socket
import logging
import multiprocessing
import yaml
from server import Server

HOST = "0.0.0.0"
PORT = 10000

SERVERS_CONFIGURATION = {
    0: (HOST, PORT, socket.socket(socket.AF_INET, socket.SOCK_STREAM)),
    1: (HOST, PORT+1, socket.socket(socket.AF_INET, socket.SOCK_STREAM)),
    2: (HOST, PORT+2, socket.socket(socket.AF_INET, socket.SOCK_STREAM)),
    3: (HOST, PORT+3, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
}

def main():
    global SERVERS_CONFIGURATION
    server_id = os.environ.get("SERVER_ID")
    if server_id is None and len(sys.argv) != 2:
        logging.error("Usage: python3 main.py <server_id>")
        sys.exit(1)
    try:
        if server_id:
            server_id = int(server_id)
        else:
            server_id = int(sys.argv[1])
    except ValueError:
        sys.exit(1)
    
    blockchain_directory = os.path.join(os.getcwd(), 'blockchain')
    if not os.path.exists(blockchain_directory):
        os.mkdir(blockchain_directory)
    
    config_file = os.path.join(os.getcwd(), 'config.yaml')
    if os.path.exists(config_file):
        with open("config.yaml", "r") as config:
            SERVERS_CONFIGURATION = yaml.safe_load(config)
        for id in SERVERS_CONFIGURATION:
            SERVERS_CONFIGURATION[id].append(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        SERVERS_CONFIGURATION[server_id][0] = HOST
    
    server = Server(SERVERS_CONFIGURATION, server_id)
    server.run()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    multiprocessing.set_start_method("fork")
    try:
        main()
    except KeyboardInterrupt:
        logging.error("Aborted execution.")