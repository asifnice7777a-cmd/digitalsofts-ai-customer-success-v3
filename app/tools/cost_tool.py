from langchain_core.tools import tool

RATE_CARD = {
    "web development": (5000, 15000),
    "mobile app": (8000, 25000),
    "erp": (20000, 60000),
    "ai solution": (10000, 40000),
    "cloud migration": (7000, 30000),
    "custom software": (10000, 50000),
}


@tool
def estimate_project_cost(project_type: str, complexity: str = "medium") -> str:
    """Estimate the project cost range in USD given a project type and complexity (low/medium/high)."""
    key = project_type.lower().strip()
    base_low, base_high = (10000, 30000)
    for name, (low, high) in RATE_CARD.items():
        if name in key or key in name:
            base_low, base_high = low, high
            break
    multiplier = {"low": 0.7, "medium": 1.0, "high": 1.6}.get(complexity.lower(), 1.0)
    low = int(base_low * multiplier)
    high = int(base_high * multiplier)
    return f"Estimated cost for {project_type} ({complexity} complexity): ${low:,} - ${high:,} USD"
