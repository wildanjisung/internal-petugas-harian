
import pandas as pd
import streamlit as st
from streamlit_calendar import calendar

st.set_page_config(layout="wide")

# Compact CSS
st.markdown("""
<style>
.block-container {
    padding-top: 0.7rem;
}
</style>
""", unsafe_allow_html=True)

EXCLUDED_PETUGAS = ["Cthbot", "Caritahub Superadmin"]


@st.cache_data
def load_data(file):
    df = pd.read_excel(file)

    df['Dibuat pada'] = pd.to_datetime(df['Dibuat pada'])
    df['tanggal'] = df['Dibuat pada'].dt.date
    df['tahun'] = df['Dibuat pada'].dt.year
    df['bulan'] = df['Dibuat pada'].dt.month
    df['minggu'] = df['Dibuat pada'].dt.isocalendar().week

    df['Terakhir Diperbarui oleh'] = (
        df['Terakhir Diperbarui oleh']
        .astype(str)
        .str.strip()
        .str.title()
    )

    df = df[~df['Terakhir Diperbarui oleh'].isin(EXCLUDED_PETUGAS)]

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
            "title": f"{row['jumlah']}/{total_petugas}",
            "start": str(row['tanggal']),
            "color": color
        })

    return events, total_petugas


def build_individual_events(df, petugas):
    df_petugas = df[df['Terakhir Diperbarui oleh'] == petugas]

    dates = df_petugas['tanggal'].unique()

    events = [
        {
            "title": "✔",
            "start": str(date),
            "color": "#2ecc71"
        }
        for date in dates
    ]

    return events


def ranking_petugas(df):
    rank = (
        df.groupby('Terakhir Diperbarui oleh')['tanggal']
        .nunique()
        .reset_index(name='Hari Aktif')
        .sort_values(by='Hari Aktif', ascending=False)
    )
    return rank


# SIDEBAR IMPORT
with st.sidebar:
    st.header("📂 Data Source")
    uploaded_file = st.file_uploader("Import Excel", type=["xlsx"])
    st.caption("""Upload hanya sekali.
Dashboard akan fokus ke data.""")


st.title("📊 Monitoring Petugas")

if uploaded_file:

    df = load_data(uploaded_file)
    all_petugas = get_all_petugas(df)

    events, total_petugas = build_global_events(df, all_petugas)

    today = pd.Timestamp.today().date()
    today_count = df[df['tanggal'] == today]['Terakhir Diperbarui oleh'].nunique()

    # KPI
    c1, c2, c3 = st.columns(3)
    c1.metric("Total", total_petugas)
    c2.metric("Hari Ini", today_count)
    compliance = (today_count/total_petugas*100) if total_petugas else 0
    c3.metric("Compliance", f"{compliance:.0f}%")

    view = st.segmented_control(
        "",
        ["Global", "Individu", "Ranking"],
        default="Global"
    )

    magnify = st.toggle("🔎 Magnifier", value=False)
    calendar_height = 520 if not magnify else 850

    if view == "Global":

        calendar(
            events=events,
            options={
                "initialView": "dayGridMonth",
                "height": calendar_height
            },
            key="global_calendar"
        )

    elif view == "Individu":

        petugas = st.radio(
            "",
            all_petugas,
            horizontal=True
        )

        individual_events = build_individual_events(df, petugas)

        calendar(
            events=individual_events,
            options={
                "initialView": "dayGridMonth",
                "height": calendar_height
            },
            key="individual_calendar"
        )

    else:

        colA, colB, colC = st.columns(3)

        selected_year = colA.selectbox(
            "Tahun",
            sorted(df['tahun'].unique()),
            index=len(sorted(df['tahun'].unique()))-1
        )

        df_filtered = df[df['tahun'] == selected_year]

        selected_month = colB.selectbox(
            "Bulan",
            ["Semua"] + list(range(1,13))
        )

        if selected_month != "Semua":
            df_filtered = df_filtered[df_filtered['bulan'] == selected_month]

        selected_week = colC.selectbox(
            "Minggu",
            ["Semua"] + sorted(df_filtered['minggu'].unique())
        )

        if selected_week != "Semua":
            df_filtered = df_filtered[df_filtered['minggu'] == selected_week]

        rank_df = ranking_petugas(df_filtered)

        st.dataframe(rank_df, use_container_width=True, height=520)

else:
    st.info("⬅️ Upload Excel dari sidebar untuk mulai dashboard.")
