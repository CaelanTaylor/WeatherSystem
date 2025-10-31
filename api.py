from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import datetime
from ollama import Client
import json
import os
import traceback

# --- CONFIGURATION ---
OLLAMA_HOST = "http://ai.local:11434"
OLLAMA_MODEL = "gemma3:4b"
CONFIG_FILE = "config.json" 

# Create Ollama client for remote connection
ollama_client = Client(host=OLLAMA_HOST)

# Flask setup
app = Flask(__name__)
CORS(app)


# --- CONFIG HELPER FUNCTIONS ---

def get_default_settings():
    return {
        "location": "Test Location",
        "enable_storage": True
    }

def load_settings():
    """Loads settings from config.json, or returns defaults on failure."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            print(f"Error reading or decoding {CONFIG_FILE}. Using default settings.")
            return get_default_settings()
    else:
        # If file doesn't exist, return defaults
        return get_default_settings()

def save_settings(settings):
    """Saves settings to config.json."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
        return True
    except IOError as e:
        print(f"Error writing to {CONFIG_FILE}: {e}")
        return False


# --- DB & GENERAL HELPER FUNCTIONS ---

def generate_timestamps(interval_seconds, duration_minutes):
    now = datetime.datetime.now()
    timestamps = [
        (now - datetime.timedelta(seconds=i * interval_seconds)).strftime('%d-%m-%Y %H:%M:%S')
        for i in range(int(duration_minutes * 60 / interval_seconds))
    ]
    return timestamps


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="spring",
        database="weatherdata"
    )


#settings route

@app.route('/settings', methods=['GET', 'POST'])
def settings_route():
    """Handles loading and saving application settings via config.json."""
    if request.method == 'GET':
        return jsonify(load_settings())
    
    elif request.method == 'POST':
        data = request.json
        
        if not isinstance(data, dict) or 'location' not in data or not isinstance(data.get('enable_storage'), bool):
            return jsonify({"error": "Invalid request payload. Must include 'location' (string) and 'enable_storage' (boolean)."}), 400
        
        settings_to_save = {
            "location": str(data['location']).strip(),
            "enable_storage": data['enable_storage']
        }

        if save_settings(settings_to_save):
            return jsonify({"message": "Settings saved"}), 200
        else:
            return jsonify({"error": "Could not save settings due to file system error"}), 500

#dashboard route

@app.route('/latest')
def latest():
    settings = load_settings()
    current_location = settings['location']

    mydb = get_db_connection()
    mycursor = mydb.cursor()
    query = """
        SELECT date, time, location, windspeed, winddirection
        FROM weatherdata
        WHERE location = %s
        ORDER BY date DESC, time DESC
        LIMIT 1
    """
    mycursor.execute(query, (current_location,))
    row = mycursor.fetchone()
    mydb.close()

    if row:
        data = {
            "date": str(row[0]),
            "time": str(row[1]),
            "location": row[2],
            "windspeed": float(row[3]),
            "winddirection": float(row[4]),
        }
        print(f"Latest data for {current_location}:", data)
        return jsonify(data)
    return jsonify({"error": f"No data found for location: {current_location}"}), 404

#10m trend route

@app.route('/trend10m')
def trend10m():
    settings = load_settings()
    current_location = settings['location']
    
    # Define the interval in seconds
    INTERVAL_SECONDS = 15

    mydb = get_db_connection()
    mycursor = mydb.cursor()

    query = f"""
        SELECT 
            FROM_UNIXTIME(FLOOR(UNIX_TIMESTAMP(CONCAT(date, ' ', time)) / {INTERVAL_SECONDS}) * {INTERVAL_SECONDS}) AS interval_start,
            CONVERT(CAST(AVG(windspeed) AS DECIMAL(10, 5)), CHAR(50)) AS avg_wind, 
            CONVERT(CAST(MAX(windspeed) AS DECIMAL(10, 5)), CHAR(50)) AS max_gust, 
            CONVERT(CAST(AVG(winddirection) AS DECIMAL(10, 5)), CHAR(50)) AS avg_dir
        FROM weatherdata
        WHERE CONCAT(date, ' ', time) >= DATE_SUB(NOW(), INTERVAL 10 MINUTE)
        AND location = %s
        GROUP BY interval_start
        ORDER BY interval_start ASC
    """
    mycursor.execute(query, (current_location,))
    rows = mycursor.fetchall()
    mydb.close()

    data = [
        {"time": str(row[0]).split(' ')[1], "avg_wind": float(row[1]), "max_gust": float(row[2]), "avg_dir": float(row[3])}
        for row in rows
    ]
    print(f"Trend 10m data (15-sec intervals) for {current_location}:", data)
    return jsonify(data)

#1h trend route

