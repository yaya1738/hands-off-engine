#!/bin/bash
# Quick Submit - Job Applications
# Opens each application URL and shows content to copy/paste

echo "=============================================="
echo "JOB APPLICATION QUICK SUBMIT"
echo "=============================================="
echo ""
echo "Your credentials:"
echo "Email: siegel.yaz@gmail.com"
echo "Password: Ysieys20177"
echo ""
echo "Starting with TOP 3 (highest match)..."
echo ""

# 1. SynRes (95% match) - HIGHEST PRIORITY
echo "=============================================="
echo "1. SYNRES - Senior Python Engineer (95% match)"
echo "=============================================="
echo "URL: https://form.jotform.com/253356690270156"
echo ""
echo "CRITICAL: Include word 'EXCELED' in submission"
echo ""
echo "Application content:"
echo "--------------------"
cat synres_application.md
echo ""
echo "Press ENTER to open form in browser..."
read
xdg-open "https://form.jotform.com/253356690270156" 2>/dev/null || open "https://form.jotform.com/253356690270156" 2>/dev/null
echo ""
echo "✓ Form opened. Fill and submit, then press ENTER to continue..."
read

# 2. Pydantic (92% match)
echo ""
echo "=============================================="
echo "2. PYDANTIC - Solutions Engineer (92% match)"
echo "=============================================="
echo "Method: Email to careers@pydantic.dev"
echo ""
echo "Subject: Solutions Engineer Application - Yair Siegel"
echo ""
echo "Application content:"
echo "--------------------"
cat pydantic_application.md
echo ""
echo "Copy the above content and email to: careers@pydantic.dev"
echo "Press ENTER when sent..."
read

# 3. Renaissance (91% match)
echo ""
echo "=============================================="
echo "3. RENAISSANCE - Research Engineer/MLE (91%)"
echo "=============================================="
echo "URL: https://web.miniextensions.com/JMaVfmSS6p3XZLecqZfJ"
echo ""
echo "Application content:"
echo "--------------------"
cat renaissance_philanthropy_application.md
echo ""
echo "Press ENTER to open form in browser..."
read
xdg-open "https://web.miniextensions.com/JMaVfmSS6p3XZLecqZfJ" 2>/dev/null || open "https://web.miniextensions.com/JMaVfmSS6p3XZLecqZfJ" 2>/dev/null
echo ""
echo "✓ Form opened. Fill and submit, then press ENTER to continue..."
read

echo ""
echo "=============================================="
echo "TOP 3 COMPLETE! ✓"
echo "=============================================="
echo ""
echo "Continue with remaining 4 applications? (y/n)"
read answer

if [ "$answer" = "y" ]; then
    # 4. CrossnoKaye (90%)
    echo ""
    echo "4. CROSSNOKAYE - Senior Software Engineer (90%)"
    echo "Email to: careers@crossnokaye.com"
    echo "Subject: Senior Software Engineer - Python Application"
    cat crossnokaye_application.md
    echo ""
    echo "Press ENTER when sent..."
    read

    # 5. DuckDuckGo (88%)
    echo ""
    echo "5. DUCKDUCKGO - Senior Backend Engineer (88%)"
    echo "URL: https://jobs.ashbyhq.com/duck-duck-go"
    cat duckduckgo_application.md
    echo ""
    read
    xdg-open "https://jobs.ashbyhq.com/duck-duck-go" 2>/dev/null || open "https://jobs.ashbyhq.com/duck-duck-go" 2>/dev/null
    echo "Press ENTER when submitted..."
    read

    # 6. Intuition (87%)
    echo ""
    echo "6. INTUITION MACHINES - ML Security Engineer (87%)"
    echo "URL: https://apply.workable.com/imachines/"
    cat intuition_machines_application.md
    echo ""
    read
    xdg-open "https://apply.workable.com/imachines/" 2>/dev/null || open "https://apply.workable.com/imachines/" 2>/dev/null
    echo "Press ENTER when submitted..."
    read

    # 7. Beautiful.ai (85%)
    echo ""
    echo "7. BEAUTIFUL.AI - Senior Engineer (85%)"
    echo "URL: https://www.beautiful.ai/careers"
    cat beautiful_ai_application.md
    echo ""
    read
    xdg-open "https://www.beautiful.ai/careers" 2>/dev/null || open "https://www.beautiful.ai/careers" 2>/dev/null
    echo "Press ENTER when submitted..."
    read
fi

echo ""
echo "=============================================="
echo "ALL APPLICATIONS COMPLETE! 🎉"
echo "=============================================="
echo ""
echo "Next steps:"
echo "1. Check email for confirmations"
echo "2. Follow up in 1 week if no response"
echo "3. Monitor siegel.yaz@gmail.com for interview requests"
echo ""
echo "Expected timeline: 2-8 weeks for responses"
echo "Expected outcome: 30% chance of at least 1 interview"
echo ""
