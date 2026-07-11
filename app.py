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
PT_MONTH_DISPLAY = dict(zip(EN_MONTHS, PT_MONTHS))
PT_TO_EN = {v: k for k, v in PT_MONTH_DISPLAY.items()}

# Parse separated data using data_loader
overview_data, monthly_data, weekly_data, clients_metadata = data_loader.load_data(sheets_data)

# Retrieve active weekly sheet for columns mapping
proj_sheet = None
for s in ["Projeção", "Projeo"]:
    if s in sheets_data:
        proj_sheet = s
        break

if proj_sheet:
    df_proj = sheets_data[proj_sheet]
    m_map_proj = data_loader.map_columns(df_proj)
else:
    df_proj = sheets_data.get("Planejamento")
    m_map_proj = data_loader.map_columns(df_proj)

# Find available months (months containing weekly columns in Projeção sheet)
available_months_en = [m for m in EN_MONTHS if m in m_map_proj and len(m_map_proj[m]["weekly"]) > 0]
available_months_pt = [PT_MONTH_DISPLAY[m] for m in available_months_en]

if not available_months_en:
    st.error("Nenhum mês com monitoramento semanal encontrado na planilha.")
    st.stop()

# Determine default month (latest containing weekly actuals > 0)
default_month_en = available_months_en[-1]
for m in reversed(available_months_en):
    has_data = False
    for w_idx in range(len(m_map_proj[m]["weekly"])):
        w_sum = sum(data_loader.clean_val(weekly_data[c]["GMV"]["weekly"][m][w_idx]) for c in weekly_data)
        if w_sum > 0:
            has_data = True
            break
    if has_data:
        default_month_en = m
        break
default_month_pt = PT_MONTH_DISPLAY[default_month_en]

# 1. FILTERS ROW
col_m_filt, col_w_filt, col_g_filt, col_ref = st.columns([1.5, 1.5, 2, 1])

with col_m_filt:
    month_sel_pt = st.selectbox(
        "Mês de Monitoramento",
        available_months_pt,
        index=available_months_pt.index(default_month_pt)
    )
    month_sel_en = PT_TO_EN[month_sel_pt]

# Determine week options for the selected month
weekly_cols = m_map_proj[month_sel_en]["weekly"]
num_weeks = len(weekly_cols)
week_options = [f"Semana {i+1}" for i in range(num_weeks)]

# Determine default week (latest containing weekly actuals > 0)
default_week_idx = 0
for w_idx in reversed(range(num_weeks)):
    w_sum = sum(data_loader.clean_val(weekly_data[c]["GMV"]["weekly"][month_sel_en][w_idx]) for c in weekly_data)
    if w_sum > 0:
        default_week_idx = w_idx
        break

with col_w_filt:
    week_sel_label = st.selectbox(
        "Semana de Análise",
        week_options,
        index=default_week_idx
    )
    selected_week_idx = week_options.index(week_sel_label)

with col_g_filt:
    group_filter = st.selectbox(
        "Grupo de Clientes",
        ["Todos", "Grupo Alife Nino", "Grupo Bold", "Grupo Drumattos", "Independente"],
        index=0
    )

with col_ref:
    st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Filter clients list
filtered_clients = []
for client in weekly_data:
    group = clients_metadata.get(client, {}).get("group", "Independente")
    if group_filter == "Todos" or group == group_filter:
        filtered_clients.append(client)

# Format helper functions
def fmt_currency(val):
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_qty(val):
    return f"{int(val):,}".replace(",", ".")

def clean_val(val):
    return data_loader.clean_val(val)

# Header Row
col_title, col_status = st.columns([3, 1])

# Header Title
with col_title:
    st.markdown(f'''
    <div class="cockpit-header">
        <h1 class="cockpit-title">HANZO DO BRASIL</h1>
        <div class="cockpit-subtitle">
            Mês: <b>{month_sel_pt} 2026</b> | 
            Semana: <b>{week_sel_label}</b> | 
            Última Atualização: {last_modified.strftime("%d/%m/%Y %H:%M:%S")}
        </div>
    </div>
    ''', unsafe_allow_html=True)

# 2x2 Grid Columns Layout
st.markdown('<br>', unsafe_allow_html=True)
row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

