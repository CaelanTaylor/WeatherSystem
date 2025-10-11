from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import datetime
from config import load_config, save_config

app = Flask(__name__)
CORS(app)

# Load configuration settings globally on startup
location, db_enabled = load_config()

def generate_timestamps(interval_seconds, duration_minutes):
    """Generates a list of timestamps at the specified interval for the given duration."""
    now = datetime.datetime.now()
    timestamps = []
    # Calculate the number of intervals
    num_intervals = int(duration_minutes * 60 / interval_seconds)
    
    for i in range(num_intervals):
        # Calculate the time for the *start* of the interval
        timestamp = now - datetime.timedelta(seconds=i * interval_seconds)
        # We only take the time part as the original query uses CURDATE()
        timestamps.append(timestamp.strftime('%H:%M:%S'))
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
    # MODIFICATION: Filter by the current location
    query = "SELECT date, time, location, windspeed, winddirection, wtemp, atemp FROM weatherdata WHERE location = %s ORDER BY date DESC, time DESC LIMIT 1"
    mycursor.execute(query, (location,)) # Pass location as a parameter
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
            "atemp": row[6]
        }
        print("Latest data:", data)
        return jsonify(data)
    else:
        return jsonify({"error": f"No data found for location: {location}"}), 404

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
    
    # MODIFICATION: Added location filter
    query = f"""
        SELECT date, time, AVG(windspeed) AS avg_wind, MAX(windspeed) AS max_gust, AVG(winddirection) AS avg_dir
        FROM weatherdata
        WHERE date = CURDATE() AND time IN ({in_clause}) AND location = %s
        GROUP BY date, time
        ORDER BY time ASC
    """
    
    # MODIFICATION: Execute with timestamps first, then location
    params = tuple(timestamps) + (location,)
    mycursor.execute(query, params)
    
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
    
    # MODIFICATION: Added location filter
    query = f"""
        SELECT date, time, AVG(windspeed) AS avg_wind, MAX(windspeed) AS max_gust, AVG(winddirection) AS avg_dir
        FROM weatherdata
        WHERE date = CURDATE() AND time IN ({in_clause}) AND location = %s
        GROUP BY date, time
        ORDER BY time ASC
    """
    
    # MODIFICATION: Execute with timestamps first, then location
    params = tuple(timestamps) + (location,)
    mycursor.execute(query, params)
    
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

@app.route('/save_settings', methods=['POST'])
def save_settings():
    global location, db_enabled # Declare global to modify the module-level variables
    data = request.get_json()
    new_location = data.get('location', 'Test Location')
    new_db_enabled = data.get('dbEnabled', True)
    
    save_config(new_location, new_db_enabled)
    
    # Reload the configuration in the API process for immediate use
    location, db_enabled = load_config()
    
    return jsonify({'message': 'Settings saved successfully'})

@app.route('/get_settings')
def get_settings():
    # Helper endpoint to fetch current settings for the frontend (settings.html)
    current_location, current_db_enabled = load_config()
    return jsonify({
        'location': current_location,
        'dbEnabled': current_db_enabled
    })

if __name__ == '__main__':
    # Adjust host and port as needed based on your setup
    app.run(host='0.0.0.0', port=5001, debug=True)