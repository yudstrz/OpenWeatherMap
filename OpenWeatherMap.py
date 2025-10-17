import os
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
API_KEY = "52bf74effb7223642f508b09cf04b348"  # ✅ Free API Key kamu

# ========== SIDEBAR ==========
st.sidebar.title("⚙️ Konfigurasi Dashboard")

cities_input = st.sidebar.text_area(
    "🌍 Daftar Kota (pisahkan dengan koma)",
    "Jakarta, Bandung, Surabaya"
)
units = st.sidebar.selectbox("🌡️ Unit suhu", ("metric", "imperial"), index=0)
lang = st.sidebar.selectbox("🗣️ Bahasa", ("id", "en"))
refresh_minutes = st.sidebar.slider("⏱️ Update tiap (menit)", 1, 30, 10)

st.sidebar.markdown("---")
st.sidebar.caption("💡 Menggunakan OpenWeatherMap Current Weather API (Gratis).")

# ========== HELPER FUNCTIONS ==========
@st.cache_data(ttl=CACHE_TTL)
def fetch_weather(city_name, api_key=API_KEY, units="metric", lang="id"):
    """Ambil data cuaca dari API gratis"""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city_name, "appid": api_key, "units": units, "lang": lang}
    resp = requests.get(url, params=params, timeout=10)
    if resp.status_code != 200:
        return {"error": f"{city_name}: HTTP {resp.status_code} - {resp.text}"}
    data = resp.json()
    return {
        "city": city_name,
        "timestamp": datetime.utcfromtimestamp(data["dt"]).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "temp": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "pressure": data["main"]["pressure"],
        "weather": data["weather"][0]["description"],
        "icon": data["weather"][0]["icon"],
        "lat": data["coord"]["lat"],
        "lon": data["coord"]["lon"],
    }


def append_to_csv(data_dict, file_path=DATA_FILE):
    """Simpan data ke CSV"""
    df = pd.DataFrame([data_dict])
    if os.path.exists(file_path):
        df.to_csv(file_path, mode="a", header=False, index=False)
    else:
        df.to_csv(file_path, index=False)


def load_history(file_path=DATA_FILE):
    """Muat data historis"""
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=["city", "timestamp", "temp", "humidity", "pressure"])
    return pd.read_csv(file_path)


# ========== FETCH WEATHER ==========
cities = [c.strip() for c in cities_input.split(",") if c.strip()]
st.title("🌦️ Live Weather Dashboard — Multi City (Gratis API)")
st.caption(f"⏱️ Data diperbarui setiap {refresh_minutes} menit | Cache aktif {CACHE_TTL//60} menit")

progress = st.progress(0)
results = []
for i, city in enumerate(cities):
    progress.progress((i + 1) / len(cities))
    data = fetch_weather(city)
    if "error" in data:
        st.error(data["error"])
    else:
        results.append(data)
        append_to_csv(data)

progress.empty()

# ========== DISPLAY ==========
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

    # Load History
    df_hist = load_history()
    if not df_hist.empty:
        df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"])
        cities_unique = df_hist["city"].unique()

        # Suhu
        st.subheader("🌡️ Grafik Suhu")
        fig_temp = go.Figure()
        for city in cities_unique:
            df_city = df_hist[df_hist["city"] == city]
            fig_temp.add_trace(go.Scatter(x=df_city["timestamp"], y=df_city["temp"], mode="lines+markers", name=city))
        fig_temp.update_layout(xaxis_title="Waktu", yaxis_title="Suhu (°C)", template="plotly_dark")
        st.plotly_chart(fig_temp, use_container_width=True)

        # Kelembapan
        st.subheader("💧 Grafik Kelembapan")
        fig_hum = go.Figure()
        for city in cities_unique:
            df_city = df_hist[df_hist["city"] == city]
            fig_hum.add_trace(go.Scatter(x=df_city["timestamp"], y=df_city["humidity"], mode="lines+markers", name=city))
        fig_hum.update_layout(xaxis_title="Waktu", yaxis_title="Kelembapan (%)", template="plotly_dark")
        st.plotly_chart(fig_hum, use_container_width=True)

        # Tekanan
        st.subheader("🧭 Grafik Tekanan Udara")
        fig_press = go.Figure()
        for city in cities_unique:
            df_city = df_hist[df_hist["city"] == city]
            fig_press.add_trace(go.Scatter(x=df_city["timestamp"], y=df_city["pressure"], mode="lines+markers", name=city))
        fig_press.update_layout(xaxis_title="Waktu", yaxis_title="Tekanan (hPa)", template="plotly_dark")
        st.plotly_chart(fig_press, use_container_width=True)

    else:
        st.info("Belum ada data historis. Akan otomatis tersimpan saat fetch berikutnya.")

    # Peta
    st.subheader("🗺️ Lokasi Kota di Peta")
    st.map(df_current[["lat", "lon"]])

    # Data JSON
    with st.expander("📦 Data JSON Lengkap"):
        for res in results:
            st.json(res)

else:
    st.warning("Tidak ada data yang berhasil diambil. Pastikan nama kota benar.")

# Footer
st.markdown("---")
st.caption("""
🌤️ **OpenWeatherMap Dashboard**
- Data dari [OpenWeatherMap Current Weather API](https://openweathermap.org/current)
- Cache otomatis 10 menit
- CSV log: `weather_history.csv`
- Cocok untuk: demo, smart city, atau riset lingkungan
""")
