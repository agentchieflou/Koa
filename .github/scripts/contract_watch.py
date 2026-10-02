"""Report whether this-next-please has published a `mobile-contract-v*` tag newer than `contract/PIN`'s.

Stdlib only. Never fails the job: every outcome, including "the tags could not be listed", is a line in the log and
in the job summary, and the exit code is 0. A newer tag is a `::warning::` so it shows on the run.
"""
from __future__ import annotations
import os
import re
import subprocess
import sys

UPSTREAM = "https://github.com/agentchieflou/this-next-please"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TAG = re.compile(r"^mobile-contract-v(\d+)$")


def pinned_tag() -> str:
    with open(os.path.join(ROOT, "contract", "PIN"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("tag: "):
                return line[5:].strip()
    return ""


def published_tags() -> list[str]:
    out = subprocess.run(["git", "ls-remote", "--tags", "--refs", UPSTREAM, "refs/tags/mobile-contract-v*"],
                         capture_output=True, text=True, timeout=60, check=True).stdout
    return [line.split("refs/tags/", 1)[1] for line in out.splitlines() if "refs/tags/" in line]


def report(text: str, warn: bool = False) -> None:
    print(f"::warning::{text}" if warn else text)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(text + "\n")


def main() -> int:
    pin = pinned_tag()
    m = TAG.match(pin)
    if not m:
        report(f"contract/PIN names no mobile-contract tag ({pin!r}); nothing to compare.", warn=True)
        return 0
    try:
        tags = published_tags()
    except (OSError, subprocess.SubprocessError) as e:
        report(f"Could not list {UPSTREAM}'s tags ({e}); the pin is {pin}.", warn=True)
        return 0
    versions = sorted(int(TAG.match(t).group(1)) for t in tags if TAG.match(t))
    if pin not in tags:
        report(f"The pinned tag {pin} is not published yet (this-next-please#599); "
               f"published: {', '.join(tags) or 'none'}.")
    newer = [v for v in versions if v > int(m.group(1))]
    if newer:
        report(f"A newer contract is published: mobile-contract-v{newer[-1]} (pinned: {pin}). Adopt it in one PR "
               "that replaces contract/ and contract/PIN together, then fix what tests/ reports.", warn=True)
    else:
        report(f"No mobile-contract tag newer than {pin}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
