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
    mycursor.execute("SELECT date, time, location, windspeed, winddirection, wtemp, atemp FROM weatherdata ORDER BY id DESC LIMIT 1")
    row = mycursor.fetchone()
    mydb.close()
    if row:
        return jsonify({
            "date": row[0],
            "time": row[1],
            "location": row[2],
            "windspeed": row[3],
            "winddirection": row[4],
            "wtemp": row[5],
            "atemp": row[6]
        })
    else:
        return jsonify({"error": "No data"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)