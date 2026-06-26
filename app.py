"""
Visualisasi Spasio-Temporal Pendidikan Sumatera Barat
======================================================
Aplikasi Streamlit untuk eksplorasi data aktual dan forecast
Rata-rata Lama Sekolah (RLS) dan Angka Melek Huruf (AMH)
per kabupaten/kota di Sumatera Barat, 2010–2035.
"""

import json
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# ============================================================
# KONFIGURASI HALAMAN
# ============================================================
st.set_page_config(
    page_title="Pendidikan Sumatera Barat",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CUSTOM CSS — Tampilan Akademik Profesional
# ============================================================
st.markdown("""
<style>
/* ── Font & Warna Dasar ────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Sidebar ───────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f2942 0%, #1a3a5c 100%);
    border-right: 1px solid #2a4a6e;
}
[data-testid="stSidebar"] * {
    color: #e2eaf4 !important;
}
[data-testid="stSidebar"] .stRadio label {
    color: #b8cce4 !important;
}
[data-testid="stSidebar"] hr {
    border-color: #2a4a6e !important;
}
[data-testid="stSidebar"] .stSlider > div > div > div {
    background: #2196f3 !important;
}

/* ── Kartu Metrik ───────────────────────────────────── */
.metric-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 18px 22px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    margin-bottom: 8px;
}
.metric-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #64748b;
    margin-bottom: 4px;
}
.metric-value {
    font-size: 28px;
    font-weight: 700;
    color: #0f2942;
    line-height: 1;
}
.metric-delta {
    font-size: 12px;
    margin-top: 4px;
}
.metric-delta.up   { color: #16a34a; }
.metric-delta.down { color: #dc2626; }

/* ── Badge Status ───────────────────────────────────── */
.badge-actual {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    background: #dbeafe;
    color: #1e40af;
}
.badge-forecast {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    background: #fef3c7;
    color: #92400e;
}

/* ── Header Section ─────────────────────────────────── */
.section-header {
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #64748b;
    padding: 4px 0 8px 0;
    border-bottom: 2px solid #e2e8f0;
    margin-bottom: 16px;
}

/* ── Judul Utama ────────────────────────────────────── */
.main-title {
    font-size: 26px;
    font-weight: 700;
    color: #0f2942;
    margin: 0;
    line-height: 1.2;
}
.main-subtitle {
    font-size: 14px;
    color: #64748b;
    margin-top: 4px;
}

/* ── Tabel ──────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 8px;
    overflow: hidden;
}

/* ── Plotly Container ───────────────────────────────── */
.js-plotly-plot {
    border-radius: 10px;
}

/* Hilangkan padding berlebih */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# LOAD DATA
# ============================================================
@st.cache_data
def load_data():
    df = pd.read_csv("education_forecast.csv")
    df["Tahun"] = df["Tahun"].astype(int)
    df["RLS"]   = pd.to_numeric(df["RLS"],  errors="coerce")
    df["AMH"]   = pd.to_numeric(df["AMH"],  errors="coerce")
    return df


@st.cache_data
def load_geojson():
    with open("sumbar.geojson", "r", encoding="utf-8") as f:
        return json.load(f)


try:
    df      = load_data()
    geojson = load_geojson()
except FileNotFoundError as e:
    st.error(f"File tidak ditemukan: {e}\nPastikan `education_forecast.csv` dan `sumbar.geojson` ada di direktori yang sama dengan `app.py`.")
    st.stop()


# ============================================================
# KONSTANTA
# ============================================================
TAHUN_MIN       = int(df["Tahun"].min())   # 2010
TAHUN_MAX       = int(df["Tahun"].max())   # 2035
TAHUN_BATAS     = 2025                     # Aktual s/d 2025, Forecast 2026–
KABUPATEN_LIST  = sorted(df["Kabupaten_Kota"].unique())

LABEL_INDIKATOR = {
    "RLS": "Rata-rata Lama Sekolah (Tahun)",
    "AMH": "Angka Melek Huruf (%)",
}
GEOJSON_NAME_KEY = "nama"   # pakai field 'nama' di GeoJSON sumbar


# ============================================================
# MAPPING NAMA GEOJSON → CSV (manual, 100% akurat)
# ============================================================
# GeoJSON 'nama' → nama CSV 'Kabupaten_Kota'
NAME_MAP = {
    "Kabupaten Kepulauan Mentawai" : "Kab. Kepulauan Mentawai",
    "Kabupaten Pesisir Selatan"    : "Kab. Pesisir Selatan",
    "Kabupaten Solok"              : "Kab. Solok",
    "Kabupaten Sijunjung"          : "Kab. Sijunjung",
    "Kabupaten Tanah Datar"        : "Kab. Tanah Datar",
    "Kabupaten Padang Pariaman"    : "Kab. Padang Pariaman",
    "Kabupaten Agam"               : "Kab. Agam",
    "Kabupaten Lima Puluh Kota"    : "Kab. Lima Puluh Kota",
    "Kabupaten Pasaman"            : "Kab. Pasaman",
    "Kabupaten Solok Selatan"      : "Kab. Solok Selatan",
    "Kabupaten Dharmasraya"        : "Kab. Dharmasraya",
    "Kabupaten Pasaman Barat"      : "Kab. Pasaman Barat",
    "Kota Padang"                  : "Kota Padang",
    "Kota Solok"                   : "Kota Solok",
    "Kota Sawahlunto"              : "Kota Sawahlunto",
    "Kota Padang Panjang"          : "Kota Padang Panjang",
    "Kota Bukittinggi"             : "Kota Bukittinggi",
    "Kota Payakumbuh"              : "Kota Payakumbuh",
    "Kota Pariaman"                : "Kota Pariaman",
}
# Balik: CSV → GeoJSON (untuk lookup di peta)
CSV_TO_GEO = {v: k for k, v in NAME_MAP.items()}


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("## Visualisasi Pendidikan\nSumatera Barat")
    st.markdown("---")

    # Slider Tahun
    st.markdown("**Tahun**")
    tahun_dipilih = st.slider(
        label="Tahun",
        min_value=TAHUN_MIN,
        max_value=TAHUN_MAX,
        value=2020,
        step=1,
        label_visibility="collapsed",
    )
    if tahun_dipilih <= TAHUN_BATAS:
        st.markdown(f'<span class="badge-actual">Data Aktual · {tahun_dipilih}</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="badge-forecast">Hasil Forecast · {tahun_dipilih}</span>', unsafe_allow_html=True)

    st.markdown("---")

    # Pilih Indikator
    st.markdown("**Indikator**")
    indikator = st.radio(
        label="Indikator",
        options=["RLS", "AMH"],
        format_func=lambda x: "RLS — Rata-rata Lama Sekolah" if x == "RLS" else "AMH — Angka Melek Huruf",
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Pilih Kabupaten (untuk grafik — alternatif click)
    st.markdown("**Kabupaten / Kota**")
    kabupaten_dipilih = st.selectbox(
        label="Kabupaten",
        options=KABUPATEN_LIST,
        index=KABUPATEN_LIST.index("Kota Padang") if "Kota Padang" in KABUPATEN_LIST else 0,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption("Sumber data: BPS Sumatera Barat\nModel Forecast: Prophet (Meta)\n© 2025 Skripsi Visualisasi Spasio-Temporal")


# ============================================================
# HEADER UTAMA
# ============================================================
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown(
        '<p class="main-title">Visualisasi Spasio-Temporal Pendidikan Sumatera Barat</p>'
        f'<p class="main-subtitle">{LABEL_INDIKATOR[indikator]} · 2010–2035</p>',
        unsafe_allow_html=True
    )
with col_status:
    status_str = "Data Aktual" if tahun_dipilih <= TAHUN_BATAS else "Hasil Forecast"
    badge_cls  = "badge-actual" if tahun_dipilih <= TAHUN_BATAS else "badge-forecast"
    st.markdown(f'<br><span class="{badge_cls}" style="font-size:13px">{status_str} · {tahun_dipilih}</span>', unsafe_allow_html=True)

st.markdown("---")


# ============================================================
# DATA TAHUN DIPILIH (untuk Peta & Metrik)
# ============================================================
df_tahun = df[df["Tahun"] == tahun_dipilih].copy()


# ============================================================
# BAGIAN 1 — PETA CHOROPLETH
# ============================================================
st.markdown('<div class="section-header">Peta Choropleth</div>', unsafe_allow_html=True)

col_map, col_kpi = st.columns([3, 1])

with col_map:
    # Siapkan data untuk peta — mapping CSV → nama GeoJSON field 'nama'
    map_data = df_tahun[["Kabupaten_Kota", indikator, "Status"]].copy()
    map_data["geo_name"] = map_data["Kabupaten_Kota"].map(CSV_TO_GEO)

    # Label hover
    map_data["hover_text"] = map_data.apply(
        lambda r: (
            f"<b>{r['Kabupaten_Kota']}</b><br>"
            f"Tahun : {tahun_dipilih}<br>"
            f"{indikator} : {r[indikator]:.2f}<br>"
            f"Status : {r['Status']}"
        ),
        axis=1,
    )

    val_min = df[indikator].min()
    val_max = df[indikator].max()

    fig_map = px.choropleth_mapbox(
        map_data,
        geojson=geojson,
        featureidkey=f"properties.{GEOJSON_NAME_KEY}",
        locations="geo_name",
        color=indikator,
        color_continuous_scale="YlGnBu",
        range_color=(val_min, val_max),
        mapbox_style="carto-positron",
        zoom=6.8,
        center={"lat": -0.75, "lon": 100.4},
        opacity=0.80,
        custom_data=["hover_text"],
        labels={indikator: LABEL_INDIKATOR[indikator]},
    )

    fig_map.update_traces(
        hovertemplate="%{customdata[0]}<extra></extra>"
    )

    fig_map.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=500,
        coloraxis_colorbar=dict(
            title=dict(text=indikator, font=dict(size=12)),
            thickness=14,
            len=0.7,
            tickfont=dict(size=11),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": False})

with col_kpi:
    # Statistik ringkasan tahun dipilih
    st.markdown(f"**Statistik {tahun_dipilih}**")

    nilai_max   = df_tahun[indikator].max()
    nilai_min   = df_tahun[indikator].min()
    nilai_mean  = df_tahun[indikator].mean()
    kab_max     = df_tahun.loc[df_tahun[indikator].idxmax(), "Kabupaten_Kota"]
    kab_min     = df_tahun.loc[df_tahun[indikator].idxmin(), "Kabupaten_Kota"]

    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Tertinggi</div>
        <div class="metric-value">{nilai_max:.2f}</div>
        <div class="metric-delta up">↑ {kab_max}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Rata-rata Provinsi</div>
        <div class="metric-value">{nilai_mean:.2f}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Terendah</div>
        <div class="metric-value">{nilai_min:.2f}</div>
        <div class="metric-delta down">↓ {kab_min}</div>
    </div>
    """, unsafe_allow_html=True)

    # Kabupaten terpilih
    kab_data_tahun = df_tahun[df_tahun["Kabupaten_Kota"] == kabupaten_dipilih]
    if not kab_data_tahun.empty:
        kab_val = kab_data_tahun[indikator].values[0]
        kab_status = kab_data_tahun["Status"].values[0]
        badge_cls2 = "badge-actual" if kab_status == "Actual" else "badge-forecast"
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #2563eb; margin-top:12px">
            <div class="metric-label">{kabupaten_dipilih}</div>
            <div class="metric-value">{kab_val:.2f}</div>
            <div class="metric-delta" style="margin-top:6px">
                <span class="{badge_cls2}">{kab_status}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


st.markdown("---")


# ============================================================
# BAGIAN 2 — GRAFIK TREN
# ============================================================
st.markdown('<div class="section-header">Grafik Perkembangan</div>', unsafe_allow_html=True)

df_kab = df[df["Kabupaten_Kota"] == kabupaten_dipilih].sort_values("Tahun")

df_actual   = df_kab[df_kab["Status"] == "Actual"]
df_forecast = df_kab[df_kab["Status"] == "Forecast"]

fig_trend = go.Figure()

# Garis Aktual
fig_trend.add_trace(go.Scatter(
    x=df_actual["Tahun"],
    y=df_actual[indikator],
    mode="lines+markers",
    name="Aktual",
    line=dict(color="#1d4ed8", width=2.5),
    marker=dict(size=7, symbol="circle", color="#1d4ed8"),
    hovertemplate="<b>%{x}</b><br>" + indikator + ": %{y:.2f}<br>Status: Aktual<extra></extra>",
))

# Titik sambung antara aktual–forecast
if not df_actual.empty and not df_forecast.empty:
    tahun_batas_row = df_actual.iloc[-1]
    fig_trend.add_trace(go.Scatter(
        x=[tahun_batas_row["Tahun"], df_forecast["Tahun"].iloc[0]],
        y=[tahun_batas_row[indikator], df_forecast[indikator].iloc[0]],
        mode="lines",
        line=dict(color="#94a3b8", width=1.5, dash="dot"),
        showlegend=False,
        hoverinfo="skip",
    ))

# Garis Forecast
fig_trend.add_trace(go.Scatter(
    x=df_forecast["Tahun"],
    y=df_forecast[indikator],
    mode="lines+markers",
    name="Forecast",
    line=dict(color="#f59e0b", width=2.5, dash="dash"),
    marker=dict(size=7, symbol="circle-open", color="#f59e0b"),
    hovertemplate="<b>%{x}</b><br>" + indikator + ": %{y:.2f}<br>Status: Forecast<extra></extra>",
))

# Area shading — Forecast
if not df_forecast.empty:
    y_vals = df_forecast[indikator].tolist()
    fig_trend.add_trace(go.Scatter(
        x=df_forecast["Tahun"].tolist() + df_forecast["Tahun"].tolist()[::-1],
        y=[v + 0.05 for v in y_vals] + [v - 0.05 for v in y_vals[::-1]],
        fill="toself",
        fillcolor="rgba(245, 158, 11, 0.08)",
        line=dict(color="rgba(255,255,255,0)"),
        showlegend=False,
        hoverinfo="skip",
    ))

# Garis vertikal tahun dipilih
y_range_min = df_kab[indikator].min() * 0.98
y_range_max = df_kab[indikator].max() * 1.02
fig_trend.add_vline(
    x=tahun_dipilih,
    line_width=2,
    line_dash="solid",
    line_color="#ef4444",
    annotation_text=f"  {tahun_dipilih}",
    annotation_position="top right",
    annotation_font=dict(color="#ef4444", size=12),
)

# Titik highlight tahun dipilih
kab_val_terpilih = df_kab[df_kab["Tahun"] == tahun_dipilih]
if not kab_val_terpilih.empty:
    fig_trend.add_trace(go.Scatter(
        x=[tahun_dipilih],
        y=[kab_val_terpilih[indikator].values[0]],
        mode="markers",
        marker=dict(size=13, color="#ef4444", symbol="circle"),
        name=f"Tahun {tahun_dipilih}",
        hovertemplate=f"<b>{tahun_dipilih}</b><br>{indikator}: " + "%{y:.2f}<extra></extra>",
    ))

# Garis batas aktual–forecast
fig_trend.add_vline(
    x=TAHUN_BATAS + 0.5,
    line_width=1.5,
    line_dash="dot",
    line_color="#94a3b8",
    annotation_text="  Batas Forecast",
    annotation_position="top left",
    annotation_font=dict(color="#94a3b8", size=10),
)

fig_trend.update_layout(
    title=dict(
        text=f"Tren {indikator} — {kabupaten_dipilih}",
        font=dict(size=15, color="#0f2942"),
        x=0,
    ),
    xaxis=dict(
        title="Tahun",
        tickmode="linear",
        tick0=TAHUN_MIN,
        dtick=1,
        tickangle=-45,
        gridcolor="#f1f5f9",
        linecolor="#e2e8f0",
        range=[TAHUN_MIN - 0.5, TAHUN_MAX + 0.5],
    ),
    yaxis=dict(
        title=LABEL_INDIKATOR[indikator],
        gridcolor="#f1f5f9",
        linecolor="#e2e8f0",
        range=[y_range_min, y_range_max],
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        font=dict(size=12),
    ),
    plot_bgcolor="#ffffff",
    paper_bgcolor="rgba(0,0,0,0)",
    height=370,
    margin=dict(l=0, r=10, t=50, b=30),
    hovermode="x unified",
)

st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})


