# Meralco Rate API

Simple API that scrapes the latest Meralco electricity rate from their official website.

## Features

- Get current Meralco electricity rates in PHP/kWh
- Returns JSON data with rate, source URL, and timestamp
- Fast and lightweight FastAPI implementation
- Automatic API documentation with Swagger UI

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Meralco-Rate-API.git
cd Meralco-Rate-API
```

2. Create a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running Locally

Start the server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### Get Current Rate
```
GET /rate
```

**Response:**
```json
{
  "rate": 13.4702,
  "unit": "PHP/kWh",
  "source": "https://company.meralco.com.ph/news-and-advisories/higher-rates-november-2025",
  "last_updated": "2025-11-13T19:16:57.748640"
}
```

Returns API information and available endpoints.

#### API Documentation
```
GET /docs
```

## Requirements

- Python 3.11+
- FastAPI
- Uvicorn
- Requests
- BeautifulSoup4

See `requirements.txt` for full dependencies.