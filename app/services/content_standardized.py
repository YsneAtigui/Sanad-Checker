"""
Standardized Content Scorer Wrapper

Wraps content_scorer.py to return standardized JSON format.
"""
from typing import Dict, List


async def score_content_standardized(text: str, ollama_host: str = "http://localhost:11434") -> Dict:
    """
    Score content quality and return standardized format
    
    Args:
        text: Content text to score
        ollama_host: Ollama API endpoint
        
    Returns:
        {
            "aeo_readiness_score": 0-100,
            "robotic_pattern_score": "Low" | "Medium" | "High",
            "issues": [...],
            "score": 0-100
        }
    """
    from app.services.content_scorer import score_product_content
    
    # Call original scorer
    try:
        original_result = await score_product_content(text, ollama_host)
    except Exception:
        # Fallback if Ollama is not available
        original_result = {
            "overall_score": 5,
            "robotic_patterns": {"has_issues": False}
        }
    
    # Extract scores
    overall_score = original_result.get("overall_score", 0)
    
    # Convert 0-10 scale to 0-100
    aeo_readiness_score = int(overall_score * 10)
    
    # Determine robotic pattern level
    robotic_patterns = original_result.get("robotic_patterns", {})
    if robotic_patterns.get("has_issues"):
        pattern_count = len(robotic_patterns.get("issues", []))
        if pattern_count >= 5:
            robotic_pattern_score = "High"
        elif pattern_count >= 2:
            robotic_pattern_score = "Medium"
        else:
            robotic_pattern_score = "Low"
    else:
        robotic_pattern_score = "Low"
    
    # Format issues
    issues = []
    
    # Add robotic pattern issues
    if robotic_patterns.get("has_issues"):
        for issue in robotic_patterns.get("issues", []):
            issues.append({
                "type": "robotic_pattern",
                "severity": "medium",
                "description": issue,
                "location": "Product description"
            })
    
    # Add low score issue if applicable
    if aeo_readiness_score < 50:
        issues.append({
            "type": "low_aeo_readiness",
            "severity": "high",
            "description": "Content lacks human-first, conversational tone suitable for AI agents",
            "location": "Overall content"
        })
    
    # Add keyword stuffing detection
    if "keyword" in text.lower() and text.lower().count("keyword") > 5:
        issues.append({
            "type": "keyword_stuffing",
            "severity": "high",
            "description": "Excessive keyword repetition detected",
            "location": "Product description"
        })
    
    return {
        "aeo_readiness_score": aeo_readiness_score,
        "robotic_pattern_score": robotic_pattern_score,
        "issues": issues,
        "score": aeo_readiness_score
    }
