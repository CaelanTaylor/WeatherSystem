from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import datetime
import ollama

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
        })
    print("Trend 10m data:", data)  # Debugging statement
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
        })
    print("Trend 1h data:", data)  # Debugging statement
    return jsonify(data)

@app.route('/trend24h')
def trend24h():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="spring",
        database="weatherdata"
    )
    mycursor = mydb.cursor()

    query = f"""
        SELECT 
            AVG(windspeed) AS avg_wind,
            MAX(windspeed) AS max_gust,
            AVG(winddirection) AS avg_dir
        FROM weatherdata
        WHERE date = CURDATE()
    """

    mycursor.execute(query)
    rows = mycursor.fetchall()
    mydb.close()

    data = []
    if rows:
        data.append({
            "avg_wind": rows[0][0],
            "max_gust": rows[0][1],
            "avg_dir": rows[0][2]
        })
    print("Trend 1h data:", data)
    return jsonify(data)

@app.route('/get_recent_weather_data', methods=['GET'])
def get_recent_weather_data():
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="spring",
            database="weatherdata"
        )
        mycursor = mydb.cursor()

        query = """
            SELECT date, time, windspeed, winddirection, wtemp, atemp
            FROM weatherdata
            ORDER BY date DESC, time DESC
            LIMIT 10;  -- Get the 10 most recent records
        """
        mycursor.execute(query)
        data = mycursor.fetchall()
        mycursor.close()
        mydb.close()

        # Format the data into a list of dictionaries
        formatted_data = []
        for row in data:
            formatted_data.append({
                'date': row[0],
                'time': row[1],
                'windspeed': row[2],
                'winddirection': row[3],
                'wtemp': row[4],
                'atemp': row[5]
            })

        return jsonify(formatted_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate_forecast', methods=['POST'])
def generate_forecast():
    try:
        data = request.get_json()
        weather_data = data['weather_data']

        # Format the data into a string for the prompt
        data_string = "\n".join([
            f"Date: {row['date']}, Time: {row['time']}, Wind Speed: {row['windspeed']} knots, Wind Direction: {row['winddirection']} degrees, Temperature: {row['wtemp']} °C"
            for row in weather_data
        ])

        # Generate the forecast using Ollama
        try:
            response = ollama.chat(
                model="gemma3:1b",
                messages=[
                    {'role': 'user', 'content': f"Here is the recent weather data:\n\n{data_string}\n\nPredict the wind speed and direction for each hour of the next 36 hours. Provide the prediction in a table format with columns for 'Hour', 'Wind Speed (knots)', and 'Wind Direction (degrees)'. Today is {datetime.date.today().strftime('%Y-%m-%d')}. Do not ask questions or have any fluff. Just give the forecast."}
                ]
            )
            forecast = response['message']['content']
        except Exception as e:
            return jsonify({'error': f'Error calling Ollama API: {str(e)}'}), 500

        return jsonify(forecast)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)