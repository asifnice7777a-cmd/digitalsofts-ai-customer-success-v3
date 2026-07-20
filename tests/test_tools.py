from app.tools.cost_tool import estimate_project_cost
from app.tools.timeline_tool import estimate_project_timeline
from app.tools.proposal_tool import generate_proposal_summary
from app.tools.meeting_tool import create_meeting_request


def test_estimate_project_cost():
    result = estimate_project_cost.invoke({"project_type": "web development", "complexity": "medium"})
    assert "$" in result
    assert "web development" in result


def test_estimate_project_timeline():
    result = estimate_project_timeline.invoke({"project_type": "erp", "complexity": "high"})
    assert "weeks" in result


def test_generate_proposal_summary():
    result = generate_proposal_summary.invoke({
        "client_name": "John", "company": "Acme", "project_type": "AI solution",
        "budget": "$20,000", "timeline": "10 weeks",
    })
    assert "John" in result
    assert "Acme" in result


def test_create_meeting_request():
    result = create_meeting_request.invoke({"client_name": "John", "preferred_date": "Monday", "purpose": "demo"})
    assert "Meeting request created" in result
    assert "John" in result
