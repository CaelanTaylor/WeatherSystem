import time
import threading
import mysql.connector
import ollama
import socket
from config import load_config, save_config  # Import functions from config.py

# Load configuration settings
location, db_enabled = load_config() # 👈 Location is loaded here

# Set Variables
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
mydb = None
if db_enabled:
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="spring",
            database="weatherdata"
        )
        mycursor = mydb.cursor()
        print(f"Database connection successful. Inserting data for location: {location}")
    except mysql.connector.Error as err:
        print(f"Database connection failed: {err}")
        db_enabled = False # Disable DB operations if connection fails
else:
    print("Database is disabled in config. Data will not be stored.")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    HOST = ''  # Listen on all interfaces
    PORT = 50000
    try:
        s.bind((HOST, PORT))
        print(f"Listening for incoming data on port {PORT}...")
    except Exception as e:
        print(f"Error binding socket: {e}")
        exit()

    while True:
        s.listen(1)
        conn, addr = s.accept()
        with conn:
            data = conn.recv(1024)
            if data:
                data_str = data.decode('utf-8')
                data_list = data_str.split(',')
                try:
                    # Assuming data_list contains: windspeed, winddirection, wtemp, atemp
                    windspd, winddir, wtemp, atemp = map(float, data_list)
                except ValueError as ve:
                    print(f"Error parsing received data: {ve}. Data was: {data_str}")
                    continue

                # Get date and time in MySQL format
                date = getdate()
                currtime = gettime()

                if db_enabled and mydb:
                    try:
                        # Prepare and execute SQL
                        sql = "INSERT INTO weatherdata (date, time, location, windspeed, winddirection, wtemp, atemp) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                        val = (date, currtime, location, windspd, winddir, wtemp, atemp) # 👈 USES THE LOCATION VARIABLE
                        mycursor.execute(sql, val)
                        mydb.commit()
                        print(f"Inserted data for {location} at {currtime}: Wind={windspd}, Dir={winddir}")
                    except mysql.connector.Error as err:
                        print(f"Error inserting data into database: {err}")
                else:
                     print(f"Received data (not saved): Wind={windspd}, Dir={winddir}")