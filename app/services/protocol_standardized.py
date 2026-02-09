"""
Standardized Protocol Service Wrapper

Wraps the existing protocol.py functions to return standardized JSON matching frontend schema.
"""
from typing import Dict
from app.services.protocol import check_aeo_protocols as _check_protocols_original


async def check_aeo_protocols_standardized(base_url: str) -> Dict:
    """
    Check AEO protocols and return standardized format
    
    Returns:
        {
            "checks": [...],
            "score": 0-100
        }
    """
    # Call original function
    original_result = await _check_protocols_original(base_url)
    
    # Transform to standardized format
    checks = []
    
    # 1. llms.txt check
    llms_txt = original_result.get("llms_txt", {})
    checks.append({
        "name": "llms.txt",
        "status": _map_status(llms_txt.get("status")),
        "detail": _get_detail(llms_txt),
        "raw_content": llms_txt.get("content", "") if llms_txt.get("status") == "found" else ""
    })
    
    # 2. agent-card.json check
    agent_card = original_result.get("agent_card", {})
    checks.append({
        "name": "agent-card.json",
        "status": _map_status(agent_card.get("status")),
        "detail": _get_detail(agent_card),
        "raw_content": ""  # JSON content can be added if needed
    })
    
    # 3. robots.txt check
    robots_txt = original_result.get("robots_txt", {})
    checks.append({
        "name": "robots.txt",
        "status": _map_status(robots_txt.get("status")),
        "detail": _get_detail(robots_txt),
        "raw_content": ""  # Content can be added if needed
    })
    
    # Calculate score
    passed = sum(1 for check in checks if check["status"] in ["found", "valid"])
    score = round((passed / len(checks)) * 100)
    
    return {
        "checks": checks,
        "score": score
    }


def _map_status(status: str) -> str:
    """Map internal status to standardized status"""
    status_map = {
        "found": "found",
        "missing": "not_found",
        "error": "not_found",
        "invalid": "invalid"
    }
    return status_map.get(status, "not_found")


def _get_detail(check_result: Dict) -> str:
    """Extract detail message from check result"""
    if check_result.get("issue"):
        return check_result["issue"]
    elif check_result.get("valid_structure"):
        return "File found and valid"
    elif check_result.get("schema_valid"):
        return "Agent card found and valid"  
    elif check_result.get("status") == "found":
        issues = check_result.get("issues", [])
        if issues:
            return "; ".join(issues)
        return "File found"
    else:
        return check_result.get("recommendation", "Check failed")
