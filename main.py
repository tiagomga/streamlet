import socket
import sys
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
    print(SERVERS_CONFIGURATION)
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <server_id>", file=sys.stderr, flush=True)
        sys.exit(1)
    try:
        server_id = int(sys.argv[1])
    except ValueError:
        sys.exit(1)
    server = Server(SERVERS_CONFIGURATION, server_id)

if __name__ == "__main__":
    main()