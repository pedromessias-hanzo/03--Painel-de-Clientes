import os
import pandas as pd
import numpy as np

CLEAN_NAME_MAP = {
    "BACIO DI LATTE (+200)": "Bacio di Latte",
    "BACIO DI LATTE": "Bacio di Latte",
    "CHIQUINHO (+1000)": "Chiquinho",
    "CHIQUINHO": "Chiquinho",
    "CAMARADA CAMARÃO": "Camarada Camarão",
    "CAMARADA CAMARO": "Camarada Camarão",
    "ESFIHA IMIGRANTES (4)": "Esfiha Imigrantes",
    "ESFIHA IMIGRANTES": "Esfiha Imigrantes",
    "FROOTY (2)": "Frooty",
    "FROOTY": "Frooty",
    "GULA GULA (10)": "Gula Gula",
    "GULA GULA": "Gula Gula",
    "ITAL'IN HOUSE (200)": "Ital'in House",
    "ITAL'IN HOUSE": "Ital'in House",
    "MANA POKE (70)": "Mana Poke",
    "MANA POKE": "Mana Poke",
    "MILK MOO (+780)": "Milk Moo",
    "MILKY MOO": "Milk Moo",
    "OLIVERS (8)": "Olivers",
    "OLIVERS": "Olivers",
    "PAPILA (7)": "Papila",
    "PAPILA": "Papila",
    "PIZZA HUT (+250)": "Pizza Hut",
    "PIZZA HUT": "Pizza Hut",
    "QUI O QUA": "Qui o Qua",
    "TASTEFY (+180)": "Tastefy",
    "TASTEFY": "Tastefy",
    "VINIL BURGER (05)": "Vinil Burger",
    "VINIL BURGER": "Vinil Burger",
    "WE COFFEE (15)": "We Coffee",
    "WE COFFEE": "We Coffee",
    "OUTBACK (180)": "Outback",
    "OUTBACK": "Outback",
    "NINETTO": "Ninetto",
    "NINO CUCINA": "Nino Cucina",
    "TATU BOLA": "Tatu Bola",
    "BOA PRAÇA": "Boa Praça",
    "BOA PRAA": "Boa Praça",
    "RAINHA": "Rainha",
    "DEAL WISH LIST": "Deal Wish List",
    "01 DEAL WISH LIST": "Deal Wish List 1",
    "02 DEAL WISH LIST": "Deal Wish List 2",
}

STATUS_MAP = {
    "Bacio di Latte": "Ativo",
    "Pizza Hut": "Ativo",
    "Qui o Qua": "Ativo",
    "Esfiha Imigrantes": "Ativo",
    "Milk Moo": "Ativo",
    "Mana Poke": "Ativo",
    "Gula Gula": "Ativo",
    "We Coffee": "Ativo",
    "Olivers": "Ativo",
    "Papila": "Ativo",
    "Vinil Burger": "Ativo",
    "Chiquinho": "Novo Cliente",
    "Frooty": "Novo Cliente",
    "Ital'in House": "Novo Cliente",
    "Tastefy": "Novo Cliente",
    "Camarada Camarão": "Novo Cliente",
    "Outback": "Novo Cliente",
    "Ninetto": "Pipeline",
    "Nino Cucina": "Pipeline",
    "Tatu Bola": "Pipeline",
    "Boa Praça": "Pipeline",
    "Rainha": "Pipeline",
    "Deal Wish List": "Wish List",
    "Deal Wish List 1": "Wish List",
    "Deal Wish List 2": "Wish List",
}

GROUP_MAP = {
    "Ninetto": "Grupo Alife Nino",
    "Nino Cucina": "Grupo Alife Nino",
    "Tatu Bola": "Grupo Alife Nino",
    "Boa Praça": "Grupo Alife Nino",
    "Rainha": "Grupo Alife Nino",
    "Camarada Camarão": "Grupo Drumattos",
    "Outback": "Grupo Bold",
}

