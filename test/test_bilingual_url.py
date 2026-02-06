"""
Quick test for bilingual URL construction

Run with: python test_bilingual_url.py
"""

from urllib.parse import urlparse, urlunparse


def test_url_construction(url: str):
    """Test bilingual URL construction logic"""
    
    parsed = urlparse(url)
    path = parsed.path.rstrip('/')
    
    # Detect if URL already has language code
    has_ar = path.startswith('/ar/') or path == '/ar'
    has_en = path.startswith('/en/') or path == '/en'
    
    if has_ar:
        base_path = path[3:] if path.startswith('/ar/') else '/'
        ar_path = path
        en_path = '/en' + base_path
    elif has_en:
        base_path = path[3:] if path.startswith('/en/') else '/'
        ar_path = '/ar' + base_path
        en_path = path
    else:
        ar_path = '/ar' + path
        en_path = '/en' + path
    
    ar_url = urlunparse((parsed.scheme, parsed.netloc, ar_path, '', '', ''))
    en_url = urlunparse((parsed.scheme, parsed.netloc, en_path, '', '', ''))
    
    return ar_url, en_url


# Test cases
test_urls = [
    "https://hijabti.ae/products/shimmer-georgette-hijab-dusty-rose",
    "https://hijabti.ae/ar/products/shimmer-georgette-hijab-dusty-rose",
    "https://hijabti.ae/en/products/shimmer-georgette-hijab-dusty-rose",
]

print("Testing Bilingual URL Construction:")
print("=" * 80)

for url in test_urls:
    ar, en = test_url_construction(url)
    print(f"\nOriginal: {url}")
    print(f"Arabic:   {ar}")
    print(f"English:  {en}")
    print("-" * 80)
