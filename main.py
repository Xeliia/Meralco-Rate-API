import re
import json
import datetime
import requests
import logging
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Meralco Rate API",
    description="Simple API that scrapes the latest Meralco electricity rate",
    version="1.0.0"
)

app.mount("/assets", StaticFiles(directory="assets"), name="assets")

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("assets/favicon.ico")

BASE_URL = "https://company.meralco.com.ph"
NEWS_URL = f"{BASE_URL}/news-and-advisories"

def get_latest_rates_links(limit=5):
    """Finds the most recent news articles containing 'rates' in link text or URL."""
    r = requests.get(NEWS_URL, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    rate_links = []
    seen_urls = set()
    seen_months = set()  # Track unique month-year combinations

    # Find all <a> tags under news list region:
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)

        if ("/news-and-advisories/" in href and 
            ("rate" in href.lower() or "rate" in text.lower())):
            # Make absolute if needed
            if not href.startswith("http"):
                full = BASE_URL + href
            else:
                full = href

            # Extract month/year to check uniqueness
            month, year = extract_month_year_from_url(full)
            month_year_key = f"{month}-{year}"

            # Only add if we haven't seen this URL AND this month-year combo
            if full not in seen_urls and month_year_key not in seen_months:
                seen_urls.add(full)
                if month and year:  # Only track if we successfully extracted month/year
                    seen_months.add(month_year_key)
                rate_links.append(full)
                print(f"Found rate link {len(rate_links)}: {full} ({month} {year})")  # Debug print

            if len(rate_links) >= limit:
                break

    if not rate_links:
        print("WARNING: No rate links found.")
    return rate_links

def extract_month_year_from_url(url):
    """Extract month and year from URL like 'higher-rates-november-2025'."""
    months = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    
    url_lower = url.lower()
    
    # Try to find month and year in URL
    for month_name, month_num in months.items():
        if month_name in url_lower:
            # Look for 4-digit year
            year_match = re.search(r'20\d{2}', url)
            if year_match:
                return month_name.capitalize(), int(year_match.group(0))
    
    return None, None

def extract_rate(url):
    """Scrapes the ₱/kWh value from the advisory page."""
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    
    text = soup.get_text(" ", strip=True)
    
    # Try multiple patterns
    patterns = [
        r"to\s+P(\d+\.\d{4})\s+per\s+kWh",
        r"P(\d+\.\d{4})\s+per\s+kWh",
        r"overall\s+rate[^P]*P(\d+\.\d{4})\s+per\s+kWh",
        r"(?:Php|PHP)\s*(\d+\.\d{4})\s+per\s+kWh",
        r"(\d+\.\d{4})\s+per\s+kWh"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    
    return None

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Meralco Rate API",
        "endpoints": {
            "/rate": "Get the latest electricity rate",
            "/rates/history": "Get the latest 5 electricity rates",
            "/docs": "API documentation"
        }
    }

@app.get("/rate")
async def get_current_rate():
    """Fetches and returns the latest Meralco electricity rate."""
    try:
        latest_links = get_latest_rates_links(limit=1)
        if not latest_links:
            raise HTTPException(status_code=404, detail="No rates advisory found")
        
        url = latest_links[0]
        rate = extract_rate(url)
        if rate is None:
            raise HTTPException(status_code=500, detail="Could not extract rate from the page")
        
        month, year = extract_month_year_from_url(url)
        
        return {
            "rate": rate,
            "unit": "PHP/kWh",
            "month": month,
            "year": year,
            "source": url,
            "last_updated": datetime.datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch data from Meralco: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/rates/history")
async def get_rate_history():
    """Fetches and returns the latest 5 Meralco electricity rates."""
    try:
        latest_links = get_latest_rates_links(limit=5)
        
        print(f"Found {len(latest_links)} links")  # Debug
        
        if not latest_links:
            raise HTTPException(status_code=404, detail="No rates advisory found")
        
        rates_data = []
        for url in latest_links:
            try:
                rate = extract_rate(url)
                month, year = extract_month_year_from_url(url)
                
                print(f"Processing: {url}")  # Debug
                print(f"Rate: {rate}, Month: {month}, Year: {year}")  # Debug
                
                if rate is not None and month is not None and year is not None:
                    rates_data.append({
                        "rate": rate,
                        "unit": "PHP/kWh",
                        "month": month,
                        "year": year,
                        "source": url
                    })
            except Exception as e:
                print(f"Error processing {url}: {str(e)}")  # Debug
                continue  # Skip this URL and continue with others
        
        if not rates_data:
            raise HTTPException(status_code=404, detail="Could not extract rates from any page")
        
        return {
            "rates": rates_data,
            "count": len(rates_data),
            "last_updated": datetime.datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch data from Meralco: {str(e)}")
    except Exception as e:
        print(f"Error in get_rate_history: {str(e)}")  # Debug
        import traceback
        traceback.print_exc()  # Print full stack trace
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)