---
name: human-first-scorer
description: Analyze Arabic content quality using Ollama LLM to detect robotic vs human-first writing. Score content for keyword stuffing, unnatural patterns, and AEO readiness. Use when auditing product descriptions, checking for AI-generated spam, or evaluating content authenticity.
---

# Human-First Content Scorer

Use local Ollama models to score Arabic e-commerce content for "humanity" vs robotic/SEO-stuffed patterns.

## Scoring Dimensions

Evaluate content across these dimensions:

### Core Human-First Metrics
1. **Naturalness** (0-10): How human/conversational the text feels
2. **Keyword Stuffing** (0-10): Repetition and unnatural keyword usage (lower is worse)
3. **AEO Readiness** (0-10): Structured for Q&A and direct answers
4. **Dialect Usage** (0-10): Presence of regional Arabic variants (authenticity signal)

### Advanced Arabic Quality Metrics

#### 1. Linguistic Precision (Dialect vs. MSA)

Validate authentic Arabic usage for e-commerce:

**Checklist:**
- [ ] **Local Terminology**: Uses correct local term for target market (e.g., Jawwal [جوال] for Saudi Arabia vs. Hatif [هاتف] for formal contexts)
- [ ] **Avoid Literal Translation**: Free from "Google Translate" phrasing that feels robotic or grammatically awkward in Arabic
- [ ] **Root-Word Clarity**: Uses strong Arabic verbs and nouns that allow AI to map product to its "Semantic Root"

**Examples:**
```python
# GOOD: Local terminology
"جوال آيفون 15 برو ماكس"  # Jawwal (Saudi/Gulf)

# BAD: Literal translation
"هاتف محمول آيفون 15 برو ماكس"  # Hatif mahmoul (too formal/translated)

# GOOD: Root-word clarity
"تصميم أنيق بخامات فاخرة"  # Strong verbs and nouns

# BAD: Weak phrasing
"شكل حلو وخامة كويسة"  # Vague, informal
```

#### 2. Structural Scannability (RTL Layout)

Optimize for right-to-left reading and AI parsing:

**Checklist:**
- [ ] **Direct Answer Front-Loading**: Most important Arabic sentence (Price, Benefit, or Use Case) in first 100 characters
- [ ] **Spec Tables**: Product specs in HTML table (AI models parse Arabic tables significantly better than bullet points)
- [ ] **Header Hierarchy**: Uses H2/H3 tags that mirror how people ask questions in Arabic (e.g., "ما هي مميزات هذا المنتج؟")

**Examples:**
```html
<!-- GOOD: Front-loaded answer -->
<p>عباية كريب فاخرة بسعر 299 ريال مع توصيل مجاني لجميع مدن المملكة.</p>

<!-- BAD: Buried answer -->
<p>نقدم لكم مجموعة متنوعة من العبايات... [200 words]... السعر 299 ريال</p>

<!-- GOOD: Spec table -->
<table>
  <tr><th>القماش</th><td>كريب فاخر</td></tr>
  <tr><th>المقاس</th><td>متوفر من S إلى XL</td></tr>
</table>

<!-- GOOD: Question-based headers -->
<h2>ما هي مميزات هذا المنتج؟</h2>
<h3>كيف أختار المقاس المناسب؟</h3>
```

#### 3. Technical Authority (Arabic Metadata)

Verify Arabic metadata completeness for AI trust:

**Checklist:**
- [ ] **Arabic Schema Strings**: `name` and `description` fields in JSON-LD provided in clear Arabic
- [ ] **Arabic Alt-Text**: Images have descriptive Arabic alt-text (e.g., "عباية كريب سوداء بتطريز يدوي")
- [ ] **Local Trust Signals**: Local payment methods mentioned in text (Mada, STC Pay, Tamara) - AI uses these to verify "Local Expertise"

**Examples:**
```json
// GOOD: Arabic JSON-LD
{
  "@type": "Product",
  "name": "عباية كريب سوداء فاخرة",
  "description": "عباية من قماش الكريب الفاخر بتطريز يدوي..."
}

// BAD: English metadata for Arabic page
{
  "@type": "Product",
  "name": "Black Crepe Abaya",
  "description": "Luxury crepe abaya..."
}
```

