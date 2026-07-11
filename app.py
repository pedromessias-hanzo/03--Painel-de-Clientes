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
    .compact-table thead {
        display: none !important; /* Remove grey header bar visually */
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
    mode_options = ["📅 Semana Selecionada", "📈 Acumulado no Mês", "🏆 Acumulado no Ano"]
    default_mode_idx = 1 # MTD
else:
    mode_options = ["📈 Consolidado do Mês", "🏆 Acumulado no Ano"]
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
    if "Ano" in viz_mode:
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
            
            if "Semana" in viz_mode:
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
        ach = v["proj"] / v["plan"] if "Ano" in viz_mode or "Mês" in viz_mode or not has_weeks_data else v["actual"] / v["plan"]
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

# Header Row
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown(f'''
    <div class="cockpit-header">
        <h1 class="cockpit-title">HANZO DO BRASIL</h1>
        <div class="cockpit-subtitle">
            Mês: <b>{month_sel_pt} 2026</b> | 
            Semana: <b>{week_sel_label if has_weeks_data else "Sem divisão semanal"}</b> | 
            Modo: <b>{viz_mode[2:]}</b> | 
            Grupo: <b>{group_filter}</b> | 
            Última Atualização: {last_modified.strftime("%d/%m/%Y %H:%M:%S")}
        </div>
    </div>
    ''', unsafe_allow_html=True)

with col_status:
    st.markdown(f'''
    <div class="status-badge-container">
        <div class="status-badge {badge_class}">
            STATUS DO MÊS: {overall_farol} {overall_status}
        </div>
    </div>
    ''', unsafe_allow_html=True)

# 2. EXECUTIVE KPI CARDS ROW (at the top)
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
    
    # Real x Planejado status and percent
    if c_vals["plan"] == 0:
        real_pct_str = "- %"
        real_farol = "⚪"
        real_color = "#64748B"
    else:
        real_ratio = c_vals["actual"] / c_vals["plan"]
        real_pct = ((c_vals["actual"] - c_vals["plan"]) / c_vals["plan"]) * 100
        real_pct_str = f"{real_pct:+.1f}%".replace(".", ",")
        
        if real_ratio >= 1.0:
            real_farol = "🟢"
            real_color = "#166534"
        elif real_ratio >= 0.90:
            real_farol = "🟡"
            real_color = "#854D0E"
        else:
            real_farol = "🔴"
            real_color = "#991B1B"
            
    # Projeção x Planejado status and percent
    if c_vals["plan"] == 0:
        proj_pct_str = "- %"
        proj_farol = "⚪"
        proj_color = "#64748B"
    else:
        proj_ratio = c_vals["proj"] / c_vals["plan"]
        proj_pct = ((c_vals["proj"] - c_vals["plan"]) / c_vals["plan"]) * 100
        proj_pct_str = f"{proj_pct:+.1f}%".replace(".", ",")
        
        if proj_ratio >= 1.0:
            proj_farol = "🟢"
            proj_color = "#166534"
        elif proj_ratio >= 0.90:
            proj_farol = "🟡"
            proj_color = "#854D0E"
        else:
            proj_farol = "🔴"
            proj_color = "#991B1B"
            
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
            <div style="margin-top:0.4rem; border-top:1px solid #E2E8F0; padding-top:0.4rem; font-size:0.8rem; font-weight:700;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.25rem;">
                    <span style="color:#475569;">Real x Planejado:</span>
                    <span style="color:{real_color}; font-weight:800;">{real_pct_str} <span class="kpi-light">{real_farol}</span></span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:#475569;">Projeção x Planejado:</span>
                    <span style="color:{proj_color}; font-weight:800;">{proj_pct_str} <span class="kpi-light">{proj_farol}</span></span>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

st.markdown('<br>', unsafe_allow_html=True)

# New Section: Evolução dos Indicadores — Planejado, Real e Projeção
st.markdown('<div class="quadrant-title" style="margin-top:0.5rem; margin-bottom:1rem;">Evolução dos Indicadores — Planejado, Real e Projeção</div>', unsafe_allow_html=True)

col_chart_sel, _ = st.columns([2.5, 5.5])
with col_chart_sel:
    sel_indicator = st.selectbox(
        "Indicador em análise",
        ["GMV", "Receita", "Pedidos", "Ticket Médio"],
        key="sel_indicator_evolution_chart"
    )

# Map key names
ind_key_map = {
    "GMV": "GMV",
    "Receita": "Receita Hanzo",
    "Pedidos": "Pedidos",
    "Ticket Médio": "Ticket Médio"
}
chart_metric_key = ind_key_map[sel_indicator]
chart_fmt = fmt_qty if sel_indicator == "Pedidos" else fmt_currency
short_label = {"GMV": "GMV", "Receita Hanzo": "Receita", "Pedidos": "Pedidos", "Ticket Médio": "Ticket Médio"}[chart_metric_key]

# Helper to calculate Planejado, Real and Projeção pelo Ritmo Atual series dynamically
def get_indicator_series(metric):
    x_lbls = []
    y_p = []
    y_r = []
    y_pr = []
    
    if has_weeks_data and "Ano" not in viz_mode:
        # Weekly view: "Semana Selecionada" or "Acumulado no Mês"
        weekly_cols_active = m_map_proj[month_sel_en]["weekly"]
        num_w = len(weekly_cols_active)
        x_lbls = [f"Semana {i+1}" for i in range(num_w)]
        sel_i = selected_week_idx
        
        weights_row = df_proj.iloc[3]
        w_weights = [data_loader.clean_val(weights_row[col]) for col in weekly_cols_active]
        sum_w = sum(w_weights)
        if sum_w == 0:
            w_weights = [1.0 / num_w] * num_w
        else:
            w_weights = [w / sum_w for w in w_weights]
            
        m_plan_val = sum(data_loader.clean_val(monthly_data[c][metric]["plan"][month_sel_en]) for c in filtered_clients)
        
        # Real weekly values
        r_vals_all = []
        for w in range(num_w):
            w_real_val = sum(data_loader.clean_val(weekly_data[c][metric]["weekly"][month_sel_en][w]) for c in filtered_clients)
            r_vals_all.append(w_real_val)
            
        if "Semana" in viz_mode:
            # Single week values
            for w in range(num_w):
                y_p.append(m_plan_val * w_weights[w])
                y_r.append(r_vals_all[w] if w <= sel_i else None)
                
            # Ritmo semanal médio for projection (non-accumulated: average of past weeks)
            past_real_vals = [v for v in r_vals_all[:sel_i+1] if v is not None]
            avg_ritmo = sum(past_real_vals) / len(past_real_vals) if past_real_vals else 0.0
            
            for w in range(num_w):
                if w < sel_i:
                    y_pr.append(None)
                elif w == sel_i:
                    y_pr.append(y_r[sel_i]) # start at last real for continuity
                else:
                    y_pr.append(avg_ritmo)
        else:
            # Acumulado no Mês (MTD)
            acc_real = 0.0
            for w in range(num_w):
                y_p.append(m_plan_val * sum(w_weights[:w+1]))
                if w <= sel_i:
                    acc_real += r_vals_all[w]
                    y_r.append(acc_real)
                else:
                    y_r.append(None)
                    
            # Ritmo semanal médio for projection (accumulated)
            avg_ritmo = y_r[sel_i] / (sel_i + 1) if (sel_i + 1) > 0 else 0.0
            
            for w in range(num_w):
                if w < sel_i:
                    y_pr.append(None)
                elif w == sel_i:
                    y_pr.append(y_r[sel_i])
                else:
                    y_pr.append(y_r[sel_i] + avg_ritmo * (w - sel_i))
    else:
        # Monthly / YTD view: Jan to Dec
        x_lbls = PT_MONTHS
        sel_i = EN_MONTHS.index(month_sel_en)
        
        m_plan_vals = [sum(data_loader.clean_val(monthly_data[c][metric]["plan"][m]) for c in filtered_clients) for m in EN_MONTHS]
        m_real_vals = [sum(data_loader.clean_val(monthly_data[c][metric]["real"][m]) for c in filtered_clients) for m in EN_MONTHS]
        
        if "Ano" in viz_mode:
            # YTD accumulated monthly series
            acc_p = 0.0
            acc_r = 0.0
            for m_idx in range(12):
                acc_p += m_plan_vals[m_idx]
                y_p.append(acc_p)
                if m_idx <= sel_i:
                    acc_r += m_real_vals[m_idx]
                    y_r.append(acc_r)
                else:
                    y_r.append(None)
                    
            avg_ritmo = y_r[sel_i] / (sel_i + 1) if (sel_i + 1) > 0 else 0.0
            for m_idx in range(12):
                if m_idx < sel_i:
                    y_pr.append(None)
                elif m_idx == sel_i:
                    y_pr.append(y_r[sel_i])
                else:
                    y_pr.append(y_r[sel_i] + avg_ritmo * (m_idx - sel_i))
        else:
            # Consolidado do Mês (monthly non-accumulated)
            for m_idx in range(12):
                y_p.append(m_plan_vals[m_idx])
                y_r.append(m_real_vals[m_idx] if m_idx <= sel_i else None)
                
            past_real = [v for v in m_real_vals[:sel_i+1] if v is not None]
            avg_ritmo = sum(past_real) / len(past_real) if past_real else 0.0
            for m_idx in range(12):
                if m_idx < sel_i:
                    y_pr.append(None)
                elif m_idx == sel_i:
                    y_pr.append(y_r[sel_i])
                else:
                    y_pr.append(avg_ritmo)
                    
    return x_lbls, y_p, y_r, y_pr

# Compute the actual indicator series
if chart_metric_key == "Ticket Médio":
    x_labels, y_plan_gmv, y_real_gmv, y_proj_gmv = get_indicator_series("GMV")
    _, y_plan_ped, y_real_ped, y_proj_ped = get_indicator_series("Pedidos")
    
    y_plan = [y_plan_gmv[i] / y_plan_ped[i] if y_plan_ped[i] > 0 else 0.0 for i in range(len(x_labels))]
    y_real = [y_real_gmv[i] / y_real_ped[i] if y_real_ped[i] is not None and y_real_ped[i] > 0 else None for i in range(len(x_labels))]
    y_proj = [y_proj_gmv[i] / y_proj_ped[i] if y_proj_ped[i] is not None and y_proj_ped[i] > 0 else None for i in range(len(x_labels))]
else:
    x_labels, y_plan, y_real, y_proj = get_indicator_series(chart_metric_key)

# Identify index coordinates
if has_weeks_data and "Ano" not in viz_mode:
    selected_idx = selected_week_idx
else:
    selected_idx = EN_MONTHS.index(month_sel_en)

# Calculate indicators for status annotations
plan_real_last = y_plan[selected_idx]
real_last = y_real[selected_idx] if y_real[selected_idx] is not None else 0.0

plan_proj_last = y_plan[-1]
proj_last = y_proj[-1] if y_proj[-1] is not None else 0.0

# Annotation labels and colors
if plan_real_last == 0:
    real_gap_val = 0.0
    real_farol = "⚪"
    real_color = "#64748B"
    real_status_label = "Real x Planejado: - % ⚪"
else:
    real_ratio = real_last / plan_real_last
    real_gap_val = ((real_last - plan_real_last) / plan_real_last) * 100
    if real_ratio >= 1.0:
        real_farol = "🟢"
        real_color = "#166534"
    elif real_ratio >= 0.90:
        real_farol = "🟡"
        real_color = "#854D0E"
    else:
        real_farol = "🔴"
        real_color = "#991B1B"
    real_status_label = f"Real x Planejado: {real_gap_val:+.1f}% {real_farol}".replace(".", ",")

if plan_proj_last == 0:
    proj_gap_val = 0.0
    proj_farol = "⚪"
    proj_status_label = "Projeção x Planejado: - % ⚪"
else:
    proj_ratio = proj_last / plan_proj_last
    proj_gap_val = ((proj_last - plan_proj_last) / plan_proj_last) * 100
    if proj_ratio >= 1.0:
        proj_farol = "🟢"
    elif proj_ratio >= 0.90:
        proj_farol = "🟡"
    else:
        proj_farol = "🔴"
    proj_status_label = f"Projeção x Planejado: {proj_gap_val:+.1f}% {proj_farol}".replace(".", ",")

# Compute shaded desvio areas
# A) Real area: from start up to selected_idx
valid_x = x_labels[:selected_idx+1]
valid_plan = y_plan[:selected_idx+1]
valid_real = [v if v is not None else 0.0 for v in y_real[:selected_idx+1]]

fill_x_real = valid_x + valid_x[::-1]
fill_y_real = valid_plan + valid_real[::-1]

if plan_real_last == 0:
    fill_color_real = 'rgba(100,116,139,0.04)'
else:
    fill_color_real = 'rgba(22, 101, 52, 0.08)' if real_last >= plan_real_last else 'rgba(153, 27, 27, 0.08)'

# B) Projeção area: from selected_idx to end
valid_proj_x = x_labels[selected_idx:]
valid_proj_plan = y_plan[selected_idx:]
valid_proj_val = [v if v is not None else 0.0 for v in y_proj[selected_idx:]]

fill_x_proj = valid_proj_x + valid_proj_x[::-1]
fill_y_proj = valid_proj_plan + valid_proj_val[::-1]

if plan_proj_last == 0:
    fill_color_proj = 'rgba(100,116,139,0.02)'
else:
    fill_color_proj = 'rgba(22, 101, 52, 0.04)' if proj_last >= plan_proj_last else 'rgba(153, 27, 27, 0.04)'

# Plotly Line Chart
fig_ind = go.Figure()

# Add Shaded Areas in the background
fig_ind.add_trace(go.Scatter(
    x=fill_x_real, y=fill_y_real,
    fill='toself',
    fillcolor=fill_color_real,
    line=dict(color='rgba(0,0,0,0)'),
    showlegend=False,
    hoverinfo='skip'
))

fig_ind.add_trace(go.Scatter(
    x=fill_x_proj, y=fill_y_proj,
    fill='toself',
    fillcolor=fill_color_proj,
    line=dict(color='rgba(0,0,0,0)'),
    showlegend=False,
    hoverinfo='skip'
))

# Generate custom tooltips for the lines
tooltip_texts = []
for i, lbl in enumerate(x_labels):
    p_val = y_plan[i]
    r_val = y_real[i]
    pr_val = y_proj[i]
    
    r_str = chart_fmt(r_val) if r_val is not None else "—"
    pr_str = chart_fmt(pr_val) if pr_val is not None else "—"
    
    r_pct_str = "—"
    r_f = ""
    if r_val is not None:
        r_pct = ((r_val - p_val)/p_val)*100 if p_val > 0 else 0.0
        r_pct_str = f"{r_pct:+.1f}%".replace(".", ",")
        r_f = "🟢" if p_val == 0 or (r_val/p_val) >= 1.0 else "🟡" if (r_val/p_val) >= 0.90 else "🔴"
        
    pr_pct_str = "—"
    pr_f = ""
    if pr_val is not None:
        pr_pct = ((pr_val - p_val)/p_val)*100 if p_val > 0 else 0.0
        pr_pct_str = f"{pr_pct:+.1f}%".replace(".", ",")
        pr_f = "🟢" if p_val == 0 or (pr_val/p_val) >= 1.0 else "🟡" if (pr_val/p_val) >= 0.90 else "🔴"
        
    tooltip_texts.append(
        f"Indicador: {sel_indicator}<br>"
        f"Período: {lbl}<br>"
        f"Planejado: {chart_fmt(p_val)}<br>"
        f"Real: {r_str}<br>"
        f"Projeção: {pr_str}<br>"
        f"Real x Planejado: {r_pct_str} {r_f}<br>"
        f"Projeção x Planejado: {pr_pct_str} {pr_f}"
    )

# Add Lines
fig_ind.add_trace(go.Scatter(
    x=x_labels, y=y_plan,
    name="Planejado",
    mode='lines+markers',
    line=dict(color='#002060', width=3),
    text=tooltip_texts,
    hovertemplate="%{text}<extra></extra>"
))

fig_ind.add_trace(go.Scatter(
    x=x_labels, y=y_real,
    name="Real",
    mode='lines+markers',
    line=dict(color=real_color, width=3),
    text=tooltip_texts,
    hovertemplate="%{text}<extra></extra>"
))

fig_ind.add_trace(go.Scatter(
    x=x_labels, y=y_proj,
    name="Projeção pelo Ritmo Atual",
    mode='lines+markers',
    line=dict(color='#D97706', width=3, dash='dash'),
    text=tooltip_texts,
    hovertemplate="%{text}<extra></extra>"
))

# Status annotations pointing to the respective points
fig_ind.add_annotation(
    x=x_labels[selected_idx], y=real_last,
    text=real_status_label,
    showarrow=True,
    arrowhead=1,
    ax=65, ay=-35,
    font=dict(size=11, color=real_color, family="sans-serif"),
    bgcolor="rgba(255,255,255,0.95)",
    bordercolor=real_color,
    borderwidth=1,
    borderpad=4
)

fig_ind.add_annotation(
    x=x_labels[-1], y=proj_last,
    text=proj_status_label,
    showarrow=True,
    arrowhead=1,
    ax=65, ay=35,
    font=dict(size=11, color='#D97706', family="sans-serif"),
    bgcolor="rgba(255,255,255,0.95)",
    bordercolor='#D97706',
    borderwidth=1,
    borderpad=4
)

# Dynamic axis scale range calculation
all_visible_vals = [v for v in y_plan + [x for x in y_real if x is not None] + [x for x in y_proj if x is not None]]
if all_visible_vals:
    ymin = min(all_visible_vals)
    ymax = max(all_visible_vals)
    margin = (ymax - ymin) * 0.12
    if margin == 0:
        margin = ymax * 0.12 if ymax > 0 else 1.0
    range_y_axis = [max(0.0, ymin - margin), ymax + margin]
else:
    range_y_axis = None

fig_ind.update_layout(
    height=360,
    margin=dict(l=10, r=80, t=10, b=10),
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.12,
        xanchor="center",
        x=0.5,
        font=dict(size=11),
        itemclick="toggle",
        itemdoubleclick="toggleothers"
    ),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
    yaxis=dict(showgrid=True, gridcolor="#F1F5F9", range=range_y_axis) if range_y_axis else dict(showgrid=True, gridcolor="#F1F5F9")
)

