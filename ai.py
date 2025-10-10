import ollama
import mysql.connector
import datetime

# Database connection details
db_host = "localhost"
db_user = "root"
db_password = "spring"
db_database = "weatherdata"

# Ollama model to use
ollama_model = "smollm2:360m"

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

def generate_forecast(data):
    """Generates a weather forecast using the provided data."""
    if not data:
        return "No data available to generate a forecast."

    # Format the data into a string for the prompt
    data_string = "\n".join([
        f"Date: {row[0]}, Time: {row[1]}, Wind Speed: {row[2]} knots, Wind Direction: {row[3]} degrees, Temperature: {row[4]} °C"
        for row in data
    ])

    try:
        response = ollama.chat(
            model=ollama_model,
            messages=[
                {'role': 'user', 'content': f"Here is the recent weather data:\n\n{data_string}\n\nCreate a simple forecast for the morning, noon, afternoon, evening, night and early morning for each of the days. Units in knots and celsius. Today is {datetime.date.today().strftime('%Y-%m-%d')}."}
            ]
        )

        # Attempt to extract the forecast from the response
        if isinstance(response, dict) and 'response' in response:
            forecast = response['response']
        elif isinstance(response, str):
            forecast = response
        else:
            forecast = "Could not extract forecast from response."

        return forecast

    except Exception as e:
        return f"Error generating forecast: {e}"

if __name__ == "__main__":
    weather_data = get_recent_weather_data(days=7)
    if weather_data:
        forecast = generate_forecast(weather_data)
        print(forecast)
    else:
        print("Failed to retrieve weather data.")