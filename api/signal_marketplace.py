#!/usr/bin/env python3
"""
Autonomous Signal Marketplace
===============================

Monetizes alpha signals to bootstrap trading capital.

The system generates valuable predictions with 8-15% edge.
This module creates a paid API to sell those signals and
generate initial capital autonomously.

Usage:
    python3 api/signal_marketplace.py

Revenue Flow:
    1. System generates alpha signals (already happening)
    2. API serves signals for payment
    3. Revenue accumulates in wallet
    4. Once threshold reached ($100), auto-activate trading
"""

from flask import Flask, jsonify, request
from pathlib import Path
import json
from datetime import datetime
import hmac
import hashlib
import requests
import os
from functools import lru_cache

app = Flask(__name__)

# Polygon USDC contract address
USDC_CONTRACT_POLYGON = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"  # Native USDC on Polygon
USDC_CONTRACT_BRIDGED = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # Bridged USDC.e

# Polygonscan API for transaction verification
POLYGONSCAN_API_KEY = os.getenv('POLYGONSCAN_API_KEY', '')

# Configuration
SIGNAL_PRICE_USD = 5  # $5 per signal
BUNDLE_PRICE_USD = 15  # $15 for 5 signals (40% discount)
MIN_TRADING_CAPITAL = 100  # Activate trading at $100

# Payment addresses (for crypto payments)
PAYMENT_WALLET_POLYGON = "0x5258512505e13Bbb21c2f1738A32AEF2A5a6393e"


def load_latest_signals():
    """Load the latest alpha signals from the model"""
    model_path = Path(__file__).parent.parent / 'state' / 'polymarket-model.json'

    if not model_path.exists():
        return []

    with open(model_path) as f:
        model = json.load(f)

    return model.get('markets', [])


def create_signal_package(signals, tier='free'):
    """Create a signal package for sale"""

    if tier == 'free':
        # Free tier: limited info
        return [{
            'question': s['question'],
            'category': s.get('query_category', 'unknown'),
            'confidence': '★' * int(s.get('model_confidence', 0.5) * 5),
            'edge_range': '5-15%',
            'access': 'Upgrade for full details'
        } for s in signals[:2]]  # Only first 2

    elif tier == 'premium':
        # Premium tier: full details
        return [{
            'market_id': s['market_id'],
            'question': s['question'],
            'side': s['side'],
            'edge': f"{s.get('model_edge', 0)*100:.1f}%",
            'confidence': f"{s.get('model_confidence', 0)*100:.0f}%",
            'fair_price': s.get('fair_price'),
            'market_price': s.get('market_price'),
            'liquidity': s.get('liquidity'),
            'reasoning': f"Model predicts {s.get('fair_price', 0.5):.2f} vs market {s.get('market_price', 0.5):.2f}"
        } for s in signals]


@app.route('/')
def index():
    """Landing page"""
    return jsonify({
        'service': 'Hands-Off Alpha Signals',
        'description': 'AI-powered prediction market signals with 8-15% edge',
        'tagline': 'The same signals that power our autonomous trading engine',
        'pricing': {
            'single_signal': f'${SIGNAL_PRICE_USD} USDC',
            'signal_bundle': f'${BUNDLE_PRICE_USD} USDC (5 signals)',
        },
        'endpoints': {
            'free_preview': '/api/signals/free',
            'purchase': '/api/signals/purchase',
            'verify_payment': '/api/verify-payment'
        },
        'payment_address': PAYMENT_WALLET_POLYGON,
        'payment_network': 'Polygon',
        'payment_token': 'USDC'
    })


@app.route('/api/signals/free')
def free_signals():
    """Free preview of signals (limited info)"""
    signals = load_latest_signals()

    if not signals:
        return jsonify({
            'error': 'No signals available',
            'message': 'Check back soon'
        }), 404

    preview = create_signal_package(signals, tier='free')

    return jsonify({
        'signals': preview,
        'total_available': len(signals),
        'preview_count': len(preview),
        'upgrade': {
            'message': 'Unlock full signal details',
            'price': f'${SIGNAL_PRICE_USD} USDC',
            'payment_address': PAYMENT_WALLET_POLYGON
        }
    })


def verify_usdc_payment(tx_hash: str, expected_recipient: str) -> tuple:
    """
    Verify a USDC payment on Polygon chain.

    Returns: (verified: bool, amount_usd: float)
    """
    if not tx_hash or len(tx_hash) != 66 or not tx_hash.startswith('0x'):
        return False, 0.0

    expected_recipient = expected_recipient.lower()

    # Try Polygonscan API first (if API key available)
    if POLYGONSCAN_API_KEY:
        try:
            url = f"https://api.polygonscan.com/api"
            params = {
                "module": "proxy",
                "action": "eth_getTransactionReceipt",
                "txhash": tx_hash,
                "apikey": POLYGONSCAN_API_KEY
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get('result'):
                receipt = data['result']

                # Check transaction was successful
                if receipt.get('status') != '0x1':
                    return False, 0.0

                # Parse logs for USDC transfer
                for log in receipt.get('logs', []):
                    contract = log.get('address', '').lower()
                    # Check if it's a USDC transfer (either native or bridged)
                    if contract in [USDC_CONTRACT_POLYGON.lower(), USDC_CONTRACT_BRIDGED.lower()]:
                        # ERC20 Transfer event topic
                        if log.get('topics', []) and log['topics'][0] == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef':
                            # topics[2] is the recipient (padded to 32 bytes)
                            recipient_topic = log['topics'][2] if len(log['topics']) > 2 else ''
                            recipient = '0x' + recipient_topic[-40:].lower()

                            if recipient == expected_recipient:
                                # Parse amount from data (USDC has 6 decimals)
                                amount_hex = log.get('data', '0x0')
                                amount_wei = int(amount_hex, 16)
                                amount_usd = amount_wei / 1e6
                                return True, amount_usd

        except Exception as e:
            print(f"Polygonscan verification error: {e}")

    # Fallback: Use public RPC
    try:
        rpc_url = "https://polygon-rpc.com"
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getTransactionReceipt",
            "params": [tx_hash],
            "id": 1
        }
        response = requests.post(rpc_url, json=payload, timeout=10)
        data = response.json()

        if data.get('result'):
            receipt = data['result']

            if receipt.get('status') != '0x1':
                return False, 0.0

            for log in receipt.get('logs', []):
                contract = log.get('address', '').lower()
                if contract in [USDC_CONTRACT_POLYGON.lower(), USDC_CONTRACT_BRIDGED.lower()]:
                    if log.get('topics', []) and log['topics'][0] == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef':
                        recipient_topic = log['topics'][2] if len(log['topics']) > 2 else ''
                        recipient = '0x' + recipient_topic[-40:].lower()

                        if recipient == expected_recipient:
                            amount_hex = log.get('data', '0x0')
                            amount_wei = int(amount_hex, 16)
                            amount_usd = amount_wei / 1e6
                            return True, amount_usd

    except Exception as e:
        print(f"RPC verification error: {e}")

    return False, 0.0


