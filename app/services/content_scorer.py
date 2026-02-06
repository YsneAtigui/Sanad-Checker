"""Human-First Content Scorer Service

Analyze Arabic content quality using Ollama LLM to detect robotic vs human-first writing.
"""

import httpx
import asyncio
import re
import json
from typing import Dict, Optional
from bs4 import BeautifulSoup


async def score_content_with_ollama(text: str, ollama_host: str = "http://localhost:11434", model: str = "qwen3:8b") -> Dict:
    """
    Score content using local Ollama instance
    
    Args:
        text: Content to score
        ollama_host: Ollama API endpoint
        model: Model to use (qwen3:8b for Arabic)
    
    Returns:
        Scoring results from LLM
    """
    
    prompt = f"""You are an Arabic content quality analyzer for e-commerce.

Analyze this product description and score it (0-10) across these dimensions:
1. Naturalness: Does it sound human and conversational? (10 = very human, 0 = very robotic)
2. Keyword Stuffing: Is it repetitive or over-optimized? (10 = no stuffing, 0 = heavy stuffing)
3. AEO Readiness: Does it answer questions directly and clearly? (10 = perfect for Q&A, 0 = poor)
4. Dialect Usage: Does it use regional Arabic (Khaliji/Gulf) naturally? (10 = authentic dialect, 0 = none)

Text to analyze:
{text[:1000]}

Return ONLY a valid JSON object with no additional text:
{{
  "naturalness": <score 0-10>,
  "keyword_stuffing_reverse": <score 0-10>,
  "aeo_readiness": <score 0-10>,
  "dialect_usage": <score 0-10>,
  "reasoning": "<brief explanation in English>"
}}"""
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{ollama_host}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # More deterministic
                        "top_p": 0.9
                    }
                }
            )
            
            if response.status_code != 200:
                return {
                    "error": f"Ollama API error: {response.status_code}",
                    "naturalness": 5,
                    "keyword_stuffing_reverse": 5,
                    "aeo_readiness": 5,
                    "dialect_usage": 5,
                    "reasoning": "Failed to get LLM response"
                }
            
            result = response.json()
            llm_response = result.get("response", "")
            
            return parse_ollama_response(llm_response)
            
    except Exception as e:
        return {
            "error": str(e),
            "naturalness": 5,
            "keyword_stuffing_reverse": 5,
            "aeo_readiness": 5,
            "dialect_usage": 5,
            "reasoning": f"Exception: {str(e)}"
        }


def parse_ollama_response(response: str) -> Dict:
    """Parse JSON response from Ollama"""
    
    try:
        # Try to extract JSON from response
        # Sometimes Ollama wraps the JSON in markdown code blocks
        if "```json" in response:
            json_start = response.find("```json") + 7
            json_end = response.find("```", json_start)
            json_str = response[json_start:json_end].strip()
        elif "```" in response:
            json_start = response.find("```") + 3
            json_end = response.find("```", json_start)
            json_str = response[json_start:json_end].strip()
        else:
            # Try to find JSON object
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            json_str = response[json_start:json_end]
        
        parsed = json.loads(json_str)
        
        # Ensure all required fields exist
        return {
            "naturalness": float(parsed.get("naturalness", 5)),
            "keyword_stuffing_reverse": float(parsed.get("keyword_stuffing_reverse", 5)),
            "aeo_readiness": float(parsed.get("aeo_readiness", 5)),
            "dialect_usage": float(parsed.get("dialect_usage", 5)),
            "reasoning": parsed.get("reasoning", "")
        }
        
    except Exception as e:
        return {
            "error": f"Failed to parse response: {str(e)}",
            "naturalness": 5,
            "keyword_stuffing_reverse": 5,
            "aeo_readiness": 5,
            "dialect_usage": 5,
            "reasoning": "Failed to parse LLM response",
            "raw_response": response[:500]
        }


def detect_robotic_patterns(text: str) -> Dict:
    """
    Quick heuristic checks for robotic content
    
    Args:
        text: Content to check
    
    Returns:
        Pattern detection results
    """
    
    words = text.split()
    issues = []
    
    # 1. Keyword repetition
    word_freq = {}
    for word in words:
        if len(word) > 3:  # Skip short words
            word_lower = word.lower()
            word_freq[word_lower] = word_freq.get(word_lower, 0) + 1
    
    repeated_words = {w: c for w, c in word_freq.items() if c >= 5}
    if repeated_words:
        issues.append({
            "type": "keyword_repetition",
            "words": list(repeated_words.keys())[:3],  # Top 3
            "severity": "medium"
        })
    
    # 2. All caps (screaming)
    if len(text) > 10 and text.isupper():
        issues.append({
            "type": "all_caps",
            "severity": "high"
        })
    
    # 3. No punctuation
    if len(text) > 50 and not any(p in text for p in [".", "!", "?", "،", "؟", "؛"]):
        issues.append({
            "type": "no_punctuation",
            "severity": "low"
        })
    
    # 4. English keywords in Arabic text (detect Arabic chars)
    has_arabic = bool(re.search(r'[\u0600-\u06FF]', text))
    if has_arabic:
        english_pattern = re.compile(r'\b[a-zA-Z]{4,}\b')
        english_words = english_pattern.findall(text)
        if len(english_words) > 5:
            issues.append({
                "type": "mixed_language",
                "count": len(english_words),
                "severity": "medium"
            })
    
    # 5. SEO patterns (repetitive templates)
    seo_patterns = [
        (r'احسن .+ في .+', 'best_in_pattern_ar'),
        (r'افضل .+ في .+', 'best_in_pattern_ar'),
        (r'best .+ in .+', 'best_in_pattern_en')
    ]
    
    for pattern, name in seo_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if len(matches) >= 3:
            issues.append({
                "type": "seo_template_repetition",
                "pattern": name,
                "count": len(matches),
                "severity": "high"
            })
    
    # Calculate score (10 = perfect, penalty for each issue)
    score = max(0, 10 - len(issues) * 2)
    
    return {
        "has_issues": len(issues) > 0,
        "issues": issues,
        "score": score
    }


