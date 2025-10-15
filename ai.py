from ollama import Client
import mysql.connector
import datetime
import threading

# ----------------------------
# CONFIGURATION
# ----------------------------

# Remote Ollama server
OLLAMA_HOST = "http://10.0.0.61:11434"  
OLLAMA_MODEL = "gemma3:1b"

# MySQL connection
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "spring"
DB_DATABASE = "weatherdata"

# Create a client that connects to the remote Ollama host
ollama_client = Client(host=OLLAMA_HOST)


# ----------------------------
# FUNCTIONS
# ----------------------------

def get_recent_weather_data(days=7):
    """Fetches recent weather data from the database."""
    try:
        mydb = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE
        )
        mycursor = mydb.cursor()
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=days)

        query = """
            SELECT date, time, windspeed, winddirection, wtemp, atemp
            FROM weatherdata
            WHERE date BETWEEN %s AND %s
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
        f"Date: {row[0]}, Time: {row[1]}, Wind Speed: {row[2]} knots, "
        f"Wind Direction: {row[3]}°, Water Temp: {row[4]}°C, Air Temp: {row[5]}°C"
        for row in data
    ])

    now = datetime.datetime.now()
    current_time = now.strftime('%H:%M:%S')

    try:
        print("Starting forecast generation...")

        # Call remote Ollama server
        response = ollama_client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    'role': 'user',
                    'content': (
                        f"Here is the recent weather data:\n\n{data_string}\n\n"
                        f"Predict the wind speed and direction for each hour of the next 36 hours. "
                        f"Provide the prediction in a table format with columns for "
                        f"'Hour', 'Wind Speed (knots)', and 'Wind Direction (degrees)'. "
                        f"Today is {datetime.date.today()} and time is {current_time}. "
                        f"No commentary, no questions — just the forecast table."
                    )
                }
            ]
        )

        print("Raw response from Ollama:", response)  # For debugging

        # Handle both response formats safely
        if isinstance(response, dict):
            if "message" in response and "content" in response["message"]:
                forecast = response["message"]["content"]
            elif "messages" in response and len(response["messages"]) > 0:
                forecast = response["messages"][-1].get("content", "")
            else:
                forecast = str(response)
        else:
            forecast = str(response)

        print("Forecast generation complete.")
        callback_function(forecast)

    except Exception as e:
        print("Error during forecast generation:", e)
        callback_function(f"Error generating forecast: {e}")


def callback_function(forecast):
    """Callback function to display the forecast."""
    print("\n--- FORECAST OUTPUT ---")
    print(forecast)
    print("-----------------------\n")


def main():
    weather_data = get_recent_weather_data(days=7)
    if weather_data:
        thread = threading.Thread(target=generate_forecast, args=(weather_data, callback_function))
        thread.start()
    else:
        print("Failed to retrieve weather data.")


# ----------------------------
# MAIN ENTRY POINT
# ----------------------------
if __name__ == "__main__":
    main()
