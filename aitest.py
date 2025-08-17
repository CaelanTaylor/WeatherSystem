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

start = time.time()
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
    model='qwen2.5:0.5b',  # or 'mistral', etc.
    messages=[
        {'role': 'user', 'content': f"Here is the weather database:\n\n{db_content}\n\nSummarize the recent weather trends for\n\n{location}\n\nand make a prediction for the time until the next day. The units are in knots and celsius."}
    ]
)
print(response['message']['content'])
finish = time.time()
print(f"Time taken for qwen2.5:0.5 response: {finish - start:.2f} seconds")

start = time.time()
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
    model='smollm2:135m',  # or 'mistral', etc.
    messages=[
        {'role': 'user', 'content': f"Here is the weather database:\n\n{db_content}\n\nSummarize the recent weather trends for\n\n{location}\n\nand make a prediction for the time until the next day. The units are in knots and celsius."}
    ]
)
print(response['message']['content'])
finish = time.time()
print(f"Time taken for Smollm2:135m response: {finish - start:.2f} seconds")

start = time.time()
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
finish = time.time()
print(f"Time taken for Smollm2:360m response: {finish - start:.2f} seconds")

start = time.time()
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
    model='phi3:mini',  # or 'mistral', etc.
    messages=[
        {'role': 'user', 'content': f"Here is the weather database:\n\n{db_content}\n\nSummarize the recent weather trends for\n\n{location}\n\nand make a prediction for the time until the next day. The units are in knots and celsius."}
    ]
)
print(response['message']['content'])
finish = time.time()
print(f"Time taken for phi3:mini response: {finish - start:.2f} seconds")

start = time.time()
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
    model='tinyllama:latest',  # or 'mistral', etc.
    messages=[
        {'role': 'user', 'content': f"Here is the weather database:\n\n{db_content}\n\nSummarize the recent weather trends for\n\n{location}\n\nand make a prediction for the time until the next day. The units are in knots and celsius."}
    ]
)
print(response['message']['content'])
finish = time.time()
print(f"Time taken for Tinyllama:latest response: {finish - start:.2f} seconds")

start = time.time()
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
    model='gemma3:270m',  # or 'mistral', etc.
    messages=[
        {'role': 'user', 'content': f"Here is the weather database:\n\n{db_content}\n\nSummarize the recent weather trends for\n\n{location}\n\nand make a prediction for the time until the next day. The units are in knots and celsius."}
    ]
)
print(response['message']['content'])
finish = time.time()
print(f"Time taken for Gemma3:270m response: {finish - start:.2f} seconds")

start = time.time()
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
    model='gemma3:1b',  # or 'mistral', etc.
    messages=[
        {'role': 'user', 'content': f"Here is the weather database:\n\n{db_content}\n\nSummarize the recent weather trends for\n\n{location}\n\nand make a prediction for the time until the next day. The units are in knots and celsius."}
    ]
)
print(response['message']['content'])
finish = time.time()
print(f"Time taken for Gemma3:1b response: {finish - start:.2f} seconds")

start = time.time()
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
    model='llama3.2:1b',  # or 'mistral', etc.
    messages=[
        {'role': 'user', 'content': f"Here is the weather database:\n\n{db_content}\n\nSummarize the recent weather trends for\n\n{location}\n\nand make a prediction for the time until the next day. The units are in knots and celsius."}
    ]
)
print(response['message']['content'])
finish = time.time()
print(f"Time taken for llama3.2:1b response: {finish - start:.2f} seconds")