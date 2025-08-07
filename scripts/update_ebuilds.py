#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright 2025 Florian Albrechtskirchinger <falbrechtskirchinger@gmail.com>
#
# SPDX-License-Identifier: MIT

import glob
import json
import os
import requests
import subprocess


BRAVE_RELEASES = "https://api.github.com/repos/brave/brave-browser/releases"


def extract_version(path):
    return os.path.basename(path).split("-", 2)[-1].rsplit(".", 1)[0]


# For sorting ebuilds by version
def version_key(path):
    version = extract_version(path)
    return [int(part) for part in version.split(".")]


def get_latest_releases():
    releases = {
        "stable": None,
        "beta": None,
        "nightly": None,
    }
    have_all_releases = lambda: all(x for x in releases.values())

    headers = {"Accept": "application/vnd.github.v3+json"}
    response = requests.get(BRAVE_RELEASES, headers=headers)
    response.raise_for_status()
    for release in response.json():
        for key, name in (
            ("stable", "Release "),
            ("beta", "Beta "),
            ("nightly", "Nightly "),
        ):
            if not releases[key] and release["name"].startswith(name):
                tag = release["tag_name"]
                assert tag[0] == "v"
                releases[key] = tag[1:]

        if have_all_releases():
            break

    if not have_all_releases():
        raise RuntimeError("Could not find latest release for all channels.")

    return releases


def get_new_releases(releases, repo_dir):
    new_releases = dict()
    for key, version in releases.items():
        suffix = "" if key == "stable" else f"-{key}"
        ebuild_path = os.path.join(
            repo_dir, f"www-client/brave-browser{suffix}/brave-browser{suffix}-{version}.ebuild"
        )
        if not os.path.exists(ebuild_path):
            new_releases[key] = releases[key]

    return new_releases


def update_ebuilds(new_releases, repo_dir, commit_changes=False):
    new_ebuilds = dict()
    for key, version in new_releases.items():
        suffix = "" if key == "stable" else f"-{key}"
        ebuild_dir = os.path.join(repo_dir, f"www-client/brave-browser{suffix}")
        ebuilds = sorted(
            glob.glob(os.path.join(ebuild_dir, "*.ebuild")), key=version_key
        )

        if len(ebuilds) == 0:
            raise RuntimeError(f"No ebuilds in '{ebuild_dir}'.")

        added = []
        dropped = []
        for ebuild in ebuilds[:-1]:
            os.unlink(ebuild)
            dropped.append(extract_version(ebuild))

        pkg = f"brave-browser{suffix}"
        new_ebuild = os.path.join(ebuild_dir, "{pkg}-{version}.ebuild")
        os.copy(ebuilds[-1], new_ebuild)

        new_ebuilds[key] = os.path.relpath(new_ebuild, repo_dir)
        added.append(f"{version}")

        if commit_changes:
            message = ", ".join(
                filter(
                    None,
                    [
                        "added: " + ", ".join(added) if added else None,
                        "dropped: " + ", ".join(dropped) if dropped else None,
                    ],
                )
            )

            subprocess.run(["git", "add", ebuild_dir], check=True)
            subprocess.run(
                ["git", "commit", "-m", "www-client/{pkg}: {message}"], check=True
            )


def main():
    repo_dir = os.join(os.dirname(__file__), "..")

    releases = get_latest_releases()
    new_releases = get_new_releases(releases, repo_dir)
    new_ebuilds = update_ebuilds(new_releases, repo_dir)

    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            print(f"new_ebuilds<<<EOF\n{json.dumps(new_ebuilds)}\nEOF\n", file=f)


if __name__ == "__main__":
    main()
