import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
import datetime
import requests
import io
import email.utils

# Set Page Config
st.set_page_config(
    page_title="Hanzo Executive Commercial Cockpit",
    page_icon="🏛",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load CSS Stylesheet for custom styling
st.markdown("""
<style>
    /* Executive Cockpit Styling */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FFFFFF;
        color: #0F172A;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Header and Title Styles */
    .cockpit-header {
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    .cockpit-title {
        color: #002060;
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .cockpit-subtitle {
        color: #64748B;
        font-size: 0.95rem;
        margin-top: 0.2rem;
    }
    
    /* Large Month Status Badge */
    .status-badge-container {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        justify-content: center;
        height: 100%;
    }
    .status-badge {
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.1rem;
        text-align: center;
        border: 1px solid transparent;
        display: inline-block;
        margin-bottom: 0.5rem;
    }
    .status-green {
        background-color: #F0FDF4;
        color: #166534;
        border-color: #BBF7D0;
    }
    .status-yellow {
        background-color: #FEF9C3;
        color: #854D0E;
        border-color: #FEF08A;
    }
    .status-red {
        background-color: #FEF2F2;
        color: #991B1B;
        border-color: #FCA5A5;
    }
    
    /* Card Styles */
    .cockpit-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .card-title {
        color: #002060;
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 0.75rem;
        border-bottom: 1px solid #F1F5F9;
        padding-bottom: 0.25rem;
    }
    
    /* KPI Indicators formatting */
    .kpi-main-val {
        font-size: 1.8rem;
        font-weight: 800;
        color: #002060;
        line-height: 1.1;
    }
    .kpi-sub-label {
        font-size: 0.8rem;
        color: #64748B;
        font-weight: 600;
        margin-top: 0.4rem;
    }
    .kpi-sub-val {
        font-size: 0.95rem;
        font-weight: 700;
        color: #0F172A;
    }
    .kpi-light {
        font-size: 1rem;
        display: inline-block;
        vertical-align: middle;
        margin-left: 0.25rem;
    }
    
    /* Executive Summary Bullet Points */
    .summary-bullet {
        font-size: 0.9rem;
        line-height: 1.4;
        margin-bottom: 0.4rem;
        color: #334155;
    }
    
    /* Tight Table formatting */
    .compact-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.82rem;
    }
    .compact-table th {
        background-color: #F8FAFC;
        color: #475569;
        font-weight: 700;
        text-align: left;
        padding: 0.35rem 0.5rem;
        border-bottom: 1px solid #E2E8F0;
    }
    .compact-table td {
        padding: 0.35rem 0.5rem;
        border-bottom: 1px solid #F1F5F9;
        color: #0F172A;
    }
    .compact-table tr:hover {
        background-color: #F8FAFC;
    }
    
    /* Hide Streamlit components */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Import Data Loader
import data_loader

# Google Drive Configuration
# Copy your public Google Drive file ID here to host the data source online.
# If left as placeholder or empty, it will fall back to reading the local "Planejamento 2026.xlsx".
GOOGLE_DRIVE_FILE_ID = "paste_file_id_here"

@st.cache_data(ttl=300)
def load_and_cache_data():
    try:
        # Check if Google Drive file ID is set
        if GOOGLE_DRIVE_FILE_ID and GOOGLE_DRIVE_FILE_ID != "paste_file_id_here" and GOOGLE_DRIVE_FILE_ID.strip() != "":
            file_id = GOOGLE_DRIVE_FILE_ID.strip()
            # Direct download URL for binary files uploaded to Google Drive
            url = f"https://drive.google.com/uc?export=download&id={file_id}"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            content = response.content
            # Check if Google Drive demands login/auth page (returned as HTML instead of binary xlsx)
            if b"google.com" in content[:100] and b"html" in content[:100].lower():
                # Try export sheet format in case it is a converted Google Sheets file
                url_export = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
                response = requests.get(url_export, headers=headers, timeout=30)
                response.raise_for_status()
                content = response.content
                
            data_bytes = io.BytesIO(content)
            xl = pd.ExcelFile(data_bytes)
            
            # Retrieve last modified time from response header, fallback to current time
            last_modified = datetime.datetime.now()
            if "Last-Modified" in response.headers:
                try:
                    last_modified = email.utils.parsedate_to_datetime(response.headers["Last-Modified"])
                except:
                    pass
        else:
            # Fallback to local spreadsheet path
            excel_path = os.path.join(os.path.dirname(__file__), "Planejamento 2026.xlsx")
            if not os.path.exists(excel_path):
                raise FileNotFoundError(
                    "Planilha local 'Planejamento 2026.xlsx' não encontrada e GOOGLE_DRIVE_FILE_ID não está configurado."
                )
            xl = pd.ExcelFile(excel_path)
            mtime = os.path.getmtime(excel_path)
            last_modified = datetime.datetime.fromtimestamp(mtime)
            
        # Parse all sheets into dict of dataframes to ensure return values are fully serializable for cache_data
        sheets_data = {}
        for s in xl.sheet_names:
            if s in ["Planejamento", "Projeção", "Projeo"]:
                sheets_data[s] = xl.parse(s, header=None)
            else:
                sheets_data[s] = xl.parse(s)
                
        return sheets_data, last_modified, None
    except Exception as e:
        return None, None, str(e)

# Load data workbook sheets dictionary
sheets_data, last_modified, load_error = load_and_cache_data()

if load_error:
    st.error(f"Erro ao carregar planilha: {load_error}")
    st.stop()

# Helper cleanup name mappings
PT_MONTHS = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
EN_MONTHS = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
EN_TO_PT = dict(zip(EN_MONTHS, PT_MONTHS))

# Parse monthly data using data_loader
overview_data, monthly_data, _, clients_metadata = data_loader.load_data(sheets_data)

# Retrieve active sheet to extract weights row and dynamic columns mapping
df_pl = sheets_data.get("Planejamento")
m_map_pl = data_loader.map_columns(df_pl)
has_weekly = any(m_map_pl[m]["weekly"] for m in m_map_pl)

if has_weekly:
    df_active = df_pl
    m_map = m_map_pl
else:
    proj_sheet = None
    for s in ["Projeção", "Projeo"]:
        if s in sheets_data:
            proj_sheet = s
            break
    if proj_sheet:
        df_active = sheets_data[proj_sheet]
        m_map = data_loader.map_columns(df_active)
    else:
        df_active = df_pl
        m_map = m_map_pl

# 1. AUTOMATIC MONTH & WEEK DETECTION
latest_weekly_month = None
for m in EN_MONTHS:
    if m in m_map and m_map[m]["weekly"]:
        latest_weekly_month = m

if not latest_weekly_month:
    latest_weekly_month = "jul" # Safe fallback

# Determine Current Week index (0-based) inside the month
weekly_cols = m_map[latest_weekly_month]["weekly"]
current_week_idx = 0
for idx, col in enumerate(weekly_cols):
    col_sum = 0.0
    for client in monthly_data:
        col_sum += monthly_data[client]["GMV"]["weekly"][latest_weekly_month][idx]
    if col_sum > 0:
        current_week_idx = idx

current_week_label = f"Semana {current_week_idx + 1}"
monitoring_month_label = f"{EN_TO_PT[latest_weekly_month]} 2026"

# Load weekly weights from Row 3 (index 3) of the active sheet
weights_row = df_active.iloc[3]
weekly_weights = [data_loader.clean_val(weights_row[col]) for col in weekly_cols]
sum_weights = sum(weekly_weights)
if sum_weights == 0:
    weekly_weights = [1.0 / len(weekly_cols)] * len(weekly_cols)
else:
    weekly_weights = [w / sum_weights for w in weekly_weights]

# Proration factor up to current week
proration_factor = sum(weekly_weights[:current_week_idx + 1])

# 2. GLOBAL FILTERS (Only Client Group selectbox)
col_filter, col_refresh = st.columns([3, 1])
with col_filter:
    group_filter = st.selectbox(
        "Filtrar por Grupo de Clientes",
        ["Todos", "Grupo Alife Nino", "Grupo Bold", "Grupo Drumattos", "Independente"],
        index=0
    )
with col_refresh:
    st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Filter clients list
filtered_clients = []
for client in monthly_data:
    group = clients_metadata.get(client, {}).get("group", "Independente")
    if group_filter == "Todos" or group == group_filter:
        filtered_clients.append(client)

# Format functions
def fmt_currency(val):
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_qty(val):
    return f"{int(val):,}".replace(",", ".")

def fmt_pct(val):
    return f"{val:+.1f}%".replace(".", ",")

def clean_val(val):
    return data_loader.clean_val(val)

# Core Metrics Aggregations for group
# A) GMV
gmv_plan = sum(monthly_data[c]["GMV"]["plan"][latest_weekly_month] for c in filtered_clients)
gmv_real = sum(monthly_data[c]["GMV"]["real"][latest_weekly_month] for c in filtered_clients)
gmv_prorated = gmv_plan * proration_factor
gmv_factor = gmv_real / gmv_prorated if gmv_prorated > 0 else 1.0
gmv_forecast = gmv_plan * gmv_factor
gmv_ach = gmv_forecast / gmv_plan if gmv_plan > 0 else 0.0

# B) Receita
rec_plan = sum(monthly_data[c]["Receita Hanzo"]["plan"][latest_weekly_month] for c in filtered_clients)
rec_real = sum(monthly_data[c]["Receita Hanzo"]["real"][latest_weekly_month] for c in filtered_clients)
rec_prorated = rec_plan * proration_factor
rec_factor = rec_real / rec_prorated if rec_prorated > 0 else 1.0
rec_forecast = rec_plan * rec_factor
rec_ach = rec_forecast / rec_plan if rec_plan > 0 else 0.0

# C) Pedidos
ped_plan = sum(monthly_data[c]["Pedidos"]["plan"][latest_weekly_month] for c in filtered_clients)
ped_real = sum(monthly_data[c]["Pedidos"]["real"][latest_weekly_month] for c in filtered_clients)
ped_prorated = ped_plan * proration_factor
ped_factor = ped_real / ped_prorated if ped_prorated > 0 else 1.0
ped_forecast = ped_plan * ped_factor
ped_ach = ped_forecast / ped_plan if ped_plan > 0 else 0.0

# D) Ticket Médio
tkt_plan = gmv_plan / ped_plan if ped_plan > 0 else 0.0
tkt_real = gmv_real / ped_real if ped_real > 0 else 0.0
tkt_prorated = gmv_prorated / ped_prorated if ped_prorated > 0 else 0.0
tkt_forecast = gmv_forecast / ped_forecast if ped_forecast > 0 else 0.0
tkt_ach = tkt_forecast / tkt_plan if tkt_plan > 0 else 0.0

# Traffic light formatting function
def get_farol_kpi(ach_val):
    if ach_val >= 0.95:
        return "🟢", "Dentro da Meta"
    elif ach_val >= 0.90:
        return "🟡", "Atenção"
    else:
        return "🔴", "Abaixo da Meta"

# Overall month status
avg_ach = (gmv_ach + rec_ach + ped_ach + tkt_ach) / 4
overall_farol, overall_status = get_farol_kpi(avg_ach)

# Header Row
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown(f'''
    <div class="cockpit-header">
        <h1 class="cockpit-title">HANZO DO BRASIL</h1>
        <div class="cockpit-subtitle">
            Mês de Monitoramento: <b>{monitoring_month_label}</b> | 
            Semana de Análise: <b>{current_week_label}</b> | 
            Última Atualização: {last_modified.strftime("%d/%m/%Y %H:%M:%S")}
        </div>
    </div>
    ''', unsafe_allow_html=True)

with col_status:
    badge_class = "status-green" if avg_ach >= 0.95 else ("status-yellow" if avg_ach >= 0.90 else "status-red")
    st.markdown(f'''
    <div class="status-badge-container">
        <div class="status-badge {badge_class}">
            STATUS DO MÊS: {overall_farol} {overall_status}
        </div>
    </div>
    ''', unsafe_allow_html=True)

# Executive Insights List (max 5 bullets)
st.markdown('<div class="cockpit-card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">Insights de Gestão Executiva</div>', unsafe_allow_html=True)

bullets = []
# Bullet 1: Revenue Plan/Real Status
if rec_real >= rec_prorated:
    bullets.append(f"✔ <b>Faturamento Realizado</b> ({fmt_currency(rec_real)}) está <b>acima</b> do orçado proporcional ({fmt_currency(rec_prorated)}).")
else:
    bullets.append(f"⚠ <b>Faturamento Realizado</b> ({fmt_currency(rec_real)}) está <b>abaixo</b> do orçado proporcional ({fmt_currency(rec_prorated)}).")

# Bullet 2: GMV growth
gmv_growth_str = ""
if current_week_idx > 0:
    gmv_curr_wk = sum(monthly_data[c]["GMV"]["weekly"][latest_weekly_month][current_week_idx] for c in filtered_clients)
    gmv_prev_wk = sum(monthly_data[c]["GMV"]["weekly"][latest_weekly_month][current_week_idx-1] for c in filtered_clients)
    if gmv_prev_wk > 0:
        gw = (gmv_curr_wk - gmv_prev_wk) / gmv_prev_wk
        if gw > 0:
            bullets.append(f"✔ <b>GMV Comercial</b> cresceu <b>{gw*100:+.1f}%</b> na comparação com a semana anterior.")
        elif gw < 0:
            bullets.append(f"⚠ <b>GMV Comercial</b> caiu <b>{gw*100:+.1f}%</b> na comparação com a semana anterior.")

# Bullet 3: Concentration
client_gmvs = {c: sum(monthly_data[c]["GMV"]["weekly"][latest_weekly_month][:current_week_idx+1]) for c in filtered_clients}
sorted_c_gmv = sorted(client_gmvs.items(), key=lambda x: x[1], reverse=True)
total_group_gmv = sum(client_gmvs.values())
if total_group_gmv > 0 and len(sorted_c_gmv) >= 2:
    top2_share = (sorted_c_gmv[0][1] + sorted_c_gmv[1][1]) / total_group_gmv
    if top2_share >= 0.50:
        bullets.append(f"⚠ <b>Concentração comercial alta:</b> Os dois maiores clientes representam <b>{top2_share*100:.1f}%</b> do GMV do grupo.")

# Bullet 4: Forecast closing status
bullets.append(f"✔ O fechamento projetado (Forecast) indica atingimento de <b>{avg_ach*100:.1f}%</b> do orçamento comercial.")

for b in bullets[:5]:
    st.markdown(f'<div class="summary-bullet">{b}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('<br>', unsafe_allow_html=True)

# 4 Columns Grid Layout
col1, col2, col3, col4 = st.columns(4)

metrics_setup = [
    {
        "col": col1,
        "title": "GMV COMERCIAL",
        "key": "GMV",
        "fmt": fmt_currency,
        "plan": gmv_plan,
        "real": gmv_real,
        "forecast": gmv_forecast,
        "ach": gmv_ach,
        "prorated": gmv_prorated,
        "factor": gmv_factor
    },
    {
        "col": col2,
        "title": "FATURAMENTO (RECEITA)",
        "key": "Receita Hanzo",
        "fmt": fmt_currency,
        "plan": rec_plan,
        "real": rec_real,
        "forecast": rec_forecast,
        "ach": rec_ach,
        "prorated": rec_prorated,
        "factor": rec_factor
    },
    {
        "col": col3,
        "title": "PEDIDOS ENTREGUES",
        "key": "Pedidos",
        "fmt": fmt_qty,
        "plan": ped_plan,
        "real": ped_real,
        "forecast": ped_forecast,
        "ach": ped_ach,
        "prorated": ped_prorated,
        "factor": ped_factor
    },
    {
        "col": col4,
        "title": "TICKET MÉDIO",
        "key": "Ticket Médio",
        "fmt": fmt_currency,
        "plan": tkt_plan,
        "real": tkt_real,
        "forecast": tkt_forecast,
        "ach": tkt_ach,
        "prorated": tkt_prorated,
        "factor": tkt_ach
    }
]

for m_idx, m_info in enumerate(metrics_setup):
    with m_info["col"]:
        # KPI CARD
        kpi_farol, kpi_status = get_farol_kpi(m_info["ach"])
        st.markdown(f'''
        <div class="cockpit-card">
            <div class="card-title">{m_info["title"]}</div>
            <div class="kpi-main-val">{m_info["fmt"](m_info["real"])}</div>
            <div style="display:flex; justify-content:space-between; margin-top:0.75rem;">
                <div>
                    <div class="kpi-sub-label">PLANEJADO</div>
                    <div class="kpi-sub-val">{m_info["fmt"](m_info["plan"])}</div>
                </div>
                <div>
                    <div class="kpi-sub-label">FORECAST</div>
                    <div class="kpi-sub-val">{m_info["fmt"](m_info["forecast"])}</div>
                </div>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.5rem; border-top:1px solid #F1F5F9; padding-top:0.5rem;">
                <span style="font-size:0.85rem; font-weight:700; color:#475569;">Atingimento Forecast:</span>
                <span style="font-size:0.95rem; font-weight:800; color:{'#166534' if m_info["ach"]>=0.95 else ('#854D0E' if m_info["ach"]>=0.90 else '#991B1B')};">
                    {m_info["ach"]*100:.1f}% <span class="kpi-light">{kpi_farol}</span>
                </span>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        st.markdown('<br>', unsafe_allow_html=True)
        
        # CLIENT RANKINGS DATA PREPARATION
        # Build client-level rankings data list
        client_rankings = []
        for client in filtered_clients:
            # Weekly actual
            val_wk = monthly_data[client][m_info["key"]]["weekly"][latest_weekly_month][current_week_idx]
            # Accumulated actual
            val_accum = sum(monthly_data[client][m_info["key"]]["weekly"][latest_weekly_month][:current_week_idx+1])
            # Planned prorated target
            val_plan_month = monthly_data[client][m_info["key"]]["plan"][latest_weekly_month]
            val_plan_prorated = val_plan_month * proration_factor
            
            # Special calculations for Ticket Médio
            if m_info["key"] == "Ticket Médio":
                # Weekly actual = Weekly GMV / Weekly Pedidos
                wk_gmv = monthly_data[client]["GMV"]["weekly"][latest_weekly_month][current_week_idx]
                wk_ped = monthly_data[client]["Pedidos"]["weekly"][latest_weekly_month][current_week_idx]
                val_wk = wk_gmv / wk_ped if wk_ped > 0 else 0.0
                
                # Accumulated actual = Accumulated GMV / Accumulated Pedidos
                acc_gmv = sum(monthly_data[client]["GMV"]["weekly"][latest_weekly_month][:current_week_idx+1])
                acc_ped = sum(monthly_data[client]["Pedidos"]["weekly"][latest_weekly_month][:current_week_idx+1])
                val_accum = acc_gmv / acc_ped if acc_ped > 0 else 0.0
                
                # Plan prorated target = Prorated GMV / Prorated Pedidos
                p_gmv = monthly_data[client]["GMV"]["plan"][latest_weekly_month] * proration_factor
                p_ped = monthly_data[client]["Pedidos"]["plan"][latest_weekly_month] * proration_factor
                val_plan_prorated = p_gmv / p_ped if p_ped > 0 else 0.0
                
            # Weekly growth compared to previous week
            if current_week_idx == 0:
                growth_str = "N/A"
            else:
                if m_info["key"] == "Ticket Médio":
                    prev_gmv = monthly_data[client]["GMV"]["weekly"][latest_weekly_month][current_week_idx-1]
                    prev_ped = monthly_data[client]["Pedidos"]["weekly"][latest_weekly_month][current_week_idx-1]
                    val_prev = prev_gmv / prev_ped if prev_ped > 0 else 0.0
                else:
                    val_prev = monthly_data[client][m_info["key"]]["weekly"][latest_weekly_month][current_week_idx-1]
                
                if val_prev > 0:
                    gw = (val_wk - val_prev) / val_prev
                    growth_str = f"{gw*100:+.1f}%"
                else:
                    growth_str = "0,0%"
            
            # Achievement & Farol
            is_zero_zero = (val_plan_prorated == 0 and val_accum == 0)
            if is_zero_zero:
                ach_val = 0.0
                ach_str = "- %"
                farol = "—"
            else:
                if val_plan_prorated > 0:
                    ach_val = val_accum / val_plan_prorated
                    ach_str = f"{ach_val*100:.1f}%"
                    if ach_val >= 0.95:
                        farol = "🟢"
                    elif ach_val >= 0.90:
                        farol = "🟡"
                    else:
                        farol = "🔴"
                else:
                    ach_val = 1.0
                    ach_str = "100,0%"
                    farol = "🟢"
                    
            client_rankings.append({
                "client": client,
                "wk_val": val_wk,
                "accum": val_accum,
                "ach_val": ach_val,
                "ach_str": ach_str,
                "farol": farol,
                "growth": growth_str,
                "is_zero_zero": is_zero_zero
            })
            
        # SECTION 2: TOP 5 RANKING
        # Sort rule: is_zero_zero at the end, then wk_val descending
        sorted_top = sorted(client_rankings, key=lambda x: (x["is_zero_zero"], -x["wk_val"]))
        
        st.markdown(f'''
        <div class="cockpit-card">
            <div class="card-title">Quem Puxou o Resultado? (Top 5)</div>
            <table class="compact-table">
                <thead>
                    <tr>
                        <th>Rk</th>
                        <th>Cliente</th>
                        <th>Semana</th>
                        <th>Acumulado</th>
                        <th>Atig.</th>
                        <th>Farol</th>
                    </tr>
                </thead>
                <tbody>
        ''', unsafe_allow_html=True)
        
        for r_num, row in enumerate(sorted_top[:5]):
            st.markdown(f'''
                    <tr>
                        <td><b>{r_num+1}</b></td>
                        <td>{row["client"]}</td>
                        <td>{m_info["fmt"](row["wk_val"])}</td>
                        <td>{m_info["fmt"](row["accum"])}</td>
                        <td>{row["ach_str"]}</td>
                        <td>{row["farol"]}</td>
                    </tr>
            ''', unsafe_allow_html=True)
            
        st.markdown('</tbody></table></div>', unsafe_allow_html=True)
        st.markdown('<br>', unsafe_allow_html=True)
        
        # SECTION 3: BOTTOM 5 RANKING
        # Sort rule: is_zero_zero at the end, then wk_val ascending
        sorted_bottom = sorted(client_rankings, key=lambda x: (x["is_zero_zero"], x["wk_val"]))
        
        st.markdown(f'''
        <div class="cockpit-card">
            <div class="card-title">Quem Prejudicou o Resultado? (Bottom 5)</div>
            <table class="compact-table">
                <thead>
                    <tr>
                        <th>Rk</th>
                        <th>Cliente</th>
                        <th>Semana</th>
                        <th>Acumulado</th>
                        <th>Atig.</th>
                        <th>Farol</th>
                    </tr>
                </thead>
                <tbody>
        ''', unsafe_allow_html=True)
        
        for r_num, row in enumerate(sorted_bottom[:5]):
            st.markdown(f'''
                    <tr>
                        <td><b>{r_num+1}</b></td>
                        <td>{row["client"]}</td>
                        <td>{m_info["fmt"](row["wk_val"])}</td>
                        <td>{m_info["fmt"](row["accum"])}</td>
                        <td>{row["ach_str"]}</td>
                        <td>{row["farol"]}</td>
                    </tr>
            ''', unsafe_allow_html=True)
            
        st.markdown('</tbody></table></div>', unsafe_allow_html=True)
        st.markdown('<br>', unsafe_allow_html=True)
        
        # SECTION 4: LINE CHART PROJECTIONS
        # Prepare cumulative weekly values for charts
        weeks_labels = [f"Sem {w+1}" for w in range(len(weekly_cols))]
        
        # Cumulative Plan curve
        plan_curve = []
        acc_plan = 0.0
        for w in range(len(weekly_cols)):
            acc_plan += m_info["plan"] * weekly_weights[w]
            plan_curve.append(acc_plan)
            
        # Cumulative Actual curve (up to current week)
        actual_curve = []
        acc_actual = 0.0
        for w in range(len(weekly_cols)):
            if w <= current_week_idx:
                wk_act_sum = 0.0
                for client in filtered_clients:
                    if m_info["key"] == "Ticket Médio":
                        wk_gmv = monthly_data[client]["GMV"]["weekly"][latest_weekly_month][w]
                        wk_ped = monthly_data[client]["Pedidos"]["weekly"][latest_weekly_month][w]
                        wk_act_sum += wk_gmv / wk_ped if wk_ped > 0 else 0.0
                    else:
                        wk_act_sum += monthly_data[client][m_info["key"]]["weekly"][latest_weekly_month][w]
                
                if m_info["key"] == "Ticket Médio":
                    cum_gmv = sum(monthly_data[c]["GMV"]["weekly"][latest_weekly_month][i] for c in filtered_clients for i in range(w+1))
                    cum_ped = sum(monthly_data[c]["Pedidos"]["weekly"][latest_weekly_month][i] for c in filtered_clients for i in range(w+1))
                    acc_actual = cum_gmv / cum_ped if cum_ped > 0 else 0.0
                else:
                    acc_actual += wk_act_sum
                actual_curve.append(acc_actual)
            else:
                actual_curve.append(None)
                
        # Cumulative Forecast curve
        forecast_curve = []
        for w in range(len(weekly_cols)):
            if w <= current_week_idx:
                forecast_curve.append(actual_curve[w])
            else:
                if m_info["key"] == "Ticket Médio":
                    forecast_curve.append(tkt_forecast)
                else:
                    forecast_curve.append(forecast_curve[w-1] + (m_info["plan"] * weekly_weights[w] * m_info["factor"]))
                    
        # Render line chart with Plotly
        fig = go.Figure()
        
        # Add Planned curve
        fig.add_trace(go.Scatter(
            x=weeks_labels,
            y=plan_curve,
            name="Planejado",
            line=dict(color="#002060", width=3)
        ))
        
        # Add Actual curve
        fig.add_trace(go.Scatter(
            x=weeks_labels,
            y=actual_curve,
            name="Realizado",
            line=dict(color="#166534", width=3),
            connectgaps=False
        ))
        
        # Add Forecast curve
        fig.add_trace(go.Scatter(
            x=weeks_labels,
            y=forecast_curve,
            name="Forecast",
            line=dict(color="#64748B", width=2, dash="dash")
        ))
        
        fig.update_layout(
            height=200,
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9")
        )
        
        st.markdown(f'''
        <div class="cockpit-card">
            <div class="card-title">Vamos Bater a Meta? (Projeção)</div>
        ''', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