```html
<!-- GOOD: Arabic alt-text -->
<img src="abaya.jpg" alt="عباية كريب سوداء بتطريز يدوي">

<!-- BAD: No alt-text or English -->
<img src="abaya.jpg" alt="Black abaya">
```

**Local Trust Signals:**
```markdown
✅ GOOD:
"الدفع عند الاستلام متاح | الدفع بالتقسيط عبر تمارا | مدى وApple Pay مقبولة"

❌ BAD:
"Payment on delivery available | Credit cards accepted"
```

## Ollama Integration

Use local Llama-3 or specialized Arabic models:

```python
import httpx

async def score_content_with_ollama(text: str, lang: str = "ar"):
    """
    Score content using local Ollama instance with enhanced Arabic quality checks
    """
    
    prompt = f"""
You are an Arabic content quality analyzer for e-commerce, specialized in Gulf Arabic (Khaliji) markets.

Analyze this product description and score it (0-10) across these dimensions:
1. Naturalness: Does it sound human and conversational?
2. Keyword Stuffing: Is it repetitive or over-optimized? (10 = no stuffing, 0 = heavy stuffing)
3. AEO Readiness: Does it answer questions directly?
4. Dialect Usage: Does it use regional Arabic (Khaliji) naturally?
5. Linguistic Precision: Does it use local terminology (e.g., جوال not هاتف محمول)? Is it free from literal translation?
6. Translation Quality: Is it free from "Google Translate" awkwardness?

Text:
{text}

Return ONLY a JSON object:
{{
  "naturalness": <score>,
  "keyword_stuffing_reverse": <score>,
  "aeo_readiness": <score>,
  "dialect_usage": <score>,
  "linguistic_precision": <score>,
  "translation_quality": <score>,
  "reasoning": "<brief explanation>",
  "local_terminology_used": <true/false>
}}
"""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",  # or "aya" for better Arabic support
                "prompt": prompt,
                "stream": False
            },
            timeout=30.0
        )
        
        result = response.json()
        return parse_ollama_response(result["response"])
```

## Robotic Pattern Detection

Pre-LLM heuristics to catch obvious issues:

```python
def detect_robotic_patterns(text: str) -> dict:
    """
    Quick heuristic checks before LLM scoring
    """
    from arabic_normalizer import normalize_arabic
    import re
    
    normalized = normalize_arabic(text)
    words = normalized.split()
    
    issues = []
    
    # 1. Keyword repetition
    word_freq = {}
    for word in words:
        if len(word) > 3:  # Skip short words
            word_freq[word] = word_freq.get(word, 0) + 1
    
    repeated_words = {w: c for w, c in word_freq.items() if c >= 5}
    if repeated_words:
        issues.append({
            "type": "keyword_repetition",
            "words": repeated_words,
            "severity": "medium"
        })
    
    # 2. All caps (screaming)
    if text.isupper():
        issues.append({
            "type": "all_caps",
            "severity": "high"
        })
    
    # 3. No punctuation
    if not any(p in text for p in [".", "!", "?", "،", "؟"]):
        issues.append({
            "type": "no_punctuation",
            "severity": "low"
        })
    
    # 4. English keywords in Arabic text
    english_pattern = re.compile(r'[a-zA-Z]{4,}')
    english_words = english_pattern.findall(text)
    if len(english_words) > 3:
        issues.append({
            "type": "mixed_language",
            "english_words": english_words,
            "severity": "medium"
        })
    
    # 5. SEO patterns (e.g., "احسن [keyword] في [location]" repeated)
    seo_patterns = [
        r'احسن .+ في .+',
        r'افضل .+ في .+',
        r'best .+ in .+'
    ]
    
    for pattern in seo_patterns:
        matches = re.findall(pattern, text)
        if len(matches) >= 3:
            issues.append({
                "type": "seo_template_repetition",
                "pattern": pattern,
                "severity": "high"
            })
    
    return {
        "has_issues": len(issues) > 0,
        "issues": issues,
        "score": max(0, 10 - len(issues) * 2)  # Penalty-based score
    }
```

## AEO Readiness Indicators

Check for question-answering structure:

```python
def check_technical_authority(jsonld: dict, html: str) -> dict:
    """
    Check Arabic metadata completeness and local trust signals
    """
    from bs4 import BeautifulSoup
    import re
    
    issues = []
    
    # Check JSON-LD for Arabic strings
    if jsonld:
        name = jsonld.get("name", "")
        description = jsonld.get("description", "")
        
        # Detect Arabic characters
        arabic_pattern = re.compile(r'[\u0600-\u06FF]')
        
        if not arabic_pattern.search(name):
            issues.append({
                "type": "non_arabic_name",
                "severity": "high",
                "message": "Product name in JSON-LD is not in Arabic"
            })
        
        if not arabic_pattern.search(description):
            issues.append({
                "type": "non_arabic_description",
                "severity": "high",
                "message": "Product description in JSON-LD is not in Arabic"
            })
    
    # Check for Arabic alt-text
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        images = soup.find_all('img')
        
        missing_alt = 0
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
    
    # Check for local payment method mentions (trust signals)
    text_combined = str(jsonld) + " " + (html or "")
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
    
    return {
        "has_issues": len(issues) > 0,
        "issues": issues,
        "local_trust_signals": found_local_payments,
        "score": max(0, 10 - len(issues) * 2.5)
    }


def check_structural_scannability(text: str, html: str = None) -> dict:
    """
    Check RTL layout optimization and front-loading
    """
    from bs4 import BeautifulSoup
    
    issues = []
    
    # Check if first 100 characters contain key info (price, benefit)
    first_100 = text[:100] if len(text) >= 100 else text
    
    # Price patterns in Arabic
    price_patterns = [r'\d+\s*ريال', r'\d+\s*SAR', r'\d+\s*درهم']
    has_early_price = any(re.search(pattern, first_100) for pattern in price_patterns)
    
    if not has_early_price:
        issues.append({
            "type": "no_front_loaded_price",
            "severity": "medium",
            "message": "Price not mentioned in first 100 characters"
        })
    
    # Check for HTML tables (better for Arabic specs)
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table')
        
        if len(tables) == 0:
            issues.append({
                "type": "no_spec_tables",
                "severity": "low",
                "message": "No HTML tables found (recommended for Arabic spec display)"
            })
        
        # Check for question-based headers
        question_headers = []
        for h in soup.find_all(['h2', 'h3']):
            if any(q in h.get_text() for q in ['ما هي', 'ما هو', 'كيف', 'لماذا', 'متى']):
                question_headers.append(h.get_text())
        
        if len(question_headers) == 0:
            issues.append({
                "type": "no_question_headers",
                "severity": "medium",
                "message": "No question-based H2/H3 headers (e.g., 'ما هي مميزات المنتج؟')"
            })
    
    return {
        "has_issues": len(issues) > 0,
        "issues": issues,
        "has_early_price": has_early_price,
        "score": max(0, 10 - len(issues) * 2.5)
    }


def check_aeo_readiness(text: str, html_structure: str = None):
    """
    Check if content is structured for Answer Engines
    """
    from arabic_normalizer import normalize_arabic
    
    normalized = normalize_arabic(text)
    
    aeo_signals = []
    
    # 1. Direct Q&A headers
    question_patterns = [
        r'كيف استخدم',  # How to use
        r'ما هو',       # What is
        r'لماذا',       # Why
        r'متى',         # When
        r'اين',         # Where
    ]
    
    for pattern in question_patterns:
        if re.search(pattern, normalized):
            aeo_signals.append("direct_question")
    
    # 2. H2/H3 structure (if HTML provided)
    if html_structure:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_structure, 'html.parser')
        
        h2_count = len(soup.find_all('h2'))
        h3_count = len(soup.find_all('h3'))
        
        if h2_count >= 2:
            aeo_signals.append("structured_headings")
    
    # 3. Experience signals (local dialect, specific scenarios)
    experience_patterns = [
        r'جربته',      # I tried it
        r'استخدمته',   # I used it
        r'ينفع ل',     # Good for (Khaliji)
        r'مناسب ل',    # Suitable for
    ]
    
    for pattern in experience_patterns:
        if re.search(pattern, normalized):
            aeo_signals.append("experience_signal")
    
    return {
        "aeo_ready": len(aeo_signals) >= 2,
        "signals": aeo_signals,
        "score": min(10, len(aeo_signals) * 3)
    }
```