metrics_setup = [
    {
        "slot": row1_col1,
        "title": "GMV COMERCIAL",
        "key": "GMV",
        "fmt": fmt_currency,
        "is_monetary": True
    },
    {
        "slot": row1_col2,
        "title": "FATURAMENTO (RECEITA)",
        "key": "Receita Hanzo",
        "fmt": fmt_currency,
        "is_monetary": True
    },
    {
        "slot": row2_col1,
        "title": "PEDIDOS ENTREGUES",
        "key": "Pedidos",
        "fmt": fmt_qty,
        "is_monetary": False
    },
    {
        "slot": row2_col2,
        "title": "TICKET MÉDIO",
        "key": "Ticket Médio",
        "fmt": fmt_currency,
        "is_monetary": True
    }
]

# Calculate overall status badge based on monthly cards achievements
achievements_list = []

for m_info in metrics_setup:
    metric_key = m_info["key"]
    
    # 1. MONTHLY DATA (from Planejamento)
    gmv_plan_m = sum(data_loader.clean_val(monthly_data[c]["GMV"]["plan"][month_sel_en]) for c in filtered_clients)
    gmv_real_m = sum(data_loader.clean_val(monthly_data[c]["GMV"]["real"][month_sel_en]) for c in filtered_clients)
    
    ped_plan_m = sum(data_loader.clean_val(monthly_data[c]["Pedidos"]["plan"][month_sel_en]) for c in filtered_clients)
    ped_real_m = sum(data_loader.clean_val(monthly_data[c]["Pedidos"]["real"][month_sel_en]) for c in filtered_clients)
    
    rec_plan_m = sum(data_loader.clean_val(monthly_data[c]["Receita Hanzo"]["plan"][month_sel_en]) for c in filtered_clients)
    rec_real_m = sum(data_loader.clean_val(monthly_data[c]["Receita Hanzo"]["real"][month_sel_en]) for c in filtered_clients)
    
    if metric_key == "GMV":
        m_plan_m = gmv_plan_m
        m_real_m = gmv_real_m
    elif metric_key == "Receita Hanzo":
        m_plan_m = rec_plan_m
        m_real_m = rec_real_m
    elif metric_key == "Pedidos":
        m_plan_m = ped_plan_m
        m_real_m = ped_real_m
    else: # Ticket Médio
        # Monthly Average Ticket must be calculated as Monthly Actual GMV / Monthly Actual Orders
        m_plan_m = gmv_plan_m / ped_plan_m if ped_plan_m > 0 else 0.0
        m_real_m = gmv_real_m / ped_real_m if ped_real_m > 0 else 0.0
        
    # Calculate Weekly accumulated actual from Projeção up to selected week
    real_accum_weekly = 0.0
    for w in range(selected_week_idx + 1):
        for client in filtered_clients:
            if metric_key == "Ticket Médio":
                # Accumulated GMV / Accumulated Orders
                acc_gmv_wk = sum(data_loader.clean_val(weekly_data[client]["GMV"]["weekly"][month_sel_en][i]) for i in range(w+1))
                acc_ped_wk = sum(data_loader.clean_val(weekly_data[client]["Pedidos"]["weekly"][month_sel_en][i]) for i in range(w+1))
                real_accum_weekly = acc_gmv_wk / acc_ped_wk if acc_ped_wk > 0 else 0.0
            else:
                real_accum_weekly += data_loader.clean_val(weekly_data[client][metric_key]["weekly"][month_sel_en][w])
                
    # Calculate Projeção pelo ritmo atual
    # Elapsed weeks count containing actual GMV data > 0
    elapsed_w_data = 0
    for w in range(selected_week_idx + 1):
        w_sum = sum(data_loader.clean_val(weekly_data[c]["GMV"]["weekly"][month_sel_en][w]) for c in weekly_data)
        if w_sum > 0:
            elapsed_w_data += 1
    K = max(1, elapsed_w_data)
    
    if metric_key == "Ticket Médio":
        # Projection of Ticket = Projected GMV / Projected Orders
        acc_gmv_sel = sum(data_loader.clean_val(weekly_data[c]["GMV"]["weekly"][month_sel_en][w]) for c in filtered_clients for w in range(selected_week_idx + 1))
        acc_ped_sel = sum(data_loader.clean_val(weekly_data[c]["Pedidos"]["weekly"][month_sel_en][w]) for c in filtered_clients for w in range(selected_week_idx + 1))
        
        proj_gmv_r = (acc_gmv_sel / K) * num_weeks
        proj_ped_r = (acc_ped_sel / K) * num_weeks
        
        proj_ritmo = proj_gmv_r / proj_ped_r if proj_ped_r > 0 else 0.0
    else:
        proj_ritmo = (real_accum_weekly / K) * num_weeks
        
    # Achievement %
    if m_plan_m > 0:
        ach_pct = proj_ritmo / m_plan_m
    else:
        ach_pct = 0.0
        
    achievements_list.append((metric_key, m_plan_m, ach_pct))

