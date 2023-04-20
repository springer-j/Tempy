from time import sleep
import socket
import board
from w1thermsensor import W1ThermSensor
import adafruit_dht
import psutil
from rpi_lcd import LCD
from datetime import datetime
from gpiozero import LED

#----------------------------------------------------------------------------------

# Needed for some fuckin reason to make sure DHT11 works
for proc in psutil.process_iter():
    if proc.name() == "libgpiod_pulsein" or proc.name() == "libgpiod_pulsei":
        proc.kill()


#----------------------------------------------------------------------------------

# Server info

HOST = "SERVER IP"  # The server's hostname or IP address
PORT = 65432  # The port used by the server

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Devices
probe_data = W1ThermSensor()
room_data = adafruit_dht.DHT11(board.D23)
lcd = LCD()

red = LED(16)
yellow = LED(20)
green = LED(21)
white = LED(12)
lcd = LCD()

lights = [red,yellow,green,white]

update_interval = 1
write_interval = 0

data_file = "/home/tinker/Programs/aquabox/temps.txt"

# Aquarium "good" temp range
min_temp = 76
max_temp = 81
critical_low = 68
critical_high = 85

#----------------------------------------------------------------------------------
# Server funtions


def connect():
    while True:
        try:
            client.connect((HOST, PORT))
            print("[~] Connected to server")
            return client
            break
        except ConnectionRefusedError as error:
            print("[X] ", error)
    


def reconnect():
    client = socket.socket()
    #connected = False
    #while not connected:
    try:
        client.connect((HOST,PORT))
        connect = True
        print("[~] Reconnected to server")
        return client
    except socket.error:
        print("[X] Connection failed.")

#----------------------------------------------------------------------------------

def format_temp(temp):
    if temp == 0:
        return None
    return str((temp * 1.8) + 32)[0:4]


def lights_on():
    for led in lights:
        led.on()


def lights_off():
    for led in lights:
        led.off()


def light_check():
    print("[~] Running light check.")
    lights_on()
    sleep(3)
    lights_off()
        

# Contains the sleep value, flickers run light
def lap():
    sleep(update_interval - 0.4)
    white.on()
    sleep(0.1)
    white.off()
    sleep(0.1)
    white.on()
    sleep(0.1)
    white.off()
    sleep(0.1)
    

def status_lights(probe):
    temp = float(probe)
    if temp > critical_high or temp < critical_low:
        green.off()
        yellow.off()
        red.on()
        return 
    elif temp < min_temp or temp > max_temp:
        green.off()
        yellow.on()
        red.off()
        return
    else:
        green.on()
        yellow.off()
        red.off()
        return


def set_lcd(probe, room, critical=False):
    if critical:
        lcd.clear()
        lcd.text("CRITICAL TEMP!",1)
        lcd.text(f"PROBE: {probe_temp} F", 2)
    else:
        lcd.clear()
        lcd.text(f"Probe: {probe} F", 1)
        # room = None if errored out prior
        if not room:
            lcd.text(f"Room: ERROR",2)
        else:
            lcd.text(f"Room: {room} F",2)


def read_sensors(): # Returns probe, room
    probe_raw = probe_data.get_temperature()
    # Shitty DHT11 throws a lot of errors
    try:
        room_raw = room_data.temperature
    except RuntimeError as error:
        room_raw = None
        print('[!] ' + error.args[0])
    except Exception as error:
        room_raw = None
        print('[X] ' + error.args[0])

    if room_raw:
        return format_temp(probe_raw), format_temp(room_raw)
    return format_temp(probe_raw), None


def print_temps(probe_temp, room_temp, critical=False):
    now = datetime.now()
    time = now.strftime("%H:%M:%S")
    if critical:
        print("\n" + time)
        print("[X] CRITICAL TEMP!")
        print("[X] PROBE: ", probe_temp)
        if not room_temp:
            print("[~] ROOM: SENSOR ERROR")
        else:
            print("[~] ROOM: ", room_temp)
    else:
        print("\n" + time)
        print("[~] PROBE: ", probe_temp)
        if not room_temp:
            print("[~] ROOM: SENSOR ERROR")
        else:
            print("[~] ROOM: ", room_temp)
    
#----------------------------------------------------------------------------------
# Main loop

def main(client):
    sample_count = 0
    light_check()
    while True: 
        now = datetime.now()
        time = now.strftime("%H:%M:%S")
        date = now.strftime("%m/%d/%y")
        # Flips true when temps outside of min/max
        critical = False
        # Catches errors to be sent to the server
        try:
            probe_temp, room_temp = read_sensors()
            # Check for critical
            if float(probe_temp) < critical_low or float(probe_temp) > critical_high:
                print_temps(probe_temp, room_temp, critical=True)
                set_lcd(probe_temp, room_temp, critical=True)
            else:
                print_temps(probe_temp, room_temp)
                set_lcd(probe_temp, room_temp)
                
            status_lights(probe_temp)
                
        except KeyboardInterrupt:
            # file.write("\n[X] CTRL+C DETECTED")
            print("[X] CTRL+C DETECTED")
            lcd.clear()
            lights_off()
            # file.close()
            break

        if sample_count == write_interval:
            # Check if active connection with server
            if client:
                try:
                    if critical:
                        client.send(f'{probe_temp} {room_temp}'.encode('utf-8'))
                    else:
                        client.send(f"{probe_temp} {room_temp}".encode())
                    print("[!] Wrote to server")
                # Happens when disconnected during this loop
                except BrokenPipeError as error:
                    print("[!] Connection lost to server.")
                    client = reconnect()
            # Try to reestablish connection
            else:
                client = reconnect()
            sample_count = 0
        else:
            sample_count += 1
        
        lap()


client = connect()
main(client)

#----------------------------------------------------------------------------------
