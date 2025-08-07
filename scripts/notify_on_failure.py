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
    new_ebuilds = json.loads(os.environ("NEW_EBUILDS"))

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

    failed_jobs = []
    for job in jobs:
        print(f"job name {job['name']}")
        if job["conclusion"] == "failure":
            if job["name"] == "update-ebuilds":
                failed_jobs.append("Update ebuilds")
            elif job["name"].startswith("test-ebuild"):
                matrix_key = job["name"].split("(")[-1].split(")")[0].strip()
                failed_jobs.append(
                    f"Test ebuild ({new_ebuilds.get(matrix_key, 'unknown')})"
                )
    if failed_jobs:
        print("Sending email for failed jobs")

        password = os.getenv("GMAIL_APP_PASSWORD")
        email = "falbrechtskirchinger@gmail.com"

        msg = MIMEText(
            "The following workflow jobs have failed:\n\n"
            + "\n".join([f"  * {job}" for job in failed_jobs])
        )
        msg["Subject"] = "another-brave-overlay: GitHub workflow failed"
        msg["From"] = email
        msg["To"] = email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(email, password)
        server.send_message(msg)


if __name__ == "__main__":
    main()
