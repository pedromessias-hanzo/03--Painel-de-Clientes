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

# Load CSS Stylesheet for professional BI dashboard look
st.markdown("""
<style>
    /* Premium Board Dashboard Styling */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FFFFFF;
        color: #0F172A;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Executive Header */
    .cockpit-header {
        border-bottom: 3px solid #002060;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    .cockpit-title {
        color: #002060;
        font-size: 2.4rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .cockpit-subtitle {
        color: #64748B;
        font-size: 1rem;
        margin-top: 0.2rem;
    }
    
    /* Top Filters Bar styling */
    div[data-testid="stHorizontalBlock"] {
        margin-bottom: 0.5rem;
    }
    
    /* Large Status Badges */
    .status-badge-container {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        justify-content: center;
        height: 100%;
    }
    .status-badge {
        padding: 0.65rem 1.25rem;
        border-radius: 6px;
        font-weight: 700;
        font-size: 1rem;
        text-align: center;
        border: 1px solid transparent;
        display: inline-block;
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
    .status-neutral {
        background-color: #F1F5F9;
        color: #475569;
        border-color: #CBD5E1;
    }
    
    /* KPI Metric Cards */
    .kpi-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.25rem;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05);
    }
    .kpi-card-title {
        color: #64748B;
        font-size: 0.9rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    .kpi-main-val {
        font-size: 2.1rem;
        font-weight: 800;
        color: #002060;
        line-height: 1.1;
    }
    .kpi-sub-row {
        display: flex;
        justify-content: space-between;
        margin-top: 0.75rem;
        border-top: 1px solid #E2E8F0;
        padding-top: 0.5rem;
    }
    .kpi-sub-label {
        font-size: 0.75rem;
        color: #64748B;
        font-weight: 600;
    }
    .kpi-sub-val {
        font-size: 0.85rem;
        font-weight: 700;
        color: #0F172A;
    }
    .kpi-light {
        font-size: 0.95rem;
        display: inline-block;
        vertical-align: middle;
        margin-left: 0.25rem;
    }
    
    /* Quadrant Container card */
    .quadrant-container {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05);
        margin-bottom: 1.5rem;
    }
    .quadrant-title {
        color: #002060;
        font-size: 1.3rem;
        font-weight: 800;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* Responsive HTML Table styling with font size 12-13px */
    .table-container {
        width: 100%;
        overflow-x: auto;
        margin-bottom: 0.75rem;
    }
    .compact-table {
        width: 100%;
        table-layout: fixed;
        border-collapse: collapse;
        font-size: 12.5px !important;
    }
    .compact-table td {
        padding: 5px 0.5rem;
        height: 30px;
        max-height: 30px;
        border-bottom: 1px solid #F1F5F9;
        color: #0F172A;
    }
    .compact-table tr:hover {
        background-color: #F1F5F9;
    }
    
    /* Specific column alignments classes */
    .col-rank {
        text-align: center;
    }
    .col-client {
        text-align: left;
        white-space: normal;
        word-wrap: break-word;
    }
    .col-curr {
        text-align: right;
        white-space: nowrap;
    }
    .col-share {
        text-align: right;
        white-space: nowrap;
    }
    
    /* Highlight Rank 1 */
    .row-rank1 {
        background-color: #F0FDF4 !important;
        font-weight: 700 !important;
    }
    
    /* Table headers text color */
    .table-section-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #475569;
        margin-top: 0.5rem;
        margin-bottom: 0.4rem;
        border-left: 3px solid #64748B;
        padding-left: 0.5rem;
    }
    
    /* Hide default streamlit items */
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
        if GOOGLE_DRIVE_FILE_ID and GOOGLE_DRIVE_FILE_ID != "paste_file_id_here" and GOOGLE_DRIVE_FILE_ID.strip() != "":
            file_id = GOOGLE_DRIVE_FILE_ID.strip()
            url = f"https://drive.google.com/uc?export=download&id={file_id}"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            content = response.content
            
            if b"google.com" in content[:100] and b"html" in content[:100].lower():
                url_export = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
                response = requests.get(url_export, headers=headers, timeout=30)
                response.raise_for_status()
                content = response.content
                
            data_bytes = io.BytesIO(content)
            xl = pd.ExcelFile(data_bytes)
            
            last_modified = datetime.datetime.now()
            if "Last-Modified" in response.headers:
                try:
                    last_modified = email.utils.parsedate_to_datetime(response.headers["Last-Modified"])
                except:
                    pass
        else:
            excel_path = os.path.join(os.path.dirname(__file__), "Planejamento 2026.xlsx")
            if not os.path.exists(excel_path):
                raise FileNotFoundError(
                    "Planilha local 'Planejamento 2026.xlsx' não encontrada e GOOGLE_DRIVE_FILE_ID não está configurado."
                )
            xl = pd.ExcelFile(excel_path)
            mtime = os.path.getmtime(excel_path)
            last_modified = datetime.datetime.fromtimestamp(mtime)
            
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

# Parse Data
overview_data, monthly_data, weekly_data, clients_metadata = data_loader.load_data(sheets_data)

# Retrieve active sheet to map weeks dynamically
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

# Find available months (months with weekly monitoring)
available_months_en = [m for m in EN_MONTHS if m in m_map_proj and len(m_map_proj[m]["weekly"]) > 0]
available_months_pt = [PT_MONTH_DISPLAY[m] for m in available_months_en]

# Month selection filter contains Jan-Dec chronologically
month_sel_pt = st.selectbox(
    "Mês",
    PT_MONTHS,
    index=PT_MONTHS.index("Julho") # Default July
)
month_sel_en = PT_TO_EN[month_sel_pt]

# Determine week options dynamically for June onward (if weekly data exists)
has_weeks_data = (month_sel_en in m_map_proj and len(m_map_proj[month_sel_en]["weekly"]) > 0)
weekly_cols = m_map_proj[month_sel_en]["weekly"] if has_weeks_data else []
num_weeks = len(weekly_cols)
week_options = [f"Semana {i+1}" for i in range(num_weeks)]

# Determine default week (latest week in that month with actuals > 0)
default_week_idx = 0
if has_weeks_data:
    for w_idx in reversed(range(num_weeks)):
        w_sum = sum(data_loader.clean_val(weekly_data[c]["GMV"]["weekly"][month_sel_en][w_idx]) for c in weekly_data)
        if w_sum > 0:
            default_week_idx = w_idx
            break

# Render conditional Week Filter
col_w_filt, col_mode_filt, col_g_filt, col_ref = st.columns([1.5, 2, 2, 1])

with col_w_filt:
    if has_weeks_data:
        week_sel_label = st.selectbox(
            "Semana",
            week_options,
            index=default_week_idx
        )
        selected_week_idx = week_options.index(week_sel_label)
    else:
        st.selectbox("Semana", ["Sem divisão semanal"], disabled=True)
        selected_week_idx = 0

# Determine mode options dynamically
if has_weeks_data:
    mode_options = ["📅 Selected Week", "📈 Month To Date (MTD)", "🏆 Year To Date (YTD)"]
    default_mode_idx = 1 # MTD
else:
    mode_options = ["📈 Consolidado do Mês", "🏆 Year To Date (YTD)"]
    default_mode_idx = 0 # Consolidado do Mês

with col_mode_filt:
    viz_mode = st.selectbox(
        "Modo de Visualização",
        mode_options,
        index=default_mode_idx
    )

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

# Filter clients list based on group selection
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

# Months up to selected for YTD calculations
months_up_to = EN_MONTHS[:EN_MONTHS.index(month_sel_en) + 1]

# Global metrics aggregations helper
def get_kpi_metrics(metric_key):
    actual = 0.0
    planned = 0.0
    projection = 0.0
    
    # 1. ACTUAL & PLANNED VALUE (based on Mode)
    if "YTD" in viz_mode:
        for m in months_up_to:
            for c in filtered_clients:
                actual += data_loader.clean_val(monthly_data[c][metric_key]["real"][m])
                planned += data_loader.clean_val(monthly_data[c][metric_key]["plan"][m])
                
        # Projection rhythm YTD = (YTD_Actual / elapsed_months) * 12
        elapsed_m = 0
        for m in months_up_to:
            m_sum = sum(data_loader.clean_val(monthly_data[c]["GMV"]["real"][m]) for c in weekly_data)
            if m_sum > 0:
                elapsed_m += 1
        K_m = max(1, elapsed_m)
        projection = (actual / K_m) * 12
    else:
        m_plan_month = sum(data_loader.clean_val(monthly_data[c][metric_key]["plan"][month_sel_en]) for c in filtered_clients)
        m_real_month = sum(data_loader.clean_val(monthly_data[c][metric_key]["real"][month_sel_en]) for c in filtered_clients)
        
        if not has_weeks_data:
            actual = m_real_month
            planned = m_plan_month
            projection = m_real_month
        else:
            weekly_cols_active = m_map_proj[month_sel_en]["weekly"]
            weights_row = df_proj.iloc[3]
            weekly_weights = [data_loader.clean_val(weights_row[col]) for col in weekly_cols_active]
            sum_weights = sum(weekly_weights)
            if sum_weights == 0:
                weekly_weights = [1.0 / len(weekly_cols_active)] * len(weekly_cols_active)
            else:
                weekly_weights = [w / sum_weights for w in weekly_weights]
                
            elapsed_w = 0
            for w in range(selected_week_idx + 1):
                w_sum = sum(data_loader.clean_val(weekly_data[c]["GMV"]["weekly"][month_sel_en][w]) for c in weekly_data)
                if w_sum > 0:
                    elapsed_w += 1
            K_w = max(1, elapsed_w)
            
            if "Week" in viz_mode:
                for c in filtered_clients:
                    actual += data_loader.clean_val(weekly_data[c][metric_key]["weekly"][month_sel_en][selected_week_idx])
                planned = m_plan_month * weekly_weights[selected_week_idx]
                projection = (actual / 1) * len(weekly_cols_active)
            else:
                for w in range(selected_week_idx + 1):
                    for c in filtered_clients:
                        actual += data_loader.clean_val(weekly_data[c][metric_key]["weekly"][month_sel_en][w])
                planned = m_plan_month * sum(weekly_weights[:selected_week_idx + 1])
                projection = (actual / K_w) * len(weekly_cols_active)
            
    if metric_key == "Ticket Médio":
        actual_gmv, planned_gmv, proj_gmv = get_kpi_metrics("GMV")
        actual_ped, planned_ped, proj_ped = get_kpi_metrics("Pedidos")
        
        actual = actual_gmv / actual_ped if actual_ped > 0 else 0.0
        planned = planned_gmv / planned_ped if planned_ped > 0 else 0.0
        projection = proj_gmv / proj_ped if proj_ped > 0 else 0.0
        
    return actual, planned, projection

# 2. CALCULATION OF THE 4 CORE KPI VALUES
gmv_act, gmv_pla, gmv_prj = get_kpi_metrics("GMV")
rec_act, rec_pla, rec_prj = get_kpi_metrics("Receita Hanzo")
ped_act, ped_pla, ped_prj = get_kpi_metrics("Pedidos")
tkt_act, tkt_pla, tkt_prj = get_kpi_metrics("Ticket Médio")

kpis_values = {
    "GMV": {"actual": gmv_act, "plan": gmv_pla, "proj": gmv_prj},
    "Receita Hanzo": {"actual": rec_act, "plan": rec_pla, "proj": rec_prj},
    "Pedidos": {"actual": ped_act, "plan": ped_pla, "proj": ped_prj},
    "Ticket Médio": {"actual": tkt_act, "plan": tkt_pla, "proj": tkt_prj}
}

# Calculate overall status badge based on achievements
kpi_achievements = []
for k, v in kpis_values.items():
    if v["plan"] > 0:
        ach = v["proj"] / v["plan"] if "YTD" in viz_mode or "MTD" in viz_mode or not has_weeks_data else v["actual"] / v["plan"]
    else:
        ach = 0.0
    kpi_achievements.append(ach)

avg_kpi_ach = sum(kpi_achievements) / 4
if avg_kpi_ach >= 0.95:
    overall_farol, overall_status, badge_class = "🟢", "Dentro da Meta", "status-green"
elif avg_kpi_ach >= 0.90:
    overall_farol, overall_status, badge_class = "🟡", "Atenção", "status-yellow"
else:
    overall_farol, overall_status, badge_class = "🔴", "Abaixo da Meta", "status-red"

# Top KPIs Row
col_c1, col_c2, col_c3, col_c4 = st.columns(4)

kpis_setup = [
    {"col": col_c1, "title": "GMV COMERCIAL", "key": "GMV", "fmt": fmt_currency},
    {"col": col_c2, "title": "FATURAMENTO (RECEITA)", "key": "Receita Hanzo", "fmt": fmt_currency},
    {"col": col_c3, "title": "PEDIDOS ENTREGUES", "key": "Pedidos", "fmt": fmt_qty},
    {"col": col_c4, "title": "TICKET MÉDIO", "key": "Ticket Médio", "fmt": fmt_currency}
]

for card in kpis_setup:
    k_key = card["key"]
    c_vals = kpis_values[k_key]
    
    if c_vals["plan"] == 0:
        gap_pct_str = "Meta não definida"
        card_farol = "—"
        card_color = "#64748B"
    else:
        gap_val = ((c_vals["actual"] - c_vals["plan"]) / c_vals["plan"]) * 100
        gap_pct_str = f"{gap_val:+.1f}%".replace(".", ",")
        
        ach_pct = c_vals["proj"] / c_vals["plan"] if "YTD" in viz_mode or "MTD" in viz_mode or not has_weeks_data else c_vals["actual"] / c_vals["plan"]
        if ach_pct >= 0.95:
            card_farol = "🟢"
            card_color = "#166534"
        elif ach_pct >= 0.90:
            card_farol = "🟡"
            card_color = "#854D0E"
        else:
            card_farol = "🔴"
            card_color = "#991B1B"
            
    with card["col"]:
        st.markdown(f'''
        <div class="kpi-card">
            <div class="kpi-card-title">{card["title"]}</div>
            <div class="kpi-main-val" style="font-size:30px !important;">{card["fmt"](c_vals["actual"])}</div>
            <div class="kpi-sub-row">
                <div>
                    <div class="kpi-sub-label">PLANEJADO</div>
                    <div class="kpi-sub-val">{card["fmt"](c_vals["plan"])}</div>
                </div>
                <div>
                    <div class="kpi-sub-label">PROJEÇÃO RITMO ATUAL</div>
                    <div class="kpi-sub-val">{card["fmt"](c_vals["proj"])}</div>
                </div>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.4rem; border-top:1px solid #E2E8F0; padding-top:0.4rem;">
                <span style="font-size:0.8rem; font-weight:700; color:#475569;">Desvio Real/Plan:</span>
                <span style="font-size:0.85rem; font-weight:800; color:{card_color};">
                    {gap_pct_str} <span class="kpi-light">{card_farol}</span>
                </span>
            </div>
        </div>
        ''', unsafe_allow_html=True)

st.markdown('<br>', unsafe_allow_html=True)

# Inform discretely if month has only consolidated monthly data
if not has_weeks_data:
    st.info("Este mês possui apenas dados consolidados mensais.")

# 2x2 Quadrants Layout
row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

quadrants_setup = [
    {"slot": row1_col1, "title": "GMV COMERCIAL", "key": "GMV", "fmt": fmt_currency, "is_ticket": False},
    {"slot": row1_col2, "title": "FATURAMENTO (RECEITA)", "key": "Receita Hanzo", "fmt": fmt_currency, "is_ticket": False},
    {"slot": row2_col1, "title": "PEDIDOS ENTREGUES", "key": "Pedidos", "fmt": fmt_qty, "is_ticket": False},
    {"slot": row2_col2, "title": "TICKET MÉDIO", "key": "Ticket Médio", "fmt": fmt_currency, "is_ticket": True}
]

total_weeks_sel = len(m_map_proj[month_sel_en]["weekly"]) if month_sel_en in m_map_proj else 0

for quad in quadrants_setup:
    q_key = quad["key"]
    
    # 1. EXTRACT CLIENT RANKINGS DATA
    client_data_list = []
    has_client_level_data = True
    
    if "YTD" in viz_mode:
        total_ytd_real = sum(data_loader.clean_val(monthly_data[c][q_key]["real"][m]) for c in filtered_clients for m in months_up_to)
        if total_ytd_real == 0:
            has_client_level_data = False
        else:
            for client in filtered_clients:
                curr_val = sum(data_loader.clean_val(monthly_data[client][q_key]["real"][m]) for m in months_up_to)
                accum_val = sum(data_loader.clean_val(monthly_data[client][q_key]["plan"][m]) for m in months_up_to)
                orders_count = sum(data_loader.clean_val(monthly_data[client]["Pedidos"]["real"][m]) for m in months_up_to)
                
                if quad["is_ticket"]:
                    acc_gmv = sum(data_loader.clean_val(monthly_data[client]["GMV"]["real"][m]) for m in months_up_to)
                    curr_val = acc_gmv / orders_count if orders_count > 0 else 0.0
                    
                    acc_gmv_plan = sum(data_loader.clean_val(monthly_data[client]["GMV"]["plan"][m]) for m in months_up_to)
                    acc_ped_plan = sum(data_loader.clean_val(monthly_data[client]["Pedidos"]["plan"][m]) for m in months_up_to)
                    accum_val = acc_gmv_plan / acc_ped_plan if acc_ped_plan > 0 else 0.0
                    
                client_data_list.append({
                    "client": client, "curr": curr_val, "accum": accum_val, "orders": orders_count
                })
    else:
        if not has_weeks_data:
            total_real_month = sum(data_loader.clean_val(monthly_data[c][q_key]["real"][month_sel_en]) for c in filtered_clients)
            if total_real_month == 0:
                has_client_level_data = False
            else:
                for client in filtered_clients:
                    curr_val = data_loader.clean_val(monthly_data[client][q_key]["real"][month_sel_en])
                    accum_val = data_loader.clean_val(monthly_data[client][q_key]["plan"][month_sel_en])
                    orders_count = data_loader.clean_val(monthly_data[client]["Pedidos"]["real"][month_sel_en])
                    
                    if quad["is_ticket"]:
                        acc_gmv = data_loader.clean_val(monthly_data[client]["GMV"]["real"][month_sel_en])
                        curr_val = acc_gmv / orders_count if orders_count > 0 else 0.0
                        
                        acc_gmv_plan = data_loader.clean_val(monthly_data[client]["GMV"]["plan"][month_sel_en])
                        acc_ped_plan = data_loader.clean_val(monthly_data[client]["Pedidos"]["plan"][month_sel_en])
                        accum_val = acc_gmv_plan / acc_ped_plan if acc_ped_plan > 0 else 0.0
                        
                    client_data_list.append({
                        "client": client, "curr": curr_val, "accum": accum_val, "orders": orders_count
                    })
        else:
            for client in filtered_clients:
                target_m = data_loader.clean_val(weekly_data[client][q_key]["plan"][month_sel_en])
                
                weights_row = df_proj.iloc[3]
                weekly_weights = [data_loader.clean_val(weights_row[col]) for col in weekly_cols]
                sum_weights = sum(weekly_weights)
                if sum_weights == 0:
                    weekly_weights = [1.0 / len(weekly_cols)] * len(weekly_cols)
                else:
                    weekly_weights = [w / sum_weights for w in weekly_weights]
                    
                if "Week" in viz_mode:
                    curr_val = data_loader.clean_val(weekly_data[client][q_key]["weekly"][month_sel_en][selected_week_idx])
                    accum_val = sum(data_loader.clean_val(weekly_data[client][q_key]["weekly"][month_sel_en][w]) for w in range(selected_week_idx + 1))
                    orders_count = data_loader.clean_val(weekly_data[client]["Pedidos"]["weekly"][month_sel_en][selected_week_idx])
                    
                    if quad["is_ticket"]:
                        wk_gmv = data_loader.clean_val(weekly_data[client]["GMV"]["weekly"][month_sel_en][selected_week_idx])
                        if orders_count == 0:
                            continue
                        curr_val = wk_gmv / orders_count
                        
                        acc_gmv_wk = sum(data_loader.clean_val(weekly_data[client]["GMV"]["weekly"][month_sel_en][w]) for w in range(selected_week_idx + 1))
                        acc_ped_wk = sum(data_loader.clean_val(weekly_data[client]["Pedidos"]["weekly"][month_sel_en][w]) for w in range(selected_week_idx + 1))
                        accum_val = acc_gmv_wk / acc_ped_wk if acc_ped_wk > 0 else 0.0
                else:
                    curr_val = sum(data_loader.clean_val(weekly_data[client][q_key]["weekly"][month_sel_en][w]) for w in range(selected_week_idx + 1))
                    accum_val = sum(data_loader.clean_val(monthly_data[client][q_key]["real"][m]) for m in months_up_to)
                    orders_count = sum(data_loader.clean_val(weekly_data[client]["Pedidos"]["weekly"][month_sel_en][w]) for w in range(selected_week_idx + 1))
                    
                    if quad["is_ticket"]:
                        acc_gmv_wk = sum(data_loader.clean_val(weekly_data[client]["GMV"]["weekly"][month_sel_en][w]) for w in range(selected_week_idx + 1))
                        if orders_count == 0:
                            continue
                        curr_val = acc_gmv_wk / orders_count
                        
                        ytd_gmv = sum(data_loader.clean_val(monthly_data[client]["GMV"]["real"][m]) for m in months_up_to)
                        ytd_ped = sum(data_loader.clean_val(monthly_data[client]["Pedidos"]["real"][m]) for m in months_up_to)
                        accum_val = ytd_gmv / ytd_ped if ytd_ped > 0 else 0.0
                        
                client_data_list.append({
                    "client": client, "curr": curr_val, "accum": accum_val, "orders": orders_count
                })

    group_curr_total = sum(c["curr"] for c in client_data_list)
    sorted_top = sorted(client_data_list, key=lambda x: (-x["curr"], x["client"]))
    
    filtered_bottom = [r for r in client_data_list if r["curr"] > 0 and r["accum"] > 0 and r["client"].strip() != ""]
    sorted_bottom = sorted(filtered_bottom, key=lambda x: (x["curr"], x["client"]))

    # 2. CHALLENGE CARD METRICS PREPARATION (Projeção)
    if "YTD" in viz_mode:
        if quad["is_ticket"]:
            g_tgt = sum(data_loader.clean_val(monthly_data[c]["GMV"]["plan"][m]) for c in filtered_clients for m in EN_MONTHS)
            p_tgt = sum(data_loader.clean_val(monthly_data[c]["Pedidos"]["plan"][m]) for c in filtered_clients for m in EN_MONTHS)
            target_val = g_tgt / p_tgt if p_tgt > 0 else 0.0
        else:
            target_val = sum(data_loader.clean_val(monthly_data[c][q_key]["plan"][m]) for c in filtered_clients for m in EN_MONTHS)
        accum_challenge = kpis_values[q_key]["actual"]
    else:
        if quad["is_ticket"]:
            g_tgt = sum(data_loader.clean_val(weekly_data[c]["GMV"]["plan"][month_sel_en]) for c in filtered_clients)
            p_tgt = sum(data_loader.clean_val(weekly_data[c]["Pedidos"]["plan"][month_sel_en]) for c in filtered_clients)
            target_val = g_tgt / p_tgt if p_tgt > 0 else 0.0
        else:
            target_val = sum(data_loader.clean_val(weekly_data[c][q_key]["plan"][month_sel_en]) for c in filtered_clients)
        accum_challenge = kpis_values[q_key]["actual"]

    diff_challenge = None
    is_latest_wk = (selected_week_idx == len(weekly_cols) - 1)
    
    if is_latest_wk and "YTD" not in viz_mode and has_weeks_data:
        diff_list = [weekly_data[c][q_key]["diff"][month_sel_en] for c in filtered_clients]
        diff_numeric = [clean_val(x) for x in diff_list if x is not None and not pd.isna(x)]
        if len(diff_numeric) == len(filtered_clients):
            diff_challenge = -sum(diff_numeric)
            
    if diff_challenge is None:
        diff_challenge = target_val - accum_challenge

    if "YTD" in viz_mode:
        remaining_months_count = 11 - EN_MONTHS.index(month_sel_en)
        weeks_left_curr = len(weekly_cols) - (selected_week_idx + 1) if has_weeks_data else 0
        rem_weeks = weeks_left_curr + (4 * remaining_months_count)
    else:
        rem_weeks = len(weekly_cols) - (selected_week_idx + 1) if has_weeks_data else 0

    if target_val == 0:
        challenge_msg = "Meta não definida"
        req_avg_str = "0"
        challenge_status = "—"
        challenge_color = "#64748B"
        badge_theme = "status-neutral"
    elif diff_challenge <= 0:
        challenge_msg = "Meta já atingida"
        req_avg_str = "0"
        challenge_status = "🟢"
        challenge_color = "#166534"
        badge_theme = "status-green"
    else:
        challenge_msg = f"Faltam {quad['fmt'](diff_challenge)} para atingir a meta."
        if rem_weeks > 0:
            req_avg_val = diff_challenge / rem_weeks
            req_avg_str = quad["fmt"](req_avg_val)
            challenge_status = "🟡"
            challenge_color = "#854D0E"
            badge_theme = "status-yellow"
        else:
            challenge_msg = "Mês encerrado abaixo da meta" if "YTD" not in viz_mode else "Ano encerrado abaixo da meta"
            req_avg_str = "N/A"
            challenge_status = "🔴"
            challenge_color = "#991B1B"
            badge_theme = "status-red"

    # Render inside Slot Card
    with quad["slot"]:
        st.markdown(f'<div class="quadrant-container">', unsafe_allow_html=True)
        st.markdown(f'<div class="quadrant-title">{quad["title"]}</div>', unsafe_allow_html=True)
        
        # 1. TOP 5 CLIENTS TABLE
        tbl_top_title = "🏆 Top 5 Clientes do Mês" if not has_weeks_data else "🏆 Top 5 Clients"
        st.markdown(f'<div class="table-section-title">{tbl_top_title}</div>', unsafe_allow_html=True)
        
        if not has_client_level_data:
            msg_unavail = "Ranking YTD por client indisponível para este período." if "YTD" in viz_mode else "Ranking por cliente indisponível para este mês."
            st.markdown(f'<div style="text-align:center; color:#64748B; font-size:13px; margin: 0.5rem 0;">{msg_unavail}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'''
            <div class="table-container">
                <table class="compact-table">
                    <colgroup>
                        <col style="width: 8%;">
                        <col style="width: 54%;">
                        <col style="width: 24%;">
                        <col style="width: 14%;">
                    </colgroup>
                    <tbody>
            ''', unsafe_allow_html=True)
            
            for idx, row in enumerate(sorted_top[:5]):
                share_str = f"{(row['curr']/group_curr_total)*100:.1f}%" if group_curr_total > 0 else "0.0%"
                row_class = "row-rank1" if idx == 0 else ""
                st.markdown(f'''
                        <tr class="{row_class}">
                            <td class="col-rank"><b>{idx+1}</b></td>
                            <td class="col-client">{row["client"]}</td>
                            <td class="col-curr">{quad["fmt"](row["curr"])}</td>
                            <td class="col-share">{share_str}</td>
                        </tr>
                ''', unsafe_allow_html=True)
            st.markdown('</tbody></table></div>', unsafe_allow_html=True)
            
        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        
        # 2. BOTTOM 5 CLIENTS TABLE
        tbl_bot_title = "📉 Bottom 5 Clientes com Movimentação no Mês" if not has_weeks_data else "📉 Bottom 5 Clients with Activity"
        st.markdown(f'<div class="table-section-title">{tbl_bot_title}</div>', unsafe_allow_html=True)
        
        if not has_client_level_data:
            msg_unavail = "Ranking YTD por client indisponível para este período." if "YTD" in viz_mode else "Ranking por cliente indisponível para este mês."
            st.markdown(f'<div style="text-align:center; color:#64748B; font-size:13px; margin: 0.5rem 0;">{msg_unavail}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'''
            <div class="table-container">
                <table class="compact-table">
                    <colgroup>
                        <col style="width: 8%;">
                        <col style="width: 54%;">
                        <col style="width: 24%;">
                        <col style="width: 14%;">
                    </colgroup>
                    <tbody>
            ''', unsafe_allow_html=True)
            
            for idx, row in enumerate(sorted_bottom[:5]):
                share_str = f"{(row['curr']/group_curr_total)*100:.1f}%" if group_curr_total > 0 else "0.0%"
                row_class = "row-rank1" if idx == 0 else ""
                st.markdown(f'''
                        <tr class="{row_class}">
                            <td class="col-rank"><b>{idx+1}</b></td>
                            <td class="col-client">{row["client"]}</td>
                            <td class="col-curr">{quad["fmt"](row["curr"])}</td>
                            <td class="col-share">{share_str}</td>
                        </tr>
                ''', unsafe_allow_html=True)
                
            if not sorted_bottom:
                st.markdown('<tr><td colspan="4" style="text-align:center; color:#64748B; padding: 0.5rem 0;">Nenhum cliente ativo no período.</td></tr>', unsafe_allow_html=True)
            st.markdown('</tbody></table></div>', unsafe_allow_html=True)
            
        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        
        # 3. EVOLUTION CHART
        st.markdown(f'<div class="table-section-title">Evolução Histórica</div>', unsafe_allow_html=True)
        
        fig = go.Figure()
        
        plan_MoM = []
        real_MoM = []
        
        for m in EN_MONTHS:
            if m in m_map_proj:
                cl_plan = sum(data_loader.clean_val(monthly_data[c][q_key]["plan"][m]) for c in filtered_clients)
                cl_real = sum(data_loader.clean_val(monthly_data[c][q_key]["real"][m]) for c in filtered_clients)
                
                if quad["is_ticket"]:
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
            if cl_real > 0 or m == month_sel_en:
                real_MoM.append(cl_real)
            else:
                real_MoM.append(None)
                
        fig.add_trace(go.Scatter(
            x=PT_MONTHS, y=plan_MoM, name="Planejado", line=dict(color="#002060", width=2.5)
        ))
        fig.add_trace(go.Scatter(
            x=PT_MONTHS, y=real_MoM, name="Realizado", line=dict(color="#166534", width=2.5), connectgaps=False
        ))
        
        sel_idx = EN_MONTHS.index(month_sel_en)
        sel_val = real_MoM[sel_idx] if real_MoM[sel_idx] is not None else plan_MoM[sel_idx]
        fig.add_trace(go.Scatter(
            x=[PT_MONTHS[sel_idx]], y=[sel_val],
            marker=dict(color="#D97706", size=10, line=dict(color="#FFFFFF", width=2)),
            showlegend=False
        ))
        
        fig.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        
        # 4. CHALLENGE TO TARGET CARD
        st.markdown(f'''
        <div class="kpi-card" style="border: 1px solid #E2E8F0; padding:1rem; background-color:#FFFFFF;">
            <div style="font-size:0.8rem; font-weight:700; color:#64748B; letter-spacing:0.5px; text-transform:uppercase;">
                DESAFIO PARA A META ({"ANUAL" if "YTD" in viz_mode else "MENSAL"})
            </div>
            <div style="font-size:1.15rem; font-weight:800; color:{challenge_color}; margin-top:0.4rem; margin-bottom:0.75rem;">
                {challenge_status} {challenge_msg}
            </div>
            <div style="display:flex; justify-content:space-between;">
                <div>
                    <div class="kpi-sub-label">Semanas Restantes</div>
                    <div class="kpi-sub-val" style="font-size:1.1rem;">{rem_weeks}</div>
                </div>
                <div>
                    <div class="kpi-sub-label">Necessidade Semanal Restante</div>
                    <div class="kpi-sub-val" style="font-size:1.1rem; color:{challenge_color};">{req_avg_str}</div>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
