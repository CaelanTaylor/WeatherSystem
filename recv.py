from sx126x import sx126x
import time
import threading
import mysql.connector
import ollama
import queue

location = "Test Location"

global msg, message, windspd, winddir, wtemp, atemp

message = None
msg = None  

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

sql = "INSERT INTO weatherdata (date, time, location, windspeed, winddirection, wtemp, atemp) VALUES (%s, %s, %s, %s, %s, %s, %s)"

SERIAL_PORT = "/dev/ttyS0"

lora = sx126x(
    serial_num="/dev/ttyS0",
    freq=433,
    addr=0x0022,
    power=22,
    rssi=True
)

msg_queue = queue.Queue()

def recv():
    global msg
    while True:
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
            msg_queue.put(msg)
t1 = threading.Thread(target=recv)

t1.start()

while True:
    time.sleep(1)
    while not msg_queue.empty():
        print(msg_queue.get())
        mycursor.execute("SELECT * FROM weatherdata")
        rows = mycursor.fetchall()
        columns = [desc[0] for desc in mycursor.description]

        # Format the data as a string
        db_content = "Weather Data:\n"
        db_content += ", ".join(columns) + "\n"
        for row in rows:
            db_content += ", ".join(str(item) for item in row) + "\n"
        print("1")
        response = ollama.chat(
            model='smollm2:360m',  # or 'mistral', etc.
            messages=[
                {'role': 'user', 'content': f"Here is the weather database:\n\n{db_content}\n\nSummarize the recent weather trends for\n\n{location}\n\nand make a prediction for the time until the next day. The units are in knots and celsius."}
            ]
        )
        print(response['message']['content'])
