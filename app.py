import requests
import math
import streamlit as st
from datetime import date

TOURNAMENT_STATUS = {
    "Roland Garros":   {"start": date(2026, 5, 25), "end": date(2026, 6, 8)},
    "Australian Open": {"start": date(2026, 1, 13), "end": date(2026, 1, 26)},
    "Wimbledon":       {"start": date(2026, 6, 29), "end": date(2026, 7, 12)},
    "US Open":         {"start": date(2026, 8, 24), "end": date(2026, 9, 6)},
}

def get_tournament_state(name):
    today = date.today()
    t = TOURNAMENT_STATUS[name]
    if t["start"] <= today <= t["end"]:
        return "active"
    elif today > t["end"]:
        return "completed"
    else:
        return "upcoming"

VENUES = {
    "Roland Garros": {"lat": 48.8464, "lon": 2.2492, "surface": "clay"},
    "Australian Open": {"lat": -37.8230, "lon": 144.9795, "surface": "hard"},
    "Wimbledon": {"lat": 51.4334, "lon": -0.2144, "surface": "grass"},
    "US Open": {"lat": 40.6975, "lon": -73.8517, "surface": "hard"},
}

def fetch_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["temperature_2m", "relative_humidity_2m", "windspeed_10m", "direct_radiation"],
        "timezone": "auto"
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data["current"]

def calculate_wet_bulb(temp, humidity):
    wb = (temp * (0.151977 * (humidity + 8.313659) ** 0.5)
          + 0.00391838 * humidity ** 1.5
          * (0.023101 * humidity - 4.686035)
          - 0.548535
          + math.atan(temp + humidity - 1.504080)
          + math.atan(humidity - 10.023420)
          - math.atan(0.636980))
    return round(wb, 1)

def calculate_globe_temp(air_temp, solar_radiation, wind_speed_kmh):
    solar_radiation = max(0, solar_radiation)
    wind_speed_ms = wind_speed_kmh * 0.2778
    if wind_speed_ms < 0.1:
        wind_speed_ms = 0.1
    tg = air_temp + (0.0256 * solar_radiation) - (3.5 * wind_speed_ms) + 3.0
    return round(tg, 1)

def calculate_wbgt(air_temp, humidity, solar_radiation, wind_speed_kmh):
    tnwb = calculate_wet_bulb(air_temp, humidity)
    tg = calculate_globe_temp(air_temp, solar_radiation, wind_speed_kmh)
    wbgt = round(0.7 * tnwb + 0.2 * tg + 0.1 * air_temp, 1)
    return wbgt

ALBEDO = {
    "clay": 0.27,
    "hard": 0.12,
    "grass": 0.22,
}

def calculate_surface_temp(air_temp, solar_radiation, surface):
    albedo = ALBEDO[surface]
    absorbed = solar_radiation * (1 - albedo)
    uplift = absorbed / 80
    return round(air_temp + uplift, 1)

def get_all_venues():
    results = {}
    for name, info in VENUES.items():
        weather = fetch_weather(info["lat"], info["lon"])
        wbgt = calculate_wbgt(
            weather["temperature_2m"],
            weather["relative_humidity_2m"],
            weather["direct_radiation"],
            weather["windspeed_10m"]
        )
        surface_temp = calculate_surface_temp(
            weather["temperature_2m"],
            weather["direct_radiation"],
            info["surface"]
        )
        results[name] = {
            "surface": info["surface"],
            "air_temp": weather["temperature_2m"],
            "humidity": weather["relative_humidity_2m"],
            "wind_speed": weather["windspeed_10m"],
            "solar_radiation": weather["direct_radiation"],
            "wet_bulb": wbgt,
            "surface_temp": surface_temp,
        }
    return results

def fetch_historical(lat, lon, start_date, end_date):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ["temperature_2m", "relative_humidity_2m", 
                   "windspeed_10m", "direct_radiation"],
        "timezone": "auto"
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data["hourly"]

TOURNAMENT_WINDOWS = {
    "Roland Garros":   {"start": "05-22", "end": "06-11"},
    "Australian Open": {"start": "01-14", "end": "02-02"},
    "Wimbledon":       {"start": "06-24", "end": "07-14"},
    "US Open":         {"start": "08-26", "end": "09-08"},
}

INCIDENTS = {
    "Roland Garros": {
        2022: "Paula Badosa retires R3 vs Kudermetova — extreme heat exhaustion",
        2026: "Jakub Menšík collapses in wheelchair after 4.5hrs in 32°C on unshaded outer court"
    },
    "Australian Open": {
        2020: "Dalila Jakupović collapses qualifying R1 — severe coughing fit in heat and bushfire smoke",
        2024: "Terence Atmane retires R1 vs Medvedev — full-body cramping, broken down in tears, serving underhand"
    },
    "Wimbledon": {
        2021: "Emma Raducanu retires R16 vs Tomljanović — hyperventilation and breathing difficulties in stagnant humid heat under roof"
    },
    "US Open": {
        2023: "Medvedev vs Rublev QF — looks into camera: 'One player is gonna die and they're gonna see.' Heat index over 38°C",
        2024: "Yoshihito Nishioka collapses R1 — full-body cramps, unable to stand, medical evacuation from court in fifth set"
    }
}

@st.cache_data(ttl=3600)
def get_historical_trends():
    results = {}
    years = list(range(2020, 2026))

    for name, info in VENUES.items():
        window = TOURNAMENT_WINDOWS[name]
        yearly_data = []

        for year in years:
            start = f"{year}-{window['start']}"
            end = f"{year}-{window['end']}"
            try:
                hourly = fetch_historical(info["lat"], info["lon"], start, end)
                temps = hourly["temperature_2m"]
                humidities = hourly["relative_humidity_2m"]
                winds = hourly["windspeed_10m"]
                radiations = hourly["direct_radiation"]
                wbgts = [
                    calculate_wbgt(t, h, r / 12, w)
                    for t, h, r, w in zip(temps, humidities, radiations, winds)
                ]
                peak_wbgt = round(max(wbgts), 1)
                yearly_data.append({"year": year, "peak_wet_bulb": peak_wbgt})
            except Exception as e:
                print(f"{name} {year}: {e}")
                yearly_data.append({"year": year, "peak_wet_bulb": None})

        results[name] = {
            "data": yearly_data,
            "incidents": INCIDENTS.get(name, {})
        }

    return results

if __name__ == "__main__":
    data = get_all_venues()
    for venue, values in data.items():
        print(f"\n{venue}")
        for k, v in values.items():
            print(f"  {k}: {v}")