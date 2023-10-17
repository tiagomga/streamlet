from server import Server
from broadcastserver import BroadcastServer
from multiprocessing import Process

def main():
    for process_num in range(1, 5):
        child_process = Process(target=run_processes, args=(process_num,))
        child_process.start()
    broadcast_server = Process(target=run_broadcast)
    broadcast_server.start()

def run_processes(process_num):
    Server().run(port=20000+process_num)

def run_broadcast():
    BroadcastServer().run()

if __name__ == "__main__":
    main()