import pandas as pd
import numpy as np
import time
import re


class SchemaError(Exception):
    pass


class DataAgent:
    EXPECTED_SCHEMA = {
        "campaign_name": str,
        "adset_name": str,
        "date": "datetime",
        "spend": float,
        "impressions": float,
        "clicks": float,
        "ctr": float,
        "purchases": float,
        "revenue": float,
        "roas": float,
        "creative_type": str,
        "creative_message": str,
        "audience_type": str,
        "platform": str,
        "country": str,
    }

    def __init__(self, csv_path, logger=None, config=None):
        self.csv_path = csv_path
        self.logger = logger
        self.config = config or {}
        self.df = None

    # --------------------------------------------------------
    # Load CSV
    # --------------------------------------------------------
    def load(self):
        t0 = time.time()
        try:
            df = pd.read_csv(self.csv_path)
        except Exception as e:
            raise SchemaError(f"Failed to load CSV: {e}")

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # validate schema BEFORE cleaning types
        self._validate_schema(df)

        # safe cleaning
        self._clean_types(df)

        load_time = round(time.time() - t0, 3)
        if self.logger:
            self.logger.info({"event": "data_loaded", "rows": len(df), "time_sec": load_time})

        self.df = df
        return df

    # --------------------------------------------------------
    # Schema Validation
    # --------------------------------------------------------
    def _normalize_col(self, col):
        return re.sub(r"[^a-z0-9]", "", str(col).lower())

    def _detect_drift(self, df_columns):
        mode = getattr(self, "drift_mode", None) or self.config.get("schema_drift_mode", "fail")

        expected = set(self.EXPECTED_SCHEMA)
        actual = set(df_columns)

        missing = [c for c in expected if c not in actual]
        extra = [c for c in actual if c not in expected]

        norm_expected = {self._normalize_col(c): c for c in expected}
        norm_actual = {self._normalize_col(c): c for c in actual}

        near_miss = []
        for ncol, raw in norm_actual.items():
            if ncol in norm_expected and norm_expected[ncol] not in actual:
                near_miss.append({"expected": norm_expected[ncol], "actual": raw})

        # Missing columns are always severe
        # Extra columns are not considered "drift" for failure purposes
        severity = len(missing) / max(1, len(expected))

        details = {
            "missing": missing,
            "extra": extra,
            "near_miss": near_miss,
            "severity": round(severity, 3),
        }

        # No drift
        if not missing and not near_miss:
            if extra and self.logger:
                self.logger.warning({"event": "extra_columns_detected", "columns": extra})
            return

        # Missing columns should fail if mode=fail
        if missing:
            if mode == "warn":
                if self.logger:
                    self.logger.warning({"event": "schema_drift_warning", "details": details})
                return
            if mode == "fail":
                raise SchemaError(f"Schema drift detected: {details}")
            return

        # Only near miss drift → fail only if mode = fail
        if near_miss and mode == "fail":
            raise SchemaError(f"Schema drift detected: {details}")

        if self.logger:
            self.logger.warning({"event": "schema_drift_warning", "details": details})

    def _validate_schema(self, df):
        missing = [c for c in self.EXPECTED_SCHEMA if c not in df.columns]
        extra = [c for c in df.columns if c not in self.EXPECTED_SCHEMA]
        null_report = df.isnull().mean().round(3).to_dict()

        # Missing columns ALWAYS validated through drift detection
        if missing:
            self._detect_drift(df.columns)
            # if drift detector didn’t raise, this is warn-mode
            return

        # Extra columns are allowed (warn only)
        if extra and self.logger:
            self.logger.warning({"event": "extra_columns_detected", "columns": extra})

        # Severe nulls → always error
        severe_nulls = {c: r for c, r in null_report.items() if r > 0.5}
        if severe_nulls:
            raise SchemaError(f"Columns with >50% null values detected: {severe_nulls}")

        # All dates invalid
        if "date" in df.columns and df["date"].isnull().all():
            raise SchemaError("All values in 'date' parsed to null — bad date format")

        # Now check for drift
        self._detect_drift(df.columns)

        if self.logger:
            self.logger.info({
                "event": "schema_validated",
                "missing": missing,
                "extra": extra,
                "null_report": null_report,
            })

    # --------------------------------------------------------
    # Type Cleaning
    # --------------------------------------------------------
    def _clean_types(self, df):
        for col, expected in self.EXPECTED_SCHEMA.items():
            if col not in df.columns:
                continue

            if expected == float:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                df[col] = df[col].replace([np.inf, -np.inf], np.nan).fillna(0.0)

            elif expected == str:
                df[col] = df[col].astype(str).replace("nan", "").fillna("")

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------
    def summary(self):
        if self.df is None:
            raise ValueError("Dataset not loaded")

        df = self.df
        ts = df.groupby("date").agg({
            "spend": "sum",
            "impressions": "sum",
            "clicks": "sum",
            "purchases": "sum",
            "revenue": "sum",
        }).sort_index()

        ts["ctr"] = ts["clicks"] / ts["impressions"].replace(0, 1)
        ts["roas"] = ts["revenue"] / ts["spend"].replace(0, 1)

        cs = df.groupby("campaign_name").agg({
            "spend": "sum",
            "impressions": "sum",
            "clicks": "sum",
            "purchases": "sum",
            "revenue": "sum",
        })

        cs["ctr"] = cs["clicks"] / cs["impressions"].replace(0, 1)
        cs["roas"] = cs["revenue"] / cs["spend"].replace(0, 1)

        return {
            "timeseries": ts.reset_index().to_dict(orient="records"),
            "campaign_summary": cs.reset_index().to_dict(orient="records"),
            "schema": df.dtypes.astype(str).to_dict(),
        }
