#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright 2025 Florian Albrechtskirchinger <falbrechtskirchinger@gmail.com>
#
# SPDX-License-Identifier: MIT

import argparse
import json
import os
import subprocess

from shared import (
    CHANNELS,
    collect_test_results,
    extract_version,
    get_ebuilds,
    make_name_from_channel,
    require_gha,
    set_output,
    version_key,
)


def build_test_matrix(mode, commits=None):
    matrix = []
    if mode == "latest-ebuilds":
        for channel in CHANNELS:
            ebuilds, _ = get_ebuilds(channel, only_latest=True, relative_paths=True)
            if len(ebuilds) == 0:
                raise RuntimeError(f"No ebuilds found for channel '{channel}'.")

            latest_version = extract_version(ebuilds[0])
            matrix.append(
                {
                    "channel": channel,
                    "version": latest_version,
                    "ebuild_path": ebuilds[0],
                }
            )
    elif mode == "new-ebuilds":
        assert len(commits) == 2
        result = subprocess.run(
            [
                "git",
                "diff-tree",
                "--diff-filter=A",
                "--no-commit-id",
                "--name-only",
                "-r",
                *commits,
                "--",
                "www-client/",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        new_ebuilds = [
            ebuild
            for ebuild in result.stdout.splitlines()
            if ebuild.endswith(".ebuild")
        ]
        new_ebuilds.sort(
            key=lambda ebuild: [os.path.dirname(ebuild)] + version_key(ebuild)
        )
        name_to_channel = {
            f"www-client/{make_name_from_channel(channel)[0]}/": channel
            for channel in CHANNELS
        }

        for ebuild in new_ebuilds:
            channel = name_to_channel[os.path.dirname(ebuild)]
            entry = matrix.append(
                {
                    "channel": channel,
                    "ebuild_path": ebuild,
                    "version": extract_version(ebuild),
                }
            )
    else:
        raise ValueError(f"Invalid mode '{mode}'.")

    return matrix


def main():
    parser = argparse.ArgumentParser(
        description="GitHub action functions for ebuild testing."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--build-test-matrix",
        action="store_true",
        help="Build the matrix of ebuilds to test.",
    )
    group.add_argument(
        "--collect-test-results",
        action="store_true",
        help="Collect the test results.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--latest-ebuilds",
        action="store_true",
        help="Use the latest ebuild for each channel.",
    )
    mode.add_argument(
        "--new-ebuilds",
        nargs=2,
        metavar=("COMMIT1", "COMMIT2"),
        help="Only include newly added ebuilds between <COMMIT1> and <COMMIT2>. Limited to one ebuild per channel and assumed to be latest.",
    )
    parser.add_argument(
        "--from-event",
        action="store_true",
        help="Obtain run ID from workflow_run event.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output.",
    )
    args = parser.parse_args()

    require_gha()

    if args.build_test_matrix:
        mode = "new-ebuilds" if args.new_ebuilds else "latest-ebuilds"
        test_matrix = build_test_matrix(mode, commits=args.new_ebuilds or None)
        set_output("test_matrix", json.dumps(test_matrix))
        if args.verbose:
            print(json.dumps(test_matrix, indent=2))


    if args.collect_test_results:
        test_results = collect_test_results(from_event=args.from_event)
        set_output("test_results", json.dumps(test_results))
        if args.verbose:
            print(json.dumps(test_results, indent=2))


if __name__ == "__main__":
    main()
