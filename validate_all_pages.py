import os
import pandas as pd
import numpy as np
import data_loader

# Define spreadsheet path
excel_path = "Planejamento 2026.xlsx"
overview_data, monthly_data, optimistic_monthly_data, clients_metadata = data_loader.load_data(excel_path)

# Determine active realized months
EN_MONTHS = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
realized_months = []
for m in EN_MONTHS:
    m_sum = sum(monthly_data[c]["GMV"]["real"].get(m, 0.0) for c in monthly_data)
    if m_sum > 0:
        realized_months.append(m)

print("="*60)
print("DASHBOARD VALIDATION REPORT VS. SPREADSHEET")
print("="*60)
print(f"Spreadsheet Path: {excel_path}")
print(f"Active Realized Months in 2026: {realized_months}")
print(f"Total Clients Loaded: {len(clients_metadata)}")
print("="*60)

# ----------------------------------------------------
# PAGE 1: VISÃO EXECUTIVA
# ----------------------------------------------------
print("\n--- PAGE 1: VISÃO EXECUTIVA PRESIDÊNCIA ---")
# Let's check YTD (Jan-Jun) and Full Year
for period_name, months in [("YTD (Accumulated Jan-Jun)", realized_months), ("Full Year (Forecast)", EN_MONTHS)]:
    print(f"\nPeriod: {period_name}")
    gmv_plan = 0.0
    gmv_real = 0.0
    rec_plan = 0.0
    rec_real = 0.0
    ped_plan = 0.0
    ped_real = 0.0
    
    for c in monthly_data:
        for m in months:
            gmv_plan += monthly_data[c]["GMV"]["plan"].get(m, 0.0)
            rec_plan += monthly_data[c]["Receita Hanzo"]["plan"].get(m, 0.0)
            ped_plan += monthly_data[c]["Pedidos"]["plan"].get(m, 0.0)
            
            if m in realized_months:
                gmv_real += monthly_data[c]["GMV"]["real"].get(m, 0.0)
                rec_real += monthly_data[c]["Receita Hanzo"]["real"].get(m, 0.0)
                ped_real += monthly_data[c]["Pedidos"]["real"].get(m, 0.0)
            else:
                if period_name == "Full Year (Forecast)":
                    # Future actuals replaced by plan
                    gmv_real += monthly_data[c]["GMV"]["plan"].get(m, 0.0)
                    rec_real += monthly_data[c]["Receita Hanzo"]["plan"].get(m, 0.0)
                    ped_real += monthly_data[c]["Pedidos"]["plan"].get(m, 0.0)
                    
    gmv_var = gmv_real - gmv_plan
    gmv_var_pct = gmv_var / gmv_plan if gmv_plan > 0 else 0.0
    rec_var = rec_real - rec_plan
    rec_var_pct = rec_var / rec_plan if rec_plan > 0 else 0.0
    ped_var = ped_real - ped_plan
    ped_var_pct = ped_var / ped_plan if ped_plan > 0 else 0.0
    
    take_rate_real = rec_real / gmv_real if gmv_real > 0 else 0.0
    take_rate_plan = rec_plan / gmv_plan if gmv_plan > 0 else 0.0
    
    print(f"  GMV Plan:       R$ {gmv_plan:,.2f}")
    print(f"  GMV Realized:   R$ {gmv_real:,.2f} (Var: {gmv_var_pct*100:+.2f}%)")
    print(f"  Revenue Plan:   R$ {rec_plan:,.2f}")
    print(f"  Revenue Real:   R$ {rec_real:,.2f} (Var: {rec_var_pct*100:+.2f}%)")
    print(f"  Pedidos Plan:   {ped_plan:,.0f}")
    print(f"  Pedidos Real:   {ped_real:,.0f} (Var: {ped_var_pct*100:+.2f}%)")
    print(f"  Take Rate Plan: {take_rate_plan*100:.2f}% | Take Rate Real: {take_rate_real*100:.2f}%")

# Status Count
status_counts = {}
for c, meta in clients_metadata.items():
    status_counts[meta["status"]] = status_counts.get(meta["status"], 0) + 1
print("\nClient Counts by Status:")
for k, v in status_counts.items():
    print(f"  {k}: {v}")

