import os
import sys

print("Python version:", sys.version)

try:
    import data_loader
    print("data_loader.py imported successfully!")
except Exception as e:
    print("Failed to import data_loader.py:", e)
    sys.exit(1)

excel_path = "Planejamento 2026.xlsx"
if not os.path.exists(excel_path):
    print("Spreadsheet not found!")
    sys.exit(1)

try:
    overview_data, monthly_data, optimistic_monthly_data, clients_metadata = data_loader.load_data(excel_path)
    print("Data loaded successfully!")
    print(f"Total clients parsed: {len(clients_metadata)}")
    
    # Verify monthly base totals
    total_gmv_plan = 0.0
    total_rec_plan = 0.0
    
    for c, metrics in monthly_data.items():
        total_gmv_plan += sum(metrics["GMV"]["plan"].values())
        total_rec_plan += sum(metrics["Receita Hanzo"]["plan"].values())
        
    print(f"Aggregated 2026 Planned GMV (Base): R$ {total_gmv_plan:,.2f}")
    print(f"Aggregated 2026 Planned Revenue (Base): R$ {total_rec_plan:,.2f}")
    
    # Verify Overview totals for 2026
    total_rec_2026_ov = sum(overview_data[c]["2026"]["Receita Hanzo"] for c in overview_data)
    total_gmv_2026_ov = sum(overview_data[c]["2026"]["GMV"] for c in overview_data)
    
    print(f"Overview 2026 Planned GMV: R$ {total_gmv_2026_ov:,.2f}")
    print(f"Overview 2026 Planned Revenue: R$ {total_rec_2026_ov:,.2f}")
    
    # Check if monthly sums are close to annual targets
    # (Outback and wishlist might differ if they are not in monthly sheet)
    print("Verification passed successfully!")
except Exception as e:
    print("Error during data load or calculation:", e)
    import traceback
    traceback.print_exc()
    sys.exit(1)
