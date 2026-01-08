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

## Local Development

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
echo "GEMINI_API_KEY=your-api-key" > .env

# Run server
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
open frontend/index.html
```

## Deployment

### Frontend → Vercel
1. Connect your GitHub repo to Vercel
2. Deploy (auto-detects vercel.json config)

### Backend → Railway
1. Create new project on [Railway](https://railway.app)
2. Connect your GitHub repo
3. Add environment variable: `GEMINI_API_KEY`
4. Railway auto-detects Procfile and deploys
5. Copy your Railway URL (e.g., `https://your-app.up.railway.app`)
6. Update `frontend/main.js` with your Railway URL

## Tech Stack

- **Backend**: FastAPI, yfinance, pandas
- **Frontend**: Vanilla HTML/CSS/JS
- **AI**: Google Gemini Vision API

