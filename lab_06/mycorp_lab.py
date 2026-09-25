"""Building and measuring the MyCorp working copy.

Lab 6 does not call a model from a cell. Everything the model does happens in a terminal,
in `claude`, using the prompts the notebook holds. So what is left here is repository
plumbing and measurement, and none of it is the lesson.

The measurements are worth knowing the shape of, because they are the same moves a session
should make: **Glob for the paths, Grep each for the thing you care about, and read only
what you have to.** `CLAUDE.md` names that rule; these functions obey it so you can check
the session's answer against a number rather than against an impression.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from labkit.gitlab import Git

__all__ = ["build", "pytest_tail", "project_docs", "sessions",
           "show_memory", "colleague_commit", "stale_phases", "Git"]

TICKET_TEST = "tests/test_refund_amount.py"
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".DS_Store")


def _modules(repo: Path):
    """Every non-empty module under shop/. Glob for the paths, as CLAUDE.md asks."""
    return [path for path in sorted(repo.glob("shop/**/*.py")) if path.stat().st_size]


def build(lab, *, rebuild: bool = False) -> tuple[Path, Git]:
    """Make the working copy and give it a history.

    Two commits and a `lab-start` tag, so `git diff lab-start` shows everything you have
    done at any point. The ticket's failing test goes in its own commit, which is what
    makes the tests-first lane visible later.
    """
    source = lab.dir / "mycorp"
    repo = lab.workspace / "mycorp"
    git = Git(repo)

    if rebuild and repo.exists():
        shutil.rmtree(repo)

    if repo.exists():
        print(f"{repo.relative_to(lab.dir)} is already here, leaving it alone. "
              f"REBUILD = True starts over.")
    else:
        lab.workspace.mkdir(exist_ok=True)
        shutil.copytree(source, repo, ignore=IGNORE)
        git("init", "-q")
        git("add", "-A", "--", ":!" + TICKET_TEST)
        git("commit", "-q", "-m", "Import the MyCorp refund path")
        git("add", "-A", "--", TICKET_TEST)
        git("commit", "-q", "-m", "TKT-0053: add the failing test for a string refund amount")
        git("tag", "lab-start")
        print(f"built {repo.relative_to(lab.dir)}")

    files = [p for p in repo.rglob("*")
             if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts]
    print(f"{len(_modules(repo))} modules under shop/, {len(files)} files in all, "
          f"at {git('rev-parse', '--short', 'HEAD')} with tag {git('tag')}")
    return repo, git


def pytest_tail(repo: Path, *paths: str, lines: int = 18) -> str:
    """Run the project's tests and hand back the end of the output."""
    done = subprocess.run([sys.executable, "-m", "pytest", "-q", "--color=no", *paths],
                          cwd=repo, capture_output=True, text=True)
    return "\n".join(done.stdout.strip().splitlines()[-lines:])


def project_docs(repo: Path) -> None:
    """What the project tells Claude about itself, and what else is on offer."""
    print((repo / "CLAUDE.md").read_text(encoding="utf-8"))
    for path in sorted((repo / "docs").rglob("*.md")):
        first = path.read_text(encoding="utf-8").splitlines()[0].lstrip("# ")
        print(f"  {path.relative_to(repo)}\n      {first}")
    for path in sorted((repo / ".claude").rglob("*.md")):
        body = path.read_text(encoding="utf-8")
        summary = next((line.split(":", 1)[1].strip() for line in body.splitlines()
                        if line.startswith("description:")), body.splitlines()[0])
        print(f"  {path.relative_to(repo)}\n      {summary[:96]}")


def sessions(repo: Path) -> None:
    """Every session recorded in this working copy, newest first, id first.

    Claude Code keys transcripts by working directory, with every character that is not a
    letter or a digit turned into a hyphen, so the working copy has its own folder. The id
    is what `--resume` takes, so this prints the fork command ready to copy.
    """
    folder = Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(repo))
    print(f"transcripts: {folder}")
    found = sorted(folder.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True) \
        if folder.exists() else []
    if not found:
        print("  none yet. This is the first session in that directory.")
        return
    for path in found:
        title = folder / path.stem / "custom-title.json"
        name = json.loads(title.read_text(encoding="utf-8")).get("customTitle", "") \
            if title.exists() else ""
        print(f"  {path.stem}  {name}")
    print(f"\nto fork the newest:\n  claude --resume {found[0].stem} --fork-session")


def show_memory(repo: Path) -> None:
    """The two kinds of memory this project ships, side by side.

    The scratchpad is prose, for a person to re-read. The manifest is not prose: it
    records which phase is done, which files that phase read, and the commit the run
    started from, so a later question is answered by arithmetic rather than by judgement.
    """
    print((repo / "notes/investigation.md").read_text(encoding="utf-8"))
    manifest = json.loads((repo / "state/manifest.json").read_text(encoding="utf-8"))
    print(f"investigation:   {manifest['investigation']}")
    print(f"baseline_commit: {manifest['baseline_commit']}\n")
    for phase in manifest["phases"]:
        print(f"  {phase['status']:12} {phase['id']:20} "
              f"{len(phase['files_read'])} files read")
        print(f"  {'':12} {phase['question']}")


def colleague_commit(repo: Path, git: Git) -> None:
    """Fold the two retry counts into one module constant, and commit it.

    This is the colleague. It is what a teammate's push would look like arriving while
    your session was closed, and nothing tells a resumed session that it happened.
    """
    client = repo / "shop/refunds.py"
    body = client.read_text(encoding="utf-8")
    if "RETRY_COUNT" in body:
        print("already folded, leaving it alone")
    else:
        anchor = "from shop.gateway import GatewayRefused, GatewayTimeout\n"
        body = body.replace(anchor, anchor + "\nRETRY_COUNT = 3\n", 1)
        body = body.replace("    retry_count = 3\n", "").replace("retry_count", "RETRY_COUNT")
        client.write_text(body, encoding="utf-8")
        git("add", "--", "shop/refunds.py")
        git("commit", "-q", "-m", "Fold the two retry counts into one module constant")
        print("committed as a colleague")
    print(git("show", "--stat", "--oneline", "HEAD"))


def stale_phases(repo: Path, git: Git) -> None:
    """Which findings still stand, by arithmetic rather than by feel.

    An intersection: the files a phase read, against the files that have changed since the
    commit it started from. That is why the manifest records `files_read` and
    `baseline_commit` rather than just a summary.
    """
    manifest = json.loads((repo / "state/manifest.json").read_text(encoding="utf-8"))
    baseline = manifest["baseline_commit"]
    if not baseline:
        print("baseline_commit is still null. Run section 6 step one, then this cell.")
        print("Showing the sum against lab-start instead, so the shape is visible:")
        baseline = "lab-start"

    changed = git.changed(baseline)
    print(f"changed since {baseline}: {', '.join(sorted(changed)) or 'nothing'}\n")
    for phase in manifest["phases"]:
        if phase["status"] != "done":
            print(f"  {phase['id']:20} not done, nothing to keep or lose")
            continue
        stale = sorted(set(phase["files_read"]) & changed)
        print(f"  {phase['id']:20} "
              + (f"STALE, re-read {', '.join(stale)}" if stale else "stands"))
