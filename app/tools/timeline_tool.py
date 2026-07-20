from langchain_core.tools import tool

TIMELINE_MAP = {
    "web development": (4, 10),
    "mobile app": (8, 16),
    "erp": (12, 26),
    "ai solution": (6, 20),
    "cloud migration": (4, 12),
    "custom software": (8, 24),
}


@tool
def estimate_project_timeline(project_type: str, complexity: str = "medium") -> str:
    """Estimate the project delivery timeline in weeks given a project type and complexity (low/medium/high)."""
    key = project_type.lower().strip()
    low, high = (6, 16)
    for name, (l, h) in TIMELINE_MAP.items():
        if name in key or key in name:
            low, high = l, h
            break
    multiplier = {"low": 0.75, "medium": 1.0, "high": 1.5}.get(complexity.lower(), 1.0)
    low = max(1, int(low * multiplier))
    high = int(high * multiplier)
    return f"Estimated timeline for {project_type} ({complexity} complexity): {low}-{high} weeks"
