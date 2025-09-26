import time
import threading
import mysql.connector
import ollama
import socket

HOST = ''  # Listen on all interfaces
PORT = 5000

#Set Variables

location = "Test Location"

global msg, message, windspd, winddir, wtemp, atemp

message = None
msg = None  

#Set timing functions

def getdate():
    tm = time.localtime()
    date = time.strftime("%d/%m/%Y", tm)
    return date

def gettime():
    tm = time.localtime()
    currtime = time.strftime("%H:%M:%S", tm)
    return currtime

#Set up database connection

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="spring",
  database="weatherdata"
)

mycursor = mydb.cursor()

sql = "INSERT INTO weatherdata (date, time, location, windspeed, winddirection, wtemp, atemp) VALUES (%s, %s, %s, %s, %s, %s, %s)"

def recv():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        HOST = ''  # Listen on all interfaces
        PORT = 5000
        s.bind((HOST, PORT))
        s.listen(1)
        print("Waiting for connection...")
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            data = conn.recv(1024)
            if data:
                data_str = data.decode('utf-8')
                data_list = data_str.split(',')
                windspd, winddir, wtemp, atemp = map(float, data_list)
                print("Received:", windspd, winddir, wtemp, atemp)
t1 = threading.Thread(target=recv)

t1.start()