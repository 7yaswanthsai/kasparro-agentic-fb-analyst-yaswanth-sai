"""
Orchestrator module.

This file exists to allow future extension of the pipeline
(e.g., turning the step-by-step logic into a class).

Currently, run.py handles the end-to-end execution.
This orchestrator simply exposes a reusable function
that mirrors run.py’s workflow.
"""

from src.utils import load_config, save_json, set_seeds
from src.agents.data_agent import DataAgent
from src.agents.planner import PlannerAgent
from src.agents.insight_agent import InsightAgent
from src.agents.evaluator import EvaluatorAgent
from src.agents.creative_generator import CreativeGenerator


def run_analysis(user_query, config_path="config/config.yaml"):
    config = load_config(config_path)
    set_seeds(config.get("random_seed", 42))

    # Planner
    planner = PlannerAgent()
    plan = planner.plan(user_query)

    # Data
    data_agent = DataAgent(config["data_csv"])
    df = data_agent.load()
    summary = data_agent.summary()

    # Insights
    insight_agent = InsightAgent(df)
    hypotheses = insight_agent.generate_candidates()

    # Evaluation
    evaluator = EvaluatorAgent(df, config)
    validated = evaluator.validate(hypotheses)

    # Creative suggestions
    low_ctr_campaigns = [
        h["campaign"]
        for h in validated
        if h["valid"] and h["campaign"] is not None and "ctr" in h["hypothesis"].lower()
    ]

    creative_gen = CreativeGenerator(df)
    creatives = creative_gen.generate_for_campaigns(low_ctr_campaigns)

    return {
        "plan": plan,
        "summary": summary,
        "candidates": hypotheses,
        "validated": validated,
        "creatives": creatives
    }
