# Hands-Off System Email Setup Guide

**Goal:** Create dedicated email account for autonomous job applications and income generation.

---

## Step 1: Create Gmail Account (5 minutes)

1. **Go to:** https://accounts.google.com/signup

2. **Fill in:**
   - First name: `Yair` or `Hands-Off`
   - Last name: `Siegel` or `System`
   - Username: Pick one:
     - `handsoff.yair@gmail.com` ⭐ RECOMMENDED
     - `yair.handsoff@gmail.com`
     - `yairsiegel.income@gmail.com`
     - `yair.income.engine@gmail.com`
   - Password: Generate strong password (save it!)

3. **Important:**
   - Recovery email: `siegel.yaz@gmail.com`
   - Skip phone if possible
   - Accept terms

4. **Save credentials immediately!**

---

## Step 2: Enable 2FA and Get App Password (3 minutes)

1. **Go to Gmail Security:** https://myaccount.google.com/security

2. **Enable 2-Factor Authentication:**
   - Click "2-Step Verification"
   - Follow prompts (use your phone)
   - Complete setup

3. **Generate App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Name it: "Hands-Off System"
   - Click "Generate"
   - **Copy the 16-character password** (looks like: `abcd efgh ijkl mnop`)

4. **Important:** Save this app password - you can't see it again!

---

## Step 3: Configure System (1 minute)

1. **Edit credentials file:**
   ```bash
   nano /root/hands-off-engine/.env.handsoff_email
   ```

2. **Fill in:**
   ```bash
   HANDSOFF_EMAIL="handsoff.yair@gmail.com"
   HANDSOFF_PASSWORD="your-regular-password"
   HANDSOFF_APP_PASSWORD="abcd efgh ijkl mnop"
   ```

3. **Save and exit:** `Ctrl+X`, `Y`, `Enter`

---

## Step 4: Test Email System (30 seconds)

```bash
cd /root/hands-off-engine/autonomous
python3 email_sender.py
```

**Expected output:**
```
Email system ready!
Total emails sent: 0
Last sent: Never
```

---

## Step 5: Send Job Applications! (Automatic)

```bash
cd /root/hands-off-engine/autonomous
python3 send_job_applications.py
```

**This will automatically send:**
- ✉️ Pydantic application
- ✉️ CrossnoKaye application

**No manual copying needed!**

---

## What Happens Next

### Autonomous Features:
1. **Job applications sent** from dedicated email
2. **Responses go to** handsoff.yair@gmail.com
3. **System can monitor** inbox for replies
4. **Auto-forward** important emails to siegel.yaz@gmail.com
5. **Track all** application status automatically

### Email Uses:
- Job applications
- Freelance proposals
- Client communications
- Bounty submissions
- Partnership inquiries
- Income opportunity tracking

---

## Security Notes

✓ Dedicated email keeps income work separate
✓ App Password prevents main account exposure
✓ Recovery email ensures you never lose access
✓ Credentials in `.env.handsoff_email` (not committed to git)
✓ Can revoke App Password anytime without affecting main account

---

## Quick Reference

| File | Purpose |
|------|---------|
| `.env.handsoff_email` | Email credentials (secret) |
| `autonomous/email_sender.py` | Core email sending system |
| `autonomous/send_job_applications.py` | Auto-send job apps |
| `state/email_state.json` | Tracks sent emails |

---

## Troubleshooting

**"Authentication failed"**
- Make sure you're using APP PASSWORD, not regular password
- Check 2FA is enabled
- Regenerate app password if needed

**"Connection timeout"**
- Check internet connection
- Gmail SMTP might be temporarily down
- Try again in a few minutes

**"Credentials not found"**
- Make sure `.env.handsoff_email` is filled out
- Check file path is correct
- Verify no typos in variable names

---

**Total Setup Time: ~10 minutes**
**Then: Fully autonomous job application sending! 🚀**
