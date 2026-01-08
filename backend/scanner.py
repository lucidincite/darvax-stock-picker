"""
DarvaX Scanner - Core Logic
Implements the Non-Negotiable Trinity:
1. Uncharted Trend Engine
2. Weekly Jalwa Detector
3. Fuel Context
"""

import yfinance as yf
import pandas as pd
from typing import Optional
import warnings

warnings.filterwarnings("ignore")


def normalize_ticker(symbol: str) -> Optional[str]:
    """
    Normalize ticker symbol for Indian markets.
    Auto-appends .NS (NSE), falls back to .BO (BSE).
    """
    symbol = symbol.strip().upper()
    
    # Respect user input if already has suffix
    if symbol.endswith('.NS') or symbol.endswith('.BO'):
        return symbol
    
    # Default to NSE
    nse_symbol = f"{symbol}.NS"
    
    try:
        ticker = yf.Ticker(nse_symbol)
        hist = ticker.history(period="5d")
        if not hist.empty:
            return nse_symbol
        # Fallback to BSE
        return f"{symbol}.BO"
    except Exception:
        return None


def fetch_data(ticker: str) -> Optional[pd.DataFrame]:
    """
    Fetch 2 years of daily data and resample to Weekly.
    """
    try:
        t = yf.Ticker(ticker)
        df_daily = t.history(period="2y")
        
        if df_daily.empty:
            return None
        
        # Resample to Weekly (Friday close)
        df_weekly = df_daily.resample('W-FRI').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        
        return df_weekly
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None


def check_trend(df: pd.DataFrame) -> bool:
    """
    Gate 1: Close > 30-Week MA
    """
    if len(df) < 30:
        return False
    
    ma_30 = df['Close'].rolling(window=30).mean().iloc[-1]
    current_close = df['Close'].iloc[-1]
    
    return current_close > ma_30


def check_death_zone(df: pd.DataFrame) -> bool:
    """
    Gate 2: Reject if retracement > 79%
    Returns True if SAFE (not in death zone)
    """
    ath = df['High'].max()
    current_close = df['Close'].iloc[-1]
    
    retracement = (ath - current_close) / ath
    
    # SAFE if retracement <= 79%
    return retracement <= 0.79


def check_uncharted_territory(df: pd.DataFrame) -> bool:
    """
    Trinity 1: Close >= 90% of ATH (Uncharted Territory)
    """
    ath = df['High'].max()
    current_close = df['Close'].iloc[-1]
    
    return current_close >= (0.90 * ath)


def check_jalwa(df: pd.DataFrame) -> tuple[bool, float]:
    """
    Trinity 2: Weekly Inside Bar (Jalwa)
    Returns (is_jalwa, trigger_price)
    """
    if len(df) < 2:
        return False, 0.0
    
    # Current bar (completed week)
    curr_high = df['High'].iloc[-1]
    curr_low = df['Low'].iloc[-1]
    
    # Mother bar (week before)
    prev_high = df['High'].iloc[-2]
    prev_low = df['Low'].iloc[-2]
    
    # Inside Bar: Current is contained within previous
    is_inside = (curr_high < prev_high) and (curr_low > prev_low)
    
    # Trigger = Previous High (the breakout level)
    trigger = prev_high
    
    return is_inside, trigger


def check_volume(df: pd.DataFrame) -> str:
    """
    Trinity 3: Volume Context
    Returns: CONTRACTION, EXPANSION, or NEUTRAL
    """
    if len(df) < 21:
        return "NEUTRAL"
    
    avg_vol = df['Volume'].rolling(20).mean().iloc[-2]
    mother_vol = df['Volume'].iloc[-2]
    inside_vol = df['Volume'].iloc[-1]
    
    # Contraction on Inside Bar (bullish coil)
    if inside_vol < avg_vol:
        return "CONTRACTION"
    # Expansion on Mother Bar (fuel)
    elif mother_vol > avg_vol:
        return "EXPANSION"
    else:
        return "NEUTRAL"


def scan_ticker(symbol: str) -> Optional[dict]:
    """
    Main scanner function for a single ticker.
    Applies all Trinity filters and returns signal data.
    """
    # Normalize ticker
    ticker = normalize_ticker(symbol)
    if not ticker:
        return None
    
    # Fetch weekly data
    df = fetch_data(ticker)
    if df is None or len(df) < 30:
        return None
    
    # Gate 1: Trend
    if not check_trend(df):
        return None
    
    # Gate 2: Death Zone
    if not check_death_zone(df):
        return None
    
    # Trinity 1: Uncharted Territory
    if not check_uncharted_territory(df):
        return None
    
    # Trinity 2: Jalwa (Inside Bar)
    is_jalwa, trigger = check_jalwa(df)
    if not is_jalwa:
        return None
    
    # Trinity 3: Volume Context
    volume_status = check_volume(df)
    
    # Calculate Stop Loss
    stop_loss = round(trigger * 0.99, 2)
    current_close = round(df['Close'].iloc[-1], 2)
    
    # Calculate Distance % (how far close is from trigger)
    distance_pct = round(((trigger - current_close) / current_close) * 100, 1)
    
    # Classify Priority based on distance
    if distance_pct <= 2.0:
        priority = "SNIPER"      # Super tight coil, could trigger fast
    elif distance_pct <= 3.0:
        priority = "TIGHT"       # High quality, high alert
    elif distance_pct <= 5.0:
        priority = "STANDARD"    # Valid setup, set alerts
    else:
        priority = "WIDE"        # Loose handle, needs caution
    
    # Calculate ATH % and Blue Sky status
    ath = df['High'].max()
    ath_pct = round((current_close / ath) * 100, 1)
    
    # Blue Sky = at or near ATH (99%+), Resist = overhead supply exists
    if ath_pct >= 99:
        blue_sky = "BLUE_SKY"    # No resistance, aggressive size OK
    elif ath_pct >= 95:
        blue_sky = "NEAR_ATH"    # Very close, minimal resistance
    else:
        blue_sky = "RESIST"      # Overhead supply, standard size
    
    return {
        "ticker": ticker,
        "passed": True,
        "pattern": "WEEKLY_JALWA",
        "close": current_close,
        "trigger": round(trigger, 2),
        "stop_loss": stop_loss,
        "volume_status": volume_status,
        "distance_pct": distance_pct,
        "priority": priority,
        "ath_pct": ath_pct,
        "blue_sky": blue_sky
    }
