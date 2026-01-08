"""
DarvaX Scanner - FastAPI Backend
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from scanner import scan_ticker
from backtest import run_backtest
from chart_analyzer import analyze_chart

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

app = FastAPI(title="DarvaX Scanner", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScanRequest(BaseModel):
    tickers: List[str]


class BacktestRequest(BaseModel):
    ticker: str
    years: int = 5


class ChartAnalysisRequest(BaseModel):
    ticker: str
    image_base64: str


class SignalResponse(BaseModel):
    ticker: str
    passed: bool
    pattern: str
    close: float
    trigger: float
    stop_loss: float
    volume_status: str
    distance_pct: float
    priority: str
    ath_pct: float
    blue_sky: str


@app.get("/")
def root():
    return {"status": "DarvaX Scanner API is running"}


@app.post("/api/scan", response_model=List[SignalResponse])
def scan_tickers(request: ScanRequest):
    """
    Scan a list of tickers and return verified signals.
    """
    results = []
    
    for symbol in request.tickers:
        symbol = symbol.strip()
        if not symbol:
            continue
        
        signal = scan_ticker(symbol)
        if signal and signal.get("passed"):
            results.append(SignalResponse(**signal))
    
    return results


@app.post("/api/backtest")
def backtest_ticker(request: BacktestRequest):
    """
    Run backtest on a single ticker.
    """
    result = run_backtest(request.ticker, request.years)
    return result


@app.post("/api/analyze-chart")
def analyze_chart_endpoint(request: ChartAnalysisRequest):
    """
    Analyze a stock chart image using Gemini vision.
    Returns the DarvaX Sniper Report.
    """
    result = analyze_chart(
        image_base64=request.image_base64,
        ticker=request.ticker,
        api_key=GEMINI_API_KEY
    )
    return result
