import requests
import json
import time
from math import radians, cos, sin, asin, sqrt

# Ensure your config.txt has your OpenWeather API key
def load_api_key():
    try:
        with open("config.txt", "r") as f: 
            return f.read().strip()
    except: 
        # Fallback key from your provided snippet
        return "0ec8bcafff8b8c0828816fe1d7492b53"

WEATHER_API_KEY = load_api_key()
# The 4 cities you chose for your Sentinel Monitor
CITIES = ["Delhi", "Dehradun", "Bangalore", "Chennai"]

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 6371 * 2 * asin(sqrt(a))

def get_all_data():
    weather_results_for_web = []
    
    # encoding="utf-8" prevents crashes with special characters
    with open("sensor_data.txt", "w", encoding="utf-8") as f:
        f.write("CITY_START\n")
        
        for city in CITIES:
            try:
                # Use units=metric for Celsius
                w_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
                w_res = requests.get(w_url, timeout=5).json()
                
                lat, lon = w_res['coord']['lat'], w_res['coord']['lon']
                
                # --- ACCURACY FIX: Use 'feels_like' for real-world alerts ---
                temp = w_res['main']['feels_like'] 
                wind = w_res['wind']['speed'] * 3.6 # Convert m/s to km/h
                
                # RAIN LOGIC
                rain_data = w_res.get('rain', {})
                rain = rain_data.get('1h', rain_data.get('3h', 0.0))
                
                # CONDITION LOGIC
                weather_desc = w_res['weather'][0]['description'].lower()
                weather_id = w_res['weather'][0]['id']
                
                if weather_id < 300 or "thunder" in weather_desc or "lightning" in weather_desc:
                    alert_status = "SEVERE: THUNDERSTORM"
                elif rain > 0.0 or "rain" in weather_desc:
                    alert_status = "SEVERE: RAIN DETECTED"
                elif "mist" in weather_desc or "haze" in weather_desc:
                    alert_status = "MIST/HAZE"
                else:
                    alert_status = weather_desc.capitalize()

                # Local Quake logic
                eq_url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradiuskm=1000&minmagnitude=2.0"
                eq_res = requests.get(eq_url, timeout=5).json()
                local_mag = 0.0
                if eq_res.get('features'):
                    feat = eq_res['features'][0]
                    if haversine(lon, lat, feat['geometry']['coordinates'][0], feat['geometry']['coordinates'][1]) <= 500:
                        local_mag = feat['properties']['mag']

                # 1. Write to the TXT file for your C-Brain (Member 2)
                f.write(f"{city},{temp:.2f},{alert_status},{wind:.2f},{rain:.2f},{local_mag:.2f}\n")
                
                # 2. Store data for the JSON database (Member 3)
                weather_results_for_web.append({
                    "city": city,
                    "temp": round(temp, 1),
                    "cond": alert_status,
                    "wind": round(wind, 1),
                    "rain": round(rain, 1)
                })
                
                print(f"Captured: {city} | {temp:.1f}C")

            except Exception as e:
                f.write(f"{city},0.0,Error,0.0,0.0,0.0\n")
                print(f"Error fetching {city}: {e}")
        
        f.write("CITY_END\nEQ_START\n")
        
        # Global Quakes logic
        global_quakes = []
        try:
            g_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
            g_data = requests.get(g_url, timeout=5).json()
            for i in range(min(3, len(g_data.get("features", [])))):
                mag = g_data['features'][i]['properties']['mag']
                place = g_data['features'][i]['properties']['place'].replace(',', ' ').encode('ascii', 'ignore').decode()
                f.write(f"{mag:.2f},{place}\n")
                global_quakes.append({"mag": mag, "place": place})
        except: 
            pass
            
        f.write("EQ_END\n")

    # --- 🌉 THE BRIDGE: Save the Backend Database for the Frontend ---
    database = {
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cities": weather_results_for_web,
        "quakes": global_quakes
    }
    
    with open("Frontend1/data.json", "w") as f:
     json.dump(database, f, indent=4)
    print("--- Sentinel Data Engine Complete: TXT and JSON updated ---")

if __name__ == "__main__":
    get_all_data()