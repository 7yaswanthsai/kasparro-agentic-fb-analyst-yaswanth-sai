import sys, os
import pandas as pd
import json
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from run import main

def test_metrics_exist(tmp_path):
    # create dataset first
    df_path = tmp_path / "sample.csv"
    df_path.write_text("""campaign_name,adset_name,date,spend,impressions,clicks,ctr,purchases,revenue,roas,creative_type,creative_message,audience_type,platform,country
C1,A1,2025-01-01,100,1000,10,0.01,1,100,1.0,img,x,broad,fb,IN
""")

    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(f"""
data_csv: {df_path}
logs_dir: logs
output_dir: reports
insights_file: reports/insights.json
creatives_file: reports/creatives.json
report_file: reports/report.md
schema_drift_mode: fail
""")

    main("Test Query", str(cfg_path))

    logs = os.listdir("logs")
    assert len(logs) > 0

    latest = json.load(open(os.path.join("logs", logs[-1])))
    assert "_metrics" in latest
    assert "data_load" in latest["_metrics"]
