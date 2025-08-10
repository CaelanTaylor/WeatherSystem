import ollama

import python_weather

import asyncio
import os

import requests

API_KEY = 'LEdNkCJljVaPAalZkBJAggysOF0vlEks'
LAT_LON = '-36.8485,174.7633'
FIELDS = ['temperature', 'precipitationIntensity', 'windSpeed']
URL = 'https://api.tomorrow.io/v4/weather/forecast'

params = {
    'location': LAT_LON,
    'fields': ','.join(FIELDS),
    'timesteps': '1h',
    'units': 'metric',
    'apikey': API_KEY
}

response = requests.get(URL, params=params)

if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(f"Error: {response.status_code}")
    print(response.text)


  
response = ollama.chat(
    model='gemma3:1b',  # or 'mistral', etc.
    messages=[
        {'role': 'user', 'content': f"Here is the weather forecast:\n\n{data}\n\nCreate a simple forecast for the morning, noon, afternoon, evening, night and early morning for each of the days. Units in knots and celsius"}
    ]
)

print(response['message']['content'])