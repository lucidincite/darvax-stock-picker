"""
DarvaX Backtest Engine - "The Time Machine"
Implements the corrected backtest logic with:
1. ATH look-ahead bias fix (shift(1))
2. Volume logic fix (contraction OR expansion)
3. Percentage-based trigger buffer (0.1%)
"""

import yfinance as yf
import pandas as pd
from typing import Optional, List
import warnings

warnings.filterwarnings("ignore")


def run_backtest(ticker: str, years: int = 5) -> dict:
    """
    Run DarvaX backtest on a single ticker.
    Returns trade list and statistics.
    """
    print(f"--- BACKTESTING {ticker} ---")
    
    # 1. Fetch Daily Data (base source)
    try:
        df_daily = yf.download(ticker, period=f"{years}y", progress=False)
        if len(df_daily) < 100:
            return {"error": "Not enough data", "trades": [], "stats": {}}
    except Exception as e:
        return {"error": str(e), "trades": [], "stats": {}}

    # 2. Resample to Weekly for Pattern Detection
    df_weekly = df_daily.resample('W-FRI').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna()

    # Calculate Indicators
    df_weekly['MA_30'] = df_weekly['Close'].rolling(30).mean()
    
    # FIX #1: ATH Look-Ahead Bias - Use PREVIOUS week's cummax
    df_weekly['ATH'] = df_weekly['High'].shift(1).cummax()
    
    df_weekly['Vol_MA_20'] = df_weekly['Volume'].rolling(20).mean()

    trades = []
    
    # 3. Iterate through Weekly Candles (The "Setup" Search)
    for i in range(31, len(df_weekly) - 1):
        
        week_curr = df_weekly.iloc[i]
        week_prev = df_weekly.iloc[i-1]
        
        # Skip if indicators not ready
        if pd.isna(week_curr['MA_30']) or pd.isna(week_curr['ATH']):
            continue
        
        # A. Trend Filter (Above 30W MA)
        if week_curr['Close'] <= week_curr['MA_30']:
            continue
            
        # B. Uncharted Territory (>= 90% of ATH)
        if week_curr['Close'] < (0.90 * week_curr['ATH']):
            continue

        # C. Jalwa Detector (Inside Bar)
        is_jalwa = (week_curr['High'] < week_prev['High']) and \
                   (week_curr['Low'] > week_prev['Low'])
        
        if not is_jalwa:
            continue

        # FIX #2: Volume Logic - Accept Contraction OR Mother Expansion
        vol_ma_curr = week_curr['Vol_MA_20']
        vol_ma_prev = df_weekly.iloc[i-1]['Vol_MA_20'] if i > 0 else vol_ma_curr
        
        inside_contraction = week_curr['Volume'] < vol_ma_curr
        mother_expansion = week_prev['Volume'] > vol_ma_prev
        
        if not (inside_contraction or mother_expansion):
            continue

        # --- THE EXECUTION (Week i+1) ---
        setup_high = week_curr['High']
        
        # FIX #3: Percentage-based buffer (0.1%)
        trigger_price = setup_high * 1.001
        stop_loss = trigger_price * 0.99    # 1% Rule
        target_price = trigger_price * 1.09  # 9% Rule

        # Get Daily candles for the NEXT week
        next_week_start = df_weekly.index[i]
        next_week_end = df_weekly.index[i+1]
        
        daily_slice = df_daily[
            (df_daily.index > next_week_start) & 
            (df_daily.index <= next_week_end)
        ]
        
        if len(daily_slice) == 0:
            continue

        status = "NO_TRIGGER"
        entry_price = None
        exit_price = None
        entry_date = None
        exit_date = None
        pnl = 0.0
        in_trade = False
        
        for day_date, day_row in daily_slice.iterrows():
            if not in_trade:
                # Check for Entry
                if day_row['High'] > trigger_price:
                    in_trade = True
                    entry_price = trigger_price
                    entry_date = day_date
                    
                    # Check for same-day whipsaw
                    if day_row['Low'] < stop_loss:
                        status = "LOSS_WHIPSAW"
                        exit_price = stop_loss
                        exit_date = day_date
                        pnl = -1.0
                        break
            
            if in_trade and status == "NO_TRIGGER":
                status = "OPEN"  # Mark as entered
                
                # Check Stop Loss first (conservative)
                if day_row['Low'] < stop_loss:
                    status = "LOSS"
                    exit_price = stop_loss
                    exit_date = day_date
                    pnl = -1.0
                    break
                # Then check Target
                elif day_row['High'] > target_price:
                    status = "WIN"
                    exit_price = target_price
                    exit_date = day_date
                    pnl = 9.0
                    break
        
        # If still in trade at week end, mark as carry
        if in_trade and status == "OPEN":
            status = "CARRY"
            final_close = daily_slice.iloc[-1]['Close']
            exit_price = final_close
            exit_date = daily_slice.index[-1]
            pnl = ((final_close - trigger_price) / trigger_price) * 100

        if status != "NO_TRIGGER":
            trades.append({
                "setup_date": str(df_weekly.index[i].date()),
                "trigger": round(trigger_price, 2),
                "stop_loss": round(stop_loss, 2),
                "target": round(target_price, 2),
                "entry_date": str(entry_date.date()) if entry_date else None,
                "exit_date": str(exit_date.date()) if exit_date else None,
                "exit_price": round(exit_price, 2) if exit_price else None,
                "status": status,
                "pnl_pct": round(pnl, 2)
            })

    # 4. Calculate Statistics
    if not trades:
        return {
            "ticker": ticker,
            "error": None,
            "trades": [],
            "stats": {"total_trades": 0}
        }
    
    df_trades = pd.DataFrame(trades)
    
    wins = len(df_trades[df_trades['pnl_pct'] > 0])
    losses = len(df_trades[df_trades['pnl_pct'] < 0])
    carries = len(df_trades[df_trades['status'] == 'CARRY'])
    
    total = len(df_trades)
    win_rate = (wins / total * 100) if total > 0 else 0
    total_return = df_trades['pnl_pct'].sum()
    avg_win = df_trades[df_trades['pnl_pct'] > 0]['pnl_pct'].mean() if wins > 0 else 0
    avg_loss = df_trades[df_trades['pnl_pct'] < 0]['pnl_pct'].mean() if losses > 0 else 0
    
    stats = {
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "carries": carries,
        "win_rate": round(win_rate, 1),
        "total_return": round(total_return, 1),
        "avg_win": round(avg_win, 1),
        "avg_loss": round(avg_loss, 1),
        "expected_value": round((win_rate/100 * avg_win) + ((100-win_rate)/100 * avg_loss), 2)
    }
    
    return {
        "ticker": ticker,
        "error": None,
        "trades": trades,
        "stats": stats
    }
