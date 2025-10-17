# app.py
# 🌦️ OpenWeatherMap Dashboard (Streamlit)
# Features: multi-city support, One Call API, auto CSV logging, interactive charts.

import os
import time
from datetime import datetime
import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# ========== CONFIG ==========
st.set_page_config(
    page_title="🌦️ OpenWeatherMap Live Dashboard",
    layout="wide",
    page_icon="🌍"
)

DATA_FILE = "weather_history.csv"
CACHE_TTL = 600  # 10 minutes

# ========== SIDEBAR ==========
st.sidebar.title("⚙️ Konfigurasi Dashboard")

api_key = st.sidebar.text_input("🔑 OpenWeatherMap API Key", type="password")
cities_input = st.sidebar.text_area(
    "🌍 Daftar Kota (pisahkan dengan koma)",
    "Jakarta, Bandung, Surabaya"
)
units = st.sidebar.selectbox("🌡️ Unit suhu", ("metric", "imperial"), index=0)
lang = st.sidebar.selectbox("🗣️ Bahasa", ("id", "en"))
refresh_minutes = st.sidebar.slider("⏱️ Update tiap (menit)", 1, 30, 10)

st.sidebar.markdown("---")
st.sidebar.caption("💡 Gunakan OpenWeatherMap One Call API untuk data lengkap cuaca & kondisi lingkungan.")

# ========== HELPER FUNCTIONS ==========
@st.cache_data(ttl=CACHE_TTL)
def fetch_weather_onecall(city_name, api_key, units="metric", lang="id"):
    """Ambil data cuaca menggunakan One Call API 3.0"""
    # Step 1: Get coordinates first
    geo_url = "https://api.openweathermap.org/geo/1.0/direct"
    params_geo = {"q": city_name, "limit": 1, "appid": api_key}
    geo = requests.get(geo_url, params=params_geo, timeout=10).json()
    if not geo:
        return {"error": f"Kota '{city_name}' tidak ditemukan."}
    lat, lon = geo[0]["lat"], geo[0]["lon"]

    # Step 2: Fetch weather data
    url = "https://api.openweathermap.org/data/3.0/onecall"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": units,
        "lang": lang,
        "exclude": "minutely,hourly,alerts"
    }
    resp = requests.get(url, params=params, timeout=10)
    if resp.status_code != 200:
        return {"error": f"HTTP {resp.status_code}: {resp.text}"}
    data = resp.json()
    return {"city": city_name, "lat": lat, "lon": lon, "data": data}


def extract_metrics(city_data):
    """Ambil metrik utama dari hasil One Call API."""
    if "error" in city_data:
        return None
    current = city_data["data"]["current"]
    return {
        "city": city_data["city"],
        "timestamp": datetime.utcfromtimestamp(current["dt"]).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "temp": current.get("temp"),
        "humidity": current.get("humidity"),
        "pressure": current.get("pressure"),
        "weather": current["weather"][0]["description"],
        "icon": current["weather"][0]["icon"],
        "lat": city_data["lat"],
        "lon": city_data["lon"]
    }


def append_to_csv(data_dict, file_path=DATA_FILE):
    """Simpan data ke CSV untuk logging history"""
    df = pd.DataFrame([data_dict])
    if os.path.exists(file_path):
        df.to_csv(file_path, mode="a", header=False, index=False)
    else:
        df.to_csv(file_path, index=False)


def load_history(file_path=DATA_FILE):
    """Muat history dari CSV"""
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=["city", "timestamp", "temp", "humidity", "pressure"])
    return pd.read_csv(file_path)


# ========== FETCH WEATHER ==========
cities = [c.strip() for c in cities_input.split(",") if c.strip()]
st.title("🌦️ Live Weather Dashboard — Multi City (OpenWeatherMap One Call)")
st.caption(f"⏱️ Data diperbarui setiap {refresh_minutes} menit | Caching otomatis aktif")

