#!/usr/bin/env python3
"""
Fully Automated Job Application Submission
No manual intervention required.

Credentials: siegel.yaz@gmail.com / Ysieys20177
"""

import smtplib
import json
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime, timezone
import sys

# Credentials
EMAIL = "siegel.yaz@gmail.com"
PASSWORD = "Ysieys20177"

# Application files
APPS_DIR = Path(__file__).parent
TRACKER_FILE = APPS_DIR / "job_tracker.json"


def send_email_application(to_email, subject, body, from_email=EMAIL, password=PASSWORD):
    """Send application via email (for Pydantic, CrossnoKaye)."""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send via Gmail SMTP
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(from_email, password)
            server.send_message(msg)
            return True, "Email sent successfully"
    except Exception as e:
        return False, str(e)


def submit_pydantic():
    """Submit Pydantic application via email."""
    print("\n[1/7] Submitting Pydantic (92% match)...")

    app_file = APPS_DIR / "pydantic_application.md"
    body = app_file.read_text()

    subject = "Solutions Engineer Application - Yair Siegel"
    to_email = "careers@pydantic.dev"

    success, msg = send_email_application(to_email, subject, body)

    if success:
        print("✅ Pydantic application sent to careers@pydantic.dev")
        return "submitted"
    else:
        print(f"❌ Failed: {msg}")
        return "failed"


def submit_crossnokaye():
    """Submit CrossnoKaye application via email."""
    print("\n[2/7] Submitting CrossnoKaye (90% match)...")

    app_file = APPS_DIR / "crossnokaye_application.md"
    body = app_file.read_text()

    subject = "Senior Software Engineer - Python Application"
    to_email = "careers@crossnokaye.com"

    success, msg = send_email_application(to_email, subject, body)

    if success:
        print("✅ CrossnoKaye application sent to careers@crossnokaye.com")
        return "submitted"
    else:
        print(f"❌ Failed: {msg}")
        return "failed"


def submit_synres_automated():
    """
    SynRes requires web form submission.
    Would need browser automation (Selenium/Playwright).
    """
    print("\n[3/7] SynRes (95% match) - Web form...")
    print("ℹ️  Requires web form automation (JotForm)")
    print("    URL: https://form.jotform.com/253356690270156")
    print("    CRITICAL: Must include 'EXCELED' keyword")
    return "requires_browser"


def submit_renaissance_automated():
    """Renaissance requires web form."""
    print("\n[4/7] Renaissance (91% match) - Web form...")
    print("ℹ️  Requires web form automation")
    print("    URL: https://web.miniextensions.com/JMaVfmSS6p3XZLecqZfJ")
    return "requires_browser"


def submit_duckduckgo_automated():
    """DuckDuckGo requires web portal."""
    print("\n[5/7] DuckDuckGo (88% match) - Web portal...")
    print("ℹ️  Requires web portal automation (Ashby)")
    print("    URL: https://jobs.ashbyhq.com/duck-duck-go")
    return "requires_browser"


def submit_intuition_automated():
    """Intuition requires web portal."""
    print("\n[6/7] Intuition Machines (87% match) - Web portal...")
    print("ℹ️  Requires web portal automation (Workable)")
    print("    URL: https://apply.workable.com/imachines/")
    return "requires_browser"


def submit_beautiful_automated():
    """Beautiful.ai requires web form."""
    print("\n[7/7] Beautiful.ai (85% match) - Web form...")
    print("ℹ️  Requires web portal automation")
    print("    URL: https://www.beautiful.ai/careers")
    return "requires_browser"


def update_tracker(company, status):
    """Update job tracker with submission status."""
    try:
        tracker = json.loads(TRACKER_FILE.read_text())

        for opp in tracker['opportunities']:
            if opp['company'].lower() == company.lower():
                opp['status'] = status
                if status == 'submitted':
                    opp['submitted_date'] = datetime.now().isoformat()[:10]

        TRACKER_FILE.write_text(json.dumps(tracker, indent=2))
    except Exception as e:
        print(f"Warning: Could not update tracker: {e}")


def main():
    """Run automated submission."""
    print("=" * 80)
    print("AUTOMATED JOB APPLICATION SUBMISSION")
    print("=" * 80)
    print(f"Email: {EMAIL}")
    print(f"Applications: 7 total (2 email, 5 web form)")
    print()
    print("Starting automated submission...")
    print()

    results = {}

    # Email applications (can be fully automated)
    status = submit_pydantic()
    results['Pydantic'] = status
    update_tracker('Pydantic', status)
    time.sleep(2)

    status = submit_crossnokaye()
    results['CrossnoKaye'] = status
    update_tracker('CrossnoKaye', status)
    time.sleep(2)

    # Web form applications (need browser automation)
    status = submit_synres_automated()
    results['SynRes'] = status

    status = submit_renaissance_automated()
    results['Renaissance Philanthropy'] = status

    status = submit_duckduckgo_automated()
    results['DuckDuckGo'] = status

    status = submit_intuition_automated()
    results['Intuition Machines'] = status

    status = submit_beautiful_automated()
    results['Beautiful.ai'] = status

    # Summary
    print()
    print("=" * 80)
    print("SUBMISSION SUMMARY")
    print("=" * 80)

    submitted = sum(1 for v in results.values() if v == 'submitted')
    failed = sum(1 for v in results.values() if v == 'failed')
    requires_browser = sum(1 for v in results.values() if v == 'requires_browser')

    print(f"✅ Submitted: {submitted}/7")
    print(f"❌ Failed: {failed}/7")
    print(f"🌐 Requires browser: {requires_browser}/7")
    print()

    for company, status in results.items():
        icon = "✅" if status == "submitted" else "🌐" if status == "requires_browser" else "❌"
        print(f"  {icon} {company}: {status}")

    print()
    print("=" * 80)
    print("NEXT STEPS")
    print("=" * 80)

    if requires_browser > 0:
        print(f"\n{requires_browser} applications require web form automation:")
        print("These need browser automation (Selenium/Playwright) to handle:")
        print("  - Form field population")
        print("  - CAPTCHAs (if present)")
        print("  - File uploads (resume)")
        print("  - Multi-step forms")
        print()
        print("Options:")
        print("  1. Create Selenium/Playwright automation script")
        print("  2. Use the quick_submit.sh script for guided submission")
        print("  3. Submit manually following AUTO_SUBMIT_INSTRUCTIONS.md")

    if submitted > 0:
        print(f"\n✅ {submitted} email applications sent successfully!")
        print("Check siegel.yaz@gmail.com for confirmations (1-3 days)")

    print()


if __name__ == "__main__":
    main()
