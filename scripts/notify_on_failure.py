#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright 2025 Florian Albrechtskirchinger <falbrechtskirchinger@gmail.com>
#
# SPDX-License-Identifier: MIT

import argparse
import json
import os
import smtplib
from email.mime.text import MIMEText

from shared import get_run_id, get_run_jobs, require_gha


def send_email(subject, body):
    email = os.environ.get("NOTIFICATION_EMAIL")
    if not email:
        raise RuntimeError("NOTIFICATION_EMAIL environment variable unset or empty.")

    password = os.environ.get("GMAIL_APP_PASSWORD")
    if not password:
        raise RuntimeError("GMAIL_APP_PASSWORD environment variable unset or empty.")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = email
    msg["To"] = email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(email, password)
        server.send_message(msg)


def main():
    require_gha()

    parser = argparse.ArgumentParser(description="Send notification email on failure.")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Send test email.",
    )
    args = parser.parse_args()

    if args.test:
        send_email("another-brave-overlay: Test email", "This is a test.")
        return

    run_id = get_run_id(from_event=True)
    jobs = get_run_jobs(run_id)

    failed_jobs = [job for job in jobs if job.get("conclusion") == "failure"]
    if failed_jobs:
        print("Sending email for failed jobs")

        lines = [
            f"The following jobs failed in the '{jobs[0]["workflow_name"]}' workflow:",
            "",
        ]
        for job in failed_jobs:
            job_name = job.get("name", "Unknown Job")
            job_url = job.get("html_url", "#")
            lines.append(f"- {job_name}: {job_url}")
        body = "\n".join(lines)

        send_email("another-brave-overlay: GitHub workflow failed", body)


if __name__ == "__main__":
    main()
