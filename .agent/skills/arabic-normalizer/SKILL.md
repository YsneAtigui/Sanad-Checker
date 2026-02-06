---
name: arabic-normalizer
description: Normalize and process Arabic text for AEO auditing. Handle character variants (ي vs ى, أ vs ا), dialect detection (khaliji vs MSA), and text comparison. Use when processing Arabic content, comparing bilingual metadata, or detecting hallucinations in Arabic e-commerce data.
---

# Arabic Normalizer

Specialized Arabic text processing for AEO auditing in Middle Eastern e-commerce.

## Core Normalization Rules

Always apply these before any text comparison:

```python
def normalize_arabic(text: str) -> str:
    """Normalize Arabic text for comparison"""
    import re
    
    # Normalize Alef variants: أ إ آ -> ا
    text = re.sub(r'[أإآ]', 'ا', text)
    
    # Normalize Yaa variants: ى -> ي
    text = text.replace('ى', 'ي')
    
    # Normalize Taa Marbuta: ة -> ه (optional, use for search)
    # text = text.replace('ة', 'ه')
    
    # Remove diacritics (Tashkeel)
    arabic_diacritics = re.compile(r'[\u0617-\u061A\u064B-\u0652]')
    text = arabic_diacritics.sub('', text)
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    return text
```

## Dialect Detection

Identify regional Arabic variants for "Human-First" scoring:

**Khaliji (Gulf) markers:**
- Common words: `يا`, `عندنا`, `يعني`, `بس`
- Double plurals: `عيالات`, `ولدان`


**MSA (Modern Standard Arabic) markers:**
- Formal grammar
- Classical plurals
- Academic/news vocabulary

```python
def detect_dialect(text: str) -> dict:
    """Detect Arabic dialect markers"""
    markers = {
        "khaliji": ["يا", "عندنا", "بس"],
        "msa": True  # default if no dialect markers
    }
    
    # Count markers per dialect
    # Return dominant dialect + confidence score
```

## Bilingual Validation

Compare Arabic and English versions for consistency:

```python
def validate_bilingual_pair(ar_text: str, en_text: str, field_type: str):
    """
    Check if Arabic and English texts represent the same content
    field_type: 'price', 'product_name', 'description', etc.
    """
    
    # For prices: extract numbers and compare
    if field_type == "price":
        ar_price = extract_arabic_numbers(ar_text)
        en_price = extract_english_numbers(en_text)
        return ar_price == en_price
    
    # For text: translate or use embedding similarity
    # Flag if Arabic is just English transliterated
    if contains_latin_chars(ar_text):
        return {"valid": False, "issue": "latin_chars_in_arabic"}
```

## Hallucination Detection

Compare visible Arabic text with structured data (JSON-LD):

```python
def detect_price_hallucination(visible_text: str, jsonld_price: str):
    """
    Extract price from Arabic text and compare to JSON-LD
    """
    normalized_visible = normalize_arabic(visible_text)
    
    # Extract Arabic/English numerals
    visible_price = extract_price_from_text(normalized_visible)
    structured_price = float(jsonld_price)
    
    if abs(visible_price - structured_price) > 0.01:
        return {
            "hallucination_detected": True,
            "visible": visible_price,
            "structured": structured_price,
            "severity": "high"
        }
```

## Number Processing

Handle both Arabic-Indic (٠-٩) and Western (0-9) numerals:

```python
def extract_arabic_numbers(text: str) -> float:
    """Extract numbers from mixed Arabic/English text"""
    import re
    
    # Arabic-Indic to Western
    arabic_to_western = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
    text = text.translate(arabic_to_western)
    
    # Extract number patterns
    pattern = r'\d+\.?\d*'
    matches = re.findall(pattern, text)
    
    return float(matches[0]) if matches else None
```

## Text Quality Indicators

Flags for "Human-First" vs robotic content:

**Human indicators (good):**
- Dialect usage
- Natural questions: `كيف استخدم؟` (How do I use?)
- Personal experiences: `جربته وكان ممتاز`
- Conversational tone

**Robotic indicators (bad):**
- Keyword repetition: same word 5+ times
- Unnatural structure: no punctuation, all caps
- English keywords in Arabic: `best quality`, `premium`
- SEO patterns: `احسن [keyword] في [location]` repeated

## Critical Rules

- ALWAYS normalize before comparing Arabic strings
- For Saudi/UAE sites, expect Khaliji dialect in reviews/descriptions
- Flag if Arabic metadata is identical to English (untranslated)
- Prices should match exactly between visible text and JSON-LD
