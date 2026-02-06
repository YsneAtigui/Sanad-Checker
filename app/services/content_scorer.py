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
    
    prompt = f"""You are an Arabic content quality analyzer for e-commerce, specialized in Gulf Arabic (Khaliji) markets.

Analyze this product description and score it (0-10) across these dimensions:
1. Naturalness: Does it sound human and conversational? (10 = very human, 0 = very robotic)
2. Keyword Stuffing: Is it repetitive or over-optimized? (10 = no stuffing, 0 = heavy stuffing)
3. AEO Readiness: Does it answer questions directly and clearly? (10 = perfect for Q&A, 0 = poor)
4. Dialect Usage: Does it use regional Arabic (Khaliji/Gulf) naturally? (10 = authentic dialect, 0 = none)
5. Linguistic Precision: Does it use local terminology (e.g., جوال not هاتف محمول)? (10 = perfect local terms, 0 = literal translations)
6. Translation Quality: Is it free from "Google Translate" awkwardness? (10 = natural Arabic, 0 = robotic translation)

Text to analyze:
{text[:1000]}

Return ONLY a valid JSON object with no additional text:
{{
  "naturalness": <score 0-10>,
  "keyword_stuffing_reverse": <score 0-10>,
  "aeo_readiness": <score 0-10>,
  "dialect_usage": <score 0-10>,
  "linguistic_precision": <score 0-10>,
  "translation_quality": <score 0-10>,
  "reasoning": "<brief explanation in English>",
  "local_terminology_used": <true or false>
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
            "linguistic_precision": float(parsed.get("linguistic_precision", 5)),
            "translation_quality": float(parsed.get("translation_quality", 5)),
            "reasoning": parsed.get("reasoning", ""),
            "local_terminology_used": parsed.get("local_terminology_used", False)
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


def check_structural_scannability(text: str, html: Optional[str] = None) -> Dict:
    """
    Check RTL layout optimization and front-loading
    
    Validates:
    - Direct answer front-loading (first 100 characters)
    - HTML spec tables (better for Arabic)
    - Question-based headers
    
    Args:
        text: Content text
        html: Optional HTML for structure analysis
    
    Returns:
        Structural scannability analysis
    """
    
    issues = []
    
    # Check if first 100 characters contain key info (price, benefit)
    first_100 = text[:100] if len(text) >= 100 else text
    
    # Price patterns in Arabic
    price_patterns = [r'\d+\s*ريال', r'\d+\s*SAR', r'\d+\s*درهم', r'\d+\s*AED']
    has_early_price = any(re.search(pattern, first_100) for pattern in price_patterns)
    
    if not has_early_price and len(text) >= 100:
        issues.append({
            "type": "no_front_loaded_price",
            "severity": "medium",
            "message": "Price not mentioned in first 100 characters"
        })
    
    # Check for HTML tables (better for Arabic specs)
    has_tables = False
    question_headers = []
    
    if html:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            tables = soup.find_all('table')
            has_tables = len(tables) > 0
            
            if not has_tables:
                issues.append({
                    "type": "no_spec_tables",
                    "severity": "low",
                    "message": "No HTML tables found (recommended for Arabic spec display)"
                })
            
            # Check for question-based headers
            for h in soup.find_all(['h2', 'h3']):
                header_text = h.get_text()
                if any(q in header_text for q in ['ما هي', 'ما هو', 'كيف', 'لماذا', 'متى']):
                    question_headers.append(header_text)
            
            if len(question_headers) == 0:
                issues.append({
                    "type": "no_question_headers",
                    "severity": "medium",
                    "message": "No question-based H2/H3 headers (e.g., 'ما هي مميزات المنتج؟')"
                })
        except Exception as e:
            pass
    
    # Calculate score
    score = max(0, 10 - len(issues) * 2.5)
    
    return {
        "has_issues": len(issues) > 0,
        "issues": issues,
        "has_early_price": has_early_price,
        "has_tables": has_tables,
        "question_headers_count": len(question_headers),
        "score": round(score, 1)
    }


def check_technical_authority(jsonld: Optional[Dict], html: Optional[str]) -> Dict:
    """
    Check Arabic metadata completeness and local trust signals
    
    Validates:
    - Arabic JSON-LD strings
    - Arabic alt-text on images
    - Local payment method mentions (trust signals)
    
    Args:
        jsonld: Product JSON-LD data
        html: HTML content
    
    Returns:
        Technical authority analysis
    """
    
    issues = []
    found_local_payments = []
    missing_alt = 0
    
    # Check JSON-LD for Arabic strings
    if jsonld:
        name = jsonld.get("name", "")
        description = jsonld.get("description", "")
        
        # Detect Arabic characters
        arabic_pattern = re.compile(r'[\u0600-\u06FF]')
        
        if name and not arabic_pattern.search(str(name)):
            issues.append({
                "type": "non_arabic_name",
                "severity": "high",
                "message": "Product name in JSON-LD is not in Arabic"
            })
        
        if description and not arabic_pattern.search(str(description)):
            issues.append({
                "type": "non_arabic_description",
                "severity": "high",
                "message": "Product description in JSON-LD is not in Arabic"
            })
    
    # Check for Arabic alt-text
    if html:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            images = soup.find_all('img')
            
            for img in images:
                alt = img.get('alt', '')
                if not alt or not re.search(r'[\u0600-\u06FF]', alt):
                    missing_alt += 1
            
            if missing_alt > 0:
                issues.append({
                    "type": "missing_arabic_alt_text",
                    "severity": "medium",
                    "count": missing_alt,
                    "message": f"{missing_alt} images missing Arabic alt-text"
                })
        except Exception as e:
            pass
    
    # Check for local payment method mentions (trust signals)
    text_combined = str(jsonld or "") + " " + (html or "")
    local_payment_keywords = [
        "مدى", "Mada", "تمارا", "Tamara", "تابي", "Tabby",
        "STC Pay", "stc pay", "Apple Pay", "الدفع عند الاستلام"
    ]
    
    found_local_payments = [kw for kw in local_payment_keywords if kw in text_combined]
    
    if not found_local_payments:
        issues.append({
            "type": "no_local_trust_signals",
            "severity": "low",
            "message": "No local payment methods mentioned (Mada, Tamara, STC Pay)"
        })
    
    # Calculate score
    score = max(0, 10 - len(issues) * 2.5)
    
    return {
        "has_issues": len(issues) > 0,
        "issues": issues,
        "local_trust_signals": found_local_payments,
        "missing_alt_text_count": missing_alt,
        "score": round(score, 1)
    }


async def score_product_content(
    text: str,
    html: Optional[str] = None,
    jsonld: Optional[Dict] = None,
    ollama_host: str = "http://localhost:11434",
    model: str = "qwen3:8b"
) -> Dict:
    """
    Complete content quality scoring with advanced Arabic checks
    
    Args:
        text: Content to score
        html: Optional HTML for structure analysis
        jsonld: Optional JSON-LD Product schema
        ollama_host: Ollama API endpoint
        model: Ollama model to use
    
    Returns:
        Complete scoring results with all quality dimensions
    """
    
    # 1. Quick heuristic checks
    robotic_check = detect_robotic_patterns(text)
    
    # 2. AEO structure check
    aeo_check = check_aeo_readiness(text, html)
    
    # 3. Advanced Arabic quality checks
    structural_check = check_structural_scannability(text, html)
    technical_check = check_technical_authority(jsonld, html)
    
    # 4. LLM-based deep analysis (only if worth analyzing)
    if robotic_check["score"] >= 4 and len(text) > 20:
        llm_score = await score_content_with_ollama(text, ollama_host, model)
    else:
        llm_score = {
            "naturalness": robotic_check["score"],
            "keyword_stuffing_reverse": robotic_check["score"],
            "aeo_readiness": aeo_check["score"],
            "dialect_usage": 0,
            "linguistic_precision": 5,
            "translation_quality": 5,
            "reasoning": "Skipped LLM analysis (failed heuristic checks or too short)",
            "skipped": True
        }
    
    # Combine scores with weighted average
    scores = [
        robotic_check["score"],
        aeo_check["score"],
        structural_check["score"],
        technical_check["score"],
        llm_score.get("naturalness", 0)
    ]
    
    overall = sum(scores) / len(scores)
    
    # Generate recommendation
    recommendation = generate_recommendation(
        robotic_check, aeo_check, structural_check, technical_check, llm_score
    )
    
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
        "structural_scannability": structural_check,
        "technical_authority": technical_check,
        "llm_analysis": llm_score,
        "recommendation": recommendation
    }


def generate_recommendation(robotic: Dict, aeo: Dict, structural: Dict, technical: Dict, llm: Dict) -> str:
    """Generate actionable recommendations based on all checks"""
    
    if robotic["score"] < 5:
        return "CRITICAL: Content appears robotic or keyword-stuffed. Rewrite needed."
    elif technical["score"] < 5:
        return "FIX: Add Arabic metadata to JSON-LD and image alt-text for AI trust."
    elif structural["score"] < 5:
        return "RESTRUCTURE: Front-load key info (price, benefits) and use spec tables."
    elif aeo["score"] < 5:
        return "IMPROVE: Add Q&A structure, headings, and direct answers for AEO."
    elif llm.get("dialect_usage", 0) < 3:
        return "ENHANCE: Consider adding regional dialect (Khaliji) for authenticity."
    elif llm.get("linguistic_precision", 0) < 5:
        return "REFINE: Use local terminology (e.g., جوال not هاتف محمول) for better AI mapping."
    elif llm.get("naturalness", 0) < 7:
        return "IMPROVE: Make content more conversational and human-like."
    else:
        return "EXCELLENT: Content is human-first, AEO-ready, and locally optimized."