# ============================================================
# BAGIAN 3 — PERBANDINGAN ANTAR KABUPATEN (Tahun Dipilih)
# ============================================================
st.markdown("---")
st.markdown('<div class="section-header">Perbandingan Kabupaten/Kota</div>', unsafe_allow_html=True)

# Bar chart semua kabupaten tahun dipilih, sortir
df_bar = df_tahun.sort_values(indikator, ascending=True)
colors = ["#f59e0b" if row["Status"] == "Forecast" else "#1d4ed8" for _, row in df_bar.iterrows()]
# Sorot kabupaten terpilih
colors = [
    "#ef4444" if kab == kabupaten_dipilih else c
    for kab, c in zip(df_bar["Kabupaten_Kota"], colors)
]

fig_bar = go.Figure(go.Bar(
    y=df_bar["Kabupaten_Kota"],
    x=df_bar[indikator],
    orientation="h",
    marker_color=colors,
    text=df_bar[indikator].round(2),
    textposition="outside",
    hovertemplate="<b>%{y}</b><br>" + indikator + ": %{x:.2f}<extra></extra>",
))

fig_bar.update_layout(
    title=dict(
        text=f"{LABEL_INDIKATOR[indikator]} per Kabupaten/Kota · {tahun_dipilih}",
        font=dict(size=14, color="#0f2942"),
        x=0,
    ),
    xaxis=dict(title=LABEL_INDIKATOR[indikator], gridcolor="#f1f5f9"),
    yaxis=dict(tickfont=dict(size=11)),
    plot_bgcolor="#ffffff",
    paper_bgcolor="rgba(0,0,0,0)",
    height=580,
    margin=dict(l=10, r=60, t=50, b=20),
)

