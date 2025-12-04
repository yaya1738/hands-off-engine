#!/usr/bin/env python3
"""
Autonomous Job Application Sender
Sends prepared job applications via the hands-off email system
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from email_sender import HandsOffEmailer

# Applications to send
APPLICATIONS = [
    {
        "company": "Pydantic",
        "to": "careers@pydantic.dev",
        "subject": "Solutions Engineer Application - Yair Siegel",
        "body_file": "../applications/pydantic_application_final.txt"
    },
    {
        "company": "CrossnoKaye",
        "to": "careers@crossnokaye.com",
        "subject": "Senior Software Engineer - Python Application",
        "body_file": "../applications/crossnokaye_final.txt"
    }
]


def main():
    """Send all job applications."""
    print("="*60)
    print("AUTONOMOUS JOB APPLICATION SENDER")
    print("Hands-Off System Email")
    print("="*60)
    print()

    try:
        emailer = HandsOffEmailer()
    except ValueError as e:
        print(f"❌ Setup required: {e}")
        print("\nPlease complete email setup first:")
        print("1. Create Gmail account")
        print("2. Enable 2FA and get App Password")
        print("3. Configure .env.handsoff_email")
        return

    results = []
    for app in APPLICATIONS:
        # Read body from file
        body_path = Path(__file__).parent / app['body_file']
        if not body_path.exists():
            print(f"✗ {app['company']}: Body file not found: {app['body_file']}")
            results.append(False)
            continue

        # Remove email header lines if present
        body = body_path.read_text()
        lines = body.split('\n')
        if lines[0].startswith('To:'):
            # Skip header lines
            body = '\n'.join(lines[2:]).strip()

        # Send application
        success = emailer.send_job_application(
            company=app['company'],
            to=app['to'],
            subject=app['subject'],
            body=body
        )
        results.append(success)
        print()

    # Summary
    print("="*60)
    print(f"RESULTS: {sum(results)}/{len(results)} applications sent successfully")
    print("="*60)
    print()

    # Show stats
    stats = emailer.get_stats()
    print(f"Total emails sent ever: {stats['total_sent']}")
    print(f"Last sent: {stats['last_sent']}")


if __name__ == "__main__":
    main()
