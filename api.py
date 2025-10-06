from flask import Flask, jsonify
from flask_cors import CORS
import mysql.connector
import datetime

app = Flask(__name__)
CORS(app)  # <-- Add this line

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
    mycursor.execute("""
        SELECT 
            date, time, AVG(windspeed) AS avg_wind, MAX(windspeed) AS max_gust, AVG(winddirection) AS avg_dir
        FROM weatherdata
        WHERE date = CURDATE() AND time >= CURTIME() - INTERVAL 10 MINUTE
        GROUP BY date, time
        ORDER BY time ASC
    """)
    rows = mycursor.fetchall()
    mydb.close()
    data = []
    for row in rows:
        data.append({
            "time": str(row[1]),  # Format time for display
            "avg_wind": row[2],
            "max_gust": row[3],
            "avg_dir": row[4]
        })  # Debugging statement
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
    mycursor.execute("""
        SELECT 
            date, time, AVG(windspeed) AS avg_wind, MAX(windspeed) AS max_gust, AVG(winddirection) AS avg_dir
        FROM weatherdata
        WHERE date = CURDATE() AND time >= CURTIME() - INTERVAL 1 HOUR
        GROUP BY date, time
        ORDER BY time ASC
    """)
    rows = mycursor.fetchall()
    mydb.close()
    data = []
    for row in rows:
        data.append({
            "time": str(row[1]),  # Format time for display
            "avg_wind": row[2],
            "max_gust": row[3],
            "avg_dir": row[4]
        })  # Debugging statement
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)