## Combined Scoring

Aggregate all scoring methods:

```python
async def score_product_description(text: str, html: str = None, jsonld: dict = None):
    """
    Complete content quality scoring with advanced Arabic checks
    """
    
    # 1. Quick heuristic checks
    robotic_check = detect_robotic_patterns(text)
    
    # 2. AEO structure check
    aeo_check = check_aeo_readiness(text, html)
    
    # 3. Advanced Arabic quality checks
    structural_check = check_structural_scannability(text, html)
    technical_check = check_technical_authority(jsonld or {}, html or "")
    
    # 4. LLM-based deep analysis (only if heuristics pass minimum threshold)
    if robotic_check["score"] >= 5:
        llm_score = await score_content_with_ollama(text)
    else:
        llm_score = {"naturalness": robotic_check["score"], "reasoning": "Failed heuristic checks"}
    
    # Combine scores with weighted average
    scores = [
        robotic_check["score"],
        aeo_check["score"],
        structural_check["score"],
        technical_check["score"],
        llm_score.get("naturalness", 0)
    ]
    
    overall_score = sum(scores) / len(scores)
    
    final_score = {
        "overall": round(overall_score, 1),
        "robotic_patterns": robotic_check,
        "aeo_readiness": aeo_check,
        "structural_scannability": structural_check,
        "technical_authority": technical_check,
        "llm_analysis": llm_score,
        "recommendation": generate_recommendation(
            robotic_check, aeo_check, structural_check, technical_check, llm_score
        )
    }
    
    return final_score

def generate_recommendation(robotic, aeo, structural, technical, llm):
    """Generate actionable recommendations based on all checks"""
    if robotic["score"] < 5:
        return "REWRITE: Content appears robotic or keyword-stuffed"
    elif technical["score"] < 5:
        return "FIX: Add Arabic metadata to JSON-LD and image alt-text"
    elif structural["score"] < 5:
        return "RESTRUCTURE: Front-load key info and use spec tables"
    elif aeo["score"] < 5:
        return "IMPROVE: Add Q&A structure and direct answers"
    elif llm.get("dialect_usage", 0) < 3:
        return "ENHANCE: Add regional dialect for authenticity"
    elif llm.get("linguistic_precision", 0) < 5:
        return "REFINE: Use local terminology (e.g., جوال not هاتف محمول)"
    else:
        return "EXCELLENT: Content is human-first, AEO-ready, and locally optimized"
```

## Model Selection

**Recommended Ollama models for Arabic:**

1. **aya** (8B): Best multilingual Arabic support
2. **llama3** (8B): Good general reasoning, decent Arabic
3. **gemma2** (9B): Fast, lightweight

**Installation:**
```bash
ollama pull aya
ollama serve
```

## Output Format

```python
{
    "overall_score": 7.5,
    "robotic_patterns": {
        "score": 8,
        "issues": [...]
    },
    "aeo_readiness": {
        "score": 7,
        "signals": ["direct_question", "experience_signal"]
    },
    "structural_scannability": {
        "score": 8,
        "has_early_price": true,
        "issues": [{"type": "no_spec_tables", "severity": "low"}]
    },
    "technical_authority": {
        "score": 6,
        "local_trust_signals": ["مدى", "تمارا"],
        "issues": [{"type": "missing_arabic_alt_text", "count": 3}]
    },
    "llm_analysis": {
        "naturalness": 8,
        "keyword_stuffing_reverse": 7,
        "linguistic_precision": 6,
        "translation_quality": 7,
        "local_terminology_used": true,
        "reasoning": "..."
    },
    "recommendation": "REFINE: Use local terminology (e.g., جوال not هاتف محمول)"
}
```

## Critical Rules

- Always run heuristic checks first to save LLM calls
- Use local Ollama (privacy + speed) instead of cloud APIs
- Normalize Arabic text before pattern matching
- Scores below 5 require content rewrite
- Dialect usage is a positive signal (authenticity)
