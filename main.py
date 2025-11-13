import re
import json
import datetime
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Meralco Rate API",
    description="Simple API that scrapes the latest Meralco electricity rate",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory="assets"), name="assets")

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("assets/favicon.ico")

BASE_URL = "https://company.meralco.com.ph"
NEWS_URL = f"{BASE_URL}/news-and-advisories"

def get_latest_rates_link():
    """Finds the most recent news article containing the word 'Rates'."""
    r = requests.get(NEWS_URL, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    rate_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        link_text = a.get_text(strip=True)
        
        if ("/news-and-advisories/" in href and 
            ("rates" in href.lower() or "rates" in link_text.lower())):
            
            if not href.startswith("http"):
                href = BASE_URL + href
            
            rate_links.append({
                "url": href,
            })
    
    if rate_links:
        return rate_links[0]
    
    return None

def extract_rate_and_date(url):
    """Scrapes the ₱/kWh value and published date from the advisory page."""
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    
    text = soup.get_text(" ", strip=True)
    
    # Extract rate
    rate = None
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
            rate = float(match.group(1))
            break
    
    # Extract published date
    published_date = None
    # Look for date patterns like "November 20, 2025" or "20 November 2025"
    date_patterns = [
        r"(?:Published|Date|Posted)[\s:]+(\w+\s+\d{1,2},?\s+\d{4})",
        r"(\d{1,2}\s+\w+\s+\d{4})",
        r"(\w+\s+\d{1,2},?\s+\d{4})"
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            published_date = match.group(1)
            break
    
    # Try to find in meta tags
    if not published_date:
        meta_date = soup.find('meta', {'property': 'article:published_time'})
        if meta_date:
            published_date = meta_date.get('content')
        else:
            # Try to find time tag
            time_tag = soup.find('time')
            if time_tag:
                published_date = time_tag.get('datetime') or time_tag.get_text(strip=True)
    
    return rate, published_date

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Meralco Rate API",
        "endpoints": {
            "/rate": "Get the latest electricity rate",
            "/docs": "API documentation"
        }
    }

@app.get("/rate")
async def get_current_rate():
    try:
        latest = get_latest_rates_link()
        if not latest:
            raise HTTPException(status_code=404, detail="No rates advisory found")
        
        rate, published_date = extract_rate_and_date(latest["url"])
        if rate is None:
            raise HTTPException(status_code=500, detail="Could not extract rate from the page")
        
        response = {
            "rate": rate,
            "unit": "PHP/kWh",
            "source": latest["url"],
            "last_updated": datetime.datetime.now().isoformat()
        }
        
        if published_date:
            response["published"] = published_date
        
        return response
    
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch data from Meralco: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)