import os
import pandas as pd
import datetime

# Clean client labels to a standard display name
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
    # Handle duplicates in Overview by row indexing or raw names
    if raw_clean in CLEAN_NAME_MAP:
        return CLEAN_NAME_MAP[raw_clean]
    return raw_clean

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

def load_data(filepath):
    """
    Loads Planejamento 2026.xlsx and parses it dynamically.
    Returns:
        overview_data (dict): Annual targets and historical values (2025-2028).
        monthly_data (dict): Monthly 2026 plan/real values for Base scenario.
        optimistic_monthly_data (dict): Monthly 2026 plan values for Optimistic scenario.
        clients_metadata (dict): Mapping client -> {'status', 'group'}
    """
    if isinstance(filepath, str):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Planilha não encontrada: {filepath}")
        xl = pd.ExcelFile(filepath)
    else:
        xl = pd.ExcelFile(filepath)
    
    # 1. PARSE OVERVIEW SHEET (Annual GMV, Pedidos, Receita Hanzo for 2025-2028)
    df_ov = xl.parse("Overview")
    overview_data = {}
    current_client = None
    wishlist_counter = 0

    for i in range(len(df_ov)):
        val0 = df_ov.iloc[i, 0]
        if pd.isna(val0):
            continue
        
        val0_str = str(val0).strip()
        
        # Check if it's a metric row or a client header row
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
                        val = df_ov.iloc[i, col_idx + 1]
                        overview_data[current_client][yr][m_key] = clean_val(val)
        else:
            if 'verificar' in val0_str.lower() or 'total' in val0_str.lower():
                current_client = None
                continue
                
            raw_client = val0_str
            clean_client = clean_client_name(raw_client)
            
            # Handle the duplicate DEAL WISH LIST entries in Overview
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

    # 2. PARSE PLANEJAMENTO SHEET (2026 Monthly Plan/Real)
    df_pl = xl.parse("Planejamento")
    
    # Locate month columns
    row1 = df_pl.iloc[1].tolist()
    months_cols = {}
    for idx, val in enumerate(row1):
        if pd.notna(val) and val in ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']:
            months_cols[val] = {
                "plan": idx,
                "real": idx + 1,
                "diff": idx + 2,
                "comp": idx + 3
            }

    # Extract monthly base values
    monthly_data = parse_monthly_sheet(df_pl, months_cols)
    
    # 3. PARSE OPTIMISTIC SHEET (planej.OPS-OTIMISTA_26)
    optimistic_monthly_data = {}
    if "planej.OPS-OTIMISTA_26" in xl.sheet_names:
        df_opt = xl.parse("planej.OPS-OTIMISTA_26")
        optimistic_monthly_data = parse_monthly_sheet(df_opt, months_cols)
    else:
        # Fallback to base plan if optimistic sheet is not present
        optimistic_monthly_data = monthly_data

    # 4. COMPILE METADATA
    # We consolidate all client names from both Overview and Planejamento
    all_clients = set(overview_data.keys()).union(set(monthly_data.keys()))
    clients_metadata = {}
    for c in all_clients:
        clients_metadata[c] = {
            "status": get_client_status(c),
            "group": get_client_group(c)
        }

    return overview_data, monthly_data, optimistic_monthly_data, clients_metadata

def parse_monthly_sheet(df, months_cols):
    data = {}
    
    # Find client blocks dynamically by checking Column 9 labels
    for r in range(1, len(df)):
        lbl = df.iloc[r, 9]
        if pd.isna(lbl):
            continue
        
        lbl_str = str(lbl).strip()
        
        # Check if the next rows follow the block structure
        # A block has: [r]=client, [r+1]=% do mês, [r+2]=GMV, [r+3]=Pedidos, [r+4]=Ticket, [r+5]=Receita
        # We check if row r+2 has GMV in Col 9
        if r + 5 < len(df):
            gmv_check = str(df.iloc[r+2, 9]).strip()
            ped_check = str(df.iloc[r+3, 9]).strip()
            rec_check = str(df.iloc[r+5, 9]).strip()
            
            if 'GMV' in gmv_check and 'Pedido' in ped_check and 'Receita' in rec_check:
                client_name = clean_client_name(lbl_str)
                data[client_name] = {
                    "GMV": {"plan": {}, "real": {}},
                    "Pedidos": {"plan": {}, "real": {}},
                    "Receita Hanzo": {"plan": {}, "real": {}}
                }
                
                # Parse monthly values
                for m_name, cols in months_cols.items():
                    data[client_name]["GMV"]["plan"][m_name] = clean_val(df.iloc[r+2, cols["plan"]])
                    data[client_name]["GMV"]["real"][m_name] = clean_val(df.iloc[r+2, cols["real"]])
                    
                    data[client_name]["Pedidos"]["plan"][m_name] = clean_val(df.iloc[r+3, cols["plan"]])
                    data[client_name]["Pedidos"]["real"][m_name] = clean_val(df.iloc[r+3, cols["real"]])
                    
                    data[client_name]["Receita Hanzo"]["plan"][m_name] = clean_val(df.iloc[r+5, cols["plan"]])
                    data[client_name]["Receita Hanzo"]["real"][m_name] = clean_val(df.iloc[r+5, cols["real"]])
                    
    return data
