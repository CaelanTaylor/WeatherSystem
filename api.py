from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import datetime
from ollama import Client  # use the official Ollama Python client

# --- CONFIGURATION ---
OLLAMA_HOST = "http://ai.local:11434" 
OLLAMA_MODEL = "qwen3:1.7b"

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
        WHERE date = CURDATE() AND time >= CURTIME() - INTERVAL 10 MINUTE
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
        WHERE date = CURDATE() AND time >= CURTIME() - INTERVAL 1 HOUR
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
        WHERE date = CURDATE()
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


@app.route('/get_recent_weather_data', methods=['GET'])
def get_recent_weather_data():
    try:
        mydb = get_db_connection()
        mycursor = mydb.cursor()
        mycursor.execute("""
            SELECT date, time, windspeed, winddirection, wtemp, atemp
            FROM weatherdata
            ORDER BY date DESC, time DESC
            LIMIT 10
        """)
        rows = mycursor.fetchall()
        mydb.close()

        formatted_data = [
            {
                "date": str(row[0]),
                "time": str(row[1]),
                "windspeed": row[2],
                "winddirection": row[3],
                "wtemp": row[4],
                "atemp": row[5],
            }
            for row in rows
        ]
        return jsonify(formatted_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/generate_forecast', methods=['POST'])
def generate_forecast():
    try:
        data = request.get_json()
        weather_data = data.get("weather_data", [])

        if not weather_data:
            return jsonify({"error": "Missing weather data"}), 400

        # Format weather data as a readable text prompt
        data_string = "\n".join([
            f"Date: {row['date']}, Time: {row['time']}, "
            f"Wind Speed: {row['windspeed']} knots, "
            f"Wind Direction: {row['winddirection']}°, "
            f"Water Temp: {row['wtemp']}°C, Air Temp: {row['atemp']}°C"
            for row in weather_data
        ])

        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")

        # Send request to remote Ollama
        try:
            response = ollama_client.chat(
                model=OLLAMA_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Here is recent weather data:\n\n{data_string}\n\n"
                            f"Predict wind speed and direction for morning, midday, afternoon and night of the next 2 days. "
                            f"Provide the prediction with 'Wind Speed (knots)', "
                            f"and 'Wind Direction (degrees)'. Today is {datetime.date.today()} "
                            f"and time is {current_time}. No fluff — only the forecast based on previous weather data."
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
    app.run(host="0.0.0.0", port=5001)