def clean_client_name(raw_name):
    raw_clean = str(raw_name).strip()
    return CLEAN_NAME_MAP.get(raw_clean, raw_clean)

def get_client_status(client_name):
    return STATUS_MAP.get(client_name, "Ativo")

def get_client_group(client_name):
    return GROUP_MAP.get(client_name, "Independente")

def clean_val(val):
    if pd.isna(val) or val == '-' or str(val).strip() == '' or str(val).strip() == '#DIV/0!':
        return 0.0
    try:
        return float(val)
    except:
        return 0.0

def map_columns(df):
    """
    Scans Row 2 (index 2) of the sheet to map month columns to their respective:
      - plan
      - weekly columns (W1-W5)
      - real (accumulated actual)
      - diff
      - comp
    """
    months_map = {}
    months_list = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
    
    if df.shape[0] <= 2:
        return months_map
        
    row_labels = [str(x).strip().lower() for x in df.iloc[2]]
    
    for m in months_list:
        plan_col = None
        weekly_cols = []
        real_col = None
        diff_col = None
        comp_col = None
        
        for col_idx, label in enumerate(row_labels):
            lbl_clean = label.replace('ç', 'c').replace('ã', 'a').replace('õ', 'o').replace('é', 'e').replace('í', 'i')
            if lbl_clean == m:
                plan_col = col_idx
            elif lbl_clean == f"{m} (real)" or label == f"{m} (real)":
                real_col = col_idx
            elif f"diferenca ({m})" in lbl_clean or f"diferena ({m})" in lbl_clean:
                diff_col = col_idx
            elif f"comparativo ({m})" in lbl_clean:
                comp_col = col_idx
            elif f"{m} (semana" in lbl_clean:
                weekly_cols.append(col_idx)
                
        weekly_cols.sort()
        
        if plan_col is not None:
            months_map[m] = {
                "plan": plan_col,
                "weekly": weekly_cols,
                "real": real_col,
                "diff": diff_col,
                "comp": comp_col
            }
            
    return months_map

