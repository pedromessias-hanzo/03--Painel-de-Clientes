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
        
        for col_idx, label in enumerate(row_labels):
            if label == m:
                plan_col = col_idx
            elif f"{m} (real)" in label or label == f"{m} (real)":
                real_col = col_idx
            elif f"diferença ({m})" in label or f"diferena ({m})" in label:
                diff_col = col_idx
            elif f"{m} (semana" in label:
                weekly_cols.append(col_idx)
                
        weekly_cols.sort()
        
        if plan_col is not None:
            months_map[m] = {
                "plan": plan_col,
                "weekly": weekly_cols,
                "real": real_col,
                "diff": diff_col
            }
            
    return months_map

def load_data(sheets_data):
    """
    Loads Excel sheets from the sheets_data dictionary and returns overview and parsed data structures.
    Uses fallback sheet loader.
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
                
    # 2. LOAD PLANEJAMENTO OR PROJEÇÃO DYNAMICALLY
    df_pl = sheets_data.get("Planejamento")
    m_map_pl = map_columns(df_pl)
    has_weekly = any(m_map_pl[m]["weekly"] for m in m_map_pl)
    
    if has_weekly:
        df = df_pl
        m_map = m_map_pl
    else:
        # Fallback to Projeção
        proj_sheet = None
        for s in ["Projeção", "Projeo"]:
            if s in sheets_data:
                proj_sheet = s
                break
        if proj_sheet:
            df = sheets_data[proj_sheet]
            m_map = map_columns(df)
        else:
            df = df_pl
            m_map = m_map_pl

    # 3. PARSE METRICS
    monthly_data = {}
    
    # Locate all client rows and clean client names
    client_blocks = {}
    for r in range(1, len(df)):
        lbl = df.iloc[r, 9]
        if pd.notna(lbl):
            lbl_str = str(lbl).strip()
            # Verify structure (GMV is at r+3, Pedidos is at r+4, Receita is at r+6)
            if r + 6 < len(df):
                gmv_check = str(df.iloc[r+3, 9]).strip()
                ped_check = str(df.iloc[r+4, 9]).strip()
                rec_check = str(df.iloc[r+6, 9]).strip()
                if 'GMV' in gmv_check and 'Pedido' in ped_check and 'Receita' in rec_check:
                    client_name = clean_client_name(lbl_str)
                    client_blocks[client_name] = r
                    
    # Parse data for each client
    for client_name, r in client_blocks.items():
        monthly_data[client_name] = {
            "GMV": {"plan": {}, "real": {}, "weekly": {}},
            "Pedidos": {"plan": {}, "real": {}, "weekly": {}},
            "Ticket Médio": {"plan": {}, "real": {}, "weekly": {}},
            "Receita Hanzo": {"plan": {}, "real": {}, "weekly": {}}
        }
        
        for m_name, cols in m_map.items():
            plan_col = cols["plan"]
            real_col = cols["real"]
            weekly_cols = cols["weekly"]
            
            # 1. GMV
            monthly_data[client_name]["GMV"]["plan"][m_name] = clean_val(df.iloc[r+3, plan_col])
            monthly_data[client_name]["GMV"]["real"][m_name] = clean_val(df.iloc[r+3, real_col])
            monthly_data[client_name]["GMV"]["weekly"][m_name] = [clean_val(df.iloc[r+3, col]) for col in weekly_cols]
            
            # 2. Pedidos
            monthly_data[client_name]["Pedidos"]["plan"][m_name] = clean_val(df.iloc[r+4, plan_col])
            monthly_data[client_name]["Pedidos"]["real"][m_name] = clean_val(df.iloc[r+4, real_col])
            monthly_data[client_name]["Pedidos"]["weekly"][m_name] = [clean_val(df.iloc[r+4, col]) for col in weekly_cols]
            
            # 3. Ticket Médio
            monthly_data[client_name]["Ticket Médio"]["plan"][m_name] = clean_val(df.iloc[r+5, plan_col])
            monthly_data[client_name]["Ticket Médio"]["real"][m_name] = clean_val(df.iloc[r+5, real_col])
            monthly_data[client_name]["Ticket Médio"]["weekly"][m_name] = [clean_val(df.iloc[r+5, col]) for col in weekly_cols]
            
            # 4. Receita Hanzo
            monthly_data[client_name]["Receita Hanzo"]["plan"][m_name] = clean_val(df.iloc[r+6, plan_col])
            monthly_data[client_name]["Receita Hanzo"]["real"][m_name] = clean_val(df.iloc[r+6, real_col])
            monthly_data[client_name]["Receita Hanzo"]["weekly"][m_name] = [clean_val(df.iloc[r+6, col]) for col in weekly_cols]
            
    # Consolidate metadata
    all_clients = set(overview_data.keys()).union(set(monthly_data.keys()))
    clients_metadata = {}
    for c in all_clients:
        clients_metadata[c] = {
            "status": get_client_status(c),
            "group": get_client_group(c)
        }
        
    return overview_data, monthly_data, monthly_data, clients_metadata
