from flask import Flask, jsonify
from flask_cors import CORS
import mysql.connector

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
        return jsonify({
            "date": str(row[0]),  # Convert datetime to string
            "time": str(row[1]),  # Convert datetime to string
            "location": row[2],
            "windspeed": row[3],
            "winddirection": row[4],
            "wtemp": row[5],
            "atemp": row[6]
        })
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
            FROM_UNIXTIME(FLOOR(UNIX_TIMESTAMP(time)/15)*15) AS interval_time,
            AVG(windspeed) AS avg_wind,
            MAX(windspeed) AS max_gust,
            AVG(winddirection) AS avg_dir
        FROM weatherdata
        WHERE time >= NOW() - INTERVAL 10 MINUTE
        GROUP BY interval_time
        ORDER BY interval_time ASC
    """)
    rows = mycursor.fetchall()
    mydb.close()
    return jsonify([
        {"time": str(row[0]), "avg_wind": row[1], "max_gust": row[2], "avg_dir": row[3]}
        for row in rows
    ])

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
            FROM_UNIXTIME(FLOOR(UNIX_TIMESTAMP(time)/60)*60) AS interval_time,
            AVG(windspeed) AS avg_wind,
            MAX(windspeed) AS max_gust,
            AVG(winddirection) AS avg_dir
        FROM weatherdata
        WHERE time >= NOW() - INTERVAL 1 HOUR
        GROUP BY interval_time
        ORDER BY interval_time ASC
    """)
    rows = mycursor.fetchall()
    mydb.close()
    return jsonify([
        {"time": str(row[0]), "avg_wind": row[1], "max_gust": row[2], "avg_dir": row[3]}
        for row in rows
    ])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)