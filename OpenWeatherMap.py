import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time
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
    """Ambil data cuaca saat ini & prakiraan 5 hari (3 jam interval)"""
    try:
        # pastikan key bersih
        api_key = API_KEY.strip()
        base = "https://api.openweathermap.org/data/2.5"

        # 1️⃣ Fetch current weather
        w_url = f"{base}/weather?q={city}&appid={api_key}&units=metric&lang=id"
        w_resp = requests.get(w_url, timeout=10)

        if w_resp.status_code == 401:
            raise Exception("API key invalid atau belum aktif (HTTP 401).")
        if w_resp.status_code != 200:
            raise Exception(f"HTTP {w_resp.status_code}: {w_resp.text}")

        w = w_resp.json()
        current = {
            "city": city.title(),
            "temp": w["main"]["temp"],
            "humidity": w["main"]["humidity"],
            "pressure": w["main"]["pressure"],
            "description": w["weather"][0]["description"].title()
        }

        # 2️⃣ Fetch forecast
        f_url = f"{base}/forecast?q={city}&appid={api_key}&units=metric&lang=id"
        f_resp = requests.get(f_url, timeout=10)

        if f_resp.status_code != 200:
            st.warning(f"⚠️ Prakiraan {city.title()} gagal dimuat: {f_resp.text}")
            forecast_df = pd.DataFrame()
        else:
            f = f_resp.json()
            forecast_df = pd.DataFrame([
                {
                    "time": x["dt_txt"],
                    "temp": x["main"]["temp"],
                    "humidity": x["main"]["humidity"],
                    "pressure": x["main"]["pressure"]
                } for x in f.get("list", [])
            ])

        # 3️⃣ Simpan log
        new_row = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), **current}
        pd.DataFrame([new_row]).to_csv(csv_file, mode="a", header=False, index=False)

        time.sleep(1)  # jeda aman antar request
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
