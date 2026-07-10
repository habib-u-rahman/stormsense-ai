# Notifier Agent: sends a real email when a Critical or High alert fires
# during an autonomous background run. Chat-triggered runs never send real
# notifications — only the scheduled monitor does (state["autonomous"]),
# so a user just asking a question never spams anyone's inbox.
#
# Recipients come from two places: anyone who self-subscribed via
# POST /api/subscribe (no login — see services/subscribers.py), plus an
# optional single fallback address set directly in .env.

import os
import smtplib
import time
from email.mime.text import MIMEText

from dotenv import load_dotenv

from graph.state import StormSenseState
from services.subscribers import get_subscribers

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO")  # optional fallback recipient

# Avoid re-notifying every autonomous cycle for the same ongoing situation —
# only re-send if the alert message changed, or this many minutes have passed.
NOTIFICATION_COOLDOWN_MINUTES = float(os.getenv("NOTIFICATION_COOLDOWN_MINUTES", "30"))

# Whether we're even *capable* of sending (sender-side credentials) —
# separate from *who* to send to, which comes from subscribers + the
# optional fallback above.
_email_send_capable = all([SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD])

# In-memory dedup state — resets on restart, which is fine for a live demo
_last_sent_message = None
_last_sent_at = 0.0


def _should_notify(alert_message: str) -> bool:
    """Decide whether this alert is worth actually sending, given dedup/cooldown."""
    if alert_message != _last_sent_message:
        return True

    elapsed_minutes = (time.time() - _last_sent_at) / 60
    return elapsed_minutes >= NOTIFICATION_COOLDOWN_MINUTES


def _get_email_recipients() -> list[str]:
    recipients = [s["value"] for s in get_subscribers()]
    if ALERT_EMAIL_TO:
        recipients.append(ALERT_EMAIL_TO)
    return list(dict.fromkeys(recipients))  # de-duplicate, keep order


def send_email(subject: str, body: str, to_address: str) -> bool:
    """Send an email alert via SMTP to one recipient. Returns True on success."""
    try:
        message = MIMEText(body)
        message["Subject"] = subject
        message["From"] = SMTP_USERNAME
        message["To"] = to_address

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, [to_address], message.as_string())

        print(f"[Notifier Agent] Email alert sent to {to_address}.")
        return True
    except Exception as e:
        print(f"[Notifier Agent] Failed to send email to {to_address}: {e}")
        return False


def notifier_agent(state: StormSenseState) -> StormSenseState:
    """Send a real email if this is an autonomous run with an active High/Critical alert."""
    global _last_sent_message, _last_sent_at

    state["notification_sent"] = False

    if not state.get("autonomous"):
        return state  # chat-triggered runs never send real notifications

    if not state.get("alert_triggered") or not state.get("alert_message"):
        return state  # nothing to notify about

    alert_message = state["alert_message"]

    email_recipients = _get_email_recipients() if _email_send_capable else []

    if not email_recipients:
        print("[Notifier Agent] No send capability configured, or no subscribers yet — skipping.")
        return state

    if not _should_notify(alert_message):
        print("[Notifier Agent] Same alert within cooldown window — skipping to avoid spam.")
        return state

    subject = "StormSense AI - Disaster Alert"
    body = f"{alert_message}\n\n{state.get('final_explanation') or ''}".strip()

    sent = False
    for address in email_recipients:
        sent = send_email(subject, body, address) or sent

    if sent:
        _last_sent_message = alert_message
        _last_sent_at = time.time()

    state["notification_sent"] = sent
    return state
