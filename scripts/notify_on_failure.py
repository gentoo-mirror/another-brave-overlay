#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright 2025 Florian Albrechtskirchinger <falbrechtskirchinger@gmail.com>
#
# SPDX-License-Identifier: MIT

import json
import os
import smtplib
from email.mime.text import MIMEText

import requests


def main():
    headers = {
        "Authorization": f"token {os.environ['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github.v3+json",
    }
    run_id = os.environ["GITHUB_RUN_ID"]
    repo = os.environ["GITHUB_REPOSITORY"]
    response = requests.get(
        f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/jobs",
        headers=headers,
    )
    jobs = response.json()["jobs"]

    print(f"jobs {jobs}")

    failed_jobs = [job for job in jobs if job.get("conclusion") == "failure"]
    if failed_jobs:
        print("Sending email for failed jobs")

        lines = ["The following jobs failed in the '🚀 Update Ebuilds' workflow:", ""]
        for job in failed_jobs:
            job_name = job.get("name", "Unknown Job")
            job_url = job.get("html_url", "#")
            lines.append(f"- {job_name}: {job_url}")
        body = "\n".join(lines)

        password = os.environ["GMAIL_APP_PASSWORD"]
        email = "falbrechtskirchinger@gmail.com"

        msg = MIMEText(body)
        msg["Subject"] = "another-brave-overlay: GitHub workflow failed"
        msg["From"] = email
        msg["To"] = email

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email, password)
            server.send_message(msg)


if __name__ == "__main__":
    main()
