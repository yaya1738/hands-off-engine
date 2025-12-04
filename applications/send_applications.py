#!/usr/bin/env python3
"""
Send job applications via Gmail SMTP
Usage: python3 send_applications.py
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Gmail credentials
GMAIL_USER = "siegel.yaz@gmail.com"
GMAIL_PASS = "Ysieys20177"

# Applications to send
APPLICATIONS = [
    {
        "to": "careers@pydantic.dev",
        "subject": "Solutions Engineer Application - Yair Siegel",
        "body_file": "pydantic_application_final.txt",
        "company": "Pydantic"
    },
    {
        "to": "careers@crossnokaye.com",
        "subject": "Senior Software Engineer - Python Application",
        "body_file": "crossnokaye_final.txt",
        "company": "CrossnoKaye"
    }
]

def send_email(to, subject, body, company):
    """Send email via Gmail SMTP."""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Connect to Gmail SMTP
        print(f"Connecting to Gmail SMTP for {company}...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()

        print(f"Logging in...")
        server.login(GMAIL_USER, GMAIL_PASS)

        print(f"Sending email to {to}...")
        server.send_message(msg)
        server.quit()

        print(f"✓ {company} application sent successfully!")
        return True

    except smtplib.SMTPAuthenticationError:
        print(f"✗ Authentication failed for {company}")
        print("  Gmail may require an 'App Password' instead of your regular password.")
        print("  Visit: https://myaccount.google.com/apppasswords")
        return False

    except Exception as e:
        print(f"✗ Failed to send {company} application: {e}")
        return False

def main():
    print("="*60)
    print("JOB APPLICATION EMAIL SENDER")
    print("="*60)
    print()

    results = []

    for app in APPLICATIONS:
        # Read body from file
        body_path = Path(__file__).parent / app['body_file']
        if not body_path.exists():
            print(f"✗ {app['company']}: Body file not found: {app['body_file']}")
            results.append(False)
            continue

        body = body_path.read_text()

        # Send email
        success = send_email(
            to=app['to'],
            subject=app['subject'],
            body=body,
            company=app['company']
        )
        results.append(success)
        print()

    # Summary
    print("="*60)
    print(f"SUMMARY: {sum(results)}/{len(results)} emails sent successfully")
    print("="*60)

    if not all(results):
        print()
        print("NOTE: If authentication failed, you need a Gmail App Password:")
        print("1. Go to https://myaccount.google.com/apppasswords")
        print("2. Generate an app password for 'Mail'")
        print("3. Update GMAIL_PASS in this script with the app password")
        print("4. Run script again")

if __name__ == "__main__":
    main()
