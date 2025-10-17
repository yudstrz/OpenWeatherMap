import os
from datetime import datetime
import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# ========== CONFIG ==========
st.set_page_config(page_title="🌦️ OpenWeatherMap Dashboard (Free)", layout="wide", page_icon="🌍")

DATA_FILE = "weather_history.csv"
CACHE_TTL = 600  # 10 minutes

# ========== SIDEBAR ==========
st.sidebar.title("⚙️ Konfigurasi Dashboard")
api_key = st.sidebar.text_input("🔑 OpenWeatherMap API Key", value="52bf74effb7223642f508b09cf04b348", type="password")
cities_input = st.sidebar.text_area("🌍 Daftar Kota (pisahkan dengan koma)", "Jakarta, Bandung, Surabaya")
units = st.sidebar.selectbox("🌡️ Unit suhu", ("metric", "imperial"), index=0)
lang = st.sidebar.selectbox("🗣️ Bahasa", ("id", "en"))
refresh_minutes = st.sidebar.slider("⏱️ Update tiap (menit)", 1, 30, 10)

st.sidebar.markdown("---")
st.sidebar.caption("💡 Menggunakan API v2.5 (Gratis) dari OpenWeatherMap — cocok untuk proyek demo & edukasi.")

# ========== HELPER FUNCTIONS ==========
@st.cache_data(ttl=CACHE_TTL)
def fetch_weather(city_name, api_key, units="metric", lang="id"):
    """Ambil data cuaca kota (API gratis v2.5)"""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city_name, "appid": api_key, "units": units, "lang": lang}
    resp = requests.get(url, params=params, timeout=10)
    if resp.status_code != 200:
        return {"error": f"{city_name}: HTTP {resp.status_code} - {resp.text}"}
    data = resp.json()
    return {"city": city_name, "data": data}


def extract_metrics(city_data):
    """Ambil metrik utama"""
    if "error" in city_data:
        return None
    d = city_data["data"]
    return {
        "city": city_data["city"],
        "timestamp": datetime.utcfromtimestamp(d["dt"]).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "temp": d["main"]["temp"],
        "humidity": d["main"]["humidity"],
        "pressure": d["main"]["pressure"],
        "weather": d["weather"][0]["description"],
        "icon": d["weather"][0]["icon"],
        "lat": d["coord"]["lat"],
        "lon": d["coord"]["lon"]
    }


def append_to_csv(data_dict, file_path=DATA_FILE):
    df = pd.DataFrame([data_dict])
    if os.path.exists(file_path):
        df.to_csv(file_path, mode="a", header=False, index=False)
    else:
        df.to_csv(file_path, index=False)


def load_history(file_path=DATA_FILE):
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=["city", "timestamp", "temp", "humidity", "pressure"])
    return pd.read_csv(file_path)

# ========== MAIN APP ==========
st.title("🌦️ OpenWeatherMap Dashboard (Gratis)")
st.caption(f"⏱️ Data diperbarui setiap {refresh_minutes} menit | Cached otomatis {CACHE_TTL//60} menit")

cities = [c.strip() for c in cities_input.split(",") if c.strip()]
if not api_key:
    st.warning("Masukkan API Key terlebih dahulu.")
    st.stop()

progress = st.progress(0)
results = []
for i, city in enumerate(cities):
    progress.progress((i + 1) / len(cities))
    data = fetch_weather(city, api_key, units, lang)
    metrics = extract_metrics(data)
    if metrics:
        results.append(metrics)
        append_to_csv(metrics)
    else:
        st.error(data.get("error", f"Gagal mengambil data {city}"))
progress.empty()

# ========== DISPLAY ==========
if results:
    df_current = pd.DataFrame(results)
    st.subheader("📋 Kondisi Cuaca Terkini")
    st.dataframe(df_current[["city", "temp", "humidity", "pressure", "weather"]], use_container_width=True)

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Rata-rata Suhu", f"{df_current['temp'].mean():.1f}°")
    with col2: st.metric("Rata-rata Kelembapan", f"{df_current['humidity'].mean():.1f}%")
    with col3: st.metric("Rata-rata Tekanan", f"{df_current['pressure'].mean():.1f} hPa")

    df_hist = load_history()
    if not df_hist.empty:
        df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"])
        for metric, title, unit in [("temp", "🌡️ Suhu", "°C"), ("humidity", "💧 Kelembapan", "%"), ("pressure", "🧭 Tekanan", "hPa")]:
            st.subheader(f"{title} dari Waktu ke Waktu")
            fig = go.Figure()
            for city in df_hist["city"].unique():
                df_city = df_hist[df_hist["city"] == city]
                fig.add_trace(go.Scatter(x=df_city["timestamp"], y=df_city[metric],
                                         mode="lines+markers", name=city))
            fig.update_layout(xaxis_title="Waktu", yaxis_title=f"{title} ({unit})", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("🗺️ Peta Lokasi Kota")
        st.map(df_current[["lat", "lon"]])
    else:
        st.info("Belum ada data historis. Data akan otomatis tersimpan setiap fetch baru.")

    with st.expander("📦 Data JSON Lengkap"):
        for res in results:
            st.json(res)
else:
    st.error("Tidak ada data yang berhasil diambil.")

st.markdown("---")
st.caption("🌤️ Dashboard Cuaca dari OpenWeatherMap API v2.5")
