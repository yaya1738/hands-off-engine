"""Read-only compatibility facade for legacy PR email automation.

The former implementation invoked the GitHub CLI, used an embedded credential,
posted comments, and persisted communication state. Those side effects require
the central Factory authority path.
"""
from datetime import datetime, timezone

TRACKED_PRS = [
    {"pr": 239, "repo": "cortexlinux/cortex", "bounty": 125, "issue": 223},
    {"pr": 240, "repo": "cortexlinux/cortex", "bounty": 100, "issue": 222},
    {"pr": 241, "repo": "cortexlinux/cortex", "bounty": 25, "issue": 117},
]


class PREmailBridge:
    def __init__(self):
        self.state = {"last_check": None, "communications": [], "responses_sent": 0, "prs_tracked": len(TRACKED_PRS)}

    def load_state(self):
        return self.state

    def save_state(self):
        return False

    def gh_command(self, cmd):
        return {}

    def get_pr_comments(self, pr_num, repo):
        return []

    def get_unresponded_comments(self, pr_num, repo):
        return []

    def send_pr_comment(self, pr_num, repo, body):
        return False

    def respond_to_review_feedback(self, pr_num, repo, bounty):
        return False

    def generate_coderabbit_response(self, feedback):
        return ""

    def generate_sonar_response(self, feedback):
        return ""

    def generate_maintainer_response(self, comment, author):
        return ""

    def monitor_and_respond(self):
        self.state["last_check"] = datetime.now(timezone.utc).isoformat()
        return 0

    def subscribe_to_pr_notifications(self, pr_num, repo):
        return False

    def continuous_monitor(self, interval=300):
        raise RuntimeError(
            "[FACTORY-AUTHORITY] legacy PR communication is disabled; "
            "submit through FactoryAuthorityGateway"
        )


def main():
    print("[FACTORY-AUTHORITY] legacy PR email bridge is disabled; submit through FactoryAuthorityGateway")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
