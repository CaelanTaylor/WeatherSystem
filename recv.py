import time
import threading
import mysql.connector
import ollama
import socket
import json # Added for config management
import os   # Added for file path checks

# --- CONFIGURATION ---
CONFIG_FILE = "config.json"

# Set Variables
global msg, message, windspd, winddir, data
message = None
msg = None  
data = None


# --- HELPER FUNCTIONS ---

def get_default_settings():
    return {
        "location": "Test Location",
        "enable_storage": True
    }

def load_settings():
    """Helper to load settings from the shared JSON file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            print(f"Error reading or decoding {CONFIG_FILE} in recv.py. Using default settings.")
            return get_default_settings()
    else:
        # If file doesn't exist, return defaults
        return get_default_settings()

def getdate():
    tm = time.localtime()
    date = time.strftime("%Y-%m-%d", tm)  # MySQL DATE format
    return date

def gettime():
    tm = time.localtime()
    currtime = time.strftime("%H:%M:%S", tm)  # MySQL TIME format
    return currtime


# --- DATABASE INITIALIZATION ---

# Load initial settings
settings = load_settings()
location = settings.get('location', get_default_settings()['location'])
enable_storage = settings.get('enable_storage', get_default_settings()['enable_storage'])

mydb = None
mycursor = None

def init_db_connection(enable):
    """Initializes or closes the database connection based on the enable flag."""
    global mydb, mycursor
    if enable:
        try:
            mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                password="spring",
                database="weatherdata"
            )
            mycursor = mydb.cursor()
            print("Database connection successfully established.")
            return True
        except mysql.connector.Error as err:
            print(f"Error connecting to database: {err}. Data storage will remain disabled.")
            mydb = None
            mycursor = None
            return False
    else:
        if mydb:
            mydb.close()
        mydb = None
        mycursor = None
        return False

# Establish initial connection (if enabled)
enable_storage = init_db_connection(enable_storage)


# --- MAIN RECEIVER LOGIC ---

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    HOST = ''  # Listen on all interfaces
    PORT = 50000
    s.bind((HOST, PORT))
    print(f"Data receiver listening on port {PORT}. Storage is {'ENABLED' if enable_storage else 'DISABLED'}.")
    
    while True:
        # Check settings periodically to pick up changes
        current_settings = load_settings()
        
        # 1. Update location
        location = current_settings.get('location', location)
        
        # 2. Check and reconfigure storage state
        current_enable_storage = current_settings.get('enable_storage', enable_storage)
        if current_enable_storage != enable_storage:
             print(f"Storage setting changed from {enable_storage} to {current_enable_storage}.")
             enable_storage = init_db_connection(current_enable_storage)
             
        
        s.listen(1)
        conn, addr = s.accept()
        with conn:
            data = conn.recv(1024)
            if data:
                data_str = data.decode('utf-8')
                data_list = data_str.split(',')
                
                # Check if the data list has the expected 4 elements
                if len(data_list) == 2:
                    try:
                        windspd, winddir = map(float, data_list)
                    except ValueError:
                        print(f"Received malformed data: {data_str}")
                        continue # Skip to the next iteration
                    
                    if enable_storage and mydb and mycursor:
                        # Get date and time in MySQL format
                        date = getdate()
                        currtime = gettime()
                        
                        # Prepare and execute SQL
                        sql = "INSERT INTO weatherdata (date, time, location, windspeed, winddirection) VALUES (%s, %s, %s, %s, %s)"
                        val = (date, currtime, location, windspd, winddir)
                        try:
                            mycursor.execute(sql, val)
                            mydb.commit()
                            # print("Data saved to database.") # Uncomment for more verbose logging
                        except mysql.connector.Error as err:
                            print(f"Error saving data to MySQL: {err}. The connection might be stale.")
                            # Attempt to re-establish connection if it failed
                            self_healing = init_db_connection(True)
                            if not self_healing:
                                enable_storage = False
                                
                    else:
                        print("Data storage is disabled or DB connection is not available. Data not saved.")
                else:
                    print(f"Received data with unexpected number of values: {data_str}")