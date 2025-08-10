# SPDX-FileCopyrightText: Copyright 2025 Florian Albrechtskirchinger <falbrechtskirchinger@gmail.com>
#
# SPDX-License-Identifier: MIT

import glob
import json
import os
import re

import requests

CHANNELS_WITH_TITLE = [
    ("stable", "Release "),
    ("beta", "Beta "),
    ("nightly", "Nightly "),
]
CHANNELS = [channel for channel, _ in CHANNELS_WITH_TITLE]

GH_API_ACTION_JOBS = "https://api.github.com/repos/{repo}/actions/runs/{run_id}/jobs"


_JOB_NAME_RE = re.compile(r"^Test ebuild \((.+?)\) \[(.+?)\]$")
_VERSION_REGEX = re.compile(r"-\d[\d\.-r]+")  # TODO


def extract_version(path):
    filename = os.path.basename(path)
    assert filename.endswith(".ebuild")

    base_name = filename.rsplit(".ebuild", 1)[0]
    match = _VERSION_REGEX.search(base_name)
    if not match:
        raise ValueError(f"Could not find a valid version in '{filename}'.")

    return match.group(0)[1:]


def version_key(path):
    revision = 0
    version = version_full = extract_version(path)
    if "-r" in version:
        parts = version_full.rsplit("-r", 1)
        version = parts[0]
        revision = int(parts[1])
    return [int(part) for part in version.split(".")] + [revision]


def make_name_from_channel(channel):
    suffix = "" if channel == "stable" else f"-{channel}"
    name = f"brave-browser{suffix}"
    return name, suffix


def get_ebuilds(channel, repo_dir=None, only_latest=False, relative_paths=False):
    repo_dir = repo_dir or os.getcwd()

    name, _ = make_name_from_channel(channel)
    ebuild_dir = os.path.join(repo_dir, f"www-client/{name}")
    ebuilds = sorted(glob.glob(os.path.join(ebuild_dir, "*.ebuild")), key=version_key)

    if only_latest:
        ebuilds = [ebuilds[-1]]

    if relative_paths:
        ebuilds = [os.path.relpath(ebuild, repo_dir) for ebuild in ebuilds]

    return ebuilds, ebuild_dir


def gh_get(url, auth=False, **kwargs):
    headers = {"Accept": "application/vnd.github.v3+json"}
    if auth:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("GITHUB_TOKEN environment variable unset or empty.")
        headers["Authorization"] = f"token {token}"

    response = requests.get(url, headers=headers, **kwargs)
    response.raise_for_status()

    return response


def require_gha():
    if "GITHUB_ACTIONS" not in os.environ:
        raise RuntimeError("Not running in a GitHub Action workflow.")


def get_run_id(from_event=False):
    if from_event:
        event_path = os.environ.get("GITHUB_EVENT_PATH")
        if not event_path:
            raise RuntimeError("GITHUB_EVENT_PATH environment variable unset or empty.")

        with open(event_path, "r") as f:
            event = json.load(f)
            return event["workflow_run"]["id"]
    else:
        run_id = os.environ.get("GITHUB_RUN_ID")
        if not run_id:
            raise RuntimeError("GITHUB_RUN_ID environment variable unset or empty.")
        return run_id


def get_run_jobs(run_id):
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise RuntimeError("GITHUB_REPOSITORY environment variable unset or empty.")

    response = gh_get(GH_API_ACTION_JOBS.format(repo=repo, run_id=run_id), auth=True)
    return response.json()["jobs"]


def set_output(name, value):
    output = os.environ.get("GITHUB_OUTPUT")
    if not output:
        raise RuntimeError("GITHUB_OUTPUT environment variable unset or empty.")

    with open(output, "a") as f:
        f.write(f"{name}<<-EOF\n{value}\n-EOF\n")


def collect_test_results(from_event=False):
    run_id = get_run_id(from_event=from_event)
    jobs = get_run_jobs(run_id)
    test_results = {}
    for job in jobs:
        job_name = job.get("name", "")
        match = _JOB_NAME_RE.match(job_name)
        if match:
            ebuild_path, channel = match.groups()

            test_results[channel] = {
                "conclusion": job.get("conclusion"),
                "ebuild_path": ebuild_path,
                "version": extract_version(ebuild_path),
            }

    return test_results
