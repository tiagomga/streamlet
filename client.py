import socket
import sys

HOST = "127.0.0.1"
PORT = 5000

def print_operations():
    print("OPERATIONS:")
    print("   1 - SEND VALUE")
    print("   2 - OTHER OPERATION")
    print("   3 - EXIT")

def send_value(value):
    #TODO
    return

def main():
    print_operations()
    while True:
        user_input = input(">>> ")
        if user_input == "1":
            #TODO
            return
        elif user_input == "2":
            #TODO
            return
        elif user_input == "3":
            sys.exit(0)
    
if __name__ == "__main__":
    main()