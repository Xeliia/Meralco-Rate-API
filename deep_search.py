import requests
from bs4 import BeautifulSoup
import re

r = requests.get('https://company.meralco.com.ph/news-and-advisories')
soup = BeautifulSoup(r.text, 'html.parser')

print("="*60)
print("SEARCHING FOR ALL MONTH MENTIONS IN DIVS")
print("="*60)

months = ['january', 'february', 'march', 'april', 'may', 'june', 
          'july', 'august', 'september', 'october', 'november', 'december']

# Find all divs
all_divs = soup.find_all('div')
print(f"\nTotal divs: {len(all_divs)}")

month_divs = []
for div in all_divs:
    text = div.get_text(strip=True)
    # Check for month + rate + 202x
    if 'rate' in text.lower() and re.search(r'20\d{2}', text):
        for month in months:
            if month in text.lower():
                month_divs.append((month, text[:150], div))
                break

print(f"\nFound {len(month_divs)} divs with month + rate + year:")
for month, text, div in month_divs:
    print(f"\n{month.upper()}:")
    print(f"Text: {text}")
    
    # Find link in this div
    link = div.find('a', href=True)
    if link:
        print(f"Link: {link['href']}")
    
    print("-" * 50)

# Also check if content is hidden or lazy-loaded
print("\n" + "="*60)
print("CHECKING FOR DATA ATTRIBUTES")
print("="*60)

elements_with_data = soup.find_all(attrs={"data-url": True})
print(f"Elements with data-url: {len(elements_with_data)}")
for elem in elements_with_data[:5]:
    print(f"  {elem.name}: {elem.get('data-url')}")

elements_with_lazy = soup.find_all(attrs={"data-src": True})
print(f"\nElements with data-src (lazy load): {len(elements_with_lazy)}")
for elem in elements_with_lazy[:5]:
    print(f"  {elem.name}: {elem.get('data-src')}")