st.plotly_chart(fig_ind, use_container_width=True)
st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

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

for quad in quadrants_setup:
    q_key = quad["key"]
    
    # 1. EXTRACT CLIENT RANKINGS DATA
    client_data_list = []
    has_client_level_data = True
    
    if "Ano" in viz_mode:
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
                    
                if "Semana" in viz_mode:
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

    # 3. CHALLENGE CARD METRICS PREPARATION
    if "Ano" in viz_mode:
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
    
    if is_latest_wk and "Ano" not in viz_mode and has_weeks_data:
        diff_list = [weekly_data[c][q_key]["diff"][month_sel_en] for c in filtered_clients]
        diff_numeric = [clean_val(x) for x in diff_list if x is not None and not pd.isna(x)]
        if len(diff_numeric) == len(filtered_clients):
            diff_challenge = -sum(diff_numeric)
            
    if diff_challenge is None:
        diff_challenge = target_val - accum_challenge

    if "Ano" in viz_mode:
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
        challenge_msg = "Meta atingida"
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
            challenge_msg = "Mês encerrado abaixo da meta" if "Ano" not in viz_mode else "Ano encerrado abaixo da meta"
            req_avg_str = "N/A"
            challenge_status = "🔴"
            challenge_color = "#991B1B"
            badge_theme = "status-red"

    # Render inside Slot Card
    with quad["slot"]:
        st.markdown(f'<div class="quadrant-container">', unsafe_allow_html=True)
        st.markdown(f'<div class="quadrant-title">{quad["title"]}</div>', unsafe_allow_html=True)
        
        # Title mapping based on visualization mode
        if "Semana" in viz_mode:
            tbl_top_title = "🏆 Top 5 Clientes da Semana"
            tbl_bot_title = "📉 Bottom 5 Clientes com Atividade na Semana"
        elif "Ano" in viz_mode:
            tbl_top_title = "🏆 Top 5 Clientes no Ano"
            tbl_bot_title = "📉 Bottom 5 Clientes com Atividade no Ano"
        else:
            tbl_top_title = "🏆 Top 5 Clientes do Mês"
            tbl_bot_title = "📉 Bottom 5 Clientes com Atividade no Mês"

        # 2. TOP 5 CLIENTS TABLE
        st.markdown(f'<div class="table-section-title" style="margin-top:0.25rem;">{tbl_top_title}</div>', unsafe_allow_html=True)
        
        if not has_client_level_data:
            msg_unavail = "Ranking YTD por cliente indisponível para este período." if "Ano" in viz_mode else "Ranking por cliente indisponível para este mês."
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
        
        # 3. BOTTOM 5 CLIENTS TABLE
        st.markdown(f'<div class="table-section-title">{tbl_bot_title}</div>', unsafe_allow_html=True)
        
        if not has_client_level_data:
            msg_unavail = "Ranking YTD por cliente indisponível para este período." if "Ano" in viz_mode else "Ranking por cliente indisponível para este mês."
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
        
        # 4. TOP 5 EVOLUTION LINE CHART (Planejamento Jan-Dec)
        # Title based on mode
        if "Ano" in viz_mode:
            chart_top_title = f"Evolução Mensal - Top 5 Clientes YTD | Até {month_sel_pt}/2026"
        elif "Mês" in viz_mode:
            chart_top_title = f"Evolução Mensal - Top 5 Clientes MTD | Até {month_sel_pt}/2026"
        elif "Semana" in viz_mode:
            chart_top_title = f"Evolução Mensal - Top 5 Clientes da {week_sel_label} | Até {month_sel_pt}/2026"
        else:
            chart_top_title = f"Evolução Mensal - Top 5 Clientes | Até {month_sel_pt}/2026"
            
        st.markdown(f'<div class="table-section-title">{chart_top_title}</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.8rem; color:#64748B; margin-top:-0.5rem; margin-bottom:0.5rem;">Clique na legenda para destacar ou ocultar clientes.</div>', unsafe_allow_html=True)
        
        top_names_list = [row["client"] for row in sorted_top[:5]] if has_client_level_data and sorted_top else []
        sel_top = st.selectbox(
            "Cliente em destaque",
            ["Todos"] + top_names_list,
            key=f"sel_highlight_{q_key}_top"
        )
        
        fig_top = go.Figure()
        # High-contrast categorical palette (e.g. Blue, Green, Orange, Purple, Red)
        top_palette = ['#1f77b4', '#2ca02c', '#ff7f0e', '#9467bd', '#d62728']
        symbols_list = ['circle', 'square', 'diamond', 'cross', 'x']
        
        # Calculate Y scale range dynamically based only on months up to selected
        all_top_vals = []
        if has_client_level_data and sorted_top:
            for row in sorted_top[:5]:
                client = row["client"]
                for m_idx, m in enumerate(EN_MONTHS):
                    if m_idx <= EN_MONTHS.index(month_sel_en):
                        v = data_loader.clean_val(monthly_data[client][q_key]["real"][m])
                        if v > 0:
                            all_top_vals.append(v)
                        
        if all_top_vals:
            y_min = min(all_top_vals)
            y_max = max(all_top_vals)
            margem = (y_max - y_min) * 0.10
            if margem == 0:
                margem = y_max * 0.10 if y_max > 0 else 1.0
            range_y_top = [max(0.0, y_min - margem), y_max + margem]
        else:
            range_y_top = None
            
        short_label = {"GMV": "GMV", "Receita Hanzo": "Receita", "Pedidos": "Pedidos", "Ticket Médio": "Ticket Médio"}[q_key]
        
        if has_client_level_data and sorted_top:
            for c_idx, row in enumerate(sorted_top[:5]):
                client = row["client"]
                color = top_palette[c_idx % len(top_palette)]
                symbol = symbols_list[c_idx % len(symbols_list)]
                
                # Determine opacity and line width based on highlighting
                if sel_top == "Todos":
                    trace_opacity = 0.95
                    trace_width = 3.0
                elif client == sel_top:
                    trace_opacity = 1.0
                    trace_width = 4.0
                else:
                    trace_opacity = 0.20
                    trace_width = 1.5
                    
                y_vals = []
                tooltip_texts = []
                for m_idx, m in enumerate(EN_MONTHS):
                    if m_idx <= EN_MONTHS.index(month_sel_en):
                        m_val = data_loader.clean_val(monthly_data[client][q_key]["real"][m])
                        y_vals.append(m_val)
                        
                        m_total = sum(data_loader.clean_val(monthly_data[c][q_key]["real"][m]) for c in filtered_clients)
                        m_share = (m_val / m_total) * 100 if m_total > 0 else 0.0
                        
                        # Calculate MoM variation
                        var_str = "—"
                        if m_idx > 0:
                            prev_m = EN_MONTHS[m_idx - 1]
                            prev_v = data_loader.clean_val(monthly_data[client][q_key]["real"][prev_m])
                            if prev_v > 0:
                                mom_var = ((m_val - prev_v) / prev_v) * 100
                                var_str = f"{mom_var:+.1f}%".replace(".", ",")
                                
                        tooltip_texts.append(
                            f"Cliente: {client}<br>"
                            f"Mês: {PT_MONTH_DISPLAY[m]}<br>"
                            f"{short_label}: {quad['fmt'](m_val)}<br>"
                            f"Variação mensal: {var_str}"
                        )
                    else:
                        y_vals.append(None)
                        tooltip_texts.append("")
                    
                fig_top.add_trace(go.Scatter(
                    x=PT_MONTHS,
                    y=y_vals,
                    name=client,
                    mode='lines+markers',
                    opacity=trace_opacity,
                    line=dict(color=color, width=trace_width),
                    marker=dict(
                        size=[12 if m == month_sel_en else 6 for m in EN_MONTHS],
                        color=['#D97706' if m == month_sel_en else color for m in EN_MONTHS],
                        symbol=symbol,
                        line=dict(color='#FFFFFF', width=1.5)
                    ),
                    text=tooltip_texts,
                    hovertemplate="%{text}<extra></extra>"
                ))
                
        fig_top.update_layout(
            height=280,
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.12,
                xanchor="center",
                x=0.5,
                font=dict(size=11),
                itemclick="toggle",
                itemdoubleclick="toggleothers"
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", range=range_y_top) if range_y_top else dict(showgrid=True, gridcolor="#F1F5F9")
        )
        st.plotly_chart(fig_top, use_container_width=True)
        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        
        # 6. CHALLENGE TO TARGET CARD (Projeção)
        st.markdown(f'''
        <div class="kpi-card" style="border: 1px solid #E2E8F0; padding:1rem; background-color:#FFFFFF;">
            <div style="font-size:0.8rem; font-weight:700; color:#64748B; letter-spacing:0.5px; text-transform:uppercase;">
                DESAFIO PARA A META ({"ANUAL" if "Ano" in viz_mode else "MENSAL"})
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
