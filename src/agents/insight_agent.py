import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


class InsightAgent:
    """
    Produces hypotheses that explain CTR/ROAS changes.
    Uses heuristics + trend detection + correlations.
    """

    def __init__(self, df):
        self.df = df.copy()
        self.df["date"] = pd.to_datetime(self.df["date"])

    def generate_candidates(self):
        candidates = []

        # 1. CTR trend per campaign
        ctr_trends = self._metric_trend("ctr", by="campaign_name")
        for item in ctr_trends:
            if item["trend"] < -0.01:    # falling CTR
                candidates.append({
                    "id": f"ctr_drop_{item['campaign']}",
                    "hypothesis": "CTR is falling — creative fatigue or weak messaging",
                    "campaign": item["campaign"],
                    "metric": "ctr",
                    "direction": "decrease",
                    "evidence": item
                })

        # 2. ROAS vs Spend correlation
        roas_corr = self._roas_spend_correlation()
        if roas_corr is not None and roas_corr < -0.15:
            candidates.append({
                "id": "roas_spend_negative",
                "hypothesis": "Increasing spend correlates with decreasing ROAS",
                "metric": "roas_vs_spend",
                "value": roas_corr,
                "evidence": {"correlation": roas_corr}
            })

        # 3. Frequency fatigue (approx)
        freq_info = self._frequency_check()
        for row in freq_info:
            if row["frequency"] > 3 and row["ctr"] < 0.01:
                candidates.append({
                    "id": f"fatigue_{row['campaign']}",
                    "hypothesis": "High frequency + low CTR indicates audience fatigue",
                    "campaign": row["campaign"],
                    "metric": "frequency",
                    "evidence": row
                })

        return candidates

    def _metric_trend(self, metric, by="campaign_name"):
        results = []
        for campaign, group in self.df.groupby(by):
            group = group.sort_values("date")
            y = group[metric].values
            if len(y) < 3:
                continue
            X = np.arange(len(y)).reshape(-1, 1)
            model = LinearRegression().fit(X, y)
            slope = float(model.coef_[0])
            results.append({
                "campaign": campaign,
                "trend": slope,
                "mean": float(np.mean(y)),
                "n": len(y)
            })
        return results

    def _roas_spend_correlation(self):
        t = self.df.groupby("date").agg({
            "spend": "sum",
            "revenue": "sum"
        }).reset_index()
        if len(t) < 3:
            return None
        t["roas"] = t["revenue"] / t["spend"].replace(0, 1)
        return float(t["roas"].corr(t["spend"]))

    def _frequency_check(self):
        results = []
        for campaign, g in self.df.groupby("campaign_name"):
            days = max(1, (g["date"].max() - g["date"].min()).days + 1)
            impressions = g["impressions"].sum()
            clicks = g["clicks"].sum()

            frequency = impressions / days / 1000     # scaled
            ctr = clicks / impressions if impressions > 0 else 0

            results.append({
                "campaign": campaign,
                "frequency": float(frequency),
                "ctr": float(ctr)
            })
        return results
