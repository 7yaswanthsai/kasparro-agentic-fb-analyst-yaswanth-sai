class EvaluatorAgent:
    """
    Validates hypotheses using scoring rules.
    Produces a confidence score (0–1) and marks valid/invalid.
    """

    def __init__(self, df, config):
        self.df = df
        self.min_conf = config.get("confidence_min", 0.6)

    def validate(self, hypotheses):
        results = []

        for h in hypotheses:
            score = 0.5  # base

            evidence = h.get("evidence", {})

            # CTR-based hypotheses
            if h.get("metric") == "ctr":
                if evidence.get("trend", 0) < -0.01:
                    score += 0.2
                if evidence.get("mean", 1) < 0.02:
                    score += 0.2

            # ROAS vs spend correlation
            if h.get("id") == "roas_spend_negative":
                corr = h.get("value", 0)
                if corr < -0.20:
                    score += 0.25

            # Fatigue
            if h.get("metric") == "frequency":
                if evidence.get("frequency", 0) > 3:
                    score += 0.15
                if evidence.get("ctr", 1) < 0.01:
                    score += 0.15

            # clamp between 0 and 1
            score = max(0, min(1, score))

            results.append({
                "id": h["id"],
                "hypothesis": h["hypothesis"],
                "campaign": h.get("campaign"),
                "confidence": score,
                "valid": score >= self.min_conf,
                "raw_evidence": evidence
            })

        return results
