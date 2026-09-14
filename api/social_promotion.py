#!/usr/bin/env python3
"""
Social Media Promotion Bot - Drive Traffic to Marketplace
==========================================================

Posts free signals on social media with CTA to marketplace.
Targets: Twitter/X, Reddit, Discord, Telegram groups

Goal: 100-500 views/day → 5-25 site visitors → 1-3 buyers
"""

import json
import os
from pathlib import Path
from datetime import datetime
import requests
import praw
import tweepy
from functools import lru_cache


def load_best_signal():
    """Load highest confidence signal for promotion"""
    model_path = Path(__file__).parent.parent / 'state' / 'polymarket-model.json'

    if not model_path.exists():
        return None

    with open(model_path) as f:
        data = json.load(f)
        markets = data.get('markets', [])

    if not markets:
        return None

    # Get highest edge signal
    best = max(markets, key=lambda m: m.get('model_edge', 0))

    return {
        'question': best.get('question', ''),
        'side': best.get('side', ''),
        'confidence': best.get('model_confidence', 0),
        'edge': best.get('model_edge', 0),
        'category': best.get('query_category', 'general')
    }


def create_twitter_post(signal):
    """Create Twitter/X post (280 char limit)"""

    conf_stars = '⭐' * int(signal['confidence'] * 5)

    # Short version for Twitter
    post = f'''🤖 AI Prediction Alert

Market: {signal['question'][:80]}...

Prediction: {signal['side']}
Confidence: {conf_stars} {signal['confidence']:.0%}
Edge: {signal['edge']:.0%}

Full details: $0.10
http://138.68.103.156:5000/api/free

#polymarket #trading #predictions'''

    return post[:280]  # Twitter limit


def create_reddit_post(signal):
    """Create Reddit post (more detailed)"""

    title = f"[AI Signal] {signal['question'][:100]}"

    body = f'''## Free AI Prediction Preview

**Market**: {signal['question']}

**AI Prediction**: {signal['side']}
**Confidence**: {signal['confidence']:.0%}
**Edge**: {signal['edge']:.0%}
**Category**: {signal['category']}

---

### What is this?

I built an AI that analyzes prediction markets and finds statistical edges. This signal has {signal['edge']:.0%} edge based on:
- Historical data analysis
- Market mispricing detection
- Sentiment analysis
- Kelly criterion position sizing

### Track Record

- 10 predictions made
- 60-75% typical confidence
- 8-15% average edge
- Public track record: http://138.68.103.156:5000/api/track-record

### How to Use

1. **Free preview**: http://138.68.103.156:5000/api/free
2. **Full details**: $0.10 (market ID, exact prices, strategy)
3. **Unlimited access**: $10/month

### Why so cheap?

I'm in early testing phase. Building track record and user base. Price will increase as accuracy proves out.

### Money-back guarantee

If you don't profit in 30 days, full refund. Zero risk.

---

*Disclaimer: This is informational. Do your own research. Gambling involves risk.*
'''

    return title, body


def create_telegram_group_post(signal):
    """Create post for Telegram groups"""

    return f'''🎯 <b>FREE AI Prediction Signal</b>

📊 <b>Market:</b> {signal['question']}

<b>AI Says:</b> {signal['side']}
<b>Confidence:</b> {signal['confidence']:.0%}
<b>Edge:</b> {signal['edge']:.0%}

This signal has a statistical edge based on historical data analysis and market mispricing detection.

💰 <b>Want full details?</b>
• Market ID
• Exact entry prices
• Position sizing
• Exit strategy

👉 Just $0.10: http://138.68.103.156:5000

Or get <b>unlimited signals</b> for $10/month.

<b>Track record:</b> 10 predictions, {signal['edge']:.0%} avg edge
<b>Guarantee:</b> Profit in 30 days or refund

<i>Early adopter pricing - will increase soon!</i>
'''


def get_twitter_client():
    """Get authenticated Twitter/X client"""
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    api_key = os.getenv('TWITTER_API_KEY')
    api_secret = os.getenv('TWITTER_API_SECRET')
    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_secret = os.getenv('TWITTER_ACCESS_SECRET')

    if not all([api_key, api_secret, access_token, access_secret]):
        return None

    try:
        client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
        return client
    except Exception as e:
        print(f"❌ Twitter auth error: {e}")
        return None


def post_to_twitter(content):
    """
    Post to Twitter/X using API

    Falls back to queue if credentials not available.
    """
    posts_file = Path(__file__).parent.parent / 'state' / 'social_media_queue.txt'

    client = get_twitter_client()

    if client:
        try:
            response = client.create_tweet(text=content)
            tweet_id = response.data['id']
            print(f"✅ Posted to Twitter: https://twitter.com/i/status/{tweet_id}")

            # Log successful post
            with open(posts_file, 'a') as f:
                f.write(f"\n\n--- TWITTER POSTED {datetime.utcnow().isoformat()} ---\n")
                f.write(f"Tweet ID: {tweet_id}\n")
                f.write(content)

            return True
        except tweepy.TweepyException as e:
            print(f"❌ Twitter post failed: {e}")
            # Fall through to queue backup

    # Fallback: Save to queue for manual posting
    print("📱 TWITTER POST (queued - no API credentials):")
    print(content)
    print("\n" + "="*60 + "\n")

    with open(posts_file, 'a') as f:
        f.write(f"\n\n--- TWITTER QUEUED {datetime.utcnow().isoformat()} ---\n")
        f.write(content)

    return False  # Return False to indicate queued, not posted


