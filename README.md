# DarvaX Stock Picker

A web application implementing the DarvaX trading methodology for identifying high-probability breakout setups.

## Features

- **Trinity Scanner**: Filters stocks based on:
  - Close > 30-Week MA
  - Close >= 90% of ATH (Uncharted Territory)
  - Weekly Inside Bar (Jalwa) pattern
  
- **Priority System**: Classifies signals as SNIPER / TIGHT / STANDARD / WIDE based on distance to trigger

- **Blue Sky Indicator**: Shows ATH status (BLUE SKY / NEAR / RESIST)

- **Chart Analysis**: Gemini Vision AI for forensic chart audits

## Setup

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set your Gemini API key
export GEMINI_API_KEY="your-api-key"

# Run server
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
open frontend/index.html
```

## Usage

1. Paste ticker symbols (one per line)
2. Click "Scan for Signals"
3. Results sorted by distance (tightest first)
4. Click 📊 to analyze charts with AI

## Tech Stack

- **Backend**: FastAPI, yfinance, pandas
- **Frontend**: Vanilla HTML/CSS/JS
- **AI**: Google Gemini Vision API
