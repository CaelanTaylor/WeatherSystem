from sx126x import sx126x
import time
import threading
import mysql.connector

global msg

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="spring",
  database="weatherdata"
)

SERIAL_PORT = "/dev/ttyS0"

lora = sx126x(
    serial_num="/dev/ttyS0",
    freq=433,
    addr=0x0022,
    power=22,
    rssi=True
)

def recv():
    global message
    global msg
    while True:
        msg = lora.receive()
        if msg:
            print(msg)
            message = msg.split()
            windspd = message[0]
            atemp = message[1]
            wtemp = message[2]

t1 = threading.Thread(target=recv)

t1.start()

while True:
    time.sleep(1)
    if msg:
        print(msg)

