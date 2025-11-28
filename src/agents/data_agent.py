import pandas as pd
import numpy as np


class DataAgent:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = None

    def load(self):
        df = pd.read_csv(self.csv_path, parse_dates=["date"])

        # Convert numeric fields
        numeric_cols = ["spend", "impressions", "clicks", "purchases", "revenue", "ctr", "roas"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        self.df = df
        return df

    def summary(self):
        if self.df is None:
            raise ValueError("Dataset not loaded")

        df = self.df

        # time-series summary
        ts = df.groupby("date").agg({
            "spend": "sum",
            "impressions": "sum",
            "clicks": "sum",
            "purchases": "sum",
            "revenue": "sum"
        }).sort_index()

        ts["ctr"] = ts["clicks"] / ts["impressions"].replace(0, 1)
        ts["roas"] = ts["revenue"] / ts["spend"].replace(0, 1)

        # campaign summary
        cs = df.groupby("campaign_name").agg({
            "spend": "sum",
            "impressions": "sum",
            "clicks": "sum",
            "purchases": "sum",
            "revenue": "sum"
        })

        cs["ctr"] = cs["clicks"] / cs["impressions"].replace(0, 1)
        cs["roas"] = cs["revenue"] / cs["spend"].replace(0, 1)

        return {
            "timeseries": ts.reset_index().to_dict(orient="records"),
            "campaign_summary": cs.reset_index().to_dict(orient="records"),
            "columns": df.columns.tolist()
        }