# ----------------------------------------------------
# PAGE 2: RANKING E CONCENTRAÇÃO
# ----------------------------------------------------
print("\n--- PAGE 2: RANKING DE CLIENTES E CONCENTRAÇÃO ---")
# Top 5 share and largest client based on YTD Revenue
client_revenues_ytd = {}
for c in monthly_data:
    c_rec = sum(monthly_data[c]["Receita Hanzo"]["real"].get(m, 0.0) for m in realized_months)
    client_revenues_ytd[c] = c_rec

total_ytd_revenue = sum(client_revenues_ytd.values())
sorted_clients_by_rec = sorted(client_revenues_ytd.items(), key=lambda x: x[1], reverse=True)

print(f"Total YTD Revenue: R$ {total_ytd_revenue:,.2f}")
print("Top 5 Clients by YTD Revenue:")
top_5_sum = 0.0
for idx, (name, val) in enumerate(sorted_clients_by_rec[:5]):
    share = val / total_ytd_revenue if total_ytd_revenue > 0 else 0.0
    top_5_sum += val
    print(f"  {idx+1}. {name}: R$ {val:,.2f} ({share*100:.2f}%)")
    
share_top5 = top_5_sum / total_ytd_revenue if total_ytd_revenue > 0 else 0.0
dependency_largest = sorted_clients_by_rec[0][1] / total_ytd_revenue if total_ytd_revenue > 0 else 0.0
print(f"Share Top 5 Clients: {share_top5*100:.2f}%")
print(f"Largest Client Dependency: {dependency_largest*100:.2f}% ({sorted_clients_by_rec[0][0]})")

# ----------------------------------------------------
# PAGE 3: CLIENTES DETRATORES
# ----------------------------------------------------
print("\n--- PAGE 3: CLIENTES DETRATORES ---")
# List top 3 revenue losers YTD
client_variances = []
for c in monthly_data:
    c_plan = sum(monthly_data[c]["Receita Hanzo"]["plan"].get(m, 0.0) for m in realized_months)
    c_real = sum(monthly_data[c]["Receita Hanzo"]["real"].get(m, 0.0) for m in realized_months)
    diff = c_real - c_plan
    client_variances.append({"Cliente": c, "Plan": c_plan, "Real": c_real, "Diff": diff})
    
sorted_detractors = sorted(client_variances, key=lambda x: x["Diff"])
print("Top 3 Revenue Detractors (YTD Actual vs Plan):")
for idx, item in enumerate(sorted_detractors[:3]):
    print(f"  {idx+1}. {item['Cliente']}: Plan R$ {item['Plan']:,.2f} | Real R$ {item['Real']:,.2f} | Diff: R$ {item['Diff']:,.2f}")

# ----------------------------------------------------
# PAGE 4: FORECAST E PROJEÇÕES
# ----------------------------------------------------
print("\n--- PAGE 4: FORECAST E PROJEÇÕES ---")
# Verify Overview totals for 2026, 2027, 2028
years_proj = ["2026", "2027", "2028"]
rec_proj_base = {yr: sum(overview_data[c][yr]["Receita Hanzo"] for c in overview_data) for yr in years_proj}
gmv_proj_base = {yr: sum(overview_data[c][yr]["GMV"] for c in overview_data) for yr in years_proj}
print("Overview Sheet Multi-year Plan Totals (Base Scenario):")
for yr in years_proj:
    print(f"  {yr}: GMV R$ {gmv_proj_base[yr]:,.2f} | Revenue R$ {rec_proj_base[yr]:,.2f}")

# ----------------------------------------------------
# PAGE 5: MATRIZ ESTRATÉGICA DE CLIENTES
# ----------------------------------------------------
print("\n--- PAGE 5: MATRIZ ESTRATÉGICA DE CLIENTES ---")
# Check how many clients are in each quadrant based on 2026 revenue vs YoY growth rate (2026 Overview vs 2025 Overview)
classifications = {"Strategic": [], "Expansion": [], "At Risk": [], "Low Priority": []}
for c in overview_data:
    rev_2025 = overview_data[c]["2025"]["Receita Hanzo"]
    rev_2026 = overview_data[c]["2026"]["Receita Hanzo"]
    growth = (rev_2026 - rev_2025) / rev_2025 if rev_2025 > 0 else 0.0
    
    # Classifications
    if rev_2026 >= 100000.0:  # High Revenue threshold
        if growth >= 0.05:
            classifications["Strategic"].append(c)
        else:
            classifications["At Risk"].append(c)
    else:  # Low Revenue
        if growth >= 0.05:
            classifications["Expansion"].append(c)
        else:
            classifications["Low Priority"].append(c)