def check_aeo_readiness(text: str, html: Optional[str] = None) -> Dict:
    """
    Check if content is structured for Answer Engines
    
    Args:
        text: Content text
        html: Optional HTML for structure analysis
    
    Returns:
        AEO readiness analysis
    """
    
    aeo_signals = []
    
    # 1. Direct Q&A patterns
    question_patterns = [
        (r'كيف استخدم', 'how_to_use_ar'),
        (r'كيف تستخدم', 'how_to_use_ar'),
        (r'ما هو', 'what_is_ar'),
        (r'ما هي', 'what_is_ar'),
        (r'لماذا', 'why_ar'),
        (r'متى', 'when_ar'),
        (r'اين', 'where_ar'),
        (r'how to', 'how_to_en'),
        (r'what is', 'what_is_en'),
        (r'why ', 'why_en')
    ]
    
    for pattern, name in question_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            if name not in aeo_signals:
                aeo_signals.append("direct_question")
            break
    
    # 2. H2/H3 structure (if HTML provided)
    if html:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            h2_count = len(soup.find_all('h2'))
            h3_count = len(soup.find_all('h3'))
            
            if h2_count >= 2:
                aeo_signals.append("structured_headings")
        except:
            pass
    
    # 3. Experience/authority signals
    experience_patterns = [
        r'جربته',      # I tried it
        r'جربتها',     # I tried it (feminine)
        r'استخدمته',   # I used it
        r'ينفع ل',     # Good for (Khaliji)
        r'مناسب ل',    # Suitable for
        r'تجربتي',     # My experience
        r'tried it',
        r'my experience'
    ]
    
    for pattern in experience_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            aeo_signals.append("experience_signal")
            break
    
    # 4. List/bullet structure
    if html and ('<ul>' in html or '<ol>' in html):
        aeo_signals.append("list_structure")
    elif re.search(r'\n\s*[-•]\s+', text):
        aeo_signals.append("list_structure")
    
    # Calculate score
    score = min(10, len(aeo_signals) * 3)
    
    return {
        "aeo_ready": len(aeo_signals) >= 2,
        "signals": aeo_signals,
        "score": score
    }


async def score_product_content(
    text: str,
    html: Optional[str] = None,
    ollama_host: str = "http://localhost:11434",
    model: str = "qwen3:8b"
) -> Dict:
    """
    Complete content quality scoring
    
    Args:
        text: Content to score
        html: Optional HTML for structure analysis
        ollama_host: Ollama API endpoint
        model: Ollama model to use
    
    Returns:
        Complete scoring results
    """
    
    # 1. Quick heuristic checks
    robotic_check = detect_robotic_patterns(text)
    
    # 2. AEO structure check
    aeo_check = check_aeo_readiness(text, html)
    
    # 3. LLM-based deep analysis (only if worth analyzing)
    if robotic_check["score"] >= 4 and len(text) > 20:
        llm_score = await score_content_with_ollama(text, ollama_host, model)
    else:
        llm_score = {
            "naturalness": robotic_check["score"],
            "keyword_stuffing_reverse": robotic_check["score"],
            "aeo_readiness": aeo_check["score"],
            "dialect_usage": 0,
            "reasoning": "Skipped LLM analysis (failed heuristic checks or too short)",
            "skipped": True
        }
    
    # Combine scores
    overall = (
        robotic_check["score"] * 0.3 +
        aeo_check["score"] * 0.3 +
        llm_score.get("naturalness", 0) * 0.4
    )
    
    # Generate recommendation
    recommendation = generate_recommendation(robotic_check, aeo_check, llm_score)
    
    # Determine severity
    if overall < 5:
        severity = "critical"
    elif overall < 7:
        severity = "medium"
    else:
        severity = "low"
    
    return {
        "overall_score": round(overall, 1),
        "severity": severity,
        "robotic_patterns": robotic_check,
        "aeo_readiness": aeo_check,
        "llm_analysis": llm_score,
        "recommendation": recommendation
    }


def generate_recommendation(robotic: Dict, aeo: Dict, llm: Dict) -> str:
    """Generate actionable recommendations"""
    
    if robotic["score"] < 5:
        return "CRITICAL: Content appears robotic or keyword-stuffed. Rewrite needed."
    elif aeo["score"] < 5:
        return "IMPROVE: Add Q&A structure, headings, and direct answers for AEO."
    elif llm.get("dialect_usage", 0) < 3:
        return "ENHANCE: Consider adding regional dialect (Khaliji) for authenticity."
    elif llm.get("naturalness", 0) < 7:
        return "IMPROVE: Make content more conversational and human-like."
    else:
        return "GOOD: Content is human-first and AEO-ready."
