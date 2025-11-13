import requests
from bs4 import BeautifulSoup
import re

# Check main news page
r = requests.get('https://company.meralco.com.ph/news-and-advisories')
soup = BeautifulSoup(r.text, 'html.parser')

print("="*50)
print("FINDING ALL RATE ADVISORY LINKS")
print("="*50)

months = ['january', 'february', 'march', 'april', 'may', 'june', 
          'july', 'august', 'september', 'october', 'november', 'december']

# Find all h4 tags (the titles use h4)
all_h4 = soup.find_all('h4')
print(f"\nTotal H4 tags: {len(all_h4)}")

rate_links = []
for h4 in all_h4:
    text = h4.get_text(strip=True)
    print(f"H4: {text}")
    
    # Check if it's a rate advisory
    if 'rate' in text.lower():
        # Find the parent div and then the link
        parent = h4.find_parent('div')
        if parent:
            link = parent.find('a', href=True)
            if link and '/news-and-advisories/' in link['href']:
                href = link['href']
                if not href.startswith('http'):
                    href = 'https://company.meralco.com.ph' + href
                
                # Extract month and year from text or URL
                month = None
                year = None
                
                for m in months:
                    if m in text.lower() or m in href.lower():
                        month = m.capitalize()
                        break
                
                year_match = re.search(r'20\d{2}', text + href)
                if year_match:
                    year = int(year_match.group(0))
                
                rate_links.append({
                    'url': href,
                    'title': text,
                    'month': month,
                    'year': year
                })
                print(f"  -> Found rate link: {href}")
                print(f"     Month: {month}, Year: {year}")

print(f"\n{'='*50}")
print(f"Total rate links found: {len(rate_links)}")
print(f"{'='*50}\n")

for i, link in enumerate(rate_links, 1):
    print(f"{i}. {link['title']}")
    print(f"   URL: {link['url']}")
    print(f"   Month: {link['month']}, Year: {link['year']}")
    print()
