"""Daily Career Radar Email Digest.

Generates and sends a daily email with top career radar matches
and India opportunities. Skips silently if email credentials
are not configured.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.services.career_radar import CareerRadarService


def main():
    service = CareerRadarService()
    top = service.get_top_priority()
    india = service.get_india_feed()

    # Build email body
    body = "🎯 Career Radar — Daily Digest\n\n"
    body += f"High Priority: {top['stats']['high_priority_count']} matches\n"
    body += f"India Feed: {india['stats']['india_count']} matches\n\n"

    body += "━━━ TOP MATCHES ━━━\n\n"
    for i, job in enumerate(top["high_priority"][:10], 1):
        body += f"{i}. ⭐ {job['title']}\n"
        body += f"   🏢 {job['company']} | 📍 {job['location']}\n"
        body += f"   Score: {job['score']} | {job['date_posted']}\n"
        body += f"   🔗 {job['job_url']}\n\n"

    body += "━━━ INDIA OPPORTUNITIES ━━━\n\n"
    for i, job in enumerate(india["india_matches"][:5], 1):
        body += f"{i}. {job['title']}\n"
        body += f"   🏢 {job['company']} | 📍 {job['location']}\n"
        body += f"   Score: {job['score']}\n"
        body += f"   🔗 {job['job_url']}\n\n"

    # Send email
    email_to = os.environ.get("EMAIL_TO")
    email_from = os.environ.get("EMAIL_FROM")
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_password = os.environ.get("SMTP_PASSWORD")

    if not all([email_to, email_from, smtp_server, smtp_password]):
        print("Email credentials not configured. Skipping email.")
        print("Set EMAIL_TO, EMAIL_FROM, SMTP_SERVER, SMTP_PORT, SMTP_PASSWORD secrets.")
        print()
        print(body)
        return

    msg = MIMEMultipart()
    msg["From"] = email_from
    msg["To"] = email_to
    msg["Subject"] = f"🎯 Career Radar — {top['stats']['high_priority_count']} High Priority Matches"
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(email_from, smtp_password)
        server.send_message(msg)

    print(f"Email sent to {email_to} with {top['stats']['high_priority_count']} matches.")


if __name__ == "__main__":
    main()