if not api_key:
    st.warning("Masukkan API Key OpenWeatherMap di sidebar untuk memulai.")
    st.stop()

progress = st.progress(0)
results = []
for i, city in enumerate(cities):
    progress.progress((i + 1) / len(cities))
    data = fetch_weather_onecall(city, api_key, units, lang)
    metrics = extract_metrics(data)
    if metrics:
        results.append(metrics)
        append_to_csv(metrics)
    else:
        st.error(data.get("error", "Gagal memproses data"))

progress.empty()

# ========== DISPLAY SUMMARY ==========
if results:
    df_current = pd.DataFrame(results)
    st.subheader("📋 Kondisi Cuaca Terkini")
    st.dataframe(df_current[["city", "temp", "humidity", "pressure", "weather"]], use_container_width=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rata-rata Suhu", f"{df_current['temp'].mean():.1f}°")
    with col2:
        st.metric("Rata-rata Kelembapan", f"{df_current['humidity'].mean():.1f}%")
    with col3:
        st.metric("Rata-rata Tekanan", f"{df_current['pressure'].mean():.1f} hPa")

    # ========== LOAD HISTORY ==========
    df_hist = load_history()
    if not df_hist.empty:
        df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"])
        latest_cities = df_hist["city"].unique()

        # ========== PLOT SUHU ==========
        st.subheader("🌡️ Grafik Suhu dari Waktu ke Waktu")
        fig_temp = go.Figure()
        for city in latest_cities:
            df_city = df_hist[df_hist["city"] == city]
            fig_temp.add_trace(go.Scatter(x=df_city["timestamp"], y=df_city["temp"],
                                          mode="lines+markers", name=city))
        fig_temp.update_layout(xaxis_title="Waktu", yaxis_title="Suhu", template="plotly_dark")
        st.plotly_chart(fig_temp, use_container_width=True)

        # ========== PLOT KELEMBAPAN ==========
        st.subheader("💧 Grafik Kelembapan")
        fig_hum = go.Figure()
        for city in latest_cities:
            df_city = df_hist[df_hist["city"] == city]
            fig_hum.add_trace(go.Scatter(x=df_city["timestamp"], y=df_city["humidity"],
                                         mode="lines+markers", name=city))
        fig_hum.update_layout(xaxis_title="Waktu", yaxis_title="Kelembapan (%)", template="plotly_dark")
        st.plotly_chart(fig_hum, use_container_width=True)

        # ========== PLOT TEKANAN ==========
        st.subheader("🧭 Grafik Tekanan Udara")
        fig_press = go.Figure()
        for city in latest_cities:
            df_city = df_hist[df_hist["city"] == city]
            fig_press.add_trace(go.Scatter(x=df_city["timestamp"], y=df_city["pressure"],
                                           mode="lines+markers", name=city))
        fig_press.update_layout(xaxis_title="Waktu", yaxis_title="Tekanan (hPa)", template="plotly_dark")
        st.plotly_chart(fig_press, use_container_width=True)

    else:
        st.info("Belum ada data historis. Data akan otomatis tersimpan setiap fetch baru.")

    # ========== MAP ==========
    st.subheader("🗺️ Peta Lokasi Kota")
    st.map(df_current[["lat", "lon"]])

    # ========== RAW DATA ==========
    with st.expander("📦 Data JSON Lengkap"):
        for res in results:
            st.json(res)

else:
    st.error("Tidak ada data yang berhasil diambil.")

# ========== FOOTER ==========
st.markdown("---")
st.caption(
    f"""
    🌤️ **OpenWeatherMap Dashboard**
    - Data dari [OpenWeatherMap One Call API 3.0](https://openweathermap.org/api/one-call-3)
    - Cache otomatis: {CACHE_TTL//60} menit
    - Log tersimpan di: `{DATA_FILE}`
    - Dikembangkan untuk demo Smart City & Climate Monitoring
    """
)
