import argparse
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
sys.path.insert(0, ROOT_DIR)

from src.utils import load_config, save_json, set_seeds
from src.agents.data_agent import DataAgent
from src.agents.planner import PlannerAgent
from src.agents.insight_agent import InsightAgent
from src.agents.evaluator import EvaluatorAgent
from src.agents.creative_generator import CreativeGenerator




def main(user_query, config_path="config/config.yaml"):
    # Load config
    config = load_config(config_path)
    set_seeds(config.get("random_seed", 42))

    data_path = config["data_csv"]

    # ============= STEP 1: Planner =============
    planner = PlannerAgent()
    plan = planner.plan(user_query)

    # ============= STEP 2: Data Agent =============
    data_agent = DataAgent(data_path)
    df = data_agent.load()
    summary = data_agent.summary()

    # ============= STEP 3: Insight Agent =============
    insight_agent = InsightAgent(df)
    hypotheses = insight_agent.generate_candidates()

    # ============= STEP 4: Evaluator Agent =============
    evaluator = EvaluatorAgent(df, config)
    validated = evaluator.validate(hypotheses)

    # ============= STEP 5: Creative Generator =============
    # Pick campaigns with low CTR insights validated
    low_ctr_campaigns = [
        h["campaign"]
        for h in validated
        if h["valid"] and h["campaign"] is not None and "ctr" in h["hypothesis"].lower()
    ]

    # fallback: choose bottom 2 CTR campaigns
    if not low_ctr_campaigns:
        dfc = df.groupby("campaign_name").agg({"clicks": "sum", "impressions": "sum"})
        dfc["ctr"] = dfc["clicks"] / dfc["impressions"].replace(0, 1)
        low_ctr_campaigns = dfc.sort_values("ctr").head(2).index.tolist()

    creative_gen = CreativeGenerator(df)
    creatives = creative_gen.generate_for_campaigns(low_ctr_campaigns)

    # ============= STEP 6: Save Outputs =============
    os.makedirs(config["output_dir"], exist_ok=True)
    os.makedirs(config["logs_dir"], exist_ok=True)

    insights_path = config["insights_file"]
    creatives_path = config["creatives_file"]
    report_path = config["report_file"]
    log_file = os.path.join(
        config["logs_dir"],
        f"log_{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}.json"
    )

    # Save insights
    save_json(
        {
            "query": user_query,
            "plan": plan,
            "summary": summary,
            "candidates": hypotheses,
            "validated": validated
        },
        insights_path
    )

    # Save creative suggestions
    save_json(creatives, creatives_path)

    # Save log
    save_json(
        {
            "timestamp": datetime.utcnow().isoformat(),
            "query": user_query,
            "validated": validated
        },
        log_file
    )

    # Write markdown report
    with open(report_path, "w") as f:
        f.write(f"# Facebook Ads Performance Analysis\n")
        f.write(f"Query: **{user_query}**\n\n")

        f.write("## Key Insights\n")
        for v in validated:
            if v["valid"]:
                f.write(f"- **{v['hypothesis']}** (Campaign: {v.get('campaign')}, Confidence: {v['confidence']:.2f})\n")

        f.write("\n## Creative Recommendations\n")
        for camp, data in creatives.items():
            f.write(f"### {camp}\n")
            for s in data["suggestions"]:
                f.write(f"- {s}\n")

    print(f"[✓] Insights saved: {insights_path}")
    print(f"[✓] Creative ideas saved: {creatives_path}")
    print(f"[✓] Report saved: {report_path}")
    print(f"[✓] Log saved: {log_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query", type=str, help="User query such as 'Analyze ROAS drop'")
    parser.add_argument("--config", type=str, default="config/config.yaml")
    args = parser.parse_args()

    main(args.query, args.config)
