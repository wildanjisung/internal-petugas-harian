import pandas as pd
import streamlit as st
from streamlit_calendar import calendar

st.set_page_config(layout="wide")

@st.cache_data
def load_data(file):
    df = pd.read_excel(file)

    df['Dibuat pada'] = pd.to_datetime(df['Dibuat pada'])
    df['tanggal'] = df['Dibuat pada'].dt.date

    df['Terakhir Diperbarui oleh'] = (
        df['Terakhir Diperbarui oleh']
        .astype(str)
        .str.strip()
        .str.title()
    )

    return df


def get_all_petugas(df):
    return sorted(df['Terakhir Diperbarui oleh'].dropna().unique())


def build_global_events(df, all_petugas):
    total_petugas = len(all_petugas)

    daily = (
        df.groupby('tanggal')['Terakhir Diperbarui oleh']
        .nunique()
        .reset_index(name='jumlah')
    )

    events = []

    for _, row in daily.iterrows():
        if row['jumlah'] == total_petugas:
            color = "#2ecc71"
        elif row['jumlah'] > 0:
            color = "#f1c40f"
        else:
            color = "#e74c3c"

        events.append({
            "title": f"{row['jumlah']}/{total_petugas} petugas",
            "start": str(row['tanggal']),
            "color": color
        })

    return events, total_petugas


def build_individual_events(df, petugas):
    df_petugas = df[df['Terakhir Diperbarui oleh'] == petugas]

    dates = df_petugas['tanggal'].unique()

    events = [
        {
            "title": "Input ✔",
            "start": str(date),
            "color": "#2ecc71"
        }
        for date in dates
    ]

    return events


def ranking_petugas(df):
    rank = (
        df.groupby('Terakhir Diperbarui oleh')
        .size()
        .reset_index(name='Jumlah Input')
        .sort_values(by='Jumlah Input', ascending=False)
    )
    return rank


st.title("📊 Dashboard Monitoring Petugas")

uploaded_file = st.file_uploader("Upload file Excel", type=["xlsx"])

if uploaded_file:

    df = load_data(uploaded_file)
    all_petugas = get_all_petugas(df)

    events, total_petugas = build_global_events(df, all_petugas)

    today = pd.Timestamp.today().date()
    today_df = df[df['tanggal'] == today]
    today_count = today_df['Terakhir Diperbarui oleh'].nunique()

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Petugas", total_petugas)
    col2.metric("Sudah Input Hari Ini", today_count)
    compliance = (today_count/total_petugas*100) if total_petugas else 0
    col3.metric("Compliance", f"{compliance:.1f}%")

    st.subheader("📅 Kalender Global (Klik tanggal)")

    selected = calendar(
        events=events,
        options={"initialView": "dayGridMonth"},
        key="global_calendar"
    )

    if selected and "dateClick" in selected:
        clicked_date = pd.to_datetime(selected["dateClick"]["date"]).date()

        st.markdown(f"### 📌 Detail {clicked_date}")

        df_day = df[df['tanggal'] == clicked_date]
        sudah = set(df_day['Terakhir Diperbarui oleh'])
        belum = set(all_petugas) - sudah

        colA, colB = st.columns(2)

        with colA:
            st.success("Sudah Input")
            if sudah:
                st.write(sorted(sudah))
            else:
                st.write("Tidak ada.")

        with colB:
            st.error("Belum Input")
            if belum:
                st.write(sorted(belum))
            else:
                st.write("Semua sudah input 🎉")

    st.divider()

    st.subheader("👤 Kalender Individu")

    selected_petugas = st.selectbox("Pilih Petugas", all_petugas)

    individual_events = build_individual_events(df, selected_petugas)

    calendar(
        events=individual_events,
        options={"initialView": "dayGridMonth"},
        key="individual_calendar"
    )

    st.divider()

    st.subheader("🏆 Ranking Petugas")

    rank_df = ranking_petugas(df)
    st.dataframe(rank_df, use_container_width=True)

else:
    st.info("Upload file Excel untuk mulai dashboard.")