@app.route('/trend1h')
def trend1h():
    settings = load_settings()
    current_location = settings['location']
    
    # Define the interval in seconds
    INTERVAL_SECONDS = 60
    
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    query = f"""
        SELECT 
            FROM_UNIXTIME(FLOOR(UNIX_TIMESTAMP(CONCAT(date, ' ', time)) / {INTERVAL_SECONDS}) * {INTERVAL_SECONDS}) AS interval_start,
            CONVERT(CAST(AVG(windspeed) AS DECIMAL(10, 5)), CHAR(50)) AS avg_wind, 
            CONVERT(CAST(MAX(windspeed) AS DECIMAL(10, 5)), CHAR(50)) AS max_gust, 
            CONVERT(CAST(AVG(winddirection) AS DECIMAL(10, 5)), CHAR(50)) AS avg_dir
        FROM weatherdata
        WHERE CONCAT(date, ' ', time) >= DATE_SUB(NOW(), INTERVAL 60 MINUTE)
        AND location = %s
        GROUP BY interval_start
        ORDER BY interval_start ASC
    """
    mycursor.execute(query, (current_location,))
    rows = mycursor.fetchall()
    mydb.close()

    data = [
        {"time": str(row[0]).split(' ')[1], "avg_wind": float(row[1]), "max_gust": float(row[2]), "avg_dir": float(row[3])}
        for row in rows
    ]
    print(f"Trend 1h data (1-min intervals) for {current_location}:", data)
    return jsonify(data)

#24h trend route

@app.route('/trend24h')
def trend24h():
    settings = load_settings()
    current_location = settings['location']
    
    # Define the interval in seconds
    INTERVAL_SECONDS = 900
    
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    
    query = f"""
        SELECT 
            FROM_UNIXTIME(FLOOR(UNIX_TIMESTAMP(CONCAT(date, ' ', time)) / {INTERVAL_SECONDS}) * {INTERVAL_SECONDS}) AS interval_start,
            CONVERT(CAST(AVG(windspeed) AS DECIMAL(10, 5)), CHAR(50)) AS avg_wind, 
            CONVERT(CAST(MAX(windspeed) AS DECIMAL(10, 5)), CHAR(50)) AS max_gust, 
            CONVERT(CAST(AVG(winddirection) AS DECIMAL(10, 5)), CHAR(50)) AS avg_dir
        FROM weatherdata
        WHERE CONCAT(date, ' ', time) >= DATE_SUB(NOW(), INTERVAL 1440 MINUTE)
        AND location = %s
        GROUP BY interval_start
        ORDER BY interval_start ASC
    """
    mycursor.execute(query, (current_location,))
    rows = mycursor.fetchall()
    mydb.close()

    data = [
        {"time": str(row[0]).split(' ')[1], "avg_wind": float(row[1]), "max_gust": float(row[2]), "avg_dir": float(row[3])}
        for row in rows
    ]
    print(f"Trend 24h for {current_location}:", data)
    return jsonify(data)

#AI forecast route

@app.route('/generate_forecast', methods=['POST'])
def generate_forecast():
    try:
        settings = load_settings()
        current_location = settings['location']
        
        mydb = get_db_connection()
        mycursor = mydb.cursor()
        query = """
            SELECT
                DATE_FORMAT(TIMESTAMP(date, time), '%Y-%m-%d %H:00:00') AS hourly_timestamp,
                AVG(windspeed) AS avg_windspeed,
                MAX(windspeed) AS max_windgust,
                AVG(winddirection) AS avg_winddirection
            FROM weatherdata
            WHERE location = %s
            GROUP BY hourly_timestamp
            ORDER BY hourly_timestamp ASC
        """
        mycursor.execute(query, (current_location,))
        hourly_data = mycursor.fetchall()
        mydb.close()

        if not hourly_data:
            return jsonify({"forecast": f"No historical data available for location: {current_location}."})
        data_string = ""
        for row in hourly_data:
            ts = row[0] or "unknown"
            try:
                # Ensuring these are always floats for the LLM prompt
                avg_w = float(row[1]) if row[1] is not None else 0.0
                max_g = float(row[2]) if row[2] is not None else 0.0
                avg_d = float(row[3]) if row[3] is not None else 0.0
            except ValueError:
                avg_w, max_g, avg_d = 0.0, 0.0, 0.0
            data_string += f"Timestamp: {ts}, Avg Wind: {avg_w:.2f}, Max Gust: {max_g:.2f}, Avg Dir: {avg_d:.2f}\n"

        # --- Ollama call ---
        response = ollama_client.chat(
            model=OLLAMA_MODEL,
            messages=[{
                "role": "user",
                "content": f"Hourly wind data for {current_location}:\n{data_string}\nYou are an expert meteorologist. Predict weather for next 2 days from now including today for every 3 hours. Provide speed in knots and direction in degrees. Analyse recent situation too. Don't have any fluff. Talk as if you are just a forecast on a website. Don't ask questions. The date is {datetime.datetime.now().strftime('%Y-%m-%d')}. The time is {datetime.datetime.now().strftime('%H:%M')}."
            }]
        )
        forecast_text = response["message"]["content"]

        return jsonify({"forecast": forecast_text})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# --- MAIN ---
if __name__ == "__main__":
    # Ensure a default config file exists on startup if it doesn't
    if not os.path.exists(CONFIG_FILE):
        save_settings(get_default_settings())
        
    app.run(host="0.0.0.0", port=5001)