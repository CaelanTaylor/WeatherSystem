from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
from mysql.connector import pooling
import datetime
from ollama import Client

# --- CONFIGURATION ---
OLLAMA_HOST = "http://ai.local:11434"
OLLAMA_MODEL = "gemma3:1b"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "spring",
    "database": "weatherdata",
    "charset": "utf8mb4",
}

# --- Connection Pool ---
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="weather_pool",
    pool_size=10,
    **DB_CONFIG
)

# --- Ollama Client ---
ollama_client = Client(host=OLLAMA_HOST)

# --- Flask ---
app = Flask(__name__)
CORS(app)

# --- Helper Functions ---
def get_db_connection():
    return db_pool.get_connection()

def generate_timestamps(interval_seconds, duration_minutes):
    now = datetime.datetime.now()
    return [
        (now - datetime.timedelta(seconds=i * interval_seconds)).strftime('%Y-%m-%d %H:%M:%S')
        for i in range(int(duration_minutes * 60 / interval_seconds))
    ]

# --- ROUTES ---

@app.route('/latest')
def latest():
    try:
        mydb = get_db_connection()
        mycursor = mydb.cursor(dictionary=True)
        mycursor.execute("""
            SELECT date, time, location, windspeed, winddirection, wtemp, atemp
            FROM weatherdata
            ORDER BY date DESC, time DESC
            LIMIT 1
        """)
        row = mycursor.fetchone()
        mydb.close()

        if row:
            return jsonify(row)
        return jsonify({"error": "No data"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trend10m')
def trend10m():
    try:
        mydb = get_db_connection()
        mycursor = mydb.cursor(dictionary=True)
        mycursor.execute("""
            SELECT date, time, AVG(windspeed) AS avg_wind, MAX(windspeed) AS max_gust, AVG(winddirection) AS avg_dir
            FROM weatherdata
            WHERE CONCAT(date, ' ', time) >= DATE_SUB(NOW(), INTERVAL 10 MINUTE)
            GROUP BY date, time
            ORDER BY time ASC
        """)
        rows = mycursor.fetchall()
        mydb.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trend1h')
def trend1h():
    try:
        mydb = get_db_connection()
        mycursor = mydb.cursor(dictionary=True)
        mycursor.execute("""
            SELECT date, time, AVG(windspeed) AS avg_wind, MAX(windspeed) AS max_gust, AVG(winddirection) AS avg_dir
            FROM weatherdata
            WHERE CONCAT(date, ' ', time) >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
            GROUP BY date, time
            ORDER BY time ASC
        """)
        rows = mycursor.fetchall()
        mydb.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trend24h')
def trend24h():
    try:
        mydb = get_db_connection()
        mycursor = mydb.cursor()
        mycursor.execute("""
            SELECT AVG(windspeed), MAX(windspeed), AVG(winddirection)
            FROM weatherdata
            WHERE CONCAT(date, ' ', time) >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """)
        row = mycursor.fetchone()
        mydb.close()
        return jsonify({
            "avg_wind": row[0],
            "max_gust": row[1],
            "avg_dir": row[2]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate_forecast', methods=['POST'])
def generate_forecast():
    try:
        mydb = get_db_connection()
        mycursor = mydb.cursor()
        mycursor.execute("""
            SELECT
                DATE_FORMAT(date, '%Y-%m-%d %H:00:00') AS hourly_timestamp,
                AVG(windspeed) AS avg_windspeed,
                MAX(windspeed) AS max_windgust,
                AVG(winddirection) AS avg_winddirection,
                AVG(wtemp) AS avg_wtemp,
                AVG(atemp) AS avg_atemp
            FROM weatherdata
            GROUP BY hourly_timestamp
            ORDER BY hourly_timestamp ASC
        """)
        hourly_data = mycursor.fetchall()
        mydb.close()

        if not hourly_data:
            return jsonify({"error": "No historical data available"}), 404

        # Convert to formatted string in chunks to prevent Ollama overload
        chunks = []
        chunk_size = 500  # adjust based on dataset size
        for i in range(0, len(hourly_data), chunk_size):
            chunk = hourly_data[i:i+chunk_size]
            chunk_str = "\n".join([
                f"Timestamp: {row[0]}, Avg Wind Speed: {row[1]:.2f}, Max Wind Gust: {row[2]:.2f}, "
                f"Avg Wind Dir: {row[3]:.2f}, Avg Water Temp: {row[4]:.2f}, Avg Air Temp: {row[5]:.2f}"
                for row in chunk
            ])
            chunks.append(chunk_str)

        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")

        # Aggregate all chunks for Ollama input
        data_string = "\n".join(chunks)
        response = ollama_client.chat(
            model=OLLAMA_MODEL,
            messages=[{
                "role": "user",
                "content": (
                    f"Here is all historical hourly weather data ({len(hourly_data)} entries). "
                    f"Analyze and predict the wind conditions for the next 2 days by morning, midday, afternoon, and night. "
                    f"Provide wind speed (knots) and direction (degrees). "
                    f"Current date: {datetime.date.today()}, time: {current_time}. No extra text."
                    f"\n\n{data_string}"
                )
            }]
        )

        forecast = response["message"]["content"]
        return jsonify({"forecast": forecast})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- MAIN ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
