import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

# ===============================
# ⚙️ Konfigurasi Aplikasi
# ===============================
st.set_page_config(page_title="🌦️ Multi-City Weather Dashboard", layout="wide")

st.title("🌦️ Real-Time Weather Dashboard")
st.markdown("""
Menampilkan cuaca saat ini dan prakiraan 5 hari (3 jam sekali)  
menggunakan **OpenWeatherMap Free API** 🌍.
""")

# ===============================
# 🔑 API Key & Endpoint
# ===============================
API_KEY = "52bf74effb7223642f508b09cf04b348"
BASE_URL = "https://api.openweathermap.org/data/2.5"

# ===============================
# 📍 Input Kota dari Sidebar
# ===============================
st.sidebar.header("🏙️ Pengaturan Kota")
city_input = st.sidebar.text_area(
    "Masukkan nama kota (pisahkan dengan koma):",
    value="Jakarta,Bandung,Surabaya"
)
cities = [c.strip() for c in city_input.split(",") if c.strip()]

# ===============================
# 💾 File CSV untuk Riwayat
# ===============================
csv_file = "weather_history.csv"
if not os.path.exists(csv_file):
    pd.DataFrame(columns=["timestamp", "city", "temp", "humidity", "pressure", "description"]).to_csv(csv_file, index=False)

# ===============================
# 🧠 Fungsi Ambil Data Cuaca
# ===============================
def get_weather_data(city):
    """Ambil data cuaca saat ini & prakiraan 5 hari (3 jam interval)."""
    weather_url = f"{BASE_URL}/weather?q={city}&appid={API_KEY}&units=metric&lang=id"
    forecast_url = f"{BASE_URL}/forecast?q={city}&appid={API_KEY}&units=metric&lang=id"

    try:
        w_response = requests.get(weather_url)
        f_response = requests.get(forecast_url)

        # Cek kode HTTP
        if w_response.status_code != 200:
            raise Exception(f"HTTP {w_response.status_code} - {w_response.text}")

        w = w_response.json()
        f = f_response.json()

        current = {
            "city": city.title(),
            "temp": w["main"]["temp"],
            "humidity": w["main"]["humidity"],
            "pressure": w["main"]["pressure"],
            "description": w["weather"][0]["description"].title()
        }

        forecast_df = pd.DataFrame([
            {
                "time": x["dt_txt"],
                "temp": x["main"]["temp"],
                "humidity": x["main"]["humidity"],
                "pressure": x["main"]["pressure"]
            }
            for x in f.get("list", [])
        ])

        # Simpan history ke CSV
        new_row = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            **current
        }
        pd.DataFrame([new_row]).to_csv(csv_file, mode="a", header=False, index=False)

        return current, forecast_df

    except Exception as e:
        st.error(f"❌ {city.title()}: Gagal mengambil data. {e}")
        return None, None

# ===============================
# 🚀 Tampilkan Dashboard
# ===============================
for city in cities:
    current, forecast = get_weather_data(city)
    if current and forecast is not None:
        with st.expander(f"🌍 {current['city']}"):
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🌡️ Suhu (°C)", f"{current['temp']:.1f}")
            col2.metric("💧 Kelembapan (%)", f"{current['humidity']}%")
            col3.metric("🔽 Tekanan (hPa)", f"{current['pressure']}")
            col4.metric("🌤️ Cuaca", current['description'])

            st.write("### 📊 Prakiraan 5 Hari (Setiap 3 Jam)")
            fig, ax = plt.subplots(3, 1, figsize=(10, 6), sharex=True)

            ax[0].plot(forecast["time"], forecast["temp"], marker="o", color="tab:red")
            ax[0].set_ylabel("Suhu (°C)")

            ax[1].plot(forecast["time"], forecast["humidity"], marker="o", color="tab:blue")
            ax[1].set_ylabel("Kelembapan (%)")

            ax[2].plot(forecast["time"], forecast["pressure"], marker="o", color="tab:green")
            ax[2].set_ylabel("Tekanan (hPa)")

            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)

st.success("✅ Data berhasil dimuat dan disimpan ke `weather_history.csv`.")
