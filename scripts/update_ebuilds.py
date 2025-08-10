#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright 2025 Florian Albrechtskirchinger <falbrechtskirchinger@gmail.com>
#
# SPDX-License-Identifier: MIT

import argparse
import glob
import hashlib
import os
import shutil
import subprocess

import requests
from shared import (
    CHANNELS,
    CHANNELS_WITH_TITLE,
    collect_test_results,
    extract_version,
    get_ebuilds,
    gh_get,
    make_name_from_channel,
    require_gha,
)

BRAVE_RELEASES = "https://api.github.com/repos/brave/brave-browser/releases"
BRAVE_SOURCE_FILE = "{name}_{version}_amd64.deb"
BRAVE_SOURCE_URL = f"https://github.com/brave/brave-browser/releases/download/v{{version}}/{BRAVE_SOURCE_FILE}"
EBUILD_FILE = "{name}-{version}.ebuild"
EBUILD_FILE_PATH = f"www-client/{{name}}/{EBUILD_FILE}"
MANIFEST_HASH_ALGOS = ("BLAKE2B", "SHA512")


def get_latest_releases():
    releases = {channel: None for channel, _ in CHANNELS_WITH_TITLE}
    releases_found = 0
    page = 0
    MAX_PAGES = 5
    url = BRAVE_RELEASES
    while url and page < MAX_PAGES:
        response = gh_get(url)
        for release in response.json():
            for channel, title in CHANNELS_WITH_TITLE:
                name, _ = make_name_from_channel(channel)
                if not releases[channel] and release["name"].startswith(title):
                    tag = release["tag_name"]
                    assert tag[0] == "v"
                    version = tag[1:]

                    source_file = BRAVE_SOURCE_FILE.format(name=name, version=version)
                    asset_files = {asset["name"] for asset in release["assets"]}
                    if source_file in asset_files:
                        releases[channel] = tag[1:]
                        releases_found += 1

            if releases_found == len(releases):
                break

        if releases_found == len(releases):
            break

        url = response.links.get("next", {}).get("url")
        page += 1

    if not releases_found == len(releases):
        raise RuntimeError("Could not find latest release for all channels.")

    return releases


def get_new_releases(releases, repo_dir=None):
    new_releases = dict()
    for channel, version in releases.items():
        ebuilds, _ = get_ebuilds(channel, repo_dir=repo_dir)
        ebuild_versions = {extract_version(ebuild) for ebuild in ebuilds}
        if not version in ebuild_versions:
            new_releases[channel] = version

    return new_releases


def update_manifest(ebuild_dir, name):
    ebuilds = glob.glob(os.path.join(ebuild_dir, "*.ebuild"))
    versions = set(extract_version(ebuild) for ebuild in ebuilds)
    versions_in_manifest = set()
    sources = [
        {
            "file": BRAVE_SOURCE_FILE.format(name=name, version=version),
            "url": BRAVE_SOURCE_URL.format(name=name, version=version),
            "version": version,
        }
        for version in versions
    ]
    sources_by_filename = {source["file"]: source for source in sources}
    sources_by_version = {source["version"]: source for source in sources}
    with open(os.path.join(ebuild_dir, "Manifest"), "r") as f:
        lines = f.readlines()
        new_lines = []
        for line in lines:
            parts = line.split(" ")
            if parts[0] == "DIST":
                if parts[1] in sources_by_filename:
                    # Keep DIST lines for current ebuilds
                    new_lines.append(line)
                    versions_in_manifest.add(sources_by_filename[parts[1]]["version"])
            else:
                new_lines.append(line)

    # Add DIST lines for new ebuilds
    for version in versions - versions_in_manifest:
        source = sources_by_version[version]
        hashers = {algo: hashlib.new(algo.lower()) for algo in MANIFEST_HASH_ALGOS}
        size = 0
        with requests.get(source["url"], stream=True, timeout=300) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=8192):
                size += len(chunk)
                for hasher in hashers.values():
                    hasher.update(chunk)

        digests = {algo: hasher.hexdigest() for algo, hasher in hashers.items()}
        new_lines.append(
            f"DIST {source['file']} {size} {' '.join([f'{algo} {digest}' for algo, digest in digests.items()])}\n"
        )

    with open(os.path.join(ebuild_dir, "Manifest"), "w") as f:
        f.writelines(new_lines)


