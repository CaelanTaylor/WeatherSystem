import ollama
import mysql.connector
import datetime
import threading

# Database connection details
db_host = "localhost"
db_user = "root"
db_password = "spring"
db_database = "weatherdata"

# Ollama model to use
ollama_model = "gemma3:1b"

def get_recent_weather_data(days=7):
    """Fetches recent weather data from the database."""
    try:
        mydb = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_database
        )
        mycursor = mydb.cursor()

        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=days)

        query = f"""
            SELECT date, time, windspeed, winddirection, wtemp, atemp
            FROM weatherdata
            WHERE date >= %s AND date <= %s
            ORDER BY date, time
        """
        mycursor.execute(query, (start_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')))
        data = mycursor.fetchall()
        mycursor.close()
        mydb.close()
        return data
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def generate_forecast(data, callback_function):
    """Generates a weather forecast using the provided data."""
    if not data:
        callback_function("No data available to generate a forecast.")
        return

    # Format the data into a string for the prompt
    data_string = "\n".join([
        f"Date: {row[0]}, Time: {row[1]}, Wind Speed: {row[2]} knots, Wind Direction: {row[3]} degrees, Temperature: {row[4]} °C"
        for row in data
    ])

    try:
        response = ollama.chat(
            model=ollama_model,
            messages=[
                {'role': 'user', 'content': f"Here is the recent weather data:\n\n{data_string}\n\nPredict the wind speed and direction for each hour of the next 36 hours. Provide the prediction in a table format with columns for 'Hour', 'Wind Speed (knots)', and 'Wind Direction (degrees)'. Today is {datetime.date.today().strftime('%Y-%m-%d')}. Do not ask questions or have any fluff. Just give the forecast."}
            ]
        )

        print("Raw response from Ollama:", response)  # Print the raw response

        if isinstance(response, dict) and 'message' in response and 'content' in response['message']:
            forecast = response['message']['content']
        else:
            forecast = "Could not extract forecast from response."

        callback_function(forecast)

    except Exception as e:
        callback_function(f"Error generating forecast: {e}")

def callback_function(forecast):
    """Callback function to display the forecast."""
    print(f"Forecast: {forecast}")

def main():
    weather_data = get_recent_weather_data(days=7)
    if weather_data:
        # Start the forecast generation in a separate thread
        thread = threading.Thread(target=generate_forecast, args=(weather_data, callback_function))
        thread.start()
    else:
        print("Failed to retrieve weather data.")

if __name__ == "__main__":
    main()