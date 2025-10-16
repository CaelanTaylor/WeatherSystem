from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import datetime
from ollama import Client  # use the official Ollama Python client

# --- CONFIGURATION ---
OLLAMA_HOST = "http://ai.local:11434"
OLLAMA_MODEL = "gemma3:1b"

# Create Ollama client for remote connection
ollama_client = Client(host=OLLAMA_HOST)

# Flask setup
app = Flask(__name__)
CORS(app)


# --- HELPER FUNCTIONS ---

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
        # --- Connect to DB ---
        mydb = get_db_connection()
        mycursor = mydb.cursor()

        # --- Aggregate hourly data ---
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
            return jsonify({"error": "No historical data available."}), 404

        # --- Format Data for Ollama ---
        data_string = "\n".join([
            f"Timestamp: {row[0]}, Avg Wind Speed: {row[1]:.2f} knots, Max Wind Gust: {row[2]:.2f} knots, Avg Wind Direction: {row[3]:.2f}°"
            for row in hourly_data
        ])

        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")

        # --- Send to Ollama ---
        try:
            response = ollama_client.chat(
                model=OLLAMA_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Here is all historical weather data aggregated by the hour ({len(hourly_data)} total entries). Each entry contains the average wind speed, "
                            f"maximum wind gust, and average wind direction:\n\n{data_string}\n\n"
                            f"Analyze this hourly averaged data and predict wind conditions for the next two days, including morning, midday, afternoon, and night. "
                            f"Provide wind speed (knots) and direction (degrees). Today is {datetime.date.today()} and time is {current_time}. Only provide the forecast based on data."
                        )
                    }
                ]
            )
            forecast = response["message"]["content"]
        except Exception as e:
            return jsonify({"error": f"Ollama API error: {str(e)}"}), 500

        return jsonify({"forecast": forecast})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- MAIN ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)