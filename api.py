from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import datetime
from ollama import Client
import json  # Added for config management
import os    # Added for file path checks
import traceback

# --- CONFIGURATION ---
OLLAMA_HOST = "http://ai.local:11434"
OLLAMA_MODEL = "gemma3:4b"
CONFIG_FILE = "config.json" # New config file

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
        (now - datetime.timedelta(seconds=i * interval_seconds)).strftime('%Y-%m-%d %H:%M:%S')
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


# --- ROUTES ---

@app.route('/settings', methods=['GET', 'POST'])
def settings_route():
    """Handles loading and saving application settings."""
    if request.method == 'GET':
        # Load and return current settings
        return jsonify(load_settings())
    
    elif request.method == 'POST':
        # Save new settings
        data = request.json
        
        # Validate input
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


@app.route('/latest')
def latest():
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    mycursor.execute("""
        SELECT date, time, location, windspeed, winddirection, wtemp, atemp
        FROM weatherdata
        ORDER BY date DESC, time DESC
        LIMIT 1
    """)
    row = mycursor.fetchone()
    mydb.close()

    if row:
        data = {
            "date": str(row[0]),
            "time": str(row[1]),
            "location": row[2],
            "windspeed": row[3],
            "winddirection": row[4],
            "wtemp": row[5],
            "atemp": row[6],
        }
        print("Latest data:", data)
        return jsonify(data)
    return jsonify({"error": "No data"}), 404


@app.route('/trend10m')
def trend10m():
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    mycursor.execute("""
        SELECT date, time, AVG(windspeed) AS avg_wind, MAX(windspeed) AS max_gust, AVG(winddirection) AS avg_dir
        FROM weatherdata
        WHERE CONCAT(date, ' ', time) >= DATE_SUB(NOW(), INTERVAL 10 MINUTE)
        GROUP BY date, time
        ORDER BY time ASC
    """)
    rows = mycursor.fetchall()
    mydb.close()

    data = [
        {"time": str(row[1]), "avg_wind": row[2], "max_gust": row[3], "avg_dir": row[4]}
        for row in rows
    ]
    print("Trend 10m data:", data)
    return jsonify(data)


@app.route('/trend1h')
def trend1h():
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    mycursor.execute("""
        SELECT date, time, AVG(windspeed) AS avg_wind, MAX(windspeed) AS max_gust, AVG(winddirection) AS avg_dir
        FROM weatherdata
        WHERE CONCAT(date, ' ', time) >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        GROUP BY date, time
        ORDER BY time ASC
    """)
    rows = mycursor.fetchall()
    mydb.close()

    data = [
        {"time": str(row[1]), "avg_wind": row[2], "max_gust": row[3], "avg_dir": row[4]}
        for row in rows
    ]
    print("Trend 1h data:", data)
    return jsonify(data)


@app.route('/trend24h')
def trend24h():
    mydb = get_db_connection()
    mycursor = mydb.cursor()
    mycursor.execute("""
        SELECT AVG(windspeed), MAX(windspeed), AVG(winddirection)
        FROM weatherdata
        WHERE CONCAT(date, ' ', time) >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    """)
    row = mycursor.fetchone()
    mydb.close()

    data = []
    if row:
        data.append({
            "avg_wind": row[0],
            "max_gust": row[1],
            "avg_dir": row[2]
        })
    print("Trend 24h data:", data)
    return jsonify(data)


@app.route('/generate_forecast', methods=['POST'])
def generate_forecast():
    try:
        mydb = get_db_connection()
        mycursor = mydb.cursor()
        mycursor.execute("""
            SELECT
                DATE_FORMAT(TIMESTAMP(date, time), '%Y-%m-%d %H:00:00') AS hourly_timestamp,
                AVG(windspeed) AS avg_windspeed,
                MAX(windspeed) AS max_windgust,
                AVG(winddirection) AS avg_winddirection
            FROM weatherdata
            GROUP BY hourly_timestamp
            ORDER BY hourly_timestamp ASC
        """)
        hourly_data = mycursor.fetchall()
        mydb.close()

        if not hourly_data:
            return jsonify({"forecast": "No historical data available."})

        # --- Safe formatting ---
        data_string = ""
        for row in hourly_data:
            ts = row[0] or "unknown"
            try:
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
                "content": f"Hourly wind data:\n{data_string}\nYou are an expert meteorologist. Predict weather for next 2 days from now including today for every 3 hours. Provide speed in knots and direction in degrees. Analyse recent situation too. Don't have any fluff. Talk as if you are just a forecast on a website. Don't ask questions. The date is {datetime.datetime.now().strftime('%Y-%m-%d')}. The time is {datetime.datetime.now().strftime('%H:%M')}. Don't add notes."
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
        
    app.run(host="0.0.0.0", port=5001, debug=True)