def add_ebuilds_for_new_releases(new_releases, repo_dir, commit_changes=False):
    new_ebuilds = dict()
    for channel, version in new_releases.items():
        name, _ = make_name_from_channel(channel)

        ebuilds, ebuild_dir = get_ebuilds(channel, repo_dir=repo_dir, only_latest=True)
        if len(ebuilds) == 0:
            raise RuntimeError(f"No ebuilds for release channel '{channel}'.")
        latest_ebuild = ebuilds[0]
        new_ebuild = os.path.join(
            ebuild_dir, EBUILD_FILE.format(name=name, version=version)
        )

        shutil.copy(latest_ebuild, new_ebuild)
        update_manifest(ebuild_dir, name)
        new_ebuilds.setdefault(channel, []).append(version)

        if commit_changes:
            subprocess.run(
                ["git", "add", new_ebuild, os.path.join(ebuild_dir, "Manifest")],
                check=True,
            )
            subprocess.run(
                ["git", "commit", "-m", f"www-client/{name}: added {version}"],
                check=True,
            )

    return new_ebuilds


def update_ebuilds(repo_dir=None, commit_changes=False):
    repo_dir = repo_dir or os.getcwd()

    releases = get_latest_releases()
    new_releases = get_new_releases(releases, repo_dir)
    return add_ebuilds_for_new_releases(
        new_releases, repo_dir, commit_changes=commit_changes
    )


def prune_ebuilds(repo_dir=None, commit_changes=False, successful_channels_only=False):
    repo_dir = repo_dir or os.getcwd()

    pruned_ebuilds = dict()

    if successful_channels_only:
        test_results = collect_test_results(from_event=False)
        channels = [
            channel
            for channel, result in test_results.items()
            if result["conclusion"] == "success"
        ]
    else:
        channels = CHANNELS

    for channel in channels:
        name, _ = make_name_from_channel(channel)
        ebuilds, ebuild_dir = get_ebuilds(channel, repo_dir=repo_dir)

        if len(ebuilds) > 1:
            dropped = []
            for ebuild in ebuilds[:-1]:
                if commit_changes:
                    subprocess.run(["git", "rm", ebuild], check=True)
                else:
                    os.unlink(ebuild)
                version = extract_version(ebuild)
                dropped.append(version)
                pruned_ebuilds.setdefault(channel, []).append(version)

            update_manifest(ebuild_dir, name)

            if commit_changes:
                subprocess.run(
                    ["git", "add", os.path.join(ebuild_dir, "Manifest")], check=True
                )
                subprocess.run(
                    [
                        "git",
                        "commit",
                        "-m",
                        f"www-client/{name}: dropped {', '.join(dropped)}",
                    ],
                    check=True,
                )

    return pruned_ebuilds


def write_step_summary(new_ebuilds, pruned_ebuilds):
    require_gha()

    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_file:
        raise RuntimeError("GITHUB_STEP_SUMMARY environment variable unset or empty.")

    with open(summary_file, "a") as f:
        if new_ebuilds:
            f.write("### ✨ New ebuilds were added:\n\n")
            for channel in CHANNELS:  # Iterate new ebuilds in channel order
                if not channel in new_ebuilds:
                    continue
                name, _ = make_name_from_channel(channel)
                for version in new_ebuilds[channel]:
                    f.write(
                        f"- **{channel.capitalize()}**: `www-client/{name}-{version}`\n"
                    )
            f.write("\n")

        if pruned_ebuilds:
            f.write("### 🧹 Old ebuilds were removed:\n\n")
            for channel in CHANNELS:  # Iterate pruned ebuilds in channel order
                if not channel in pruned_ebuilds:
                    continue
                name, _ = make_name_from_channel(channel)
                for version in pruned_ebuilds[channel]:
                    f.write(
                        f"- **{channel.capitalize()}**: `www-client/{name}-{version}`\n"
                    )
            f.write("\n")


def main():
    parser = argparse.ArgumentParser(
        description="Update ebuilds for Brave browser releases."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--update",
        action="store_true",
        help="Check for new releases and update ebuilds.",
    )
    group.add_argument(
        "--prune",
        action="store_true",
        help="Prune old ebuilds.",
    )
    parser.add_argument(
        "--prune-checked",
        action="store_true",
        help="Prune only if channel was tested successfully.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Commit changes to the repository.",
    )
    parser.add_argument(
        "--step-summary",
        action="store_true",
        help="Write a GitHub step summary.",
    )
    args = parser.parse_args()

    new_ebuilds = None
    pruned_ebuilds = None
    repo_dir = os.path.join(os.path.dirname(__file__), "..")

    if args.update:
        new_ebuilds = update_ebuilds(repo_dir=repo_dir, commit_changes=args.commit)

    if args.prune:
        pruned_ebuilds = prune_ebuilds(
            repo_dir=repo_dir,
            commit_changes=True,
            successful_channels_only=args.prune_checked,
        )

    if args.step_summary:
        write_step_summary(new_ebuilds, pruned_ebuilds)


if __name__ == "__main__":
    main()
