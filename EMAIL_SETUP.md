# Turn on real OTP emails (forgot password)

The forgot-password OTP flow already works. While no mailbox is configured the
code is printed to the `manage.py runserver` terminal instead of being emailed
(it is never shown on the web page). To make codes arrive in a real inbox,
give the project one sending mailbox (3 steps, ~2 minutes):

## 1. Create an app password (your normal password will NOT work)

- **Gmail** — turn on 2-Step Verification, then create an app password:
  <https://myaccount.google.com/apppasswords> (16 characters, shown once)
- **Outlook / Hotmail** — <https://account.microsoft.com/security-settings/>
- **Yahoo** — <https://login.yahoo.com/account/security>

## 2. Run the setup wizard

```
python manage.py setup_email
```

Pick the provider, enter the mailbox address and the app password (hidden
input). It saves `onlinestudy/email_settings_local.py` (gitignored), sends a
test email to that same address, and rolls back automatically if the login
fails.

## 3. Verify an OTP really arrives

```
python manage.py check_email your.address@gmail.com --otp
```

Requires an account registered with that exact email. Check the inbox (and
Spam). If both messages arrive, restart the dev server — the reset page will
no longer show the code on screen; it will be emailed instead.

Useful checks:

- `python manage.py check_email` — report the current configuration only.
- `python manage.py setup_email --check` — same, from the setup wizard.

Notes

- Credentials can also come from environment variables
  (`EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_HOST`, `EMAIL_PORT`).
- If the SMTP send ever fails, the reset page says so instead of pretending
  the code was sent, and any earlier code stays valid.
