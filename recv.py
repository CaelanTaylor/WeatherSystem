from sx126x import sx126x
import time
import threading
import mysql.connector

location = "Test Location"

message = None

def getdate():
    tm = time.localtime()
    date = time.strftime("%d/%m/%Y", tm)
    return date

def gettime():
    tm = time.localtime()
    currtime = time.strftime("%H:%M:%S", tm)
    return currtime

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="spring",
  database="weatherdata"
)

mycursor = mydb.cursor()

sql = "INSERT INTO weather (date, time, location, windspeed, winddirection, wtemp, atemp) VALUES (%s, %s, %s, %s, %s, %s, %s)"

SERIAL_PORT = "/dev/ttyS0"

lora = sx126x(
    serial_num="/dev/ttyS0",
    freq=433,
    addr=0x0022,
    power=22,
    rssi=True
)

def recv():
    while True:
        global msg, message, windspd, winddir, wtemp, atemp
        msg = lora.receive()
        if msg:
            message = msg.split()
            windspd = message[0]
            winddir = message[1]
            wtemp = message[2]
            atemp = message[3]
            val = (getdate(), gettime(), location, windspd, winddir, wtemp, atemp)
            mycursor.execute(sql, val)
            mydb.commit()

t1 = threading.Thread(target=recv)

t1.start()

while True:
    time.sleep(1)
    if msg:
        print(message[1])