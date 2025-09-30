import time
import threading
import mysql.connector
import ollama
import socket

# Set Variables
location = "Test Location"

global msg, message, windspd, winddir, wtemp, atemp, data

message = None
msg = None  
data = None

# Set timing functions

def getdate():
    tm = time.localtime()
    date = time.strftime("%Y-%m-%d", tm)  # MySQL DATE format
    return date

def gettime():
    tm = time.localtime()
    currtime = time.strftime("%H:%M:%S", tm)  # MySQL TIME format
    return currtime

# Set up database connection

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="spring",
    database="weatherdata"
)

mycursor = mydb.cursor()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    HOST = ''  # Listen on all interfaces
    PORT = 50000
    s.bind((HOST, PORT))
    while True:
        s.listen(1)
        conn, addr = s.accept()
        with conn:
            data = conn.recv(1024)
            if data:
                data_str = data.decode('utf-8')
                data_list = data_str.split(',')
                windspd, winddir, wtemp, atemp = map(float, data_list)
                
                # Get date and time in MySQL format
                date = getdate()
                currtime = gettime()

                print(windspd, winddir, wtemp, atemp)
                
                # Prepare and execute SQL
                sql = "INSERT INTO weatherdata (date, time, location, windspeed, winddirection, wtemp, atemp) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                val = (date, currtime, location, windspd, winddir, wtemp, atemp)
                mycursor.execute(sql, val)
                mydb.commit()
