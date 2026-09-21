"""Git, for the lab that works on a real repository.

Lab 6 gives its working copy a history so that `git diff lab-start` shows everything a
session has done. Both of its notebooks need the same four lines of subprocess wiring,
so they are here instead.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Sequence

__all__ = ["Git", "IDENTITY"]

# A fixed identity, so the lab commits the same way on every machine and never picks up
# a signing configuration that would stop it committing at all.
IDENTITY = ["-c", "user.name=MyCorp Lab", "-c", "user.email=lab@mycorp.example",
            "-c", "commit.gpgsign=false", "-c", "init.defaultBranch=main"]


class Git:
    """Run git in one repository. Calling the object runs a command."""

    def __init__(self, repo: Path, identity: Sequence[str] = IDENTITY):
        self.repo = Path(repo)
        self.identity = list(identity)

    def __call__(self, *args: str) -> str:
        done = subprocess.run(
            ["git", "-C", str(self.repo), *self.identity, *args],
            capture_output=True, text=True,
        )
        if done.returncode != 0:
            print("git", " ".join(args), "failed:", done.stdout, done.stderr)
        return done.stdout.rstrip()

    def changed(self, since: str, until: str = "HEAD") -> set[str]:
        """The files that moved between two commits, as a set for intersecting."""
        listed = self("diff", "--name-only", f"{since}..{until}")
        return {line for line in listed.splitlines() if line}
