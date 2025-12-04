#!/usr/bin/env python3
"""
Job Application Automation Script
Run this to submit applications to job sites.

Usage:
    python3 submit_applications.py [company]

Companies: duckduckgo, pydantic, intuition, beautiful, synres, crossnokaye
"""

import webbrowser
import json
import sys
from pathlib import Path

# Application data
APPLICATIONS = {
    "renaissance": {
        "url": "https://www.renaissancephilanthropy.org/careers",
        "role": "Research Engineer / MLE",
        "salary": "TBD",
        "file": "renaissance_philanthropy_application.md"
    },
    "duckduckgo": {
        "url": "https://jobs.ashbyhq.com/duck-duck-go/senior-backend-engineer",
        "role": "Senior Backend Engineer",
        "salary": "$178,500 + equity",
        "file": "duckduckgo_application.md"
    },
    "pydantic": {
        "url": "https://pydantic.dev/about#join-the-team",
        "role": "Solutions Engineer",
        "salary": "TBD",
        "file": "pydantic_application.md"
    },
    "intuition": {
        "url": "https://apply.workable.com/imachines/",
        "role": "ML Security Engineer",
        "salary": "TBD",
        "file": "intuition_machines_application.md"
    },
    "beautiful": {
        "url": "https://www.beautiful.ai/careers",
        "role": "Senior Engineer",
        "salary": "$160k-250k + equity",
        "file": "beautiful_ai_application.md"
    },
    "synres": {
        "url": "https://synres.ai/careers",
        "role": "Senior Python Engineer - AI LLM Reasoning",
        "salary": "Contract TBD",
        "file": "synres_application.md"
    },
    "crossnokaye": {
        "url": "mailto:careers@crossnokaye.com?subject=Senior%20Software%20Engineer%20-%20Python%20Application",
        "role": "Senior Software Engineer - Python",
        "salary": "TBD",
        "file": "crossnokaye_application.md",
        "method": "email"
    }
}

def print_application(company: str):
    """Print application content for copy/paste."""
    app = APPLICATIONS.get(company.lower())
    if not app:
        print(f"Unknown company: {company}")
        return

    app_file = Path(__file__).parent / app["file"]
    if app_file.exists():
        print(f"\n{'='*60}")
        print(f"APPLICATION: {company.upper()}")
        print(f"Role: {app['role']}")
        print(f"Salary: {app['salary']}")
        print(f"URL: {app['url']}")
        print(f"{'='*60}\n")
        print(app_file.read_text())
    else:
        print(f"Application file not found: {app_file}")

def open_application(company: str):
    """Open application URL in browser."""
    app = APPLICATIONS.get(company.lower())
    if not app:
        print(f"Unknown company: {company}")
        return

    print(f"Opening {company} application page...")
    webbrowser.open(app["url"])
    print_application(company)

def list_applications():
    """List all applications."""
    print("\nREADY TO SUBMIT - 6 APPLICATIONS")
    print("="*60)
    for name, app in APPLICATIONS.items():
        status = "EMAIL" if app.get("method") == "email" else "WEB"
        print(f"  [{status}] {name}: {app['role']} - {app['salary']}")
    print("="*60)
    print("\nUsage: python3 submit_applications.py <company>")
    print("       python3 submit_applications.py all")

def main():
    if len(sys.argv) < 2:
        list_applications()
        return

    company = sys.argv[1].lower()

    if company == "all":
        for name in APPLICATIONS:
            open_application(name)
            print("\n" + "-"*60 + "\n")
    elif company == "list":
        list_applications()
    else:
        open_application(company)

if __name__ == "__main__":
    main()
