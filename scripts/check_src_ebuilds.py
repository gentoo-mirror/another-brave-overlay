#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright 2025 Florian Albrechtskirchinger <falbrechtskirchinger@gmail.com>
#
# SPDX-License-Identifier: MIT

import argparse
import difflib
import os
import sys

from shared import (
    BRAVE_TO_CHROME_CHANNELS,
    CHANNELS,
    GENTOO_REPO,
    get_ebuilds,
    require_gha,
)


def check_for_divergence(repo_dir=None):
    repo_dir = repo_dir or os.getcwd()
    src_dir = os.path.join(repo_dir, "src_ebuilds")

    results = {}
    for channel in CHANNELS:
        src_ebuild = get_ebuilds(
            BRAVE_TO_CHROME_CHANNELS[channel],
            repo_dir=src_dir,
            base_name="google-chrome",
            only_latest=True,
        )[0][0]
        gentoo_ebuild = get_ebuilds(
            BRAVE_TO_CHROME_CHANNELS[channel],
            repo_dir=GENTOO_REPO,
            base_name="google-chrome",
            only_latest=True,
        )[0][0]
        src_ebuild_rel = os.path.relpath(src_ebuild, src_dir)
        gentoo_ebuild_rel = os.path.relpath(gentoo_ebuild, GENTOO_REPO)
        result = {
            "channel": channel,
            "src_ebuild": src_ebuild_rel,
            "gentoo_ebuild": gentoo_ebuild_rel,
        }

        with open(src_ebuild, "r") as f1, open(gentoo_ebuild, "r") as f2:
            s1 = f1.read().splitlines()
            s2 = f2.read().splitlines()
            if s1 != s2:
                diff = difflib.unified_diff(
                    s1,
                    s2,
                    fromfile=src_ebuild_rel,
                    tofile=gentoo_ebuild_rel,
                    lineterm="",
                )
                result["diff"] = list(diff)
                results[channel] = result
    return results


def write_step_summary(title, results=None):
    require_gha()

    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_file:
        raise RuntimeError("GITHUB_STEP_SUMMARY environment variable unset or empty.")

    with open(summary_file, "a") as f:
        f.write(f"### {title}\n\n")
        if results:
            for channel in CHANNELS:  # Iterate results in channel order
                if channel not in results:
                    continue
                f.write(f"- **{channel.capitalize()}** ebuild has diverged:\n\n")
                f.write("    ```diff\n")
                for line in results[channel]["diff"]:
                    f.write(f"    {line}\n")
                f.write("    ```\n\n")


def main():
    parser = argparse.ArgumentParser(
        description="Check source ebuilds for divergence from Gentoo Google Chrome ebuilds."
    )
    parser.add_argument(
        "--step-summary",
        action="store_true",
        help="Write a GitHub step summary.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output.",
    )
    args = parser.parse_args()

    repo_dir = os.path.join(os.path.dirname(__file__), "..")
    results = check_for_divergence(repo_dir=repo_dir)
    if results:
        print("⚠️ Ebuilds have diverged:")

        if args.verbose:
            for channel in CHANNELS:
                if channel not in results:
                    continue
                print()
                print(f"- {channel.capitalize()} ebuild has diverged:")
                for line in results[channel]["diff"]:
                    print(f"{line}")
                print()

        if args.step_summary:
            write_step_summary("⚠️ Ebuilds have diverged:", results)

        sys.exit(1)
    else:
        print("✅ Ebuilds are in sync!")

        if args.step_summary:
            write_step_summary("✅ Ebuilds are in sync!")


if __name__ == "__main__":
    main()
