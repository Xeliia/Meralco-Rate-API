import requests
from bs4 import BeautifulSoup

# Try different URLs with categories
urls_to_try = [
    'https://company.meralco.com.ph/news-and-advisories',
    'https://company.meralco.com.ph/news-and-advisories?field_category_target_id=All',
    'https://company.meralco.com.ph/news-and-advisories?field_category_target_id=140',  # Electricity Rates
]

for url in urls_to_try:
    print(f"\n{'='*60}")
    print(f"Testing: {url}")
    print('='*60)
    
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Find all h4 rate titles
    h4_tags = soup.find_all('h4')
    rate_h4 = [h4 for h4 in h4_tags if 'rate' in h4.get_text().lower()]
    
    print(f"Found {len(rate_h4)} rate-related H4 tags:")
    for h4 in rate_h4:
        print(f"  - {h4.get_text(strip=True)}")