print("Client Strategic Classifications (2026 Overview Targets):")
for k, v in classifications.items():
    print(f"  {k} ({len(v)}): {', '.join(v[:5])}...")

# ----------------------------------------------------
# PAGE 6: RISCOS & OPORTUNIDADES
# ----------------------------------------------------
print("\n--- PAGE 6: RISCOS & OPORTUNIDADES ---")
# Take rates in Plan
take_rates_list = []
for c in monthly_data:
    c_rec = sum(monthly_data[c]["Receita Hanzo"]["plan"].values())
    c_gmv = sum(monthly_data[c]["GMV"]["plan"].values())
    if c_gmv > 0:
        take_rates_list.append({"Cliente": c, "Take Rate": c_rec / c_gmv, "GMV": c_gmv})
df_tr = pd.DataFrame(take_rates_list)
df_tr_low = df_tr.sort_values("Take Rate").head(3)
df_tr_high = df_tr.sort_values("Take Rate", ascending=False).head(3)

print("Top 3 Highest Take Rate Clients:")
for _, row in df_tr_high.iterrows():
    print(f"  {row['Cliente']}: {row['Take Rate']*100:.2f}% (GMV Plan: R$ {row['GMV']:,.2f})")
print("Top 3 Lowest Take Rate Clients:")
for _, row in df_tr_low.iterrows():
    print(f"  {row['Cliente']}: {row['Take Rate']*100:.2f}% (GMV Plan: R$ {row['GMV']:,.2f})")

# ----------------------------------------------------
# PAGE 7: CLIENT 360
# ----------------------------------------------------
print("\n--- PAGE 7: CLIENT 360 VIEW ---")
sample_client = "Bacio di Latte"
print(f"Sample Client: {sample_client}")
c_ann = overview_data.get(sample_client, {})
print(f"  Overview targets for {sample_client}:")
for yr in ["2025", "2026", "2027", "2028"]:
    print(f"    {yr}: GMV R$ {c_ann[yr]['GMV']:,.2f} | Revenue R$ {c_ann[yr]['Receita Hanzo']:,.2f}")

# ----------------------------------------------------
# PAGE 8: CONSELHO & INVESTIDORES
# ----------------------------------------------------
print("\n--- PAGE 8: CONSELHO & INVESTIDORES ---")
# YoY Growth for filtered clients (2026 Overview vs 2025 Actuals)
total_rec_2025_all = sum(overview_data[c]["2025"]["Receita Hanzo"] for c in overview_data)
total_rec_2026_all = sum(overview_data[c]["2026"]["Receita Hanzo"] for c in overview_data)
yoy_growth_rec = (total_rec_2026_all - total_rec_2025_all) / total_rec_2025_all if total_rec_2025_all > 0 else 0.0

total_gmv_2025_all = sum(overview_data[c]["2025"]["GMV"] for c in overview_data)
total_gmv_2026_all = sum(overview_data[c]["2026"]["GMV"] for c in overview_data)
yoy_growth_gmv = (total_gmv_2026_all - total_gmv_2025_all) / total_gmv_2025_all if total_gmv_2025_all > 0 else 0.0

print(f"Portfolio YoY Growth Rate (2026 Proj vs 2025 Real):")
print(f"  Revenue Growth: {yoy_growth_rec*100:+.2f}% (R$ {total_rec_2025_all:,.2f} -> R$ {total_rec_2026_all:,.2f})")
print(f"  GMV Growth:     {yoy_growth_gmv*100:+.2f}% (R$ {total_gmv_2025_all:,.2f} -> R$ {total_gmv_2026_all:,.2f})")
print("="*60)