# Garis rata-rata
fig_bar.add_vline(
    x=df_tahun[indikator].mean(),
    line_width=1.5,
    line_dash="dash",
    line_color="#64748b",
    annotation_text=f" Rata-rata: {df_tahun[indikator].mean():.2f}",
    annotation_position="top",
    annotation_font=dict(size=11, color="#64748b"),
)

st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

# Legenda warna
col_leg1, col_leg2, col_leg3, _ = st.columns([1, 1, 1, 3])
col_leg1.markdown('<span style="color:#1d4ed8">■</span> Data Aktual', unsafe_allow_html=True)
col_leg2.markdown('<span style="color:#f59e0b">■</span> Hasil Forecast', unsafe_allow_html=True)
col_leg3.markdown('<span style="color:#ef4444">■</span> Dipilih', unsafe_allow_html=True)


# ============================================================
# BAGIAN 4 — TABEL DATA
# ============================================================
st.markdown("---")
st.markdown('<div class="section-header">Tabel Data</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs([f" {kabupaten_dipilih}", "Semua Kabupaten · Tahun Dipilih"])

with tab1:
    df_tabel_kab = (
        df[df["Kabupaten_Kota"] == kabupaten_dipilih]
        .sort_values("Tahun")
        [["Tahun", "RLS", "AMH", "Status"]]
        .reset_index(drop=True)
    )
    df_tabel_kab["RLS"] = df_tabel_kab["RLS"].round(2)
    df_tabel_kab["AMH"] = df_tabel_kab["AMH"].round(2)

    # Sorot tahun dipilih
    def sorot_baris(row):
        if row["Tahun"] == tahun_dipilih:
            return ["background-color: #fef9c3"] * len(row)
        elif row["Status"] == "Forecast":
            return ["color: #92400e"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df_tabel_kab.style.apply(sorot_baris, axis=1),
        use_container_width=True,
        hide_index=True,
        height=380,
    )

with tab2:
    df_tabel_semua = (
        df_tahun
        .sort_values(indikator, ascending=False)
        [["Kabupaten_Kota", "RLS", "AMH", "Status"]]
        .reset_index(drop=True)
    )
    df_tabel_semua.index = df_tabel_semua.index + 1  # Peringkat mulai dari 1
    df_tabel_semua["RLS"] = df_tabel_semua["RLS"].round(2)
    df_tabel_semua["AMH"] = df_tabel_semua["AMH"].round(2)
    df_tabel_semua.insert(0, "Peringkat", df_tabel_semua.index)
    df_tabel_semua = df_tabel_semua.reset_index(drop=True)

    def sorot_dipilih(row):
        if row["Kabupaten_Kota"] == kabupaten_dipilih:
            return ["background-color: #dbeafe; font-weight:600"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df_tabel_semua.style.apply(sorot_dipilih, axis=1),
        use_container_width=True,
        hide_index=True,
        height=380,
    )


# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown(
    '<div style="text-align:center; color:#94a3b8; font-size:12px; padding:8px 0">'
    'Visualisasi Spasio-Temporal Pendidikan Sumatera Barat &nbsp;·&nbsp; '
    'Data: BPS Sumatera Barat &nbsp;·&nbsp; Model Forecast: Prophet (Meta) &nbsp;·&nbsp; '
    'Dibangun dengan Streamlit & Plotly'
    '</div>',
    unsafe_allow_html=True
)