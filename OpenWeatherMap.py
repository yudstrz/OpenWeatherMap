import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

st.set_page_config(page_title="🌦️ Multi-City Weather Dashboard", layout="wide")

st.title("🌦️ Live Weather Dashboard")
st.markdown("""
Aplikasi ini menampilkan cuaca real-time dan prakiraan 3 jam (5 hari)  
menggunakan **OpenWeatherMap Free API Plan**.
""")

# Sidebar - input API Key dan kota
st.sidebar.header("⚙️ Pengaturan")
api_key = st.sidebar.text_input("🔑 Masukkan API Key OpenWeatherMap", type="password")
cities_input = st.sidebar.text_area("🏙️ Daftar Kota (pisahkan dengan koma)", "Jakarta,Bandung,Surabaya")

# Konfigurasi file CSV
csv_file = "weather_history.csv"
if not os.path.exists(csv_file):
    pd.DataFrame(columns=["timestamp", "city", "temp", "humidity", "pressure", "description"]).to_csv(csv_file, index=False)

def get_weather(city, api_key):
    """Ambil cuaca sekarang & prakiraan 5 hari (3 jam interval)"""
    base_url = "https://api.openweathermap.org/data/2.5"
    weather_url = f"{base_url}/weather?q={city}&appid={api_key}&units=metric"
    forecast_url = f"{base_url}/forecast?q={city}&appid={api_key}&units=metric"

    try:
        w = requests.get(weather_url).json()
        f = requests.get(forecast_url).json()

        if w.get("cod") != 200:
            raise Exception(w.get("message", "Error fetching data"))

        current = {
            "city": city,
            "temp": w["main"]["temp"],
            "humidity": w["main"]["humidity"],
            "pressure": w["main"]["pressure"],
            "description": w["weather"][0]["description"].title(),
        }

        forecast_df = pd.DataFrame([{
            "time": x["dt_txt"],
            "temp": x["main"]["temp"],
            "humidity": x["main"]["humidity"],
            "pressure": x["main"]["pressure"]
        } for x in f.get("list", [])])

        # Simpan history ke CSV
        new_row = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            **current
        }
        pd.DataFrame([new_row]).to_csv(csv_file, mode="a", header=False, index=False)

        return current, forecast_df

    except Exception as e:
        st.error(f"❌ {city}: Gagal memuat data - {e}")
        return None, None

if api_key:
    cities = [c.strip() for c in cities_input.split(",") if c.strip()]
    for city in cities:
        current, forecast_df = get_weather(city, api_key)
        if current and forecast_df is not None:
            with st.expander(f"🌍 {city.title()}"):
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("🌡️ Suhu (°C)", f"{current['temp']:.1f}")
                col2.metric("💧 Kelembapan (%)", f"{current['humidity']}%")
                col3.metric("🔽 Tekanan (hPa)", f"{current['pressure']}")
                col4.metric("🌤️ Cuaca", current["description"])

                st.write("### 📊 Prakiraan 5 Hari (3 Jam Interval)")
                fig, ax = plt.subplots(3, 1, figsize=(10, 6), sharex=True)
                ax[0].plot(forecast_df["time"], forecast_df["temp"], marker="o")
                ax[0].set_ylabel("Temp (°C)")
                ax[1].plot(forecast_df["time"], forecast_df["humidity"], marker="o", color="orange")
                ax[1].set_ylabel("Humidity (%)")
                ax[2].plot(forecast_df["time"], forecast_df["pressure"], marker="o", color="green")
                ax[2].set_ylabel("Pressure (hPa)")
                plt.xticks(rotation=45)
                st.pyplot(fig)

    st.success("✅ Data berhasil dimuat. History otomatis tersimpan ke `weather_history.csv`.")
else:
    st.warning("⚠️ Masukkan API Key terlebih dahulu di sidebar untuk memulai.")
