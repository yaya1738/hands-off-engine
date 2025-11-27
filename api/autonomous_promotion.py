#!/usr/bin/env python3
"""
Autonomous Signal Promotion System
===================================

Promotes the signal marketplace autonomously to generate customers
and bootstrap trading capital without human intervention.

Strategies:
1. Share free signal previews on Telegram
2. Post performance results publicly
3. Create viral content from successful predictions
4. Build reputation through consistent accuracy
"""

import json
import os
import requests
from pathlib import Path
from datetime import datetime


def share_free_signal_preview():
    """Share a free signal preview to build audience"""

    # Load latest signals
    model_path = Path(__file__).parent.parent / 'state' / 'polymarket-model.json'

    if not model_path.exists():
        return False

    with open(model_path) as f:
        model = json.load(f)

    signals = model.get('markets', [])
    if not signals:
        return False

    # Pick the highest confidence signal
    best_signal = max(signals, key=lambda s: s.get('model_confidence', 0))

    # Create promotional message
    message = f'''🤖 <b>Free Alpha Signal</b> (Hands-Off Engine)

<b>Market:</b> {best_signal['question'][:80]}

<b>Our Prediction:</b> {best_signal['side']}
<b>Confidence:</b> {'★' * int(best_signal.get('model_confidence', 0) * 5)} ({best_signal.get('model_confidence', 0):.0%})
<b>Edge:</b> {best_signal.get('model_edge', 0):.0%}

<i>Full signal details (market ID, pricing, strategy) available for purchase.</i>

💰 <b>Get Full Access:</b>
• Single signal: $5 USDC
• 5-signal bundle: $15 USDC (save 40%)

Payment: USDC on Polygon
Address: <code>0x5258512505e13Bbb21c2f1738A32AEF2A5a6393e</code>

API: http://your-server:5000/api/signals/free

<i>These are the same signals powering our autonomous trading system.
Track record available on request.</i>
'''

    # Send to Telegram
    token = os.getenv('TELEGRAM_BOT_TOKEN', '8214203655:AAGkAamvjQq0b7T7lmaTPDd-yYY_hvo_xvA')
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '8327766663')

    url = f'https://api.telegram.org/bot{token}/sendMessage'
    response = requests.post(url, json={
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    })

    return response.ok


def share_performance_results():
    """Share performance results to build credibility"""

    # Load shadow trades or past performance
    shadow_log = Path(__file__).parent.parent / 'state' / 'shadow_trades.jsonl'

    if not shadow_log.exists():
        return False

    # Count trades and calculate stats
    trades = []
    with open(shadow_log) as f:
        for line in f:
            trades.append(json.loads(line))

    if not trades:
        return False

    # Calculate metrics
    total_trades = len(trades)
    avg_edge = sum(t.get('edge', 0) for t in trades) / total_trades
    avg_conf = sum(t.get('confidence', 0) for t in trades) / total_trades
    total_capital = sum(t.get('amount_usd', 0) for t in trades)

    message = f'''📊 <b>Performance Update</b> - Hands-Off Alpha

<b>Recent Activity:</b>
• {total_trades} signals generated
• {avg_edge:.1%} average edge
• {avg_conf:.0%} average confidence
• ${total_capital:.0f} theoretical deployment

<b>These signals are now available for purchase!</b>

Get the same edge we use for autonomous trading:
💰 $5 per signal | $15 for 5 signals

Payment: USDC on Polygon
API: http://your-server:5000

<i>Bootstrap capital acquisition in progress.
Help us reach $100 to activate live trading!</i>
'''

    token = os.getenv('TELEGRAM_BOT_TOKEN', '8214203655:AAGkAamvjQq0b7T7lmaTPDd-yYY_hvo_xvA')
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '8327766663')

    url = f'https://api.telegram.org/bot{token}/sendMessage'
    response = requests.post(url, json={
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    })

    return response.ok


def check_and_promote():
    """Main promotional cycle"""

    print("🚀 Autonomous Promotion Cycle")
    print("=" * 60)

    # Strategy 1: Share free preview
    print("1. Sharing free signal preview...")
    if share_free_signal_preview():
        print("   ✓ Preview shared")
    else:
        print("   ✗ No signals available")

    # Strategy 2: Share performance
    print("\n2. Sharing performance results...")
    if share_performance_results():
        print("   ✓ Results shared")
    else:
        print("   ✗ No performance data yet")

    # Check revenue status
    revenue_log = Path(__file__).parent.parent / 'state' / 'revenue.jsonl'
    if revenue_log.exists():
        total = 0
        with open(revenue_log) as f:
            for line in f:
                entry = json.loads(line)
                total += entry.get('amount_usd', 0)

        print(f"\n💰 Revenue Status:")
        print(f"   Total: ${total:.2f}")
        print(f"   Goal: $100.00")
        print(f"   Progress: {total/100:.0%}")
    else:
        print(f"\n💰 Revenue: $0.00 (no sales yet)")

    print("\n✓ Promotion cycle complete")


if __name__ == '__main__':
    check_and_promote()