# Overall status card calculation
overall_ach = sum(ach[2] for ach in achievements_list) / 4
if overall_ach >= 0.95:
    overall_farol, overall_status, badge_class = "🟢", "Dentro da Meta", "status-green"
elif overall_ach >= 0.90:
    overall_farol, overall_status, badge_class = "🟡", "Atenção", "status-yellow"
else:
    overall_farol, overall_status, badge_class = "🔴", "Abaixo da Meta", "status-red"

with col_status:
    st.markdown(f'''
    <div class="status-badge-container">
        <div class="status-badge {badge_class}">
            STATUS DO MÊS: {overall_farol} {overall_status}
        </div>
    </div>
    ''', unsafe_allow_html=True)


# Render all blocks
for m_info in metrics_setup:
    metric_key = m_info["key"]
    
    # 1. MONTHLY CALCULATIONS (Planejamento)
    gmv_plan_m = sum(data_loader.clean_val(monthly_data[c]["GMV"]["plan"][month_sel_en]) for c in filtered_clients)
    gmv_real_m = sum(data_loader.clean_val(monthly_data[c]["GMV"]["real"][month_sel_en]) for c in filtered_clients)
    
    ped_plan_m = sum(data_loader.clean_val(monthly_data[c]["Pedidos"]["plan"][month_sel_en]) for c in filtered_clients)
    ped_real_m = sum(data_loader.clean_val(monthly_data[c]["Pedidos"]["real"][month_sel_en]) for c in filtered_clients)
    
    rec_plan_m = sum(data_loader.clean_val(monthly_data[c]["Receita Hanzo"]["plan"][month_sel_en]) for c in filtered_clients)
    rec_real_m = sum(data_loader.clean_val(monthly_data[c]["Receita Hanzo"]["real"][month_sel_en]) for c in filtered_clients)
    
    if metric_key == "GMV":
        m_plan_m = gmv_plan_m
        m_real_m = gmv_real_m
    elif metric_key == "Receita Hanzo":
        m_plan_m = rec_plan_m
        m_real_m = rec_real_m
    elif metric_key == "Pedidos":
        m_plan_m = ped_plan_m
        m_real_m = ped_real_m
    else: # Ticket Médio
        m_plan_m = gmv_plan_m / ped_plan_m if ped_plan_m > 0 else 0.0
        m_real_m = gmv_real_m / ped_real_m if ped_real_m > 0 else 0.0

    # 2. WEEKLY AND CHALLENGE CALCULATIONS (Projeção)
    # Realized weekly accumulated up to W
    real_accum_weekly = 0.0
    for w in range(selected_week_idx + 1):
        for client in filtered_clients:
            if metric_key == "Ticket Médio":
                acc_gmv_wk = sum(data_loader.clean_val(weekly_data[client]["GMV"]["weekly"][month_sel_en][i]) for i in range(w+1))
                acc_ped_wk = sum(data_loader.clean_val(weekly_data[client]["Pedidos"]["weekly"][month_sel_en][i]) for i in range(w+1))
                real_accum_weekly = acc_gmv_wk / acc_ped_wk if acc_ped_wk > 0 else 0.0
            else:
                real_accum_weekly += data_loader.clean_val(weekly_data[client][metric_key]["weekly"][month_sel_en][w])

    # Count elapsed weeks containing actual data up to selected week
    elapsed_w_data = 0
    for w in range(selected_week_idx + 1):
        w_sum = sum(data_loader.clean_val(weekly_data[c]["GMV"]["weekly"][month_sel_en][w]) for c in weekly_data)
        if w_sum > 0:
            elapsed_w_data += 1
    K = max(1, elapsed_w_data)

    if metric_key == "Ticket Médio":
        acc_gmv_sel = sum(data_loader.clean_val(weekly_data[c]["GMV"]["weekly"][month_sel_en][w]) for c in filtered_clients for w in range(selected_week_idx + 1))
        acc_ped_sel = sum(data_loader.clean_val(weekly_data[c]["Pedidos"]["weekly"][month_sel_en][w]) for c in filtered_clients for w in range(selected_week_idx + 1))
        proj_gmv_r = (acc_gmv_sel / K) * num_weeks
        proj_ped_r = (acc_ped_sel / K) * num_weeks
        proj_ritmo = proj_gmv_r / proj_ped_r if proj_ped_r > 0 else 0.0
    else:
        proj_ritmo = (real_accum_weekly / K) * num_weeks

    # Card Atingimento % and Farol
    if m_plan_m == 0:
        ach_pct_str = "Meta não definida"
        card_farol = "—"
        ach_color = "#64748B"
    else:
        ach_pct_val = proj_ritmo / m_plan_m
        ach_pct_str = f"{ach_pct_val*100:.1f}%"
        if ach_pct_val >= 0.95:
            card_farol = "🟢"
            ach_color = "#166534"
        elif ach_pct_val >= 0.90:
            card_farol = "🟡"
            ach_color = "#854D0E"
        else:
            card_farol = "🔴"
            ach_color = "#991B1B"

    # Meta do mês (from Projeção) for challenge section
    if metric_key == "Ticket Médio":
        p_gmv_tgt = sum(data_loader.clean_val(weekly_data[c]["GMV"]["plan"][month_sel_en]) for c in filtered_clients)
        p_ped_tgt = sum(data_loader.clean_val(weekly_data[c]["Pedidos"]["plan"][month_sel_en]) for c in filtered_clients)
        target_weekly_m = p_gmv_tgt / p_ped_tgt if p_ped_tgt > 0 else 0.0
    else:
        target_weekly_m = sum(data_loader.clean_val(weekly_data[c][metric_key]["plan"][month_sel_en]) for c in filtered_clients)

    # Spreadsheet Diferença and Comparativo source priority (Diferença = Real - Plan)
    # Check if we are at the latest week and can read spreadsheet values directly
    is_latest_wk = (selected_week_idx == num_weeks - 1)
    
    diff_val = None
    comp_val = None
    if is_latest_wk:
        # Load sum of client diffs from Projeção sheet
        diff_list = [weekly_data[c][metric_key]["diff"][month_sel_en] for c in filtered_clients]
        comp_list = [weekly_data[c][metric_key]["comp"][month_sel_en] for c in filtered_clients]
        
        diff_numeric = [clean_val(x) for x in diff_list if x is not None and not pd.isna(x)]
        if len(diff_numeric) == len(filtered_clients):
            # Target challenge diff is Plan - Realized, which is negative of spreadsheet diff
            diff_val = -sum(diff_numeric)
            
        comp_numeric = [clean_val(x) for x in comp_list if x is not None and not pd.isna(x)]
        if len(comp_numeric) == len(filtered_clients) and target_weekly_m > 0:
            comp_val = (real_accum_weekly / target_weekly_m) * 100

    # Recalculate fallback
    if diff_val is None:
        diff_val = target_weekly_m - real_accum_weekly
    if comp_val is None:
        comp_val = (real_accum_weekly / target_weekly_m) * 100 if target_weekly_m > 0 else 0.0

    # Calculate remaining weeks dynamically based on columns left
    remaining_weeks = len(weekly_cols) - (selected_week_idx + 1)

    # Challenge card display conditionals
    if target_weekly_m == 0:
        challenge_msg = "Meta não definida"
        req_avg_str = "0"
        challenge_status = "—"
        challenge_color = "#64748B"
    elif diff_val <= 0:
        challenge_msg = "Meta já atingida"
        req_avg_str = "0"
        challenge_status = "🟢"
        challenge_color = "#166534"
    else:
        challenge_msg = f"Faltam {m_info['fmt'](diff_val)} para atingir a meta."
        if remaining_weeks > 0:
            req_avg_val = diff_val / remaining_weeks
            req_avg_str = m_info["fmt"](req_avg_val)
            challenge_status = "🟡"
            challenge_color = "#854D0E"
        else:
            # Final week reached
            challenge_msg = "Mês encerrado abaixo da meta"
            req_avg_str = "N/A"
            challenge_status = "🔴"
            challenge_color = "#991B1B"

    # Render on layout slot
    with m_info["slot"]:
        # MONTHLY KPI CARD
        st.markdown(f'''
        <div class="cockpit-card">
            <div class="card-title">MENSAL — {m_info["title"]}</div>
            <div class="kpi-main-val">{m_info["fmt"](m_real_m)}</div>
            <div style="display:flex; justify-content:space-between; margin-top:0.5rem;">
                <div>
                    <div class="kpi-sub-label">PLANEJADO</div>
                    <div class="kpi-sub-val">{m_info["fmt"](m_plan_m)}</div>
                </div>
                <div>
                    <div class="kpi-sub-label">PROJEÇÃO PELO RITMO ATUAL</div>
                    <div class="kpi-sub-val">{m_info["fmt"](proj_ritmo)}</div>
                </div>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.5rem; border-top:1px solid #F1F5F9; padding-top:0.5rem;">
                <span style="font-size:0.85rem; font-weight:700; color:#475569;">Atingimento Projetado:</span>
                <span style="font-size:0.95rem; font-weight:800; color:{ach_color};">
                    {ach_pct_str} <span class="kpi-light">{card_farol}</span>
                </span>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        st.markdown('<br>', unsafe_allow_html=True)
        
        # PREPARE CLIENTS DATA FOR RANKINGS
        client_ranks = []
        for client in filtered_clients:
            # Weekly actual
            if metric_key == "Ticket Médio":
                wk_gmv = data_loader.clean_val(weekly_data[client]["GMV"]["weekly"][month_sel_en][selected_week_idx])
                wk_ped = data_loader.clean_val(weekly_data[client]["Pedidos"]["weekly"][month_sel_en][selected_week_idx])
                # Exclude from Ticket Médio rankings if selected-week orders is 0 (prevents division by zero)
                if wk_ped == 0:
                    continue
                val_wk = wk_gmv / wk_ped
            else:
                val_wk = data_loader.clean_val(weekly_data[client][metric_key]["weekly"][month_sel_en][selected_week_idx])
                
            # Accumulated actual
            if metric_key == "Ticket Médio":
                acc_gmv = sum(data_loader.clean_val(weekly_data[client]["GMV"]["weekly"][month_sel_en][i]) for i in range(selected_week_idx + 1))
                acc_ped = sum(data_loader.clean_val(weekly_data[client]["Pedidos"]["weekly"][month_sel_en][i]) for i in range(selected_week_idx + 1))
                val_accum = acc_gmv / acc_ped if acc_ped > 0 else 0.0
            else:
                val_accum = sum(data_loader.clean_val(weekly_data[client][metric_key]["weekly"][month_sel_en][i]) for i in range(selected_week_idx + 1))
                
            # Planned prorated target
            target_cl = data_loader.clean_val(weekly_data[client][metric_key]["plan"][month_sel_en])
            # Load weights row from active sheet
            weights_row = df_proj.iloc[3]
            weekly_weights = [data_loader.clean_val(weights_row[col]) for col in weekly_cols]
            sum_weights = sum(weekly_weights)
            if sum_weights == 0:
                weekly_weights = [1.0 / len(weekly_cols)] * len(weekly_cols)
            else:
                weekly_weights = [w / sum_weights for w in weekly_weights]
            prorated_target_cl = target_cl * sum(weekly_weights[:selected_week_idx + 1])
            
            # Achievement and Farol
            is_zero_zero = (prorated_target_cl == 0 and val_accum == 0)
            if is_zero_zero:
                cl_ach_str = "- %"
                cl_farol = "—"
            elif target_cl == 0:
                cl_ach_str = "- %"
                cl_farol = "—"
            else:
                if prorated_target_cl > 0:
                    cl_ach_val = val_accum / prorated_target_cl
                    cl_ach_str = f"{cl_ach_val*100:.1f}%"
                    if cl_ach_val >= 0.95:
                        cl_farol = "🟢"
                    elif cl_ach_val >= 0.90:
                        cl_farol = "🟡"
                    else:
                        cl_farol = "🔴"
                else:
                    cl_ach_str = "100,0%"
                    cl_farol = "🟢"
                    
            client_ranks.append({
                "client": client,
                "wk_val": val_wk,
                "accum": val_accum,
                "ach_str": cl_ach_str,
                "farol": cl_farol
            })
            
        # TOP 5 da Semana
        sorted_top = sorted(client_ranks, key=lambda x: (-x["wk_val"], x["client"]))
        
        st.markdown(f'''
        <div class="cockpit-card">
            <div class="card-title">Quem Puxou o Resultado? (Top 5 da Semana)</div>
            <table class="compact-table">
                <thead>
                    <tr>
                        <th>Rk</th>
                        <th>Cliente</th>
                        <th>Real da Semana</th>
                        <th>Real Acumulado</th>
                        <th>Atingimento</th>
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
        
        # BOTTOM 5 da Semana (Positive performers only)
        # Filters: val_wk > 0, accum > 0, non-blank name
        filtered_bottom = [r for r in client_ranks if r["wk_val"] > 0 and r["accum"] > 0 and r["client"].strip() != ""]
        sorted_bottom = sorted(filtered_bottom, key=lambda x: (x["wk_val"], x["client"]))
        
        st.markdown(f'''
        <div class="cockpit-card">
            <div class="card-title">Quem Prejudicou o Resultado? (Bottom 5 da Semana)</div>
            <table class="compact-table">
                <thead>
                    <tr>
                        <th>Rk</th>
                        <th>Cliente</th>
                        <th>Real da Semana</th>
                        <th>Real Acumulado</th>
                        <th>Atingimento</th>
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
        
        # DESAFIO PARA A META CARD
        st.markdown(f'''
        <div class="cockpit-card">
            <div class="card-title">Desafio para a Meta (Semanal)</div>
            <div style="font-size:1.15rem; font-weight:800; color:{challenge_color}; margin-bottom:0.75rem;">
                {challenge_status} {challenge_msg}
            </div>
            <div style="display:flex; justify-content:space-between;">
                <div>
                    <div class="kpi-sub-label">Semanas Restantes</div>
                    <div class="kpi-sub-val" style="font-size:1.1rem;">{remaining_weeks}</div>
                </div>
                <div>
                    <div class="kpi-sub-label">Necessidade Média por Semana Restante</div>
                    <div class="kpi-sub-val" style="font-size:1.1rem; color:{challenge_color};">{req_avg_str}</div>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        st.markdown('<br>', unsafe_allow_html=True)
        
        # MONTH-OVER-MONTH EVOLUTION CHART (Planejamento)
        # Pull values for all 12 months
        plan_MoM = []
        real_MoM = []
        months_names_pt = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        
        for m in EN_MONTHS:
            if m in m_map_pl:
                cl_plan = sum(data_loader.clean_val(monthly_data[c][metric_key]["plan"][m]) for c in filtered_clients)
                cl_real = sum(data_loader.clean_val(monthly_data[c][metric_key]["real"][m]) for c in filtered_clients)
                
                # Special average ticket logic for MoM totals
                if metric_key == "Ticket Médio":
                    g_plan = sum(data_loader.clean_val(monthly_data[c]["GMV"]["plan"][m]) for c in filtered_clients)
                    p_plan = sum(data_loader.clean_val(monthly_data[c]["Pedidos"]["plan"][m]) for c in filtered_clients)
                    cl_plan = g_plan / p_plan if p_plan > 0 else 0.0
                    
                    g_real = sum(data_loader.clean_val(monthly_data[c]["GMV"]["real"][m]) for c in filtered_clients)
                    p_real = sum(data_loader.clean_val(monthly_data[c]["Pedidos"]["real"][m]) for c in filtered_clients)
                    cl_real = g_real / p_real if p_real > 0 else 0.0
            else:
                cl_plan = 0.0
                cl_real = 0.0
                
            plan_MoM.append(cl_plan)
            # Only append real value if it represents a past month or current month containing data
            if cl_real > 0 or m == month_sel_en:
                real_MoM.append(cl_real)
            else:
                real_MoM.append(None)
                
        # Draw plotly line chart MoM
        fig = go.Figure()
        
        # Planejado
        fig.add_trace(go.Scatter(
            x=months_names_pt,
            y=plan_MoM,
            name="Planejado",
            line=dict(color="#002060", width=2.5)
        ))
        
        # Realizado
        fig.add_trace(go.Scatter(
            x=months_names_pt,
            y=real_MoM,
            name="Realizado",
            line=dict(color="#166534", width=2.5),
            connectgaps=False
        ))
        
        # Visually highlight selected month with a large marker
        selected_month_idx = EN_MONTHS.index(month_sel_en)
        selected_month_name = PT_MONTHS[selected_month_idx]
        selected_month_val = real_MoM[selected_month_idx] if real_MoM[selected_month_idx] is not None else plan_MoM[selected_month_idx]
        
        fig.add_trace(go.Scatter(
            x=[selected_month_name],
            y=[selected_month_val],
            name="Mês Selecionado",
            marker=dict(color="#D97706", size=11, line=dict(color="#FFFFFF", width=2)),
            showlegend=True
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
            <div class="card-title">Evolução Mensal 2026 (Consolidado)</div>
        ''', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<br><br>', unsafe_allow_html=True)
