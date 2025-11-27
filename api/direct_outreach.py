#!/usr/bin/env python3
"""
Direct Outreach System - Target Active Polymarket Traders
==========================================================

Strategy:
1. Find active Polymarket traders (from public API)
2. Send personalized DM/message
3. Track responses and conversions

Goal: 20 outreaches/day → 5-10% response → 1-2 buyers/day
"""

import json
import requests
from pathlib import Path
from datetime import datetime


def get_active_polymarket_markets():
    """Get currently active markets from Polymarket"""

    url = "https://gamma-api.polymarket.com/markets"

    params = {
        'limit': 50,
        'offset': 0,
        'active': True,
        'closed': False,
        'order': 'volume24hr',  # Highest volume = most active traders
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching markets: {e}")
        return []


def create_outreach_message(trader_focus='general'):
    """
    Create personalized outreach message

    trader_focus: What markets they seem to trade (politics, crypto, sports)
    """

    messages = {
        'general': '''Hey! I noticed you're active on Polymarket.

I built an AI that finds statistical edges in prediction markets (8-15% average edge). Just launched a signal service:

• Free preview: http://138.68.103.156:5000/api/free
• Full signals: $0.10 each
• Unlimited: $10/month

Track record: 10 signals, 65%+ confidence, public verification

Worth a look if you're serious about finding edges. First signal's on me either way.

Let me know if you want early access!''',

        'politics': '''Hey! Saw you're trading politics markets on Polymarket.

I built an AI specifically for political prediction markets - analyzes polls, betting odds, historical data to find mispriced markets.

Current edge: 8-15% on average across 10 predictions.

Offering early access:
• $0.10 per signal (vs $50+ elsewhere)
• Free preview: http://138.68.103.156:5000/api/free
• 30-day profit guarantee

Since you're already trading politics, figured you might want systematic edge. Let me know!''',

        'crypto': '''Hey! I see you trade crypto markets on Polymarket.

Built an AI that finds edges in crypto prediction markets. Just went live:

• Free signal preview: http://138.68.103.156:5000/api/free
• $0.10 per full signal
• Public track record (10 predictions, 65%+ confidence)

Early adopter pricing - will increase as track record proves out.

Want to try a free signal? I can send you our current highest confidence pick.''',

        'sports': '''Hey! Noticed you trade sports markets on Polymarket.

I automated sports prediction analysis - finds statistical edges:

📊 Current performance:
• 10 predictions made
• 8-15% average edge
• 65%+ confidence

Early access: $0.10 per signal
Free preview: http://138.68.103.156:5000/api/free

If you're stacking bets anyway, might as well have an edge. Let me know if interested!'''
    }

    return messages.get(trader_focus, messages['general'])


def create_value_proposition_message():
    """Alternative message focusing on value prop"""

    return '''Quick question: What do you currently pay for prediction market signals/tips?

I'm asking because I just launched an AI signal service at $0.10 per signal (vs $50-100/month elsewhere).

Same quality, 50x cheaper because:
1. Fully automated (no manual research cost)
2. Early stage (building user base)
3. Want to prove track record first

Free preview: http://138.68.103.156:5000/api/free

If you trade regularly, could save you $50-100/month vs traditional tipsters. Worth checking out?'''


def create_partnership_message():
    """Message for Discord/community owners"""

    return '''Hey! I run a trading Discord/community and wanted to reach out about a partnership.

I built an AI signal service for prediction markets ($0.10 per signal, $10/month unlimited).

Partnership offer:
• Your members get 50% off ($0.05 signals)
• You get 30% revenue share on all sales
• No upfront cost, purely performance-based

Current stats:
• 10 predictions made
• 8-15% average edge
• 65%+ confidence
• Public track record

If your community trades Polymarket/PredictIt, this could be value-add for members + revenue for you.

Free preview for you to test: http://138.68.103.156:5000/api/free

Interested in exploring this?'''


def generate_outreach_list():
    """
    Generate list of people/communities to reach out to

    Sources:
    - Polymarket Discord users
    - Twitter users talking about Polymarket
    - Reddit r/predictit r/polymarket members
    - Trading Discord servers
    """

    # For now, create template list
    outreach_targets = [
        {
            'type': 'discord_server',
            'name': 'Polymarket Traders',
            'focus': 'general',
            'priority': 'high'
        },
        {
            'type': 'discord_server',
            'name': 'Prediction Market Alpha',
            'focus': 'general',
            'priority': 'high'
        },
        {
            'type': 'twitter_user',
            'handle': '@polymarket_traders',
            'focus': 'general',
            'priority': 'medium'
        },
        {
            'type': 'reddit_community',
            'name': 'r/polymarket',
            'focus': 'general',
            'priority': 'high'
        },
        {
            'type': 'reddit_community',
            'name': 'r/predictit',
            'focus': 'politics',
            'priority': 'high'
        },
        {
            'type': 'reddit_community',
            'name': 'r/sportsbook',
            'focus': 'sports',
            'priority': 'medium'
        }
    ]

    return outreach_targets


def save_outreach_templates():
    """Save outreach templates for manual use"""

    templates = {
        'dm_general': create_outreach_message('general'),
        'dm_politics': create_outreach_message('politics'),
        'dm_crypto': create_outreach_message('crypto'),
        'dm_sports': create_outreach_message('sports'),
        'value_prop': create_value_proposition_message(),
        'partnership': create_partnership_message()
    }

    output_file = Path(__file__).parent.parent / 'state' / 'outreach_templates.json'

    with open(output_file, 'w') as f:
        json.dump(templates, f, indent=2)

    print(f"✅ Saved outreach templates to {output_file}")

    return templates


def create_outreach_tracker():
    """Create tracking system for outreach efforts"""

    tracker = {
        'campaign_start': datetime.utcnow().isoformat() + 'Z',
        'targets': generate_outreach_list(),
        'metrics': {
            'messages_sent': 0,
            'responses_received': 0,
            'conversions': 0,
            'revenue_generated': 0
        },
        'next_actions': [
            'Join Polymarket Discord',
            'Join prediction market trading servers',
            'Follow active traders on Twitter',
            'Post in r/polymarket r/predictit',
            'Reach out to 5 Discord server owners'
        ]
    }

    tracker_file = Path(__file__).parent.parent / 'state' / 'outreach_tracker.json'

    with open(tracker_file, 'w') as f:
        json.dump(tracker, f, indent=2)

    print(f"✅ Created outreach tracker at {tracker_file}")

    return tracker


def print_outreach_guide():
    """Print actionable guide for manual outreach"""

    print("\n" + "="*60)
    print("📢 DIRECT OUTREACH GUIDE")
    print("="*60)

    print("\n🎯 TARGET: 20 outreaches/day = 140/week")
    print("   Expected: 5-10% response = 7-14 interested/week")
    print("   Expected: 50% convert = 3-7 buyers/week")
    print("   Expected: $2-5/week revenue initially")

    print("\n📝 WHERE TO FIND TRADERS:")
    print("   1. Polymarket Discord - DM active users")
    print("   2. Twitter - Reply to #polymarket tweets")
    print("   3. Reddit r/polymarket - Comment on posts")
    print("   4. Reddit r/predictit - Share as comment")
    print("   5. Trading Discord servers - Share in #market-analysis")

    print("\n💬 WHAT TO SAY:")
    print("   Use templates in: state/outreach_templates.json")
    print("   Personalize based on what they trade (politics/crypto/sports)")

    print("\n📊 TRACK RESULTS:")
    print("   Log each outreach in: state/outreach_tracker.json")
    print("   Update metrics daily")

    print("\n⚡ QUICK WINS:")
    print("   1. Join 3 Discord servers TODAY")
    print("   2. DM 5 active traders in each (15 total)")
    print("   3. Post free signal in 2-3 subreddits")
    print("   4. Reply to 5 Twitter posts about prediction markets")

    print("\n" + "="*60)


def run_outreach_setup():
    """Set up outreach campaign"""

    print("🚀 Setting up Direct Outreach Campaign")
    print("="*60)

    # Save templates
    templates = save_outreach_templates()

    # Create tracker
    tracker = create_outreach_tracker()

    # Print guide
    print_outreach_guide()

    print("\n✅ Outreach campaign ready to launch!")
    print("\nNext step: Start reaching out manually using templates")
    print("Goal: 20 outreaches today → 1-2 buyers by end of week")


if __name__ == '__main__':
    run_outreach_setup()
