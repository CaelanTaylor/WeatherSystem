from sx126x import sx126x
import time
import threading
import mysql.connector
import queue
import subprocess
import tempfile

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



def run_llamacpp(model_path, prompt):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as prompt_file:
        prompt_file.write(prompt)
        prompt_file.flush()
        result = subprocess.run(
            [
                "./llama.cpp/main",  # Adjust path to llama.cpp binary as needed
                "-m", model_path,
                "-p", prompt
            ],
            capture_output=True,
            text=True
        )
        return result.stdout

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
prompt = f"Here is the weather database:\n\n{db_content}\n\nSummarize the recent weather trends for\n\n{location}\n\nand make a prediction for the time until the next day. The units are in knots and celsius."
response = run_llamacpp("models/tinyllama-latest.gguf", prompt)
print(response)
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
prompt = f"Here is the weather database:\n\n{db_content}\n\nSummarize the recent weather trends for\n\n{location}\n\nand make a prediction for the time until the next day. The units are in knots and celsius."
response = run_llamacpp("models/gemma3-270m.gguf", prompt)
print(response)
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
prompt = f"Here is the weather database:\n\n{db_content}\n\nSummarize the recent weather trends for\n\n{location}\n\nand make a prediction for the time until the next day. The units are in knots and celsius."
response = run_llamacpp("models/gemma3-1b.gguf", prompt)
print(response)
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
prompt = f"Here is the weather database:\n\n{db_content}\n\nSummarize the recent weather trends for\n\n{location}\n\nand make a prediction for the time until the next day. The units are in knots and celsius."
response = run_llamacpp("models/llama3.2-1b.gguf", prompt)
print(response)
finish = time.time()
print(f"Time taken for llama3.2:1b response: {finish - start:.2f} seconds")