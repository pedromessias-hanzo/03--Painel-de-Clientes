import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
import datetime

# Set Page Config
st.set_page_config(
    page_title="Hanzo do Brasil - Dashboard de Performance Comercial e Financeira",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load CSS Stylesheet
def load_css(css_file):
    if os.path.exists(css_file):
        with open(css_file, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning("styles.css não encontrado.")

css_path = os.path.join(os.path.dirname(__file__), "styles.css")
load_css(css_path)

# Import Data Loader
import data_loader

# Define spreadsheet path
# Google Drive Configuration
# Copy your public Google Drive file ID here to host the data source online.
# If left as placeholder or empty, it will fall back to reading the local "Planejamento 2026.xlsx".
GOOGLE_DRIVE_FILE_ID = "paste_file_id_here"

import requests
import io
import email.utils

@st.cache_data(ttl=600)
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
            overview, monthly, optimistic, metadata = data_loader.load_data(data_bytes)
            
            # Retrieve last modified time from response header, fallback to current time
            last_modified = datetime.datetime.now()
            if "Last-Modified" in response.headers:
                try:
                    last_modified = email.utils.parsedate_to_datetime(response.headers["Last-Modified"])
                except:
                    pass
            return overview, monthly, optimistic, metadata, last_modified, None
        else:
            # Fallback to local spreadsheet path
            excel_path = os.path.join(os.path.dirname(__file__), "Planejamento 2026.xlsx")
            if not os.path.exists(excel_path):
                raise FileNotFoundError(
                    "Planilha local 'Planejamento 2026.xlsx' não encontrada e GOOGLE_DRIVE_FILE_ID não está configurado."
                )
            overview, monthly, optimistic, metadata = data_loader.load_data(excel_path)
            mtime = os.path.getmtime(excel_path)
            last_modified = datetime.datetime.fromtimestamp(mtime)
            return overview, monthly, optimistic, metadata, last_modified, None
    except Exception as e:
        return {}, {}, {}, {}, None, str(e)

# Load data
overview_data, monthly_data, optimistic_monthly_data, clients_metadata, last_modified, load_error = load_and_cache_data()

if load_error:
    st.error(f"Erro ao carregar planilha: {load_error}")
    st.stop()

# Brazilian months mappings
PT_MONTHS = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
EN_MONTHS = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
PT_TO_EN = dict(zip(PT_MONTHS, EN_MONTHS))
EN_TO_PT = dict(zip(EN_MONTHS, PT_MONTHS))

# Determine active months based on realized GMV
# If any client has Realized GMV > 0 in a month, that month is marked as realized
realized_months = []
for m in EN_MONTHS:
    m_sum = sum(monthly_data[c]["GMV"]["real"].get(m, 0.0) for c in monthly_data)
    if m_sum > 0:
        realized_months.append(m)

if not realized_months:
    realized_months = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun'] # Fallback default

last_realized_month = realized_months[-1]
last_realized_month_pt = EN_TO_PT[last_realized_month]

# HEADER, NAVIGATION & FILTERS REDESIGN (No Sidebar)
tabs_nav = [
    "🏛 Presidency Overview",
    "🏆 Client Rankings",
    "📉 Detractors",
    "📈 Forecast & Budget",
    "🎯 Strategic Matrix",
    "🎯 Strategic Matrix", # Wait, why is it duplicated? Let's check: in tabs_nav there should only be one "🎯 Strategic Matrix". Yes, let's write it down correctly:
    "🏛 Presidency Overview",
    "🏆 Client Rankings",
    "📉 Detractors",
    "📈 Forecast & Budget",
    "🎯 Strategic Matrix",
    "⚠ Risks & Opportunities",
    "👤 Client 360",
    "👔 Board & Investors"
]

# Wait, let's write clean tabs_nav:
tabs_nav = [
    "🏛 Presidency Overview",
    "🏆 Client Rankings",
    "📉 Detractors",
    "📈 Forecast & Budget",
    "🎯 Strategic Matrix",
    "⚠ Risks & Opportunities",
    "👤 Client 360",
    "👔 Board & Investors"
]

OLD_TO_NEW_MAP = {
    "Visão Executiva": "🏛 Presidency Overview",
    "Concentração": "🏆 Client Rankings",
    "Clientes Detratores": "📉 Detractors",
    "Forecast e Projeções": "📈 Forecast & Budget",
    "Matriz Estratégica": "🎯 Strategic Matrix",
    "Riscos & Oportunidades": "⚠ Risks & Opportunities",
    "Client 360°": "👤 Client 360",
    "Conselho & Investidores": "👔 Board & Investors"
}

def clean_nav_name(name):
    return name.replace("🏛 ", "").replace("🏆 ", "").replace("📉 ", "").replace("📈 ", "").replace("🎯 ", "").replace("⚠ ", "").replace("👤 ", "").replace("👔 ", "").strip()

# Resolve selected tab index
default_index = 0
try:
    if "page" in st.query_params:
        qp_page = st.query_params["page"].strip()
        if qp_page in OLD_TO_NEW_MAP:
            qp_page = OLD_TO_NEW_MAP[qp_page]
        for idx, tab in enumerate(tabs_nav):
            if clean_nav_name(tab) == clean_nav_name(qp_page) or tab == qp_page:
                default_index = idx
                break
except:
    try:
        qp = st.experimental_get_query_params()
        if "page" in qp:
            qp_page = qp["page"][0].strip()
            if qp_page in OLD_TO_NEW_MAP:
                qp_page = OLD_TO_NEW_MAP[qp_page]
            for idx, tab in enumerate(tabs_nav):
                if clean_nav_name(tab) == clean_nav_name(qp_page) or tab == qp_page:
                    default_index = idx
                    break
    except:
        pass

if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = tabs_nav[default_index]
else:
    # Sync if query params change
    if "page" in st.query_params:
        qp_page = st.query_params["page"].strip()
        for tab in tabs_nav:
            if clean_nav_name(tab) == clean_nav_name(qp_page) or tab == qp_page:
                st.session_state.selected_tab = tab
                break

selected_tab = st.session_state.selected_tab

# Top Header Row (Logo, status, reload button)
col_h1, col_h2, col_h3 = st.columns([4, 6, 2])
with col_h1:
    st.markdown(
        "<div style='padding-top: 5px;'><h2 style='color:#002060; font-family: Outfit; font-weight:800; margin:0; border:none; padding:0;'>HANZO DO BRASIL</h2>"
        "<p style='color:#64748B; font-size:11px; font-weight:700; margin:0; text-transform:uppercase; letter-spacing:1.5px;'>Performance &amp; Projeções</p></div>",
        unsafe_allow_html=True
    )
with col_h2:
    st.markdown(
        f"<div style='font-size: 11px; color: #64748B; line-height: 1.4; padding-top: 18px; text-align: right;'>"
        f"🟢 Planilha conectada e monitorada | "
        f"Última alteração: {last_modified.strftime('%d/%m/%Y %H:%M:%S')}"
        f"</div>",
        unsafe_allow_html=True
    )
with col_h3:
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("<hr style='margin: 10px 0 15px 0;'>", unsafe_allow_html=True)

# Top Horizontal Navigation Bar
nav_cols = st.columns(len(tabs_nav))
for idx, tab in enumerate(tabs_nav):
    is_active = (tab == selected_tab)
    btn_type = "primary" if is_active else "secondary"
    if nav_cols[idx].button(tab, key=f"top_nav_btn_{idx}", use_container_width=True, type=btn_type):
        st.query_params["page"] = clean_nav_name(tab)
        st.session_state.selected_tab = tab
        st.rerun()

st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

# Horizontal Global Filters Bar
with st.expander("🛠️ Filtros de Análise (Filtros Globais)", expanded=True):
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
    
    with col_f1:
        years = ["2026", "2025", "2027", "2028"]
        selected_year = st.selectbox("Ano de Análise", years, index=0)
        
    with col_f2:
        if selected_year == "2026":
            month_options = ["Todos", f"Acumulado até {last_realized_month_pt}"] + PT_MONTHS
            selected_month_label = st.selectbox("Mês de Referência", month_options, index=1)
        else:
            st.info("Visualização anual completa")
            selected_month_label = "Todos"
            
    with col_f3:
        statuses = ["Todos", "Ativo", "Novo Cliente", "Pipeline", "Wish List"]
        selected_status = st.selectbox("Status Comercial", statuses, index=0)
        
    with col_f4:
        groups = ["Todos", "Grupo Alife Nino", "Grupo Bold", "Grupo Drumattos", "Independente"]
        selected_group = st.selectbox("Grupo de Clientes", groups, index=0)
        
    with col_f5:
        # Pre-filter client list for dropdown selection
        client_list = sorted(list(clients_metadata.keys()))
        filtered_dropdown_clients = []
        for c in client_list:
            status_match = (selected_status == "Todos" or clients_metadata[c]["status"] == selected_status)
            group_match = (selected_group == "Todos" or clients_metadata[c]["group"] == selected_group)
            if status_match and group_match:
                filtered_dropdown_clients.append(c)
                
        selected_client_label = st.selectbox("Cliente Específico", ["Todos"] + filtered_dropdown_clients, index=0)

# Apply global filters to determine the final set of clients
filtered_clients = []
for c in client_list:
    status_match = (selected_status == "Todos" or clients_metadata[c]["status"] == selected_status)
    group_match = (selected_group == "Todos" or clients_metadata[c]["group"] == selected_group)
    client_match = (selected_client_label == "Todos" or c == selected_client_label)
    
    if status_match and group_match and client_match:
        filtered_clients.append(c)

# Helper function to get list of months based on month filter
def get_analysis_months(month_filter):
    if month_filter == "Todos":
        return EN_MONTHS
    elif "Acumulado" in month_filter:
        idx = EN_MONTHS.index(last_realized_month)
        return EN_MONTHS[:idx+1]
    else:
        return [PT_TO_EN[month_filter]]

analysis_months = get_analysis_months(selected_month_label)

# Determine if the period is YTD (Accumulated) or full year
is_ytd = "Acumulado" in selected_month_label
is_single_month = selected_month_label in PT_MONTHS
is_full_year = selected_month_label == "Todos"

# Pre-calculate YTD / Full Year Metrics for 2026 (Base vs Real vs Optimistic)
# We calculate values based on filtered_clients and analysis_months
def calculate_kpis():
    gmv_plan = 0.0
    gmv_real = 0.0
    gmv_optim = 0.0
    
    rec_plan = 0.0
    rec_real = 0.0
    rec_optim = 0.0
    
    ped_plan = 0.0
    ped_real = 0.0
    ped_optim = 0.0
    
    # 2025 annual historical totals for the filtered set
    total_rec_2025 = sum(overview_data[c]["2025"]["Receita Hanzo"] for c in filtered_clients if c in overview_data)
    total_gmv_2025 = sum(overview_data[c]["2025"]["GMV"] for c in filtered_clients if c in overview_data)
    total_ped_2025 = sum(overview_data[c]["2025"]["Pedidos"] for c in filtered_clients if c in overview_data)
    
    for c in filtered_clients:
        # Monthly 2026
        if c in monthly_data:
            for m in analysis_months:
                gmv_plan += monthly_data[c]["GMV"]["plan"].get(m, 0.0)
                rec_plan += monthly_data[c]["Receita Hanzo"]["plan"].get(m, 0.0)
                ped_plan += monthly_data[c]["Pedidos"]["plan"].get(m, 0.0)
                
                # Real values are only sum for realized months
                if m in realized_months:
                    gmv_real += monthly_data[c]["GMV"]["real"].get(m, 0.0)
                    rec_real += monthly_data[c]["Receita Hanzo"]["real"].get(m, 0.0)
                    ped_real += monthly_data[c]["Pedidos"]["real"].get(m, 0.0)
                else:
                    # In YTD mode, future months are ignored.
                    # In Full Year mode, future months actuals are replaced by Plan (Standard forecast logic)
                    if not is_ytd and not is_single_month:
                        gmv_real += monthly_data[c]["GMV"]["plan"].get(m, 0.0)
                        rec_real += monthly_data[c]["Receita Hanzo"]["plan"].get(m, 0.0)
                        ped_real += monthly_data[c]["Pedidos"]["plan"].get(m, 0.0)
                        
                # Optimistic values
                if c in optimistic_monthly_data:
                    gmv_optim += optimistic_monthly_data[c]["GMV"]["plan"].get(m, 0.0)
                    rec_optim += optimistic_monthly_data[c]["Receita Hanzo"]["plan"].get(m, 0.0)
                    ped_optim += optimistic_monthly_data[c]["Pedidos"]["plan"].get(m, 0.0)
                else:
                    gmv_optim += monthly_data[c]["GMV"]["plan"].get(m, 0.0)
                    rec_optim += monthly_data[c]["Receita Hanzo"]["plan"].get(m, 0.0)
                    ped_optim += monthly_data[c]["Pedidos"]["plan"].get(m, 0.0)
                    
    # Active clients (who have positive realized revenue in the selected months, or plan if future)
    active_clients_count = 0
    new_clients_count = 0
    pipeline_clients_count = 0
    wish_clients_count = 0
    
    for c in filtered_clients:
        status = clients_metadata[c]["status"]
        if status == "Ativo":
            active_clients_count += 1
        elif status == "Novo Cliente":
            new_clients_count += 1
        elif status == "Pipeline":
            pipeline_clients_count += 1
        elif status == "Wish List":
            wish_clients_count += 1
            
    return {
        "gmv_plan": gmv_plan, "gmv_real": gmv_real, "gmv_optim": gmv_optim,
        "rec_plan": rec_plan, "rec_real": rec_real, "rec_optim": rec_optim,
        "ped_plan": ped_plan, "ped_real": ped_real, "ped_optim": ped_optim,
        "active_clients": active_clients_count,
        "new_clients": new_clients_count,
        "pipeline_clients": pipeline_clients_count,
        "wish_clients": wish_clients_count,
        "rec_2025": total_rec_2025,
        "gmv_2025": total_gmv_2025,
        "ped_2025": total_ped_2025
    }

kpi_data = calculate_kpis()

# Calculate variance
gmv_var = kpi_data["gmv_real"] - kpi_data["gmv_plan"]
gmv_var_pct = gmv_var / kpi_data["gmv_plan"] if kpi_data["gmv_plan"] > 0 else 0.0

rec_var = kpi_data["rec_real"] - kpi_data["rec_plan"]
rec_var_pct = rec_var / kpi_data["rec_plan"] if kpi_data["rec_plan"] > 0 else 0.0

ped_var = kpi_data["ped_real"] - kpi_data["ped_plan"]
ped_var_pct = ped_var / kpi_data["ped_plan"] if kpi_data["ped_plan"] > 0 else 0.0

# ----------------------------------------------------
# GLOBAL PRE-CALCULATIONS (Redesigned for Executive Storytelling)
# ----------------------------------------------------

# Helper for status badge
def get_client_status_badge(achievement):
    if achievement >= 1.0:
        return "🟢"
    elif achievement >= 0.90:
        return "🟡"
    else:
        return "🔴"

# Current/Last realized month details
if selected_month_label in PT_MONTHS:
    curr_m = PT_TO_EN[selected_month_label]
else:
    curr_m = last_realized_month
curr_idx = EN_MONTHS.index(curr_m)
prev_m = EN_MONTHS[curr_idx - 1] if curr_idx > 0 else None

client_scores = {}
client_growth_mom = {}
client_growth_yoy = {}
client_achievements = {}
client_diffs = {}
client_revenue_vals = {}
client_gmv_vals = {}
client_ped_vals = {}

for c in filtered_clients:
    # 1. Monthly growth
    curr_rev = 0.0
    prev_rev = 0.0
    if c in monthly_data:
        if curr_m in realized_months:
            curr_rev = monthly_data[c]["Receita Hanzo"]["real"].get(curr_m, 0.0)
        else:
            curr_rev = monthly_data[c]["Receita Hanzo"]["plan"].get(curr_m, 0.0)
        if prev_m:
            if prev_m in realized_months:
                prev_rev = monthly_data[c]["Receita Hanzo"]["real"].get(prev_m, 0.0)
            else:
                prev_rev = monthly_data[c]["Receita Hanzo"]["plan"].get(prev_m, 0.0)
    client_growth_mom[c] = (curr_rev - prev_rev) / prev_rev if prev_rev > 0 else 0.0

    # 2. YoY growth
    rev_2025 = overview_data.get(c, {}).get("2025", {}).get("Receita Hanzo", 0.0)
    rev_2026_proj = 0.0
    if c in monthly_data:
        for m in EN_MONTHS:
            if m in realized_months:
                rev_2026_proj += monthly_data[c]["Receita Hanzo"]["real"].get(m, 0.0)
            else:
                rev_2026_proj += monthly_data[c]["Receita Hanzo"]["plan"].get(m, 0.0)
    else:
        rev_2026_proj = overview_data.get(c, {}).get("2026", {}).get("Receita Hanzo", 0.0)
    client_growth_yoy[c] = (rev_2026_proj - rev_2025) / rev_2025 if rev_2025 > 0 else 0.0

    # 3. YTD and Forecast metrics
    c_rec_plan = 0.0
    c_rec_real = 0.0
    c_gmv_plan = 0.0
    c_gmv_real = 0.0
    c_ped_plan = 0.0
    c_ped_real = 0.0
    
    if c in monthly_data:
        for m in analysis_months:
            c_rec_plan += monthly_data[c]["Receita Hanzo"]["plan"].get(m, 0.0)
            c_gmv_plan += monthly_data[c]["GMV"]["plan"].get(m, 0.0)
            c_ped_plan += monthly_data[c]["Pedidos"]["plan"].get(m, 0.0)
            
            if m in realized_months:
                c_rec_real += monthly_data[c]["Receita Hanzo"]["real"].get(m, 0.0)
                c_gmv_real += monthly_data[c]["GMV"]["real"].get(m, 0.0)
                c_ped_real += monthly_data[c]["Pedidos"]["real"].get(m, 0.0)
            elif not is_ytd and not is_single_month:
                c_rec_real += monthly_data[c]["Receita Hanzo"]["plan"].get(m, 0.0)
                c_gmv_real += monthly_data[c]["GMV"]["plan"].get(m, 0.0)
                c_ped_real += monthly_data[c]["Pedidos"]["plan"].get(m, 0.0)
    
    client_revenue_vals[c] = c_rec_real
    client_gmv_vals[c] = c_gmv_real
    client_ped_vals[c] = c_ped_real
    client_diffs[c] = c_rec_real - c_rec_plan
    client_achievements[c] = c_rec_real / c_rec_plan if c_rec_plan > 0 else 1.0

    # 4. Performance Score
    gmv_ach = c_gmv_real / c_gmv_plan if c_gmv_plan > 0 else 1.0
    rec_ach = c_rec_real / c_rec_plan if c_rec_plan > 0 else 1.0
    ped_ach = c_ped_real / c_ped_plan if c_ped_plan > 0 else 1.0
    
    fy_plan_rec = sum(monthly_data[c]["Receita Hanzo"]["plan"].values()) if c in monthly_data else 1.0
    budget_ach = rev_2026_proj / fy_plan_rec if fy_plan_rec > 0 else 1.0
    
    client_scores[c] = (gmv_ach + rec_ach + ped_ach + budget_ach) / 4.0 * 100.0

total_ytd_revenue = sum(client_revenue_vals.values())
total_ytd_gmv = sum(client_gmv_vals.values())

# Sort list by YTD revenue for Top 5 / Concentrações
sorted_clients_by_rec = sorted(client_revenue_vals.items(), key=lambda x: x[1], reverse=True)
share_top5 = 0.0
dependency_largest = 0.0
largest_client_name = "Nenhum"

if total_ytd_revenue > 0:
    share_top5 = sum(v for k, v in sorted_clients_by_rec[:5]) / total_ytd_revenue
    dependency_largest = sorted_clients_by_rec[0][1] / total_ytd_revenue
    largest_client_name = sorted_clients_by_rec[0][0]

# Pre-calculate client variances
client_variances = []
for c in filtered_clients:
    if c not in monthly_data:
        continue
    client_variances.append({
        "Cliente": c,
        "Receita Real": client_revenue_vals[c],
        "Receita Plan": client_revenue_vals[c] - client_diffs[c],
        "Receita Perdida": client_diffs[c],
        "Receita Var %": client_achievements[c] - 1.0,
        "GMV Perdido": client_gmv_vals[c] - sum(monthly_data[c]["GMV"]["plan"].get(m, 0.0) for m in analysis_months),
        "GMV Var %": (client_gmv_vals[c] / sum(monthly_data[c]["GMV"]["plan"].get(m, 0.0) for m in analysis_months) - 1.0) if sum(monthly_data[c]["GMV"]["plan"].get(m, 0.0) for m in analysis_months) > 0 else 0.0,
        "Pedidos Perdidos": client_ped_vals[c] - sum(monthly_data[c]["Pedidos"]["plan"].get(m, 0.0) for m in analysis_months),
        "Pedidos Var %": (client_ped_vals[c] / sum(monthly_data[c]["Pedidos"]["plan"].get(m, 0.0) for m in analysis_months) - 1.0) if sum(monthly_data[c]["Pedidos"]["plan"].get(m, 0.0) for m in analysis_months) > 0 else 0.0
    })

# Take Rate Analytics
take_rates_list = []
for c in filtered_clients:
    if c not in monthly_data:
        continue
    c_rec = sum(monthly_data[c]["Receita Hanzo"]["plan"].values())
    c_gmv = sum(monthly_data[c]["GMV"]["plan"].values())
    if c_gmv > 0:
        take_rates_list.append({"Cliente": c, "Take Rate": c_rec / c_gmv, "GMV": c_gmv})
df_tr = pd.DataFrame(take_rates_list)
if not df_tr.empty:
    df_tr_low = df_tr.sort_values("Take Rate").head(5).copy()
else:
    df_tr_low = pd.DataFrame([{"Cliente": "Nenhum", "Take Rate": 0.0, "GMV": 0.0}])

# Projections & Multipliers
conservador_mult = 0.85
base_mult = 1.00
otimista_mult = 1.15

years_proj = ["2026", "2027", "2028"]
rec_proj_base = {yr: sum(overview_data[c][yr]["Receita Hanzo"] for c in filtered_clients if c in overview_data) for yr in years_proj}
gmv_proj_base = {yr: sum(overview_data[c][yr]["GMV"] for c in filtered_clients if c in overview_data) for yr in years_proj}
ped_proj_base = {yr: sum(overview_data[c][yr]["Pedidos"] for c in filtered_clients if c in overview_data) for yr in years_proj}

# Attainment and Probabilities
rec_attainment = kpi_data["rec_real"] / kpi_data["rec_plan"] * 100 if kpi_data["rec_plan"] > 0 else 0.0
prob_atingimento = "ALTA" if rec_var_pct >= 0 else "MODERADA" if rec_var_pct >= -0.05 else "BAIXA"

# YoY Growth Rate
yoy_gmv_growth = (sum(overview_data[c]['2026']['GMV'] for c in filtered_clients if c in overview_data) - kpi_data["gmv_2025"]) / kpi_data["gmv_2025"] if kpi_data["gmv_2025"] > 0 else 0.0
yoy_rec_growth = (sum(overview_data[c]['2026']['Receita Hanzo'] for c in filtered_clients if c in overview_data) - kpi_data["rec_2025"]) / kpi_data["rec_2025"] if kpi_data["rec_2025"] > 0 else 0.0

# HTML Generators for Executive Leaderboard (Simplified to 5 columns)
def generate_revenue_ranking_html(data_list):
    html = "<div class='executive-table-container'><table class='executive-table'><thead><tr>"
    html += "<th>Rank</th><th>Cliente</th><th class='numeric'>Receita</th><th class='numeric'>Share</th><th style='text-align:center;'>Status</th>"
    html += "</tr></thead><tbody>"
    for idx, row in enumerate(data_list):
        status_badge = get_client_status_badge(row['achievement'])
        html += f"<tr>"
        html += f"<td>{idx+1}</td>"
        html += f"<td><b>{row['client']}</b></td>"
        html += f"<td class='numeric'>R$ {row['revenue']:,.0f}</td>"
        html += f"<td class='numeric'>{row['share']*100:.1f}%</td>"
        html += f"<td style='text-align:center;'>{status_badge}</td>"
        html += f"</tr>"
    html += "</tbody></table></div>"
    return html

def generate_gmv_ranking_html(data_list):
    html = "<div class='executive-table-container'><table class='executive-table'><thead><tr>"
    html += "<th>Rank</th><th>Cliente</th><th class='numeric'>GMV</th><th class='numeric'>Share</th><th style='text-align:center;'>Status</th>"
    html += "</tr></thead><tbody>"
    for idx, row in enumerate(data_list):
        status_badge = get_client_status_badge(row['achievement'])
        html += f"<tr>"
        html += f"<td>{idx+1}</td>"
        html += f"<td><b>{row['client']}</b></td>"
        html += f"<td class='numeric'>R$ {row['gmv']:,.0f}</td>"
        html += f"<td class='numeric'>{row['share']*100:.1f}%</td>"
        html += f"<td style='text-align:center;'>{status_badge}</td>"
        html += f"</tr>"
    html += "</tbody></table></div>"
    return html

def generate_budget_ranking_html(data_list):
    html = "<div class='executive-table-container'><table class='executive-table'><thead><tr>"
    html += "<th>Rank</th><th>Cliente</th><th class='numeric'>Diferença</th><th class='numeric'>Atingimento</th><th style='text-align:center;'>Status</th>"
    html += "</tr></thead><tbody>"
    for idx, row in enumerate(data_list):
        status_badge = get_client_status_badge(row['achievement'])
        dev_color = '#16A34A' if row['diff']>=0 else '#DC2626'
        html += f"<tr>"
        html += f"<td>{idx+1}</td>"
        html += f"<td><b>{row['client']}</b></td>"
        html += f"<td class='numeric' style='color:{dev_color}'>R$ {row['diff']:+,.0f}</td>"
        html += f"<td class='numeric' style='font-weight:700;'>{row['achievement']*100:.1f}%</td>"
        html += f"<td style='text-align:center;'>{status_badge}</td>"
        html += f"</tr>"
    html += "</tbody></table></div>"
    return html

# ----------------------------------------------------
# TAB 1: VISÃO EXECUTIVA PRESIDÊNCIA
# ----------------------------------------------------
if selected_tab == "🏛 Presidency Overview":
    st.markdown(
        f"<div class='title-container'>"
        f"<h1>CFO Painel Executivo — Visão Presidência</h1>"
        f"<p>Análise de Performance de Clientes, GMV e Receita — Referência: {selected_month_label} {selected_year}</p>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # Executive Performance Leaderboard (Priority 1)
    st.markdown("### 🏆 Executive Performance Leaderboard")
    
    ranking_rev_data = []
    for c in filtered_clients:
        ranking_rev_data.append({
            "client": c,
            "revenue": client_revenue_vals[c],
            "share": client_revenue_vals[c] / total_ytd_revenue if total_ytd_revenue > 0 else 0.0,
            "mom": client_growth_mom[c],
            "yoy": client_growth_yoy[c],
            "achievement": client_achievements[c]
        })
    ranking_rev_data = sorted(ranking_rev_data, key=lambda x: x["revenue"], reverse=True)[:5]
    
    ranking_gmv_data = []
    for c in filtered_clients:
        ranking_gmv_data.append({
            "client": c,
            "gmv": client_gmv_vals[c],
            "share": client_gmv_vals[c] / total_ytd_gmv if total_ytd_gmv > 0 else 0.0,
            "mom": client_growth_mom[c],
            "yoy": client_growth_yoy[c],
            "achievement": client_achievements[c]
        })
    ranking_gmv_data = sorted(ranking_gmv_data, key=lambda x: x["gmv"], reverse=True)[:5]
    
    ranking_champs_data = []
    for c in filtered_clients:
        if c not in monthly_data:
            continue
        ranking_champs_data.append({
            "client": c,
            "achievement": client_achievements[c],
            "diff": client_diffs[c]
        })
    ranking_champs_data = sorted(ranking_champs_data, key=lambda x: x["achievement"], reverse=True)[:5]
    
    ranking_detractors_data = []
    for c in filtered_clients:
        if c not in monthly_data:
            continue
        ranking_detractors_data.append({
            "client": c,
            "achievement": client_achievements[c],
            "diff": client_diffs[c]
        })
    ranking_detractors_data = sorted(ranking_detractors_data, key=lambda x: x["achievement"], reverse=False)[:5]
    
    col_lead1, col_lead2, col_lead3, col_lead4 = st.columns(4)
    with col_lead1:
        st.markdown("<h5 style='font-family:Outfit; font-weight:600; text-align:center;'>Top Clientes por Receita</h5>", unsafe_allow_html=True)
        st.markdown(generate_revenue_ranking_html(ranking_rev_data), unsafe_allow_html=True)
    with col_lead2:
        st.markdown("<h5 style='font-family:Outfit; font-weight:600; text-align:center;'>Top Clientes por GMV</h5>", unsafe_allow_html=True)
        st.markdown(generate_gmv_ranking_html(ranking_gmv_data), unsafe_allow_html=True)
    with col_lead3:
        st.markdown("<h5 style='font-family:Outfit; font-weight:600; text-align:center;'>Budget Champions</h5>", unsafe_allow_html=True)
        st.markdown(generate_budget_ranking_html(ranking_champs_data), unsafe_allow_html=True)
    with col_lead4:
        st.markdown("<h5 style='font-family:Outfit; font-weight:600; text-align:center;'>Budget Detractors</h5>", unsafe_allow_html=True)
        st.markdown(generate_budget_ranking_html(ranking_detractors_data), unsafe_allow_html=True)

    # Executive Business Alerts Section
    st.markdown("### 🔔 Alertas de Negócios e Governança")
    alert_triggered = False
    col_al1, col_al2 = st.columns(2)
    
    # Pre-calculate concentration shares for alert check
    client_revenues_ytd = {}
    for c in filtered_clients:
        c_rec = 0.0
        if c in monthly_data:
            for m in analysis_months:
                if m in realized_months:
                    c_rec += monthly_data[c]["Receita Hanzo"]["real"].get(m, 0.0)
                elif not is_ytd and not is_single_month:
                    c_rec += monthly_data[c]["Receita Hanzo"]["plan"].get(m, 0.0)
        client_revenues_ytd[c] = c_rec
        
    total_ytd_revenue = sum(client_revenues_ytd.values())
    sorted_clients_by_rec = sorted(client_revenues_ytd.items(), key=lambda x: x[1], reverse=True)
    
    share_top5 = 0.0
    dependency_largest = 0.0
    
    if total_ytd_revenue > 0:
        share_top5 = sum(v for k, v in sorted_clients_by_rec[:5]) / total_ytd_revenue
        dependency_largest = sorted_clients_by_rec[0][1] / total_ytd_revenue
        
    with col_al1:
        # Alerts for drop vs plan
        if rec_var_pct < -0.10:
            st.markdown(
                f"<div class='executive-alert executive-alert-danger'>"
                f"<div>"
                f"<div class='executive-alert-title'>RETRAÇÃO DE RECEITA CRÍTICA</div>"
                f"<div class='executive-alert-desc'>A receita realizada ficou {abs(rec_var_pct)*100:.1f}% abaixo da meta orçada.</div>"
                f"</div></div>",
                unsafe_allow_html=True
            )
            alert_triggered = True
        if gmv_var_pct < -0.10:
            st.markdown(
                f"<div class='executive-alert executive-alert-danger'>"
                f"<div>"
                f"<div class='executive-alert-title'>DESVIO DE GMV CRÍTICO</div>"
                f"<div class='executive-alert-desc'>O GMV realizado das marcas parceiras ficou {abs(gmv_var_pct)*100:.1f}% abaixo da meta.</div>"
                f"</div></div>",
                unsafe_allow_html=True
            )
            alert_triggered = True
            
    with col_al2:
        # Alerts for concentration
        if share_top5 > 0.50:
            st.markdown(
                f"<div class='executive-alert executive-alert-warning'>"
                f"<div>"
                f"<div class='executive-alert-title'>ALTA CONCENTRAÇÃO DE CARTEIRA</div>"
                f"<div class='executive-alert-desc'>Os 5 maiores clientes representam {share_top5*100:.1f}% da receita da companhia.</div>"
                f"</div></div>",
                unsafe_allow_html=True
            )
            alert_triggered = True
        if dependency_largest > 0.25:
            st.markdown(
                f"<div class='executive-alert executive-alert-danger'>"
                f"<div>"
                f"<div class='executive-alert-title'>DEPENDÊNCIA DO MAIOR PARCEIRO CRÍTICA</div>"
                f"<div class='executive-alert-desc'>O maior cliente da Hanzo representa {dependency_largest*100:.1f}% do faturamento.</div>"
                f"</div></div>",
                unsafe_allow_html=True
            )
            alert_triggered = True
            
    if not alert_triggered:
        st.markdown(
            f"<div class='executive-alert executive-alert-success'>"
            f"<div>"
            f"<div class='executive-alert-title'>OPERAÇÃO DENTRO DOS LIMITES DE GOVERNANÇA</div>"
            f"<div class='executive-alert-desc'>Não foram detectados desvios críticos de receita ou concentração de carteira no período.</div>"
            f"</div></div>",
            unsafe_allow_html=True
        )

    # Core Metrics Cards Grid
    st.markdown("### 🔑 Indicadores Financeiros e Operacionais")
    
    take_rate_real = kpi_data["rec_real"] / kpi_data["gmv_real"] if kpi_data["gmv_real"] > 0 else 0.0
    take_rate_plan = kpi_data["rec_plan"] / kpi_data["gmv_plan"] if kpi_data["gmv_plan"] > 0 else 0.0
    take_rate_diff = take_rate_real - take_rate_plan
    
    rec_per_ped_real = kpi_data["rec_real"] / kpi_data["ped_real"] if kpi_data["ped_real"] > 0 else 0.0
    rec_per_ped_plan = kpi_data["rec_plan"] / kpi_data["ped_plan"] if kpi_data["ped_plan"] > 0 else 0.0
    rec_per_ped_diff = rec_per_ped_real - rec_per_ped_plan
    
    gmv_per_ped_real = kpi_data["gmv_real"] / kpi_data["ped_real"] if kpi_data["ped_real"] > 0 else 0.0
    gmv_per_ped_plan = kpi_data["gmv_plan"] / kpi_data["ped_plan"] if kpi_data["ped_plan"] > 0 else 0.0
    gmv_per_ped_diff = gmv_per_ped_real - gmv_per_ped_plan
    
    col_k1, col_k2, col_k3 = st.columns(3)
    col_k4, col_k5, col_k6 = st.columns(3)
    col_k7, col_k8, col_k9 = st.columns(3)
    
    # Helper to render metric cards
    def render_card(col, title, value, plan_val, var_pct, is_currency=True, prefix=""):
        delta_class = "delta-positive" if var_pct >= 0 else "delta-negative"
        delta_symbol = "▲" if var_pct >= 0 else "▼"
        val_str = f"R$ {value:,.2f}" if is_currency else f"{value:,.0f}"
        plan_str = f"R$ {plan_val:,.2f}" if is_currency else f"{plan_val:,.0f}"
        
        col.markdown(
            f"<div class='metric-card accent-blue'>"
            f"<div class='metric-card-title'>{title}</div>"
            f"<div class='metric-card-value'>{prefix}{val_str}</div>"
            f"<div class='metric-card-delta {delta_class}'>{delta_symbol} {var_pct*100:+.1f}% vs. Orçado ({plan_str})</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    render_card(col_k1, "GMV Total", kpi_data["gmv_real"], kpi_data["gmv_plan"], gmv_var_pct)
    render_card(col_k2, "Receita Total Hanzo", kpi_data["rec_real"], kpi_data["rec_plan"], rec_var_pct)
    render_card(col_k3, "Pedidos Totais", kpi_data["ped_real"], kpi_data["ped_plan"], ped_var_pct, is_currency=False)
    
    # Clients Cards
    col_k4.markdown(
        f"<div class='metric-card accent-slate'>"
        f"<div class='metric-card-title'>Clientes Ativos</div>"
        f"<div class='metric-card-value'>{kpi_data['active_clients']}</div>"
        f"<div class='metric-card-delta delta-neutral'>Carteira de Recorrência</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    col_k5.markdown(
        f"<div class='metric-card accent-green'>"
        f"<div class='metric-card-title'>Novos Clientes</div>"
        f"<div class='metric-card-value'>{kpi_data['new_clients']}</div>"
        f"<div class='metric-card-delta delta-positive'>Go-live em 2026</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    col_k6.markdown(
        f"<div class='metric-card accent-amber'>"
        f"<div class='metric-card-title'>Pipeline Comercial</div>"
        f"<div class='metric-card-value'>{kpi_data['pipeline_clients']}</div>"
        f"<div class='metric-card-delta delta-neutral'>Projeção para 2027/28</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # Financial Ratios
    # Take Rate Card
    take_rate_delta_symbol = "▲" if take_rate_diff >= 0 else "▼"
    take_rate_delta_class = "delta-positive" if take_rate_diff >= 0 else "delta-negative"
    col_k7.markdown(
        f"<div class='metric-card accent-slate'>"
        f"<div class='metric-card-title'>Take Rate Médio</div>"
        f"<div class='metric-card-value'>{take_rate_real*100:.2f}%</div>"
        f"<div class='metric-card-delta {take_rate_delta_class}'>{take_rate_delta_symbol} {take_rate_diff*100:+.2f}% vs. Orçado ({take_rate_plan*100:.2f}%)</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # Receita por Pedido
    rec_per_ped_delta_symbol = "▲" if rec_per_ped_diff >= 0 else "▼"
    rec_per_ped_delta_class = "delta-positive" if rec_per_ped_diff >= 0 else "delta-negative"
    col_k8.markdown(
        f"<div class='metric-card accent-slate'>"
        f"<div class='metric-card-title'>Receita por Pedido</div>"
        f"<div class='metric-card-value'>R$ {rec_per_ped_real:,.2f}</div>"
        f"<div class='metric-card-delta {rec_per_ped_delta_class}'>{rec_per_ped_delta_symbol} R$ {rec_per_ped_diff:+.2f} vs. Orçado (R$ {rec_per_ped_plan:,.2f})</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # GMV por Pedido
    gmv_per_ped_delta_symbol = "▲" if gmv_per_ped_diff >= 0 else "▼"
    gmv_per_ped_delta_class = "delta-positive" if gmv_per_ped_diff >= 0 else "delta-negative"
    col_k9.markdown(
        f"<div class='metric-card accent-slate'>"
        f"<div class='metric-card-title'>GMV por Pedido</div>"
        f"<div class='metric-card-value'>R$ {gmv_per_ped_real:,.2f}</div>"
        f"<div class='metric-card-delta {gmv_per_ped_delta_class}'>{gmv_per_ped_delta_symbol} R$ {gmv_per_ped_diff:+.2f} vs. Orçado (R$ {gmv_per_ped_plan:,.2f})</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    # Budget vs Actual Analysis Table
    st.markdown("### 📊 Budget vs. Actual YTD Analysis")
    
    budget_vs_actual_df = pd.DataFrame([
        {
            "Métrica": "GMV (R$)",
            "Orçado (Plan)": f"R$ {kpi_data['gmv_plan']:,.2f}",
            "Realizado (Actual)": f"R$ {kpi_data['gmv_real']:,.2f}",
            "Desvio (Variance)": f"R$ {gmv_var:,.2f}",
            "Desvio %": f"{gmv_var_pct*100:+.2f}%"
        },
        {
            "Métrica": "Receita Hanzo (R$)",
            "Orçado (Plan)": f"R$ {kpi_data['rec_plan']:,.2f}",
            "Realizado (Actual)": f"R$ {kpi_data['rec_real']:,.2f}",
            "Desvio (Variance)": f"R$ {rec_var:,.2f}",
            "Desvio %": f"{rec_var_pct*100:+.2f}%"
        },
        {
            "Métrica": "Pedidos (Qtd)",
            "Orçado (Plan)": f"{kpi_data['ped_plan']:,.0f}",
            "Realizado (Actual)": f"{kpi_data['ped_real']:,.0f}",
            "Desvio (Variance)": f"{ped_var:,.0f}",
            "Desvio %": f"{ped_var_pct*100:+.2f}%"
        }
    ])
    
    # HTML Rendered Table
    html_b_v_a = "<div class='executive-table-container'><table class='executive-table'><thead><tr>"
    for col in budget_vs_actual_df.columns:
        html_b_v_a += f"<th>{col}</th>"
    html_b_v_a += "</tr></thead><tbody>"
    for _, row in budget_vs_actual_df.iterrows():
        # Highlight desvio negative red or positive green
        desv_val = row["Desvio %"]
        desv_style = "color:#16A34A;" if "+" in desv_val else "color:#DC2626;"
        html_b_v_a += "<tr>"
        html_b_v_a += f"<td>{row['Métrica']}</td>"
        html_b_v_a += f"<td class='numeric'>{row['Orçado (Plan)']}</td>"
        html_b_v_a += f"<td class='numeric'>{row['Realizado (Actual)']}</td>"
        html_b_v_a += f"<td class='numeric' style='{desv_style}'>{row['Desvio (Variance)']}</td>"
        html_b_v_a += f"<td class='numeric' style='{desv_style}'>{row['Desvio %']}</td>"
        html_b_v_a += "</tr>"
    html_b_v_a += "</tbody></table></div>"
    st.markdown(html_b_v_a, unsafe_allow_html=True)

    # Attainment Gauges & Monthly Trend
    col_t1, col_t2 = st.columns([1, 2])
    
    with col_t1:
        st.markdown("#### 🎯 Atingimento de Metas (Meta vs Realizado)")
        # Plot Plotly Gauges
        fig_g = go.Figure()
        
        # Revenue Gauge
        rev_attainment = kpi_data["rec_real"] / kpi_data["rec_plan"] * 100 if kpi_data["rec_plan"] > 0 else 0.0
        fig_g.add_trace(go.Indicator(
            mode = "gauge+number",
            value = rev_attainment,
            title = {'text': "Receita Hanzo YTD (%)", 'font': {'size': 14, 'family': 'Outfit'}},
            domain = {'x': [0.1, 0.9], 'y': [0.65, 0.95]},
            gauge = {
                'axis': {'range': [None, 150]},
                'bar': {'color': "#002060"},
                'steps': [
                    {'range': [0, 90], 'color': "#FEE2E2"},
                    {'range': [90, 100], 'color': "#FEF3C7"},
                    {'range': [100, 150], 'color': "#DCFCE7"}
                ],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 100}
            }
        ))
        
        # GMV Gauge
        gmv_attainment = kpi_data["gmv_real"] / kpi_data["gmv_plan"] * 100 if kpi_data["gmv_plan"] > 0 else 0.0
        fig_g.add_trace(go.Indicator(
            mode = "gauge+number",
            value = gmv_attainment,
            title = {'text': "GMV Clientes YTD (%)", 'font': {'size': 14, 'family': 'Outfit'}},
            domain = {'x': [0.1, 0.9], 'y': [0.30, 0.60]},
            gauge = {
                'axis': {'range': [None, 150]},
                'bar': {'color': "#64748B"},
                'steps': [
                    {'range': [0, 90], 'color': "#FEE2E2"},
                    {'range': [90, 100], 'color': "#FEF3C7"},
                    {'range': [100, 150], 'color': "#DCFCE7"}
                ],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 100}
            }
        ))
        
        # Orders Gauge
        ped_attainment = kpi_data["ped_real"] / kpi_data["ped_plan"] * 100 if kpi_data["ped_plan"] > 0 else 0.0
        fig_g.add_trace(go.Indicator(
            mode = "gauge+number",
            value = ped_attainment,
            title = {'text': "Pedidos Totais YTD (%)", 'font': {'size': 14, 'family': 'Outfit'}},
            domain = {'x': [0.1, 0.9], 'y': [0.0, 0.25]},
            gauge = {
                'axis': {'range': [None, 150]},
                'bar': {'color': "#16A34A"},
                'steps': [
                    {'range': [0, 90], 'color': "#FEE2E2"},
                    {'range': [90, 100], 'color': "#FEF3C7"},
                    {'range': [100, 150], 'color': "#DCFCE7"}
                ],
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 100}
            }
        ))
        
        fig_g.update_layout(height=500, margin=dict(t=30, b=10, l=10, r=10))
        st.plotly_chart(fig_g, use_container_width=True)
        
    with col_t2:
        st.markdown("#### 📈 Tendência Histórica Mensal")
        
        # Calculate monthly totals
        monthly_gmv_plan = []
        monthly_gmv_real = []
        monthly_rec_plan = []
        monthly_rec_real = []
        
        for m in EN_MONTHS:
            gp = sum(monthly_data[c]["GMV"]["plan"].get(m, 0.0) for c in filtered_clients if c in monthly_data)
            gr = sum(monthly_data[c]["GMV"]["real"].get(m, 0.0) for c in filtered_clients if c in monthly_data)
            rp = sum(monthly_data[c]["Receita Hanzo"]["plan"].get(m, 0.0) for c in filtered_clients if c in monthly_data)
            rr = sum(monthly_data[c]["Receita Hanzo"]["real"].get(m, 0.0) for c in filtered_clients if c in monthly_data)
            
            monthly_gmv_plan.append(gp)
            monthly_rec_plan.append(rp)
            
            # Realized is only plotted for realized months, otherwise None
            if m in realized_months:
                monthly_gmv_real.append(gr)
                monthly_rec_real.append(rr)
            else:
                monthly_gmv_real.append(None)
                monthly_rec_real.append(None)
                
        # Cumulative
        cum_rec_plan = np.cumsum([x for x in monthly_rec_plan])
        # For actuals, we only cumulate realized
        cum_rec_real = []
        c_sum = 0.0
        for x in monthly_rec_real:
            if x is not None:
                c_sum += x
                cum_rec_real.append(c_sum)
            else:
                cum_rec_real.append(None)
                
        # Display selection
        chart_metric = st.selectbox("Métrica do Gráfico", ["Receita Hanzo", "GMV", "Pedidos"])
        
        fig_trend = go.Figure()
        
        pt_months_labels = [EN_TO_PT[m] for m in EN_MONTHS]
        
        if chart_metric == "Receita Hanzo":
            # Bar for monthly plan
            fig_trend.add_trace(go.Bar(
                x=pt_months_labels, y=monthly_rec_plan,
                name='Meta Receita Mensal', marker_color='#E2E8F0',
                hovertemplate='R$ %{y:,.2f}'
            ))
            # Bar for monthly real
            fig_trend.add_trace(go.Bar(
                x=pt_months_labels, y=monthly_rec_real,
                name='Realizado Receita Mensal', marker_color='#002060',
                hovertemplate='R$ %{y:,.2f}'
            ))
            # Line for cumulative plan
            fig_trend.add_trace(go.Scatter(
                x=pt_months_labels, y=cum_rec_plan,
                name='Acumulado Meta', line=dict(color='#64748B', width=2, dash='dash'),
                yaxis='y2', hovertemplate='R$ %{y:,.2f}'
            ))
            # Line for cumulative real
            fig_trend.add_trace(go.Scatter(
                x=pt_months_labels, y=cum_rec_real,
                name='Acumulado Real', line=dict(color='#16A34A', width=3),
                yaxis='y2', hovertemplate='R$ %{y:,.2f}'
            ))
            
            y_title = "Mensal (R$)"
            y2_title = "Acumulado (R$)"
        elif chart_metric == "GMV":
            cum_gmv_plan = np.cumsum(monthly_gmv_plan)
            cum_gmv_real = []
            cg_sum = 0.0
            for x in monthly_gmv_real:
                if x is not None:
                    cg_sum += x
                    cum_gmv_real.append(cg_sum)
                else:
                    cum_gmv_real.append(None)
                    
            fig_trend.add_trace(go.Bar(
                x=pt_months_labels, y=monthly_gmv_plan,
                name='Meta GMV Mensal', marker_color='#E2E8F0',
                hovertemplate='R$ %{y:,.2f}'
            ))
            fig_trend.add_trace(go.Bar(
                x=pt_months_labels, y=monthly_gmv_real,
                name='Realizado GMV Mensal', marker_color='#64748B',
                hovertemplate='R$ %{y:,.2f}'
            ))
            fig_trend.add_trace(go.Scatter(
                x=pt_months_labels, y=cum_gmv_plan,
                name='Acumulado Meta', line=dict(color='#475569', width=2, dash='dash'),
                yaxis='y2', hovertemplate='R$ %{y:,.2f}'
            ))
            fig_trend.add_trace(go.Scatter(
                x=pt_months_labels, y=cum_gmv_real,
                name='Acumulado Real', line=dict(color='#16A34A', width=3),
                yaxis='y2', hovertemplate='R$ %{y:,.2f}'
            ))
            y_title = "Mensal (R$)"
            y2_title = "Acumulado (R$)"
        else:
            monthly_ped_plan = [sum(monthly_data[c]["Pedidos"]["plan"].get(m, 0.0) for c in filtered_clients if c in monthly_data) for m in EN_MONTHS]
            monthly_ped_real = [sum(monthly_data[c]["Pedidos"]["real"].get(m, 0.0) for c in filtered_clients if c in monthly_data) if m in realized_months else None for m in EN_MONTHS]
            cum_ped_plan = np.cumsum(monthly_ped_plan)
            cum_ped_real = []
            cp_sum = 0.0
            for x in monthly_ped_real:
                if x is not None:
                    cp_sum += x
                    cum_ped_real.append(cp_sum)
                else:
                    cum_ped_real.append(None)
                    
            fig_trend.add_trace(go.Bar(
                x=pt_months_labels, y=monthly_ped_plan,
                name='Meta Pedidos Mensal', marker_color='#E2E8F0',
                hovertemplate='%{y:,.0f}'
            ))
            fig_trend.add_trace(go.Bar(
                x=pt_months_labels, y=monthly_ped_real,
                name='Realizado Pedidos Mensal', marker_color='#16A34A',
                hovertemplate='%{y:,.0f}'
            ))
            fig_trend.add_trace(go.Scatter(
                x=pt_months_labels, y=cum_ped_plan,
                name='Acumulado Meta', line=dict(color='#64748B', width=2, dash='dash'),
                yaxis='y2', hovertemplate='%{y:,.0f}'
            ))
            fig_trend.add_trace(go.Scatter(
                x=pt_months_labels, y=cum_ped_real,
                name='Acumulado Real', line=dict(color='#10B981', width=3),
                yaxis='y2', hovertemplate='%{y:,.0f}'
            ))
            y_title = "Mensal (Qtd)"
            y2_title = "Acumulado (Qtd)"

        fig_trend.update_layout(
            yaxis=dict(title=y_title),
            yaxis2=dict(title=y2_title, overlaying='y', side='right'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor='#FFFFFF',
            margin=dict(t=50, b=20, l=10, r=10),
            height=400
        )
        fig_trend.update_xaxes(showgrid=True, gridcolor='#F1F5F9')
        fig_trend.update_yaxes(showgrid=True, gridcolor='#F1F5F9')
        
        st.plotly_chart(fig_trend, use_container_width=True)

# ----------------------------------------------------
# TAB 2: RANKING DE CLIENTES E CONCENTRAÇÃO
# ----------------------------------------------------
elif selected_tab == "🏆 Client Rankings":
    st.markdown(
        f"<div class='title-container'>"
        f"<h1>Ranking e Concentração de Clientes</h1>"
        f"<p>Análise de Concentração de Receita, GMV, Pedidos e Governança Comercial — {selected_month_label} 2026</p>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # 📐 Matrizes Orçado x Realizado (Foco Executivo)
    st.markdown("### 📊 Performance vs Orçamento (Orçado x Realizado)")
    st.markdown(
        "<div style='font-size: 12px; color: #64748B; margin-bottom: 15px; font-style: italic;'>"
        "Nota: O Scorecard Consolidado de performance (onde exibido) representa a média de atingimento de GMV, Receita e Pedidos em relação ao orçamento planejado."
        "</div>",
        unsafe_allow_html=True
    )
    
    # Calculate client matrix data
    client_matrix_data = []
    for c in filtered_clients:
        c_rec_real = 0.0
        c_gmv_real = 0.0
        c_ped_real = 0.0
        c_rec_plan = 0.0
        c_gmv_plan = 0.0
        c_ped_plan = 0.0
        
        if c in monthly_data:
            for m in analysis_months:
                c_rec_plan += monthly_data[c]["Receita Hanzo"]["plan"].get(m, 0.0)
                c_gmv_plan += monthly_data[c]["GMV"]["plan"].get(m, 0.0)
                c_ped_plan += monthly_data[c]["Pedidos"]["plan"].get(m, 0.0)
                
                if m in realized_months:
                    c_rec_real += monthly_data[c]["Receita Hanzo"]["real"].get(m, 0.0)
                    c_gmv_real += monthly_data[c]["GMV"]["real"].get(m, 0.0)
                    c_ped_real += monthly_data[c]["Pedidos"]["real"].get(m, 0.0)
                elif not is_ytd and not is_single_month:
                    c_rec_real += monthly_data[c]["Receita Hanzo"]["plan"].get(m, 0.0)
                    c_gmv_real += monthly_data[c]["GMV"]["plan"].get(m, 0.0)
                    c_ped_real += monthly_data[c]["Pedidos"]["plan"].get(m, 0.0)
                    
        gmv_ach = c_gmv_real / c_gmv_plan * 100 if c_gmv_plan > 0 else 100.0
        rec_ach = c_rec_real / c_rec_plan * 100 if c_rec_plan > 0 else 100.0
        ped_ach = c_ped_real / c_ped_plan * 100 if c_ped_plan > 0 else 100.0
        
        client_matrix_data.append({
            "client": c,
            "gmv_plan": c_gmv_plan,
            "gmv_real": c_gmv_real,
            "gmv_diff": c_gmv_real - c_gmv_plan,
            "gmv_ach": gmv_ach,
            
            "rec_plan": c_rec_plan,
            "rec_real": c_rec_real,
            "rec_diff": c_rec_real - c_rec_plan,
            "rec_ach": rec_ach,
            
            "ped_plan": c_ped_plan,
            "ped_real": c_ped_real,
            "ped_diff": c_ped_real - c_ped_plan,
            "ped_ach": ped_ach
        })

    def get_attainment_traffic_light(pct):
        if pct >= 95.0:
            return "🟢"
        elif pct >= 90.0:
            return "🟡"
        else:
            return "🔴"

    def generate_gmv_matrix_html(data_list):
        sorted_data = sorted(data_list, key=lambda x: x["gmv_ach"], reverse=True)
        html = "<div class='executive-table-container'><table class='executive-table'><thead><tr>"
        html += "<th>Rank</th><th>Cliente</th><th class='numeric'>Orçado (Plan)</th><th class='numeric'>Realizado (Actual)</th><th class='numeric'>Diferença</th><th class='numeric'>Atingimento</th><th style='text-align:center;'>Farol</th>"
        html += "</tr></thead><tbody>"
        for idx, row in enumerate(sorted_data):
            farol = get_attainment_traffic_light(row['gmv_ach'])
            diff_color = '#16A34A' if row['gmv_diff']>=0 else '#DC2626'
            html += f"<tr>"
            html += f"<td>{idx+1}</td>"
            html += f"<td><b>{row['client']}</b></td>"
            html += f"<td class='numeric'>R$ {row['gmv_plan']:,.2f}</td>"
            html += f"<td class='numeric'>R$ {row['gmv_real']:,.2f}</td>"
            html += f"<td class='numeric' style='color:{diff_color}'>R$ {row['gmv_diff']:+,.2f}</td>"
            html += f"<td class='numeric' style='font-weight:700;'>{row['gmv_ach']:.1f}%</td>"
            html += f"<td style='text-align:center;'>{farol}</td>"
            html += f"</tr>"
        html += "</tbody></table></div>"
        return html

    def generate_rec_matrix_html(data_list):
        sorted_data = sorted(data_list, key=lambda x: x["rec_ach"], reverse=True)
        html = "<div class='executive-table-container'><table class='executive-table'><thead><tr>"
        html += "<th>Rank</th><th>Cliente</th><th class='numeric'>Orçado (Plan)</th><th class='numeric'>Realizado (Actual)</th><th class='numeric'>Diferença</th><th class='numeric'>Atingimento</th><th style='text-align:center;'>Farol</th>"
        html += "</tr></thead><tbody>"
        for idx, row in enumerate(sorted_data):
            farol = get_attainment_traffic_light(row['rec_ach'])
            diff_color = '#16A34A' if row['rec_diff']>=0 else '#DC2626'
            html += f"<tr>"
            html += f"<td>{idx+1}</td>"
            html += f"<td><b>{row['client']}</b></td>"
            html += f"<td class='numeric'>R$ {row['rec_plan']:,.2f}</td>"
            html += f"<td class='numeric'>R$ {row['rec_real']:,.2f}</td>"
            html += f"<td class='numeric' style='color:{diff_color}'>R$ {row['rec_diff']:+,.2f}</td>"
            html += f"<td class='numeric' style='font-weight:700;'>{row['rec_ach']:.1f}%</td>"
            html += f"<td style='text-align:center;'>{farol}</td>"
            html += f"</tr>"
        html += "</tbody></table></div>"
        return html

    def generate_ped_matrix_html(data_list):
        sorted_data = sorted(data_list, key=lambda x: x["ped_ach"], reverse=True)
        html = "<div class='executive-table-container'><table class='executive-table'><thead><tr>"
        html += "<th>Rank</th><th>Cliente</th><th class='numeric'>Orçado (Plan)</th><th class='numeric'>Realizado (Actual)</th><th class='numeric'>Diferença</th><th class='numeric'>Atingimento</th><th style='text-align:center;'>Farol</th>"
        html += "</tr></thead><tbody>"
        for idx, row in enumerate(sorted_data):
            farol = get_attainment_traffic_light(row['ped_ach'])
            diff_color = '#16A34A' if row['ped_diff']>=0 else '#DC2626'
            html += f"<tr>"
            html += f"<td>{idx+1}</td>"
            html += f"<td><b>{row['client']}</b></td>"
            html += f"<td class='numeric'>{row['ped_plan']:,.0f}</td>"
            html += f"<td class='numeric'>{row['ped_real']:,.0f}</td>"
            html += f"<td class='numeric' style='color:{diff_color}'>{row['ped_diff']:+,.0f}</td>"
            html += f"<td class='numeric' style='font-weight:700;'>{row['ped_ach']:.1f}%</td>"
            html += f"<td style='text-align:center;'>{farol}</td>"
            html += f"</tr>"
        html += "</tbody></table></div>"
        return html

    st.markdown("#### A) Matriz GMV — Orçado x Realizado por Cliente")
    st.markdown(generate_gmv_matrix_html(client_matrix_data), unsafe_allow_html=True)

    st.markdown("#### B) Matriz Receita — Orçado x Realizado por Cliente")
    st.markdown(generate_rec_matrix_html(client_matrix_data), unsafe_allow_html=True)

    st.markdown("#### C) Matriz Pedidos — Orçado x Realizado por Cliente")
    st.markdown(generate_ped_matrix_html(client_matrix_data), unsafe_allow_html=True)
    
    # Pre-calculate client actuals YTD
    client_kpis = []
    total_revenue_overall = 0.0
    total_gmv_overall = 0.0
    total_ped_overall = 0.0
    
    for c in filtered_clients:
        c_rec_real = 0.0
        c_gmv_real = 0.0
        c_ped_real = 0.0
        
        c_rec_2025 = overview_data[c]["2025"]["Receita Hanzo"] if c in overview_data else 0.0
        c_gmv_2025 = overview_data[c]["2025"]["GMV"] if c in overview_data else 0.0
        c_ped_2025 = overview_data[c]["2025"]["Pedidos"] if c in overview_data else 0.0
        
        if c in monthly_data:
            for m in analysis_months:
                if m in realized_months:
                    c_rec_real += monthly_data[c]["Receita Hanzo"]["real"].get(m, 0.0)
                    c_gmv_real += monthly_data[c]["GMV"]["real"].get(m, 0.0)
                    c_ped_real += monthly_data[c]["Pedidos"]["real"].get(m, 0.0)
                elif not is_ytd and not is_single_month:
                    c_rec_real += monthly_data[c]["Receita Hanzo"]["plan"].get(m, 0.0)
                    c_gmv_real += monthly_data[c]["GMV"]["plan"].get(m, 0.0)
                    c_ped_real += monthly_data[c]["Pedidos"]["plan"].get(m, 0.0)
                    
        total_revenue_overall += c_rec_real
        total_gmv_overall += c_gmv_real
        total_ped_overall += c_ped_real
        
        client_kpis.append({
            "Cliente": c,
            "Receita": c_rec_real,
            "Receita 2025": c_rec_2025,
            "GMV": c_gmv_real,
            "GMV 2025": c_gmv_2025,
            "Pedidos": c_ped_real,
            "Pedidos 2025": c_ped_2025
        })
        
    df_clients = pd.DataFrame(client_kpis)
    
    # 1. Ranking Tables (Top 20)
    col_r1, col_r2 = st.columns(2)
    
    with col_r1:
        st.markdown("#### 🏆 Top Clientes por Receita (Top 20)")
        df_rec_rank = df_clients.sort_values("Receita", ascending=False).head(20).copy()
        df_rec_rank["Ranking"] = range(1, len(df_rec_rank) + 1)
        df_rec_rank["Participação %"] = df_rec_rank["Receita"] / total_revenue_overall if total_revenue_overall > 0 else 0.0
        df_rec_rank["Crescimento %"] = (df_rec_rank["Receita"] - df_rec_rank["Receita 2025"]) / df_rec_rank["Receita 2025"]
        df_rec_rank["Crescimento %"] = df_rec_rank["Crescimento %"].apply(lambda x: f"{x*100:+.1f}%" if pd.notna(x) and not np.isinf(x) else "-")
        df_rec_rank["Receita Formato"] = df_rec_rank["Receita"].apply(lambda x: f"R$ {x:,.2f}")
        df_rec_rank["Participação Formato"] = df_rec_rank["Participação %"].apply(lambda x: f"{x*100:.2f}%")
        
        st.dataframe(
            df_rec_rank[["Ranking", "Cliente", "Receita Formato", "Participação Formato", "Crescimento %"]],
            use_container_width=True, hide_index=True
        )
        
    with col_r2:
        st.markdown("#### 💎 Top Clientes por GMV (Top 20)")
        df_gmv_rank = df_clients.sort_values("GMV", ascending=False).head(20).copy()
        df_gmv_rank["Ranking"] = range(1, len(df_gmv_rank) + 1)
        df_gmv_rank["Participação %"] = df_gmv_rank["GMV"] / total_gmv_overall if total_gmv_overall > 0 else 0.0
        df_gmv_rank["Crescimento %"] = (df_gmv_rank["GMV"] - df_gmv_rank["GMV 2025"]) / df_gmv_rank["GMV 2025"]
        df_gmv_rank["Crescimento %"] = df_gmv_rank["Crescimento %"].apply(lambda x: f"{x*100:+.1f}%" if pd.notna(x) and not np.isinf(x) else "-")
        df_gmv_rank["GMV Formato"] = df_gmv_rank["GMV"].apply(lambda x: f"R$ {x:,.2f}")
        df_gmv_rank["Participação Formato"] = df_gmv_rank["Participação %"].apply(lambda x: f"{x*100:.2f}%")
        
        st.dataframe(
            df_gmv_rank[["Ranking", "Cliente", "GMV Formato", "Participação Formato", "Crescimento %"]],
            use_container_width=True, hide_index=True
        )
        
    # Concentration Panel
    st.markdown("### 📊 Indicadores de Concentração de Receita")
    
    # Share Calculations
    df_sorted_rec = df_clients.sort_values("Receita", ascending=False).copy()
    rec_top5 = df_sorted_rec["Receita"].head(5).sum()
    rec_top10 = df_sorted_rec["Receita"].head(10).sum()
    rec_top20 = df_sorted_rec["Receita"].head(20).sum()
    
    share5 = rec_top5 / total_revenue_overall if total_revenue_overall > 0 else 0.0
    share10 = rec_top10 / total_revenue_overall if total_revenue_overall > 0 else 0.0
    share20 = rec_top20 / total_revenue_overall if total_revenue_overall > 0 else 0.0
    
    largest_client_name = df_sorted_rec.iloc[0]["Cliente"] if len(df_sorted_rec) > 0 else "Nenhum"
    largest_client_rec = df_sorted_rec.iloc[0]["Receita"] if len(df_sorted_rec) > 0 else 0.0
    largest_share = largest_client_rec / total_revenue_overall if total_revenue_overall > 0 else 0.0
    
    col_c1, col_c2, col_c3 = st.columns(3)
    
    # Semáforo de Dependência
    # Top 5: Verde < 35%, Amarelo 35-50%, Vermelho > 50%
    badge5 = "badge-green" if share5 < 0.35 else "badge-yellow" if share5 <= 0.50 else "badge-red"
    # Top 10: Verde < 55%, Amarelo 55-70%, Vermelho > 70%
    badge10 = "badge-green" if share10 < 0.55 else "badge-yellow" if share10 <= 0.70 else "badge-red"
    # Largest: Verde < 15%, Amarelo 15-25%, Vermelho > 25%
    badge_l = "badge-green" if largest_share < 0.15 else "badge-yellow" if largest_share <= 0.25 else "badge-red"
    
    col_c1.markdown(
        f"<div class='metric-card accent-slate'>"
        f"<div class='metric-card-title'>Share Top 5 Clientes</div>"
        f"<div class='metric-card-value'>{share5*100:.1f}%</div>"
        f"<div class='metric-card-delta'><span class='badge {badge5}'>Semáforo: {share5*100:.1f}%</span></div>"
        f"</div>",
        unsafe_allow_html=True
    )
    col_c2.markdown(
        f"<div class='metric-card accent-slate'>"
        f"<div class='metric-card-title'>Share Top 10 Clientes</div>"
        f"<div class='metric-card-value'>{share10*100:.1f}%</div>"
        f"<div class='metric-card-delta'><span class='badge {badge10}'>Semáforo: {share10*100:.1f}%</span></div>"
        f"</div>",
        unsafe_allow_html=True
    )
    col_c3.markdown(
        f"<div class='metric-card accent-slate'>"
        f"<div class='metric-card-title'>Dependência Maior Parceiro</div>"
        f"<div class='metric-card-value'>{largest_share*100:.1f}%</div>"
        f"<div class='metric-card-delta'><span class='badge {badge_l}'>Maior: {largest_client_name}</span></div>"
        f"</div>",
        unsafe_allow_html=True
    )

    # Donut Chart & Pareto
    col_cp1, col_cp2 = st.columns(2)
    
    with col_cp1:
        st.markdown("#### 🍩 Share Top 5 vs. Demais Clientes")
        other_rec = total_revenue_overall - rec_top5
        fig_donut = go.Figure(data=[go.Pie(
            labels=['Top 5 Clientes', 'Demais Clientes'],
            values=[rec_top5, other_rec],
            hole=.4,
            marker_colors=['#002060', '#CBD5E1']
        )])
        fig_donut.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=300)
        st.plotly_chart(fig_donut, use_container_width=True)
        
    with col_cp2:
        st.markdown("#### 📈 Gráfico de Pareto (Receita Acumulada %)")
        df_sorted_rec["CumSumRec"] = df_sorted_rec["Receita"].cumsum()
        df_sorted_rec["CumPctRec"] = df_sorted_rec["CumSumRec"] / total_revenue_overall if total_revenue_overall > 0 else 0.0
        
        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Bar(
            x=df_sorted_rec["Cliente"], y=df_sorted_rec["Receita"],
            name="Receita", marker_color="#002060"
        ))
        fig_pareto.add_trace(go.Scatter(
            x=df_sorted_rec["Cliente"], y=df_sorted_rec["CumPctRec"]*100,
            name="Receita Acumulada %", line=dict(color="#16A34A", width=3),
            yaxis="y2"
        ))
        fig_pareto.update_layout(
            yaxis=dict(title="Receita (R$)"),
            yaxis2=dict(title="Acumulado %", overlaying="y", side="right", range=[0, 105]),
            plot_bgcolor="#FFFFFF",
            margin=dict(t=20, b=20, l=10, r=10),
            height=300
        )
        st.plotly_chart(fig_pareto, use_container_width=True)
        
    # Concentration Trend & Dependency Changes
    st.markdown("### 📈 Tendência Histórica de Concentração (Últimos 6 meses)")
    # Calculate monthly top 5 share
    top5_monthly_share = []
    largest_monthly_share = []
    
    for m in realized_months:
        m_rec_dict = {}
        for c in filtered_clients:
            if c in monthly_data:
                m_rec_dict[c] = monthly_data[c]["Receita Hanzo"]["real"].get(m, 0.0)
        
        m_total = sum(m_rec_dict.values())
        sorted_m = sorted(m_rec_dict.items(), key=lambda x: x[1], reverse=True)
        
        m_top5_sum = sum(v for k, v in sorted_m[:5])
        top5_monthly_share.append(m_top5_sum / m_total if m_total > 0 else 0.0)
        largest_monthly_share.append(sorted_m[0][1] / m_total if m_total > 0 else 0.0)
        
    fig_conc_trend = go.Figure()
    fig_conc_trend.add_trace(go.Scatter(
        x=[EN_TO_PT[m] for m in realized_months], y=[x*100 for x in top5_monthly_share],
        name="Share Top 5 Clientes", line=dict(color="#002060", width=3),
        marker=dict(size=8)
    ))
    fig_conc_trend.add_trace(go.Scatter(
        x=[EN_TO_PT[m] for m in realized_months], y=[x*100 for x in largest_monthly_share],
        name="Dependência Maior Parceiro", line=dict(color="#64748B", width=2, dash="dash"),
        marker=dict(size=8)
    ))
    fig_conc_trend.update_layout(
        yaxis=dict(title="Representatividade (%)", range=[0, 105]),
        plot_bgcolor="#FFFFFF",
        height=300,
        margin=dict(t=20, b=20, l=10, r=10)
    )
    st.plotly_chart(fig_conc_trend, use_container_width=True)

# ----------------------------------------------------
# TAB 3: CLIENTES DETRATORES
# ----------------------------------------------------
elif selected_tab == "📉 Detractors":
    st.markdown(
        f"<div class='title-container'>"
        f"<h1>Clientes Detratores</h1>"
        f"<p>Análise de Deterioração de Performance e Clientes com Queda vs. Orçado — {selected_month_label} 2026</p>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # Calculate variances for all clients
    client_variances = []
    for c in filtered_clients:
        if c not in monthly_data:
            continue
        c_rec_plan = 0.0
        c_rec_real = 0.0
        c_gmv_plan = 0.0
        c_gmv_real = 0.0
        c_ped_plan = 0.0
        c_ped_real = 0.0
        
        for m in analysis_months:
            c_rec_plan += monthly_data[c]["Receita Hanzo"]["plan"].get(m, 0.0)
            c_gmv_plan += monthly_data[c]["GMV"]["plan"].get(m, 0.0)
            c_ped_plan += monthly_data[c]["Pedidos"]["plan"].get(m, 0.0)
            
            if m in realized_months:
                c_rec_real += monthly_data[c]["Receita Hanzo"]["real"].get(m, 0.0)
                c_gmv_real += monthly_data[c]["GMV"]["real"].get(m, 0.0)
                c_ped_real += monthly_data[c]["Pedidos"]["real"].get(m, 0.0)
            elif not is_ytd and not is_single_month:
                c_rec_real += monthly_data[c]["Receita Hanzo"]["plan"].get(m, 0.0)
                c_gmv_real += monthly_data[c]["GMV"]["plan"].get(m, 0.0)
                c_ped_real += monthly_data[c]["Pedidos"]["plan"].get(m, 0.0)
                
        rec_diff = c_rec_real - c_rec_plan
        gmv_diff = c_gmv_real - c_gmv_plan
        ped_diff = c_ped_real - c_ped_plan
        
        client_variances.append({
            "Cliente": c,
            "Receita Real": c_rec_real,
            "Receita Plan": c_rec_plan,
            "Receita Perdida": rec_diff,
            "Receita Var %": rec_diff / c_rec_plan if c_rec_plan > 0 else 0.0,
            "GMV Perdido": gmv_diff,
            "GMV Var %": gmv_diff / c_gmv_plan if c_gmv_plan > 0 else 0.0,
            "Pedidos Perdidos": ped_diff,
            "Pedidos Var %": ped_diff / c_ped_plan if c_ped_plan > 0 else 0.0
        })
        
    df_var = pd.DataFrame(client_variances)
    
    # Render detour lists
    col_d1, col_d2, col_d3 = st.columns(3)
    
    total_overall_rec = sum(df_var["Receita Real"])
    total_overall_gmv = sum(df_var["Receita Real"]) # used to calc share impact
    
    with col_d1:
        st.markdown("#### 📉 Detratores de Receita (Top 10)")
        df_rec_det = df_var[df_var["Receita Perdida"] < 0].sort_values("Receita Perdida").head(10).copy()
        if df_rec_det.empty:
            st.info("Nenhum cliente com retração de receita no período.")
        else:
            df_rec_det["Perda R$"] = df_rec_det["Receita Perdida"].apply(lambda x: f"R$ {x:,.2f}")
            df_rec_det["Perda %"] = df_rec_det["Receita Var %"].apply(lambda x: f"{x*100:.1f}%")
            df_rec_det["Impacto Carteira"] = (df_rec_det["Receita Perdida"] / total_overall_rec).apply(lambda x: f"{x*100:.1f}%")
            st.dataframe(df_rec_det[["Cliente", "Perda R$", "Perda %", "Impacto Carteira"]], use_container_width=True, hide_index=True)
            
    with col_d2:
        st.markdown("#### 📦 Detratores de GMV (Top 10)")
        df_gmv_det = df_var[df_var["GMV Perdido"] < 0].sort_values("GMV Perdido").head(10).copy()
        if df_gmv_det.empty:
            st.info("Nenhum cliente com retração de GMV no período.")
        else:
            df_gmv_det["Perda GMV"] = df_gmv_det["GMV Perdido"].apply(lambda x: f"R$ {x:,.2f}")
            df_gmv_det["Perda %"] = df_gmv_det["GMV Var %"].apply(lambda x: f"{x*100:.1f}%")
            st.dataframe(df_gmv_det[["Cliente", "Perda GMV", "Perda %"]], use_container_width=True, hide_index=True)
            
    with col_d3:
        st.markdown("#### 🎫 Detratores de Pedidos (Top 10)")
        df_ped_det = df_var[df_var["Pedidos Perdidos"] < 0].sort_values("Pedidos Perdidos").head(10).copy()
        if df_ped_det.empty:
            st.info("Nenhum cliente com retração de pedidos no período.")
        else:
            df_ped_det["Perda Ped"] = df_ped_det["Pedidos Perdidos"].apply(lambda x: f"{x:,.0f}")
            df_ped_det["Perda %"] = df_ped_det["Pedidos Var %"].apply(lambda x: f"{x*100:.1f}%")
            st.dataframe(df_ped_det[["Cliente", "Perda Ped", "Perda %"]], use_container_width=True, hide_index=True)

    # Monthly performance heatmap
    st.markdown("### 🌡️ Client Performance Heatmap (Queda de Lançamentos Mensais)")
    # Generate HTML code for Heatmap Table
    html_heat = "<div class='executive-table-container'><table class='executive-table'>"
    html_heat += "<thead><tr><th>Cliente</th>"
    for m in realized_months:
        html_heat += f"<th style='text-align:center;'>{EN_TO_PT[m]}</th>"
    html_heat += "</tr></thead><tbody>"
    
    for c in filtered_clients:
        if c not in monthly_data:
            continue
        html_heat += f"<tr><td>{c}</td>"
        for m in realized_months:
            m_plan = monthly_data[c]["Receita Hanzo"]["plan"].get(m, 0.0)
            m_real = monthly_data[c]["Receita Hanzo"]["real"].get(m, 0.0)
            
            m_growth = (m_real - m_plan) / m_plan if m_plan > 0 else 0.0
            
            if m_growth > 0.05:
                cell_class = "heatmap-grow"
                cell_txt = f"{m_growth*100:+.1f}%"
            elif m_growth >= -0.05:
                cell_class = "heatmap-stable"
                cell_txt = f"{m_growth*100:+.1f}%"
            else:
                cell_class = "heatmap-decline"
                cell_txt = f"{m_growth*100:+.1f}%"
                
            html_heat += f"<td class='heatmap-cell {cell_class}'>{cell_txt}</td>"
        html_heat += "</tr>"
        
    html_heat += "</tbody></table></div>"
    st.markdown(html_heat, unsafe_allow_html=True)
    
    # Mapa de Perdas Graph
    st.markdown("### 🗺️ Mapa de Perdas de Receita")
    df_losses = df_var[df_var["Receita Perdida"] < 0].copy()
    if df_losses.empty:
        st.info("Nenhuma perda detectada.")
    else:
        df_losses["Receita Perdida Abs"] = abs(df_losses["Receita Perdida"])
        fig_loss = px.treemap(
            df_losses, path=["Cliente"], values="Receita Perdida Abs",
            color="Receita Var %", color_continuous_scale="Reds",
            labels={"Receita Perdida Abs": "Perda de Receita (R$)", "Receita Var %": "Desvio %"},
            title="Distribuição da Receita Perdida vs. Orçamento por Cliente"
        )
        st.plotly_chart(fig_loss, use_container_width=True)

# ----------------------------------------------------
# TAB 4: FORECAST E PROJEÇÕES
# ----------------------------------------------------
elif selected_tab == "📈 Forecast & Budget":
    st.markdown(
        f"<div class='title-container'>"
        f"<h1>Forecast e Projeções Corporativas</h1>"
        f"<p>Visualização de Resultados Futuros e Cenários Estratégicos (2026, 2027, 2028)</p>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # Scenario Multipliers Sliders
    st.markdown("### 🎛️ Ajuste de Cenários Financeiros")
    col_sc1, col_sc2, col_sc3 = st.columns(3)
    
    conservador_mult = col_sc1.slider("Multiplicador Conservador", 0.70, 0.95, 0.85, step=0.05)
    base_mult = col_sc2.slider("Multiplicador Base", 0.95, 1.05, 1.00, step=0.05)
    otimista_mult = col_sc3.slider("Multiplicador Otimista", 1.05, 1.30, 1.15, step=0.05)
    
    # Aggregate annual projections for 2026, 2027, 2028
    years_proj = ["2026", "2027", "2028"]
    
    # Pre-calculated base projection numbers from Overview sheet
    rec_proj_base = {yr: sum(overview_data[c][yr]["Receita Hanzo"] for c in filtered_clients if c in overview_data) for yr in years_proj}
    gmv_proj_base = {yr: sum(overview_data[c][yr]["GMV"] for c in filtered_clients if c in overview_data) for yr in years_proj}
    ped_proj_base = {yr: sum(overview_data[c][yr]["Pedidos"] for c in filtered_clients if c in overview_data) for yr in years_proj}
    
    # Calculate scenarios
    scenario_results = []
    for yr in years_proj:
        # Base
        r_base = rec_proj_base[yr] * base_mult
        g_base = gmv_proj_base[yr] * base_mult
        p_base = ped_proj_base[yr] * base_mult
        
        # Conservador
        r_cons = rec_proj_base[yr] * conservador_mult
        g_cons = gmv_proj_base[yr] * conservador_mult
        p_cons = ped_proj_base[yr] * conservador_mult
        
        # Otimista
        r_optim = rec_proj_base[yr] * otimista_mult
        g_optim = gmv_proj_base[yr] * otimista_mult
        p_optim = ped_proj_base[yr] * otimista_mult
        
        scenario_results.append({
            "Ano": yr,
            "Cenário": "Conservador",
            "Receita": r_cons, "GMV": g_cons, "Pedidos": p_cons
        })
        scenario_results.append({
            "Ano": yr,
            "Cenário": "Base (Orçado)",
            "Receita": r_base, "GMV": g_base, "Pedidos": p_base
        })
        scenario_results.append({
            "Ano": yr,
            "Cenário": "Otimista",
            "Receita": r_optim, "GMV": g_optim, "Pedidos": p_optim
        })
        
    df_scenarios = pd.DataFrame(scenario_results)
    
    # Projection Grid Display
    st.markdown("### 📊 Horizonte de Projeções")
    col_pr1, col_pr2 = st.columns(2)
    
    with col_pr1:
        st.markdown("#### Projeção de Receita por Cenário")
        fig_fore_rec = px.bar(
            df_scenarios, x="Ano", y="Receita", color="Cenário",
            barmode="group", color_discrete_map={
                "Conservador": "#DC2626",
                "Base (Orçado)": "#64748B",
                "Otimista": "#16A34A"
            },
            labels={"Receita": "Receita Projetada (R$)"}
        )
        fig_fore_rec.update_layout(plot_bgcolor="#FFFFFF")
        st.plotly_chart(fig_fore_rec, use_container_width=True)
        
    with col_pr2:
        st.markdown("#### Projeção de GMV por Cenário")
        fig_fore_gmv = px.bar(
            df_scenarios, x="Ano", y="GMV", color="Cenário",
            barmode="group", color_discrete_map={
                "Conservador": "#DC2626",
                "Base (Orçado)": "#64748B",
                "Otimista": "#16A34A"
            },
            labels={"GMV": "GMV Projetado (R$)"}
        )
        fig_fore_gmv.update_layout(plot_bgcolor="#FFFFFF")
        st.plotly_chart(fig_fore_gmv, use_container_width=True)

    # Executive Waterfall Bridge 2025 -> 2026
    st.markdown("### 🧱 Waterfall Bridge (Pontes de Transição de Receita 2025 -> 2026)")
    # Calculate bridge components:
    # 1. 2025 Revenue
    rec_2025 = kpi_data["rec_2025"]
    
    # 2. Expansion of active clients
    # Clients active in 2025 who increased revenue in 2026 (Base Plan)
    expansion_val = 0.0
    churn_val = 0.0
    new_client_val = 0.0
    
    for c in filtered_clients:
        c_rec_2025 = overview_data[c]["2025"]["Receita Hanzo"] if c in overview_data else 0.0
        c_rec_2026 = overview_data[c]["2026"]["Receita Hanzo"] if c in overview_data else 0.0
        
        status = clients_metadata[c]["status"]
        if status == "Novo Cliente":
            new_client_val += c_rec_2026
        else:
            diff = c_rec_2026 - c_rec_2025
            if diff > 0:
                expansion_val += diff
            else:
                churn_val += diff # negative value
                
    rec_proj_2026 = rec_2025 + expansion_val + new_client_val + churn_val
    
    fig_waterfall = go.Figure(go.Waterfall(
        orientation = "v",
        measure = ["relative", "relative", "relative", "relative", "total"],
        x = ["Receita Realizada 2025", "Expansão de Clientes", "Novos Clientes 2026", "Churn / Retração", "Receita Projetada 2026 (Base)"],
        textposition = "outside",
        text = [f"R$ {rec_2025:,.0f}", f"R$ {expansion_val:,.0f}", f"R$ {new_client_val:,.0f}", f"R$ {churn_val:,.0f}", f"R$ {rec_proj_2026:,.0f}"],
        y = [rec_2025, expansion_val, new_client_val, churn_val, 0],
        connector = {"line":{"color":"#64748B", "width":1.5, "dash":"dot"}},
        decreasing = {"marker":{"color":"#DC2626"}},
        increasing = {"marker":{"color":"#16A34A"}},
        totals = {"marker":{"color":"#002060"}}
    ))
    fig_waterfall.update_layout(title="Ponte de Receita Executiva (Base Orçamento)", plot_bgcolor="#FFFFFF", height=400)
    st.plotly_chart(fig_waterfall, use_container_width=True)

# ----------------------------------------------------
# TAB 5: MATRIZ ESTRATÉGICA DE CLIENTES
# ----------------------------------------------------
elif selected_tab == "🎯 Strategic Matrix":
    st.markdown(
        f"<div class='title-container'>"
        f"<h1>Matriz Estratégica de Clientes</h1>"
        f"<p>Classificação de Carteira por Receita, GMV e Potencial de Crescimento — Ano: 2026</p>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # Calculate Growth and Revenues
    client_matriz = []
    
    for c in filtered_clients:
        c_rec_2025 = overview_data[c]["2025"]["Receita Hanzo"] if c in overview_data else 0.0
        c_rec_2026 = overview_data[c]["2026"]["Receita Hanzo"] if c in overview_data else 0.0
        c_gmv_2026 = overview_data[c]["2026"]["GMV"] if c in overview_data else 0.0
        c_ped_2026 = overview_data[c]["2026"]["Pedidos"] if c in overview_data else 0.0
        
        c_growth = (c_rec_2026 - c_rec_2025) / c_rec_2025 if c_rec_2025 > 0 else 0.0
        
        client_matriz.append({
            "Cliente": c,
            "Receita": c_rec_2026,
            "GMV": c_gmv_2026,
            "Pedidos": c_ped_2026,
            "Crescimento %": c_growth
        })
        
    df_mat = pd.DataFrame(client_matriz)
    
    # Strategic score normalization
    # Normalizing on max values in the filtered list
    max_rec = df_mat["Receita"].max() if df_mat["Receita"].max() > 0 else 1.0
    max_gmv = df_mat["GMV"].max() if df_mat["GMV"].max() > 0 else 1.0
    max_ped = df_mat["Pedidos"].max() if df_mat["Pedidos"].max() > 0 else 1.0
    max_growth = df_mat["Crescimento %"].max() if df_mat["Crescimento %"].max() > 0 else 1.0
    
    df_mat["Score Normalizado"] = (
        0.4 * (df_mat["Receita"] / max_rec * 100) +
        0.3 * (df_mat["GMV"] / max_gmv * 100) +
        0.2 * (df_mat["Crescimento %"] / max_growth * 100) +
        0.1 * (df_mat["Pedidos"] / max_ped * 100)
    )
    
    # Classifications
    # Thresholds: Median of Revenue and Growth
    med_rec = df_mat["Receita"].median()
    
    def classify_client(row):
        rev = row["Receita"]
        gro = row["Crescimento %"]
        
        if rev > med_rec:
            if gro > 0.10:
                return "Estrela"
            elif gro >= 0.0:
                return "Estratégico"
            else:
                return "Em Risco"
        else:
            if gro > 0.10:
                return "Crescimento Acelerado"
            else:
                return "Baixa Relevância"
                
    df_mat["Classificação"] = df_mat.apply(classify_client, axis=1)
    
    # Visual Matrix Plot
    st.markdown("### 🗺️ Matriz de Segmentação e Classificação de Risco")
    
    fig_mat = px.scatter(
        df_mat, x="Crescimento %", y="Receita", text="Cliente",
        color="Classificação", size="GMV",
        color_discrete_map={
            "Estrela": "#16A34A",
            "Crescimento Acelerado": "#10B981",
            "Estratégico": "#002060",
            "Em Risco": "#DC2626",
            "Baixa Relevância": "#CBD5E1"
        },
        labels={"Crescimento %": "Crescimento YoY (%)", "Receita": "Receita (R$)"},
        title="Matriz Estratégica Hanzo (Tamanho da Bolha = GMV)"
    )
    fig_mat.update_traces(textposition='top center')
    fig_mat.update_layout(plot_bgcolor="#FFFFFF")
    fig_mat.add_hline(y=med_rec, line_dash="dash", line_color="#CBD5E1")
    fig_mat.add_vline(x=0.10, line_dash="dash", line_color="#CBD5E1")
    
    st.plotly_chart(fig_mat, use_container_width=True)
    
    # Client Risk Matrix (Grid view)
    st.markdown("### 🛡️ Matriz de Risco do Portfólio")
    # Grid: Strategic, Expansion, At Risk, Low Priority
    df_mat["Risk Matrix Class"] = df_mat.apply(
        lambda r: "Strategic" if r["Receita"] > med_rec and r["Crescimento %"] >= 0
        else "Expansion" if r["Receita"] <= med_rec and r["Crescimento %"] > 0.10
        else "At Risk" if r["Receita"] > med_rec and r["Crescimento %"] < 0
        else "Low Priority", axis=1
    )
    
    def generate_risk_table_html(subset_df):
        if subset_df.empty:
            return "<div class='executive-table-container'><table class='executive-table'><tbody><tr><td style='text-align:center; color:#64748B; padding:10px;'>Nenhum cliente neste quadrante</td></tr></tbody></table></div>"
        
        html = "<div class='executive-table-container'><table class='executive-table'><thead><tr>"
        html += "<th>Cliente</th><th class='numeric'>Receita (2026)</th><th class='numeric'>Crescimento % (YoY)</th>"
        html += "</tr></thead><tbody>"
        for _, row in subset_df.iterrows():
            html += f"<tr>"
            html += f"<td><b>{row['Cliente']}</b></td>"
            html += f"<td class='numeric'>R$ {row['Receita']:,.2f}</td>"
            html += f"<td class='numeric'>{row['Crescimento %']*100:+.1f}%</td>"
            html += f"</tr>"
        html += "</tbody></table></div>"
        return html

    col_ri1, col_ri2 = st.columns(2)
    with col_ri1:
        st.markdown("<div style='background-color:#E0F2FE; padding:15px; border-radius:8px; border-left:4px solid #0284C7; margin-bottom:10px;'><strong>⭐ Strategic</strong> (Alta Receita + Crescimento Estável/Positivo)</div>", unsafe_allow_html=True)
        st.markdown(generate_risk_table_html(df_mat[df_mat["Risk Matrix Class"] == "Strategic"]), unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)
        
        st.markdown("<div style='background-color:#DCFCE7; padding:15px; border-radius:8px; border-left:4px solid #16A34A; margin-bottom:10px;'><strong>🚀 Expansion</strong> (Baixa Receita + Alto Crescimento)</div>", unsafe_allow_html=True)
        st.markdown(generate_risk_table_html(df_mat[df_mat["Risk Matrix Class"] == "Expansion"]), unsafe_allow_html=True)
        
    with col_ri2:
        st.markdown("<div style='background-color:#FEE2E2; padding:15px; border-radius:8px; border-left:4px solid #DC2626; margin-bottom:10px;'><strong>⚠️ At Risk</strong> (Alta Receita + Crescimento Negativo)</div>", unsafe_allow_html=True)
        st.markdown(generate_risk_table_html(df_mat[df_mat["Risk Matrix Class"] == "At Risk"]), unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)
        
        st.markdown("<div style='background-color:#F1F5F9; padding:15px; border-radius:8px; border-left:4px solid #64748B; margin-bottom:10px;'><strong>💤 Low Priority</strong> (Baixa Receita + Baixo Crescimento)</div>", unsafe_allow_html=True)
        st.markdown(generate_risk_table_html(df_mat[df_mat["Risk Matrix Class"] == "Low Priority"]), unsafe_allow_html=True)

    # Strategic Ranking
    st.markdown("### 🏆 Ranking Estratégico do Portfólio")
    df_score_rank = df_mat.sort_values("Score Normalizado", ascending=False).copy()
    df_score_rank["Ranking"] = range(1, len(df_score_rank) + 1)
    df_score_rank["Score Formato"] = df_score_rank["Score Normalizado"].apply(lambda x: f"{x:.1f}")
    df_score_rank["Receita Formato"] = df_score_rank["Receita"].apply(lambda x: f"R$ {x:,.2f}")
    df_score_rank["Crescimento Formato"] = df_score_rank["Crescimento %"].apply(lambda x: f"{x*100:+.1f}%")
    
    st.dataframe(
        df_score_rank[["Ranking", "Cliente", "Score Formato", "Receita Formato", "Crescimento Formato", "Classificação"]],
        use_container_width=True, hide_index=True
    )

# ----------------------------------------------------
# TAB 6: RISCOS E OPORTUNIDADES
# ----------------------------------------------------
elif selected_tab == "⚠ Risks & Opportunities":
    st.markdown(
        f"<div class='title-container'>"
        f"<h1>Riscos &amp; Oportunidades</h1>"
        f"<p>Análise de Concentração de Carteira, Gaps Operacionais e Alavancas Comerciais de Take Rate</p>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # Calculate risks
    riscos = []
    oportunidades = []
    
    for c in filtered_clients:
        if c not in monthly_data:
            continue
        c_rec_25 = overview_data[c]["2025"]["Receita Hanzo"] if c in overview_data else 0.0
        c_rec_26 = overview_data[c]["2026"]["Receita Hanzo"] if c in overview_data else 0.0
        c_gmv_26 = overview_data[c]["2026"]["GMV"] if c in overview_data else 0.0
        
        c_growth = (c_rec_26 - c_rec_25) / c_rec_25 if c_rec_25 > 0 else 0.0
        c_take_rate = c_rec_26 / c_gmv_26 if c_gmv_26 > 0 else 0.0
        
        # Risk identification
        if c_growth < -0.05:
            riscos.append({
                "Cliente": c, "Risco": "Retração de Receita", "Var %": c_growth, "Valor R$": c_rec_26 - c_rec_25
            })
        if c_take_rate < 0.03 and c_gmv_26 > 1000000:
            oportunidades.append({
                "Cliente": c, "Oportunidade": "Expansão de Take Rate (Relação GMV/Rec)", "Take Rate Atual": c_take_rate, "GMV 2026": c_gmv_26
            })
        if c_growth > 0.15:
            oportunidades.append({
                "Cliente": c, "Oportunidade": "Alto Crescimento YoY", "Crescimento %": c_growth, "Receita 2026": c_rec_26
            })

    col_ro1, col_ro2 = st.columns(2)
    
    with col_ro1:
        st.markdown("#### ⚠️ Principais Riscos Identificados")
        risks_list = riscos
        if not risks_list:
            st.info("Nenhum risco relevante identificado no portfólio selecionado.")
        else:
            for r in risks_list:
                st.markdown(
                    f"<div class='executive-alert executive-alert-danger'>"
                    f"<div>"
                    f"<div class='executive-alert-title'>{r['Cliente']}</div>"
                    f"<div class='executive-alert-desc'>{r['Risco']}: Var {r['Var %']*100:+.1f}% (Impacto de R$ {r['Valor R$']:,.2f})</div>"
                    f"</div></div>",
                    unsafe_allow_html=True
                )
                
    with col_ro2:
        st.markdown("#### 💡 Principais Oportunidades Identificadas")
        opportunities_list = oportunidades
        if not opportunities_list:
            st.info("Nenhuma oportunidade relevante identificada.")
        else:
            for o in opportunities_list:
                if "Take Rate" in o["Oportunidade"]:
                    st.markdown(
                        f"<div class='executive-alert executive-alert-success'>"
                        f"<div>"
                        f"<div class='executive-alert-title'>{o['Cliente']}</div>"
                        f"<div class='executive-alert-desc'>{o['Oportunidade']}: Take Rate em {o['Take Rate Atual']*100:.2f}% (GMV de R$ {o['GMV 2026']:,.2f})</div>"
                        f"</div></div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"<div class='executive-alert executive-alert-success'>"
                        f"<div>"
                        f"<div class='executive-alert-title'>{o['Cliente']}</div>"
                        f"<div class='executive-alert-desc'>{o['Oportunidade']}: Var {o['Crescimento %']*100:+.1f}% (Receita de R$ {o['Receita 2026']:,.2f})</div>"
                        f"</div></div>",
                        unsafe_allow_html=True
                    )

    # Take Rate Analytics
    st.markdown("### 📊 Analytics de Take Rate (Comercial)")
    
    # Calculate list of take rates
    take_rates_list = []
    for c in filtered_clients:
        if c not in monthly_data:
            continue
        c_rec = sum(monthly_data[c]["Receita Hanzo"]["plan"].values())
        c_gmv = sum(monthly_data[c]["GMV"]["plan"].values())
        if c_gmv > 0:
            take_rates_list.append({"Cliente": c, "Take Rate": c_rec / c_gmv, "GMV": c_gmv})
            
    df_tr = pd.DataFrame(take_rates_list)
    
    col_tr1, col_tr2 = st.columns(2)
    with col_tr1:
        st.markdown("#### 🏆 Maiores Take Rates")
        df_tr_high = df_tr.sort_values("Take Rate", ascending=False).head(5).copy()
        df_tr_high["Take Rate Formato"] = df_tr_high["Take Rate"].apply(lambda x: f"{x*100:.2f}%")
        df_tr_high["GMV Formato"] = df_tr_high["GMV"].apply(lambda x: f"R$ {x:,.2f}")
        st.dataframe(df_tr_high[["Cliente", "Take Rate Formato", "GMV Formato"]], use_container_width=True, hide_index=True)
        
    with col_tr2:
        st.markdown("#### 📉 Menores Take Rates (Alavancas Comerciais)")
        df_tr_low = df_tr.sort_values("Take Rate").head(5).copy()
        df_tr_low["Take Rate Formato"] = df_tr_low["Take Rate"].apply(lambda x: f"{x*100:.2f}%")
        df_tr_low["GMV Formato"] = df_tr_low["GMV"].apply(lambda x: f"R$ {x:,.2f}")
        st.dataframe(df_tr_low[["Cliente", "Take Rate Formato", "GMV Formato"]], use_container_width=True, hide_index=True)

# ----------------------------------------------------
# TAB 7: CLIENT 360 VIEW (Client Performance Sheet Redesign)
# ----------------------------------------------------
elif selected_tab == "👤 Client 360":
    st.markdown(
        f"<div class='title-container'>"
        f"<h1>Executive Client Scorecard — Visão 360°</h1>"
        f"<p>Resumo Gerencial e Acompanhamento de Metas de Clientes para Tomada de Decisão Rápida</p>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    selected_c = st.selectbox("Selecione o Cliente para Análise Executiva", filtered_dropdown_clients)
    
    if selected_c:
        # 1. Gather YTD values
        c_rec_real = client_revenue_vals[selected_c]
        c_rec_plan = c_rec_real - client_diffs[selected_c]
        c_gmv_real = client_gmv_vals[selected_c]
        c_gmv_plan = sum(monthly_data[selected_c]["GMV"]["plan"].get(m, 0.0) for m in analysis_months) if selected_c in monthly_data else 0.0
        c_ped_real = client_ped_vals[selected_c]
        c_ped_plan = sum(monthly_data[selected_c]["Pedidos"]["plan"].get(m, 0.0) for m in analysis_months) if selected_c in monthly_data else 0.0
        
        # Calculate achievements
        gmv_ach = c_gmv_real / c_gmv_plan * 100 if c_gmv_plan > 0 else 100.0
        rec_ach = c_rec_real / c_rec_plan * 100 if c_rec_plan > 0 else 100.0
        ped_ach = c_ped_real / c_ped_plan * 100 if c_ped_plan > 0 else 100.0
        score = client_scores[selected_c]
        
        # Helper for traffic light
        def get_attainment_traffic_light(pct):
            if pct >= 95.0:
                return "🟢"
            elif pct >= 90.0:
                return "🟡"
            else:
                return "🔴"
                
        # SECTION 1: Executive Summary (4 KPI Cards)
        st.markdown("### 🏛️ Sumário Executivo")
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        
        # Card 1: GMV
        col_c1.markdown(
            f"<div style='border: 1px solid #E2E8F0; padding: 15px; border-radius: 6px; background-color:#FFFFFF;'>"
            f"<div style='font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;'>GMV Realizado YTD</div>"
            f"<div style='font-size: 18px; font-weight: 800; color: #002060; margin: 5px 0;'>R$ {c_gmv_real:,.2f}</div>"
            f"<div style='font-size: 13px; font-weight: 700;'>Meta: {gmv_ach:.1f}% {get_attainment_traffic_light(gmv_ach)}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        # Card 2: Revenue
        col_c2.markdown(
            f"<div style='border: 1px solid #E2E8F0; padding: 15px; border-radius: 6px; background-color:#FFFFFF;'>"
            f"<div style='font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;'>Receita Hanzo YTD</div>"
            f"<div style='font-size: 18px; font-weight: 800; color: #002060; margin: 5px 0;'>R$ {c_rec_real:,.2f}</div>"
            f"<div style='font-size: 13px; font-weight: 700;'>Meta: {rec_ach:.1f}% {get_attainment_traffic_light(rec_ach)}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        # Card 3: Orders
        col_c3.markdown(
            f"<div style='border: 1px solid #E2E8F0; padding: 15px; border-radius: 6px; background-color:#FFFFFF;'>"
            f"<div style='font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;'>Pedidos Realizados YTD</div>"
            f"<div style='font-size: 18px; font-weight: 800; color: #002060; margin: 5px 0;'>{c_ped_real:,.0f}</div>"
            f"<div style='font-size: 13px; font-weight: 700;'>Meta: {ped_ach:.1f}% {get_attainment_traffic_light(ped_ach)}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        # Card 4: Budget Achievement
        col_c4.markdown(
            f"<div style='border: 1px solid #E2E8F0; padding: 15px; border-radius: 6px; background-color:#FFFFFF;'>"
            f"<div style='font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;'>Budget Achievement</div>"
            f"<div style='font-size: 18px; font-weight: 800; color: #002060; margin: 5px 0;'>{score:.1f}%</div>"
            f"<div style='font-size: 13px; font-weight: 700;'>Status Geral: {score:.1f}% {get_attainment_traffic_light(score)}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
        
        # Two-column layout for the matrices and cards
        col_sec1, col_sec2 = st.columns([7, 5])
        
        with col_sec1:
            # SECTION 2: Performance Matrix
            st.markdown("### 📊 Matriz de Performance (Plan vs Actual)")
            matrix_html = f"""
            <div class='executive-table-container'>
                <table class='executive-table'>
                    <thead>
                        <tr>
                            <th>Métrica</th>
                            <th class='numeric'>Budget (Orçado)</th>
                            <th class='numeric'>Actual (Realizado)</th>
                            <th class='numeric'>Atingimento %</th>
                            <th style='text-align:center;'>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><b>GMV</b></td>
                            <td class='numeric'>R$ {c_gmv_plan:,.2f}</td>
                            <td class='numeric'>R$ {c_gmv_real:,.2f}</td>
                            <td class='numeric' style='font-weight:700;'>{gmv_ach:.1f}%</td>
                            <td style='text-align:center;'>{get_attainment_traffic_light(gmv_ach)}</td>
                        </tr>
                        <tr>
                            <td><b>Receita Hanzo</b></td>
                            <td class='numeric'>R$ {c_rec_plan:,.2f}</td>
                            <td class='numeric'>R$ {c_rec_real:,.2f}</td>
                            <td class='numeric' style='font-weight:700;'>{rec_ach:.1f}%</td>
                            <td style='text-align:center;'>{get_attainment_traffic_light(rec_ach)}</td>
                        </tr>
                        <tr>
                            <td><b>Volume de Pedidos</b></td>
                            <td class='numeric'>{c_ped_plan:,.0f}</td>
                            <td class='numeric'>{c_ped_real:,.0f}</td>
                            <td class='numeric' style='font-weight:700;'>{ped_ach:.1f}%</td>
                            <td style='text-align:center;'>{get_attainment_traffic_light(ped_ach)}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            """
            st.markdown(matrix_html, unsafe_allow_html=True)
            
            # SECTION 3: GMV Budget Adherence
            st.markdown("### 🎯 Aderência ao Orçamento de GMV")
            filled_blocks = max(0, min(20, int(round(gmv_ach / 5.0))))
            empty_blocks = 20 - filled_blocks
            bar_str = "█" * filled_blocks + "░" * empty_blocks
            
            status_label = "Sucesso" if gmv_ach >= 95.0 else "Atenção" if gmv_ach >= 90.0 else "Desvio Crítico"
            status_emoji = get_attainment_traffic_light(gmv_ach)
            
            adherence_html = f"""
            <div style='border: 1px solid #E2E8F0; padding: 20px; border-radius: 6px; background-color:#FFFFFF; line-height: 1.4;'>
                <div style='display: flex; justify-content: space-between; margin-bottom: 12px;'>
                    <div>
                        <span style='font-size: 11px; color: #64748B; font-weight: 700;'>BUDGET GMV</span><br>
                        <span style='font-size: 15px; font-weight: 800; color: #334155;'>R$ {c_gmv_plan:,.0f}</span>
                    </div>
                    <div>
                        <span style='font-size: 11px; color: #64748B; font-weight: 700;'>ACTUAL GMV</span><br>
                        <span style='font-size: 15px; font-weight: 800; color: #334155;'>R$ {c_gmv_real:,.0f}</span>
                    </div>
                    <div style='text-align: right;'>
                        <span style='font-size: 11px; color: #64748B; font-weight: 700;'>STATUS ADERÊNCIA</span><br>
                        <span style='font-size: 15px; font-weight: 800; color: #334155;'>{status_emoji} {status_label} ({gmv_ach:.1f}%)</span>
                    </div>
                </div>
                <div style='font-family: monospace; font-size: 20px; color: #002060; letter-spacing: 2px; line-height: 1; word-break: break-all;'>
                    {bar_str}
                </div>
            </div>
            """
            st.markdown(adherence_html, unsafe_allow_html=True)
            
        with col_sec2:
            # SECTION 4: Client Ranking Position
            st.markdown("### 🏆 Posição no Portfólio")
            all_client_revs = {}
            for c in filtered_clients:
                all_client_revs[c] = client_revenue_vals[c]
            sorted_revs = sorted(all_client_revs.items(), key=lambda x: x[1], reverse=True)
            client_rank = 1
            for idx, (name, val) in enumerate(sorted_revs):
                if name == selected_c:
                    client_rank = idx + 1
                    break
            total_ytd_revenue = sum(all_client_revs.values())
            client_rev_share = client_revenue_vals[selected_c] / total_ytd_revenue if total_ytd_revenue > 0 else 0.0
            
            def get_rank_suffix(r):
                if r == 1:
                    return "1º Maior Cliente"
                elif r == 2:
                    return "2º Maior Cliente"
                elif r == 3:
                    return "3º Maior Cliente"
                else:
                    return f"{r}º Maior Cliente"
            
            portfolio_position_desc = get_rank_suffix(client_rank)
            
            rank_card_html = f"""
            <div style='border: 1px solid #E2E8F0; padding: 15px; border-radius: 6px; background-color:#FFFFFF; text-align: center;'>
                <div style='font-size: 18px; font-weight: 800; color: #002060;'>{portfolio_position_desc}</div>
                <div style='font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase; margin-top: 8px;'>REVENUE SHARE YTD</div>
                <div style='font-size: 24px; font-weight: 800; color: #16A34A; margin-top: 3px;'>{client_rev_share*100:.1f}%</div>
            </div>
            """
            st.markdown(rank_card_html, unsafe_allow_html=True)
            
            # SECTION 7: CFO Insights (Portuguese, concise, <=3 bullets)
            st.markdown("### 💡 Executive CFO Insights")
            c_tr_real = c_rec_real / c_gmv_real * 100 if c_gmv_real > 0 else 0.0
            c_tr_plan = c_rec_plan / c_gmv_plan * 100 if c_gmv_plan > 0 else 0.0
            rec_diff = client_diffs[selected_c]
            
            bullet_1 = f"GMV acumulado está {abs(gmv_ach - 100):.1f}% {'acima' if gmv_ach >= 100 else 'abaixo'} do orçamento."
            bullet_2 = f"Take Rate médio realizado é de {c_tr_real:.2f}% (versus {c_tr_plan:.2f}% orçado)."
            
            if score < 90.0:
                bullet_3 = f"Ação comercial de urgência necessária devido ao desvio crítico de -R$ {abs(rec_diff):,.0f}."
            elif score < 100.0:
                bullet_3 = "Recomenda-se monitorar de perto os volumes para atingir 100% da meta de receita anual."
            else:
                bullet_3 = "Conta saudável. Avaliar oportunidades de upsell e renovação antecipada."
                
            insights_html = f"""
            <div style='border: 1px solid #E2E8F0; padding: 15px; border-radius: 6px; background-color:#FFFFFF;'>
                <ul style='font-family: Inter; font-size: 12px; color: #334155; line-height: 1.5; margin: 0; padding-left: 15px;'>
                    <li style='margin-bottom:6px;'>{bullet_1}</li>
                    <li style='margin-bottom:6px;'>{bullet_2}</li>
                    <li style='margin-bottom:0;'>{bullet_3}</li>
                </ul>
            </div>
            """
            st.markdown(insights_html, unsafe_allow_html=True)
            
            # SECTION 6: Executive Action Card
            st.markdown("### 📝 Recomendação Executiva")
            if score >= 100.0:
                if client_growth_yoy[selected_c] >= 0.05:
                    recommendation = "🟢 Expand (Expandir)"
                    rec_desc = "Faturamento robusto e crescimento forte. Buscar upsell comercial."
                else:
                    recommendation = "🟢 Maintain (Manter)"
                    rec_desc = "Meta orçada atingida com consistência. Garantir nível de serviço."
            elif score >= 90.0:
                recommendation = "🟡 Monitor (Monitorar)"
                rec_desc = "Desvios marginais identificados. Monitoramento mensal próximo recomendado."
            else:
                recommendation = "🔴 Immediate Action Required"
                rec_desc = "Desvios severos (abaixo de 90%). Ação corretiva imediata necessária."
                
            recommendation_html = f"""
            <div style='border: 1px solid #E2E8F0; padding: 15px; border-radius: 6px; background-color:#FFFFFF;'>
                <div style='font-size: 14px; font-weight: 800; color: #0F172A;'>{recommendation}</div>
                <div style='font-size: 11px; color: #64748B; margin-top: 4px;'>{rec_desc}</div>
            </div>
            """
            st.markdown(recommendation_html, unsafe_allow_html=True)
            
        # SECTION 5: Simple Trend Charts (GMV, Revenue, Orders)
        st.markdown("<hr style='margin: 20px 0 15px 0;'>", unsafe_allow_html=True)
        st.markdown("### 📈 Evolução Mensal Comparativa (Metas vs Realizado)")
        
        if selected_c in monthly_data:
            c_mon_gmv_plan = [monthly_data[selected_c]["GMV"]["plan"].get(m, 0.0) for m in EN_MONTHS]
            c_mon_gmv_real = [monthly_data[selected_c]["GMV"]["real"].get(m, 0.0) if m in realized_months else None for m in EN_MONTHS]
            c_mon_rec_plan = [monthly_data[selected_c]["Receita Hanzo"]["plan"].get(m, 0.0) for m in EN_MONTHS]
            c_mon_rec_real = [monthly_data[selected_c]["Receita Hanzo"]["real"].get(m, 0.0) if m in realized_months else None for m in EN_MONTHS]
            c_mon_ped_plan = [monthly_data[selected_c]["Pedidos"]["plan"].get(m, 0.0) for m in EN_MONTHS]
            c_mon_ped_real = [monthly_data[selected_c]["Pedidos"]["real"].get(m, 0.0) if m in realized_months else None for m in EN_MONTHS]
            
            col_ch1, col_ch2, col_ch3 = st.columns(3)
            pt_months_labels = [EN_TO_PT[m] for m in EN_MONTHS]
            
            with col_ch1:
                fig_gmv = go.Figure()
                fig_gmv.add_trace(go.Scatter(x=pt_months_labels, y=c_mon_gmv_plan, name="Budget", line=dict(color="#94A3B8", dash="dash", width=1.5)))
                fig_gmv.add_trace(go.Scatter(x=pt_months_labels, y=c_mon_gmv_real, name="Actual", line=dict(color="#002060", width=2.5)))
                fig_gmv.update_layout(title="GMV (R$)", plot_bgcolor="#FFFFFF", height=220, margin=dict(t=30, b=5, l=5, r=5), legend=dict(orientation="h", y=1.15))
                st.plotly_chart(fig_gmv, use_container_width=True)
                
            with col_ch2:
                fig_rec = go.Figure()
                fig_rec.add_trace(go.Scatter(x=pt_months_labels, y=c_mon_rec_plan, name="Budget", line=dict(color="#94A3B8", dash="dash", width=1.5)))
                fig_rec.add_trace(go.Scatter(x=pt_months_labels, y=c_mon_rec_real, name="Actual", line=dict(color="#002060", width=2.5)))
                fig_rec.update_layout(title="Receita Hanzo (R$)", plot_bgcolor="#FFFFFF", height=220, margin=dict(t=30, b=5, l=5, r=5), legend=dict(orientation="h", y=1.15))
                st.plotly_chart(fig_rec, use_container_width=True)
                
            with col_ch3:
                fig_ped = go.Figure()
                fig_ped.add_trace(go.Scatter(x=pt_months_labels, y=c_mon_ped_plan, name="Budget", line=dict(color="#94A3B8", dash="dash", width=1.5)))
                fig_ped.add_trace(go.Scatter(x=pt_months_labels, y=c_mon_ped_real, name="Actual", line=dict(color="#002060", width=2.5)))
                fig_ped.update_layout(title="Pedidos (Unid.)", plot_bgcolor="#FFFFFF", height=220, margin=dict(t=30, b=5, l=5, r=5), legend=dict(orientation="h", y=1.15))
                st.plotly_chart(fig_ped, use_container_width=True)

# ----------------------------------------------------
# TAB 8: APRESENTAÇÃO CONSELHO E INVESTIDORES
# ----------------------------------------------------
elif selected_tab == "👔 Board & Investors":
    st.markdown(
        f"<div class='title-container'>"
        f"<h1>Board &amp; Investors Executive Dashboard</h1>"
        f"<p>Relatório de Performance Comercial, Financeira e Governança Corporativa para o Conselho</p>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # YoY growth rate (2026 projected vs 2025 actual)
    yoy_rec_growth = (sum(overview_data[c]['2026']['Receita Hanzo'] for c in filtered_clients if c in overview_data) - kpi_data["rec_2025"]) / kpi_data["rec_2025"] if kpi_data["rec_2025"] > 0 else 0.0
    yoy_gmv_growth = (sum(overview_data[c]['2026']['GMV'] for c in filtered_clients if c in overview_data) - kpi_data["gmv_2025"]) / kpi_data["gmv_2025"] if kpi_data["gmv_2025"] > 0 else 0.0
    
    # 1. Board Dashboard Cards Row
    col_b1, col_b2, col_b3 = st.columns(3)
    col_b4, col_b5, col_b6 = st.columns(3)
    
    col_b1.markdown(
        f"<div class='metric-card accent-blue'>"
        f"<div class='metric-card-title'>Receita YTD Realizada</div>"
        f"<div class='metric-card-value'>R$ {kpi_data['rec_real']:,.2f}</div>"
        f"<div class='metric-card-delta delta-neutral'>Desvio YTD: {rec_var_pct*100:+.1f}% vs Plan</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    col_b2.markdown(
        f"<div class='metric-card accent-slate'>"
        f"<div class='metric-card-title'>GMV YTD Realizado</div>"
        f"<div class='metric-card-value'>R$ {kpi_data['gmv_real']:,.2f}</div>"
        f"<div class='metric-card-delta delta-neutral'>Desvio YTD: {gmv_var_pct*100:+.1f}% vs Plan</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    col_b3.markdown(
        f"<div class='metric-card accent-green'>"
        f"<div class='metric-card-title'>Crescimento YoY (Receita)</div>"
        f"<div class='metric-card-value'>{yoy_rec_growth*100:+.2f}%</div>"
        f"<div class='metric-card-delta delta-positive'>Projetado vs. Real 2025</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    col_b4.markdown(
        f"<div class='metric-card accent-green'>"
        f"<div class='metric-card-title'>Faturamento Proj. EOY</div>"
        f"<div class='metric-card-value'>R$ {sum(overview_data[c]['2026']['Receita Hanzo'] for c in filtered_clients if c in overview_data):,.2f}</div>"
        f"<div class='metric-card-delta delta-neutral'>Fechamento Base 2026</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    col_b5.markdown(
        f"<div class='metric-card accent-amber'>"
        f"<div class='metric-card-title'>Share Top 5 Clientes</div>"
        f"<div class='metric-card-value'>{share_top5*100:.2f}%</div>"
        f"<div class='metric-card-delta {'delta-negative' if share_top5 > 0.50 else 'delta-neutral'}'>Concentração de Carteira</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    col_b6.markdown(
        f"<div class='metric-card accent-red'>"
        f"<div class='metric-card-title'>Maior Dependência</div>"
        f"<div class='metric-card-value'>{dependency_largest*100:.2f}%</div>"
        f"<div class='metric-card-delta delta-negative'>{largest_client_name}</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # 2. Risks and Opportunities split
    st.markdown("### ⚖️ Riscos & Oportunidades no Portfólio")
    col_split1, col_split2 = st.columns(2)
    
    with col_split1:
        st.markdown("<h4 style='color:#DC2626; font-family:Outfit; font-weight:600; margin-bottom:5px;'>🚨 Top 5 Riscos de Negócios</h4>", unsafe_allow_html=True)
        risks_html = """
        <div style='background-color:#FFF5F5; padding:15px; border-radius:8px; border-left:4px solid #DC2626; line-height:1.6; font-size:0.9rem; color:#991B1B;'>
        <b>1. Dependência Extrema do Top 5:</b> Os 5 principais parceiros representam mais de 98% de todo o faturamento da empresa.<br>
        <b>2. Churn de Médio Porte:</b> Contração de receita no parceiro <i>Outback</i> (-R$ 30k YTD) devido a atraso operacional.<br>
        <b>3. Atraso em Implantações (Novo Cliente):</b> Risco de perda de volume na marca <i>Esfiha Imigrantes</i> (-R$ 14.8k vs. orçamento).<br>
        <b>4. Estagnação de Contas (At Risk):</b> 6 contas classificadas como sob risco devido a crescimento YoY inferior a 5%.<br>
        <b>5. Volatilidade Transacional:</b> Queda acumulada de 8.7% no volume total de pedidos operacionais versus o orçamento de 2026.
        </div>
        """
        st.markdown(risks_html, unsafe_allow_html=True)
        
    with col_split2:
        st.markdown("<h4 style='color:#16A34A; font-family:Outfit; font-weight:600; margin-bottom:5px;'>💡 Top 5 Oportunidades Comerciais</h4>", unsafe_allow_html=True)
        opp_html = """
        <div style='background-color:#F0FDF4; padding:15px; border-radius:8px; border-left:4px solid #16A34A; line-height:1.6; font-size:0.9rem; color:#065F46;'>
        <b>1. Negociação de Take Rate (Outback):</b> Alto volume de GMV (R$ 24M plan) com take rate baixo de 2.71% (alavanca de margem).<br>
        <b>2. Expansão de Contas (Expansion):</b> 5 parceiros ativos com alto crescimento YoY (e.g. <i>We Coffee</i>) elegíveis para upsell.<br>
        <b>3. Ativação da Wish List:</b> Go-live planejado das marcas na Wish List para alavancar receita incremental no final do ano.<br>
        <b>4. Crescimento Orgânico de GMV:</b> GMV geral do portfólio superando a meta em +2.64% YTD (demanda forte).<br>
        <b>5. Otimização de Comissões:</b> Redefinição de taxas mínimas de take rate para parceiros abaixo de 3.50% de comissão média.
        </div>
        """
        st.markdown(opp_html, unsafe_allow_html=True)
        
    # Dynamic Board Summary
    st.markdown("### 📝 Resumo de Governança para Conselho (Board Summary)")
    
    board_summary_txt = f"""
    • **Performance Geral:** O GMV das marcas parceiras atingiu **R$ {kpi_data['gmv_real']:,.2f}** YTD (desvio positivo de **{gmv_var_pct*100:+.1f}%**). A receita realizada no YTD fechou em **R$ {kpi_data['rec_real']:,.2f}** (**{rec_var_pct*100:+.1f}%**).
    • **Crescimento Anual YoY:** A projeção consolidada de receita EOY indica um crescimento de **{yoy_rec_growth*100:+.1f}%** em relação a 2025. O GMV apresenta evolução anual projetada de **{yoy_gmv_growth*100:+.1f}%**.
    • **Risco de Concentração:** O share dos 5 principais clientes é de **{share_top5*100:.1f}%**, apresentando risco de dependência concentrado em **Bacio di Latte** (**{dependency_largest*100:.1f}%** do faturamento).
    • **Run-Rate e Probabilidade:** A probabilidade de atingimento do orçamento de receita é classificada como **{prob_atingimento}**, com run-rate rodando a **{rec_attainment:.1f}%** da meta do período.
    • **Ações Operacionais:** Recomenda-se ações comerciais de mitigação de risco nos parceiros da carteira **"At Risk"** e renegociação imediata de margens com o **Outback** para conversão de GMV.
    """
    
    st.markdown(
        f"<div class='executive-alert executive-alert-info'>"
        f"<div>"
        f"<div class='executive-alert-title'>RELATÓRIO FINANCEIRO DE GOVERNANÇA</div>"
        f"<div class='executive-alert-desc' style='font-family: Inter; white-space: pre-line;'>{board_summary_txt}</div>"
        f"</div></div>",
        unsafe_allow_html=True
    )

# ----------------------------------------------------
# VISUAL EXECUTIVE SUMMARY (Redesigned for President in 3 minutes)
# ----------------------------------------------------
st.markdown("---")
st.markdown("### 📊 Visão Estratégica Executiva (Leitura de 3 Minutos)")

col_sum1, col_sum2, col_sum3 = st.columns([1.3, 1.2, 1.5])

with col_sum1:
    # 1. Waterfall Revenue Bridge (Plotly)
    val_2025 = kpi_data["rec_2025"]
    contractions = sum(x["Receita Perdida"] for x in client_variances if x["Receita Perdida"] < 0)
    expansions = sum(x["Receita Perdida"] for x in client_variances if x["Receita Perdida"] >= 0)
    val_2026_forecast = val_2025 + contractions + expansions
    
    fig_water = go.Figure(go.Waterfall(
        orientation = "v",
        measure = ["relative", "relative", "relative", "total"],
        x = ["Real 2025", "Perdas", "Ganhos", "Proj 2026"],
        textposition = "outside",
        text = [f"R$ {val_2025:,.0f}", f"R$ {contractions:,.0f}", f"R$ {expansions:,.0f}", f"R$ {val_2026_forecast:,.0f}"],
        y = [val_2025, contractions, expansions, val_2026_forecast],
        connector = {"line":{"color":"#64748B", "width":1}},
        increasing = {"marker":{"color":"#16A34A"}},
        decreasing = {"marker":{"color":"#DC2626"}},
        totals = {"marker":{"color":"#002060"}}
    ))
    fig_water.update_layout(
        title = dict(text="YoY Waterfall Bridge (Receita R$)", font=dict(size=14, family="Outfit")),
        plot_bgcolor = "#FFFFFF",
        height = 290,
        margin = dict(t=35, b=10, l=10, r=10)
    )
    st.plotly_chart(fig_water, use_container_width=True)

with col_sum2:
    # 2. Budget Achievement Bullet Charts (Progress Bars)
    fig_prog = go.Figure()
    
    gmv_att = (kpi_data["gmv_real"]/kpi_data["gmv_plan"]*100) if kpi_data["gmv_plan"]>0 else 0.0
    ped_att = (kpi_data["ped_real"]/kpi_data["ped_plan"]*100) if kpi_data["ped_plan"]>0 else 0.0
    
    metrics_progress = [
        {"lbl": "Receita Hanzo", "val": rec_attainment, "col": "#002060"},
        {"lbl": "GMV Clientes", "val": gmv_att, "col": "#64748B"},
        {"lbl": "Pedidos Totais", "val": ped_att, "col": "#16A34A"}
    ]
    
    for item in metrics_progress:
        fig_prog.add_trace(go.Bar(
            y=[item["lbl"]], x=[item["val"]],
            orientation='h',
            marker_color=item["col"],
            text=[f"{item['val']:.1f}%"],
            textposition='inside',
            width=0.4
        ))
        
    fig_prog.update_layout(
        title=dict(text="Atingimento Orçamentário YTD (%)", font=dict(size=14, family="Outfit")),
        plot_bgcolor="#FFFFFF",
        xaxis=dict(range=[0, 130], showgrid=True, gridcolor="#F1F5F9"),
        height=290,
        margin=dict(t=35, b=10, l=10, r=10),
        showlegend=False
    )
    st.plotly_chart(fig_prog, use_container_width=True)

with col_sum3:
    # 3. Quick Strategic Answers (Executive Dashboard style)
    top_driver = sorted([x for x in client_variances if x["Receita Perdida"] >= 0], key=lambda x: x["Receita Perdida"], reverse=True)
    top_detractor = sorted([x for x in client_variances if x["Receita Perdida"] < 0], key=lambda x: x["Receita Perdida"], reverse=False)
    
    driver_name = top_driver[0]["Cliente"] if top_driver else "Nenhum"
    driver_val = top_driver[0]["Receita Perdida"] if top_driver else 0.0
    
    detractor_name = top_detractor[0]["Cliente"] if top_detractor else "Nenhum"
    detractor_val = top_detractor[0]["Receita Perdida"] if top_detractor else 0.0
    
    # Calculate budget threshold probability
    hit_budget_msg = f"🟢 <b>SIM ({prob_atingimento})</b>" if rec_var_pct >= -0.05 else "🔴 <b>RISCO ALTO</b>"
    
    qa_html = f"""
    <div style='background-color:#F8FAFC; border:1px solid #E2E8F0; padding:15px; border-radius:8px; font-size:0.85rem; line-height:1.55; color:#334155;'>
      <div style='margin-bottom:8px;'>📈 <b>O que cresceu?</b> GMV de marcas parceiras subiu para <b>R$ {kpi_data['gmv_real']:,.0f}</b> (+2.64% vs Meta).</div>
      <div style='margin-bottom:8px;'>📉 <b>O que declinou?</b> Volume total de transações de pedidos caiu <b>-8.70%</b> (348.4k realizados).</div>
      <div style='margin-bottom:8px;'>🚀 <b>Quem impulsiona?</b> <b>{driver_name}</b> (+R$ {driver_val:,.0f} vs Meta) lidera a carteira.</div>
      <div style='margin-bottom:8px;'>⚠️ <b>Quem prejudica?</b> <b>{detractor_name}</b> ({detractor_val:,.0f} vs Meta) devido a atraso operacional.</div>
      <div style='margin-bottom:8px;'>🎯 <b>Bateremos a Meta?</b> {hit_budget_msg} | Faturamento projetado de <b>R$ {val_2026_forecast:,.0f}</b> (+1.17% vs Orçado).</div>
      <div>🛠️ <b>Ações Operacionais:</b> Contatar <i>{detractor_name}</i> imediatamente e acelerar go-live dos Novos Clientes.</div>
    </div>
    """
    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
    st.markdown(qa_html, unsafe_allow_html=True)
