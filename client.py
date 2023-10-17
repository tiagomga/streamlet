import socket
import sys

HOST = "127.0.0.1"
PORT = 50000

def print_operations():
    print("OPERATIONS:")
    print("   1 - SEND VALUE")
    print("   2 - OTHER OPERATION")
    print("   3 - EXIT")

def send_value():
    receiver_id = input("Receiver ID: ")
    value = input("Value: ")
    data = f"({receiver_id}, {value})".encode()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(data)

def main():
    print_operations()
    while True:
        user_input = input(">>> ")
        if user_input == "1":
            send_value()
        elif user_input == "2":
            #TODO
            return
        elif user_input == "3":
            sys.exit(0)
    
if __name__ == "__main__":
    main()