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


@app.route('/generate_forecast')
def generate_forecast():
    try:
        mydb = get_db_connection()
        mycursor = mydb.cursor()
        mycursor.execute("""
            SELECT
                -- Creates the hourly grouping key (YYYY-MM-DD HH:00:00)
                DATE_FORMAT(CONCAT(date, ' ', time), '%Y-%m-%d %H:00:00') AS hourly_timestamp,
                -- Calculates the average for each hour
                AVG(windspeed) AS avg_windspeed,
                AVG(winddirection) AS avg_winddirection,
                AVG(wtemp) AS avg_wtemp,
                AVG(atemp) AS avg_atemp
            FROM weatherdata
            GROUP BY hourly_timestamp
            ORDER BY hourly_timestamp ASC
        """)
        
        all_data = mycursor.fetchall()
        mydb.close()

        if not all_data:
            return jsonify({"error": "No historical data available for hourly aggregation."}), 404

        # --- DATA PROCESSING: CSV FORMATTING ---
        # 1. Define the CSV header
        header = "hourly_timestamp,avg_windspeed(knots),avg_winddirection(deg),avg_wtemp(C),avg_atemp(C)"

        # 2. Format the aggregated data rows as CSV rows
        data_rows = [
            f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]}"
            for row in all_data
        ]
        
        # 3. Combine the header and data rows into the final "one data thing"
        data_string = f"{header}\n" + "\n".join(data_rows)
        
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")

        # --- OLLAMA REQUEST: SYSTEM PROMPT INSTRUCTION ---
        try:
            response = ollama_client.chat(
                model=OLLAMA_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert meteorological analyst. You will receive **hourly averaged time-series data** in CSV format. This is a **large historical dataset** used only to identify long-term patterns and seasonal trends. The columns are: 'hourly_timestamp', 'avg_windspeed(knots)', 'avg_winddirection(deg)', 'avg_wtemp(C)', and 'avg_atemp(C)'."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Analyze the {len(all_data)} historical hourly observations and predict the wind conditions for the next two days (Current date is {datetime.date.today()}). "
                            f"The data is:\n\n**{data_string}**\n\n"
                            f"Provide the detailed, structured forecast, including predicted speed (knots) and direction (degrees) for morning, midday, afternoon, and night for each of the next two days. **ONLY** provide the forecast."
                        )
                    }
                ]
            )

            forecast = response["message"]["content"]
        except Exception as e:
            # If the output shows a context window or payload size error, the model is too small.
            return jsonify({"error": f"Ollama API error: {str(e)}"}), 500

        return jsonify({"forecast": forecast})

    except Exception as e:
        # Catches database connection issues
        return jsonify({"error": str(e)}), 500

# --- MAIN ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