def load_data(sheets_data):
    """
    Loads Excel sheets from the sheets_data dictionary and returns overview and parsed data structures.
    Uses separate parsing for Planejamento (monthly) and Projeção (weekly) sheets.
    """
    # 1. PARSE OVERVIEW SHEET
    overview_data = {}
    if "Overview" in sheets_data:
        df_ov = sheets_data["Overview"]
        current_client = None
        wishlist_counter = 0
        for i in range(len(df_ov)):
            val0 = df_ov.iloc[i, 0]
            if pd.isna(val0):
                continue
            val0_str = str(val0).strip()
            is_metric = False
            for m in ['% do m', 'repres.', 'gmv', 'pedidos', 'receita']:
                if m in val0_str.lower():
                    is_metric = True
                    break
            if is_metric:
                if current_client:
                    m_key = None
                    if 'gmv' in val0_str.lower():
                        m_key = 'GMV'
                    elif 'pedido' in val0_str.lower():
                        m_key = 'Pedidos'
                    elif 'receita' in val0_str.lower():
                        m_key = 'Receita Hanzo'
                    if m_key:
                        for col_idx, yr in enumerate(['2025', '2026', '2027', '2028']):
                            if col_idx + 1 < df_ov.shape[1]:
                                val = df_ov.iloc[i, col_idx + 1]
                                overview_data[current_client][yr][m_key] = clean_val(val)
            else:
                if 'verificar' in val0_str.lower() or 'total' in val0_str.lower():
                    current_client = None
                    continue
                raw_client = val0_str
                clean_client = clean_client_name(raw_client)
                if clean_client == "Deal Wish List":
                    wishlist_counter += 1
                    clean_client = f"Deal Wish List {wishlist_counter}"
                current_client = clean_client
                overview_data[current_client] = {
                    "2025": {"GMV": 0.0, "Pedidos": 0.0, "Receita Hanzo": 0.0},
                    "2026": {"GMV": 0.0, "Pedidos": 0.0, "Receita Hanzo": 0.0},
                    "2027": {"GMV": 0.0, "Pedidos": 0.0, "Receita Hanzo": 0.0},
                    "2028": {"GMV": 0.0, "Pedidos": 0.0, "Receita Hanzo": 0.0}
                }
                
    # 2. MAP COLUMNS FOR BOTH SHEET DATAFRAMES
    df_pl = sheets_data.get("Planejamento")
    m_map_pl = map_columns(df_pl)
    
    proj_sheet = None
    for s in ["Projeção", "Projeo"]:
        if s in sheets_data:
            proj_sheet = s
            break
    
    if proj_sheet:
        df_proj = sheets_data[proj_sheet]
        m_map_proj = map_columns(df_proj)
    else:
        df_proj = df_pl
        m_map_proj = m_map_pl

    # 3. PARSE MONTHLY CONSOLIDATIONS FROM PLANEJAMENTO
    monthly_data = {}
    pl_client_blocks = {}
    for r in range(1, len(df_pl)):
        lbl = df_pl.iloc[r, 9]
        if pd.notna(lbl):
            lbl_str = str(lbl).strip()
            if r + 6 < len(df_pl):
                gmv_check = str(df_pl.iloc[r+3, 9]).strip()
                ped_check = str(df_pl.iloc[r+4, 9]).strip()
                rec_check = str(df_pl.iloc[r+6, 9]).strip()
                if 'GMV' in gmv_check and 'Pedido' in ped_check and 'Receita' in rec_check:
                    client_name = clean_client_name(lbl_str)
                    pl_client_blocks[client_name] = r
                    
    for client_name, r in pl_client_blocks.items():
        monthly_data[client_name] = {
            "GMV": {"plan": {}, "real": {}},
            "Pedidos": {"plan": {}, "real": {}},
            "Ticket Médio": {"plan": {}, "real": {}},
            "Receita Hanzo": {"plan": {}, "real": {}}
        }
        for m_name, cols in m_map_pl.items():
            plan_col = cols["plan"]
            real_col = cols["real"]
            
            monthly_data[client_name]["GMV"]["plan"][m_name] = clean_val(df_pl.iloc[r+3, plan_col])
            monthly_data[client_name]["GMV"]["real"][m_name] = clean_val(df_pl.iloc[r+3, real_col])
            
            monthly_data[client_name]["Pedidos"]["plan"][m_name] = clean_val(df_pl.iloc[r+4, plan_col])
            monthly_data[client_name]["Pedidos"]["real"][m_name] = clean_val(df_pl.iloc[r+4, real_col])
            
            monthly_data[client_name]["Ticket Médio"]["plan"][m_name] = clean_val(df_pl.iloc[r+5, plan_col])
            monthly_data[client_name]["Ticket Médio"]["real"][m_name] = clean_val(df_pl.iloc[r+5, real_col])
            
            monthly_data[client_name]["Receita Hanzo"]["plan"][m_name] = clean_val(df_pl.iloc[r+6, plan_col])
            monthly_data[client_name]["Receita Hanzo"]["real"][m_name] = clean_val(df_pl.iloc[r+6, real_col])

    # 4. PARSE WEEKLY MONITORING DATA FROM PROJEÇÃO
    weekly_data = {}
    proj_client_blocks = {}
    for r in range(1, len(df_proj)):
        lbl = df_proj.iloc[r, 9]
        if pd.notna(lbl):
            lbl_str = str(lbl).strip()
            if r + 6 < len(df_proj):
                gmv_check = str(df_proj.iloc[r+3, 9]).strip()
                ped_check = str(df_proj.iloc[r+4, 9]).strip()
                rec_check = str(df_proj.iloc[r+6, 9]).strip()
                if 'GMV' in gmv_check and 'Pedido' in ped_check and 'Receita' in rec_check:
                    client_name = clean_client_name(lbl_str)
                    proj_client_blocks[client_name] = r

    for client_name, r in proj_client_blocks.items():
        weekly_data[client_name] = {
            "GMV": {"plan": {}, "real": {}, "weekly": {}, "diff": {}, "comp": {}},
            "Pedidos": {"plan": {}, "real": {}, "weekly": {}, "diff": {}, "comp": {}},
            "Ticket Médio": {"plan": {}, "real": {}, "weekly": {}, "diff": {}, "comp": {}},
            "Receita Hanzo": {"plan": {}, "real": {}, "weekly": {}, "diff": {}, "comp": {}}
        }
        for m_name, cols in m_map_proj.items():
            plan_col = cols["plan"]
            real_col = cols["real"]
            diff_col = cols["diff"]
            comp_col = cols["comp"]
            weekly_cols = cols["weekly"]
            
            # GMV
            weekly_data[client_name]["GMV"]["plan"][m_name] = clean_val(df_proj.iloc[r+3, plan_col])
            weekly_data[client_name]["GMV"]["real"][m_name] = clean_val(df_proj.iloc[r+3, real_col])
            weekly_data[client_name]["GMV"]["diff"][m_name] = df_proj.iloc[r+3, diff_col] if diff_col is not None else None
            weekly_data[client_name]["GMV"]["comp"][m_name] = df_proj.iloc[r+3, comp_col] if comp_col is not None else None
            weekly_data[client_name]["GMV"]["weekly"][m_name] = [clean_val(df_proj.iloc[r+3, col]) for col in weekly_cols]
            
            # Pedidos
            weekly_data[client_name]["Pedidos"]["plan"][m_name] = clean_val(df_proj.iloc[r+4, plan_col])
            weekly_data[client_name]["Pedidos"]["real"][m_name] = clean_val(df_proj.iloc[r+4, real_col])
            weekly_data[client_name]["Pedidos"]["diff"][m_name] = df_proj.iloc[r+4, diff_col] if diff_col is not None else None
            weekly_data[client_name]["Pedidos"]["comp"][m_name] = df_proj.iloc[r+4, comp_col] if comp_col is not None else None
            weekly_data[client_name]["Pedidos"]["weekly"][m_name] = [clean_val(df_proj.iloc[r+4, col]) for col in weekly_cols]
            
            # Ticket Médio
            weekly_data[client_name]["Ticket Médio"]["plan"][m_name] = clean_val(df_proj.iloc[r+5, plan_col])
            weekly_data[client_name]["Ticket Médio"]["real"][m_name] = clean_val(df_proj.iloc[r+5, real_col])
            weekly_data[client_name]["Ticket Médio"]["diff"][m_name] = df_proj.iloc[r+5, diff_col] if diff_col is not None else None
            weekly_data[client_name]["Ticket Médio"]["comp"][m_name] = df_proj.iloc[r+5, comp_col] if comp_col is not None else None
            weekly_data[client_name]["Ticket Médio"]["weekly"][m_name] = [clean_val(df_proj.iloc[r+5, col]) for col in weekly_cols]
            
            # Receita Hanzo
            weekly_data[client_name]["Receita Hanzo"]["plan"][m_name] = clean_val(df_proj.iloc[r+6, plan_col])
            weekly_data[client_name]["Receita Hanzo"]["real"][m_name] = clean_val(df_proj.iloc[r+6, real_col])
            weekly_data[client_name]["Receita Hanzo"]["diff"][m_name] = df_proj.iloc[r+6, diff_col] if diff_col is not None else None
            weekly_data[client_name]["Receita Hanzo"]["comp"][m_name] = df_proj.iloc[r+6, comp_col] if comp_col is not None else None
            weekly_data[client_name]["Receita Hanzo"]["weekly"][m_name] = [clean_val(df_proj.iloc[r+6, col]) for col in weekly_cols]

    # 5. CONSOLIDATE METADATA
    all_clients = set(overview_data.keys()).union(set(monthly_data.keys())).union(set(weekly_data.keys()))
    clients_metadata = {}
    for c in all_clients:
        clients_metadata[c] = {
            "status": get_client_status(c),
            "group": get_client_group(c)
        }
        
    return overview_data, monthly_data, weekly_data, clients_metadata