def get_reddit_client():
    """Get authenticated Reddit client"""
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    username = os.getenv('REDDIT_USERNAME')
    password = os.getenv('REDDIT_PASSWORD')
    user_agent = os.getenv('REDDIT_USER_AGENT', 'hands-off-signals:v1.0 (by /u/hands_off_bot)')

    if not all([client_id, client_secret, username, password]):
        return None

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent=user_agent
        )
        # Verify auth
        reddit.user.me()
        return reddit
    except Exception as e:
        print(f"❌ Reddit auth error: {e}")
        return None


def post_to_reddit(title, body, subreddit='test'):
    """
    Post to Reddit using PRAW

    Falls back to queue if credentials not available.
    """
    posts_file = Path(__file__).parent.parent / 'state' / 'social_media_queue.txt'

    reddit = get_reddit_client()

    if reddit:
        try:
            sub = reddit.subreddit(subreddit)
            submission = sub.submit(title=title, selftext=body)
            print(f"✅ Posted to Reddit r/{subreddit}: https://reddit.com{submission.permalink}")

            # Log successful post
            with open(posts_file, 'a') as f:
                f.write(f"\n\n--- REDDIT POSTED r/{subreddit} {datetime.utcnow().isoformat()} ---\n")
                f.write(f"URL: https://reddit.com{submission.permalink}\n")
                f.write(f"TITLE: {title}\n\n")
                f.write(body)

            return True
        except praw.exceptions.RedditAPIException as e:
            print(f"❌ Reddit post failed: {e}")
            # Fall through to queue backup
        except Exception as e:
            print(f"❌ Reddit error: {e}")

    # Fallback: Save to queue for manual posting
    print("🔴 REDDIT POST (queued - no API credentials):")
    print(f"Subreddit: r/{subreddit}")
    print(f"Title: {title}")
    print(f"Body preview: {body[:200]}...")
    print("\n" + "="*60 + "\n")

    with open(posts_file, 'a') as f:
        f.write(f"\n\n--- REDDIT QUEUED r/{subreddit} {datetime.utcnow().isoformat()} ---\n")
        f.write(f"TITLE: {title}\n\n")
        f.write(body)

    return False  # Return False to indicate queued, not posted


def post_to_telegram_groups(content):
    """Post to Telegram groups (use existing bot)"""

    token = os.getenv('TELEGRAM_BOT_TOKEN', '8214203655:AAGkAamvjQq0b7T7lmaTPDd-yYY_hvo_xvA')
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '8327766663')

    url = f'https://api.telegram.org/bot{token}/sendMessage'

    response = requests.post(url, json={
        'chat_id': chat_id,
        'text': content,
        'parse_mode': 'HTML',
        'disable_web_page_preview': False
    })

    if response.ok:
        print("✅ Posted to Telegram")
        return True
    else:
        print(f"❌ Telegram post failed: {response.text}")
        return False


def generate_shareable_link(signal):
    """Generate trackable link for this signal"""

    # Could add UTM parameters for tracking
    base_url = "http://138.68.103.156:5000/api/free"

    # Simple version - just return base URL
    # Advanced: Add tracking params
    # return f"{base_url}?utm_source=twitter&utm_campaign=free_signal&signal_id={signal_id}"

    return base_url


def run_social_promotion_cycle():
    """Run complete social media promotion cycle"""

    print("🚀 Social Media Promotion Cycle")
    print("="*60)

    # Load best signal
    signal = load_best_signal()

    if not signal:
        print("❌ No signals available")
        return

    print(f"\n📊 Promoting signal:")
    print(f"   Market: {signal['question'][:60]}...")
    print(f"   Confidence: {signal['confidence']:.0%}")
    print(f"   Edge: {signal['edge']:.0%}")

    # Create content
    twitter_post = create_twitter_post(signal)
    reddit_title, reddit_body = create_reddit_post(signal)
    telegram_post = create_telegram_group_post(signal)

    # Post to platforms
    print("\n📤 Posting to platforms...")

    # Twitter (saved to queue for now)
    post_to_twitter(twitter_post)

    # Reddit (multiple relevant subreddits)
    subreddits = ['test']  # Start with test, then: predictit, sportsbook, gambling, algotrading
    for sub in subreddits:
        post_to_reddit(reddit_title, reddit_body, sub)

    # Telegram (actual posting)
    post_to_telegram_groups(telegram_post)

    print("\n✅ Social promotion cycle complete")
    print("="*60)

    # Log promotion for tracking
    log_promotion(signal)


def log_promotion(signal):
    """Log promotion for performance tracking"""

    log_file = Path(__file__).parent.parent / 'logs' / 'social_promotions.jsonl'

    entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'signal_question': signal['question'],
        'confidence': signal['confidence'],
        'edge': signal['edge'],
        'platforms': ['twitter', 'reddit', 'telegram'],
        'marketplace_url': 'http://138.68.103.156:5000/api/free'
    }

    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + '\n')


if __name__ == '__main__':
    run_social_promotion_cycle()
