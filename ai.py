import ollama
import mysql.connector
import datetime
from config import load_config # 👈 New import

# Database connection details
db_host = "localhost"
db_user = "root"
db_password = "spring"
db_database = "weatherdata"

# Ollama model to use
ollama_model = "gemma3:1b"

# Load the current configuration settings
current_location, db_enabled = load_config() # 👈 Load location

def get_recent_weather_data(days=7):
    """Fetches recent weather data from the database for the current location."""
    if not db_enabled:
        print("Database is disabled in config. Skipping data fetch.")
        return None
        
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
            WHERE date >= %s AND date <= %s AND location = %s # 👈 FILTER BY LOCATION
            ORDER BY date, time
        """
        # Pass start_date, today's date, and the current_location to the execute method
        mycursor.execute(query, (start_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'), current_location)) 
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
        return f"No data available for location '{current_location}' to generate a forecast."

    # Format the data into a string for the prompt
    data_string = "\n".join([
        f"Date: {row[0]}, Time: {row[1]}, Wind Speed: {row[2]} knots, Wind Direction: {row[3]} degrees, Temperature: {row[4]} °C"
        for row in data
    ])

    try:
        response = ollama.chat(
            model=ollama_model,
            messages=[
                {'role': 'user', 'content': f"""
                Here is the recent weather data for location '{current_location}':

                {data_string}

                Create a simple wind prediction for the rest of the day just using the provided data. 
                Ignore temperature and do not make any temperature predictions. 
                Units in knots and celsius. Today is {datetime.date.today().strftime('%Y-%m-%d')}. 
                Do not ask questions or have any fluff. Just give the forecast.
                """}
            ]
        )

        print("Raw response from Ollama:", response)

        if isinstance(response, dict) and 'message' in response and 'content' in response['message']:
            forecast = response['message']['content']
        else:
            forecast = "Could not extract forecast from response."

        return forecast

    except Exception as e:
        return f"Error generating forecast: {e}"

if __name__ == "__main__":
    weather_data = get_recent_weather_data(days=7)
    if weather_data:
        forecast = generate_forecast(weather_data)
        print(f"--- AI Forecast for {current_location} ---")
        print(forecast)
    else:
        print(f"Failed to retrieve weather data for location {current_location}.")