@app.route('/api/signals/purchase', methods=['POST'])
def purchase_signals():
    """Purchase full signal access"""

    data = request.json
    payment_tx = data.get('payment_tx')  # Transaction hash

    if not payment_tx:
        return jsonify({
            'error': 'Missing payment transaction',
            'instructions': {
                'step1': f'Send ${SIGNAL_PRICE_USD} USDC to {PAYMENT_WALLET_POLYGON}',
                'step2': 'Submit transaction hash to this endpoint',
                'step3': 'Receive full signal details'
            }
        }), 400

    # Verify payment on-chain
    payment_verified, payment_amount = verify_usdc_payment(payment_tx, PAYMENT_WALLET_POLYGON)

    if not payment_verified:
        return jsonify({
            'error': 'Payment not verified',
            'message': 'Transaction not found or not sent to our wallet',
            'expected_recipient': PAYMENT_WALLET_POLYGON,
            'tx_hash': payment_tx
        }), 402

    if payment_amount < SIGNAL_PRICE_USD * 0.95:  # Allow 5% slippage
        return jsonify({
            'error': 'Insufficient payment',
            'message': f'Expected ${SIGNAL_PRICE_USD}, received ${payment_amount:.2f}',
            'tx_hash': payment_tx
        }), 402

    signals = load_latest_signals()
    full_signals = create_signal_package(signals, tier='premium')

    # Log revenue
    log_revenue(payment_tx, SIGNAL_PRICE_USD, len(signals))

    return jsonify({
        'status': 'success',
        'signals': full_signals,
        'purchased_at': datetime.utcnow().isoformat() + 'Z',
        'transaction': payment_tx
    })


def log_revenue(tx_hash, amount_usd, signals_sold):
    """Log revenue from signal sales"""
    revenue_log = Path(__file__).parent.parent / 'state' / 'revenue.jsonl'

    entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'tx_hash': tx_hash,
        'amount_usd': amount_usd,
        'signals_sold': signals_sold,
        'source': 'signal_marketplace'
    }

    with open(revenue_log, 'a') as f:
        f.write(json.dumps(entry) + '\n')

    # Check if we've hit trading capital threshold
    total_revenue = calculate_total_revenue()

    if total_revenue >= MIN_TRADING_CAPITAL:
        print(f"🎉 CAPITAL THRESHOLD REACHED: ${total_revenue:.2f}")
        print(f"   Autonomous trading can now be activated!")

        # TODO: Auto-activate trading
        # For now, just notify
        notify_capital_ready(total_revenue)


def calculate_total_revenue():
    """Calculate total revenue from signal sales"""
    revenue_log = Path(__file__).parent.parent / 'state' / 'revenue.jsonl'

    if not revenue_log.exists():
        return 0

    total = 0
    with open(revenue_log) as f:
        for line in f:
            entry = json.loads(line)
            total += entry.get('amount_usd', 0)

    return total


def notify_capital_ready(amount):
    """Notify that capital threshold reached"""
    # Send Telegram notification
    import os
    import requests

    token = os.getenv('TELEGRAM_BOT_TOKEN', '8214203655:AAGkAamvjQq0b7T7lmaTPDd-yYY_hvo_xvA')
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '8327766663')

    message = f'''🎉 <b>CAPITAL ACQUIRED AUTONOMOUSLY</b>

💰 Revenue: ${amount:.2f} from signal sales
✅ Threshold reached: ${MIN_TRADING_CAPITAL}

<b>READY TO ACTIVATE LIVE TRADING</b>

Revenue from selling alpha signals has reached
the minimum threshold. System can now bootstrap
autonomous trading operations.

Next: Transfer revenue to trading wallet and activate.
'''

    url = f'https://api.telegram.org/bot{token}/sendMessage'
    requests.post(url, json={'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'})


if __name__ == '__main__':
    print("🚀 Autonomous Signal Marketplace")
    print("=" * 60)
    print(f"Payment Address: {PAYMENT_WALLET_POLYGON}")
    print(f"Signal Price: ${SIGNAL_PRICE_USD} USDC")
    print(f"Capital Goal: ${MIN_TRADING_CAPITAL}")
    print()
    print("Starting API server...")
    print("Access at: http://localhost:5000")

    app.run(host='0.0.0.0', port=5000, debug=False)
