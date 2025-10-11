from flask import Flask, jsonify
from flask_cors import CORS
import mysql.connector
import datetime

app = Flask(__name__)
CORS(app)

def generate_timestamps(interval_seconds, duration_minutes):
    """Generates a list of timestamps at the specified interval for the given duration."""
    now = datetime.datetime.now()
    timestamps = []
    for i in range(int(duration_minutes * 60 / interval_seconds)):
        timestamp = now - datetime.timedelta(seconds=i * interval_seconds)
        timestamps.append(timestamp.strftime('%Y-%m-%d %H:%M:%S'))
    return timestamps

@app.route('/latest')
def latest():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="spring",
        database="weatherdata"
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT date, time, location, windspeed, winddirection, wtemp, atemp FROM weatherdata ORDER BY date DESC, time DESC LIMIT 1")
    row = mycursor.fetchone()
    mydb.close()
    if row:
        data = {
            "date": str(row[0]),  # Convert datetime to string
            "time": str(row[1]),  # Convert datetime to string
            "location": row[2],
            "windspeed": row[3],
            "winddirection": row[4],
            "wtemp": row[5],
            "atemp": row[6]
        }
        print("Latest data:", data)  # Debugging statement
        return jsonify(data)
    else:
        return jsonify({"error": "No data"}), 404

# Example for Flask API endpoint
@app.route('/trend10m')
def trend10m():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="spring",
        database="weatherdata"
    )
    mycursor = mydb.cursor()
    timestamps = generate_timestamps(15, 10)
    in_clause = ', '.join(['%s'] * len(timestamps))
    query = f"""
        SELECT date, time, AVG(windspeed) AS avg_wind, MAX(windspeed) AS max_gust, AVG(winddirection) AS avg_dir
        FROM weatherdata
        WHERE date = CURDATE() AND time IN ({in_clause})
        GROUP BY date, time
        ORDER BY time ASC
    """
    mycursor.execute(query, timestamps)
    rows = mycursor.fetchall()
    mydb.close()
    data = []
    for row in rows:
        data.append({
            "time": str(row[1]),
            "avg_wind": row[2],
            "max_gust": row[3],
            "avg_dir": row[4]
        })
    print("Trend 10m data:", data)
    return jsonify(data)

@app.route('/trend1h')
def trend1h():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="spring",
        database="weatherdata"
    )
    mycursor = mydb.cursor()
    timestamps = generate_timestamps(60, 60)
    in_clause = ', '.join(['%s'] * len(timestamps))
    query = f"""
        SELECT date, time, AVG(windspeed) AS avg_wind, MAX(windspeed) AS max_gust, AVG(winddirection) AS avg_dir
        FROM weatherdata
        WHERE date = CURDATE() AND time IN ({in_clause})
        GROUP BY date, time
        ORDER BY time ASC
    """
    mycursor.execute(query, timestamps)
    rows = mycursor.fetchall()
    mydb.close()
    data = []
    for row in rows:
        data.append({
            "time": str(row[1]),
            "avg_wind": row[2],
            "max_gust": row[3],
            "avg_dir": row[4]
        })
    print("Trend 1h data:", data)
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)