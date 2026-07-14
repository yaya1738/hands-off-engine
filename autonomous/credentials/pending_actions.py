"""
Generate required human actions for missing credentials.
"""

from autonomous.integrations.providers.gmail_oauth import GmailOAuth


def collect_actions():
    actions = []

    gmail = GmailOAuth().status()

    if not gmail.get("token_present"):
        actions.append({
            "integration": "gmail",
            "status": "blocked",
            "reason": "oauth_setup_required",
            "action": "complete_google_oauth_setup"
        })

    return actions


if __name__ == "__main__":
    import json
    print(json.dumps(collect_actions(), indent=2))
