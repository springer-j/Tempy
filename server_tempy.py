# echo-server.py
import sys
import socket
from datetime import datetime

HOST = "0.0.0.0"  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
server.bind((HOST, 65432))

temps = 'temps.txt'
log = 'log.txt'

print("[!] Listening on port " + str(PORT))

server.listen()

def get_now():
    now = datetime.now()
    date = now.strftime("%m/%d/%y")
    time = now.strftime("%H:%M")
    return date, time


def write_log(address, message):
    with open(log,'a') as file:
        date, time = get_now()
        time_string = f"\n[{date} | {time}]"
        addr = f" [{address}] "
        file.write(time_string + addr + message)
        

def write_temps(message):
    print("[TEMPY] Writing to log...")
    with open(temps, 'a') as file:
        date, time = get_now()
        time_string = f"\n{date} {time} "
        file.write(time_string + message)


def handle(client, address):
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            #print('MESSAGE: ', message)
            client.send("OK".encode('utf-8'))
            write_temps(message)
        except Exception as error:
            print(error.args[0])
            client.close()
            print("[X] Client disconnected.")
            write_log(address[0], "CLIENT DISCONNECTED")
            break
        except KeyboardInterrupt:
            client.close()
            print("[X] CTRL+C DETECTED")
            write_log("SERVER", "CTRL+C DETECTED")
            sys.exit()


def receive():
    while True:
        client, address = server.accept()
        print("[~] Client connected: ", address[0])
        write_log(address[0], "CLIENT CONNECTED")
        handle(client, address)


receive()
