"""Where the lab is, which model it uses, and which credential it found.

Every notebook opened with fifty to a hundred lines of this. It is all setup and none
of it is the lesson, so it lives here and each notebook gets three printed lines: the
workspace, the model, and the credential.
"""

from __future__ import annotations

import importlib
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

__all__ = ["Lab", "start"]

# The credential names the claude binary understands, in the order it prefers them.
KEY, TOKEN = "ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"

_WRONG_DIRECTORY = (
    "Run this notebook from its own folder. The working directory is {here}, and "
    "{expected} is not there. In JupyterLab the working directory follows the notebook, "
    "so open it from the file browser rather than starting the kernel elsewhere."
)

_NO_ENV = "No {env_file}. Copy .env.example to .env and read the notes at the top of it."

_NEEDS_KEY = (
    "{env_file} has no value for ANTHROPIC_API_KEY. This lab calls the Claude API "
    "directly, so a subscription login will not carry it: it needs a Console key."
)


@dataclass(frozen=True)
class Lab:
    """The paths and the settings a notebook would otherwise work out for itself."""

    dir: Path
    root: Path
    env_file: Path
    workspace: Path
    out: Path
    model: str = ""
    credential: str = ""
    staged: list = field(default_factory=list)

    def stage(self, *names: str) -> list[Path]:
        """Copy checked-in directories beside the notebook into the workspace.

        The workspace is the sandbox: it is gitignored, it is what the terminal steps
        `cd` into, and deleting it and rerunning is always safe. Editing a staged copy
        is fine, but the checked-in original wins the next time this runs.

        A staged directory is put on `sys.path`, because staged Python is meant to be
        imported. That matters for more than convenience here: a server resolves its
        data directory relative to its own file, so the staged copy finds the workspace
        corpus and the checked-in original would not.
        """
        landed = []
        for name in names:
            source = self.dir / name
            if not source.is_dir():
                raise SystemExit(f"No {source} to stage.")
            destination = self.workspace / name
            shutil.copytree(
                source, destination, dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
            )
            if str(destination) not in sys.path:
                sys.path.insert(0, str(destination))
            landed.append(destination)
        return landed

    def reload(self, *modules):
        """Re-import after editing a module beside the notebook."""
        return [importlib.reload(module) for module in modules]


def _describe_credential(env_file: Path) -> str:
    # A name left blank in .env still reaches the environment, as an empty string, and an
    # empty ANTHROPIC_API_KEY fails the run rather than falling through to a login. So drop
    # the blanks first and let the credential chosen below be one that is really set.
    for name in (KEY, TOKEN):
        if not os.environ.get(name):
            os.environ.pop(name, None)

    # The Agent SDK runs the claude binary rather than calling the API itself, so it takes
    # the credential that binary takes, in that binary's order of preference.
    if os.environ.get(KEY):
        return f"{KEY} from .env, billed to your API account"
    if os.environ.get(TOKEN):
        return f"{TOKEN} from .env, drawn from your subscription"
    return "the login claude saved, drawn from your subscription"


def start(
    *,
    model_env: str | None = "LAB_MODEL",
    credential: str = "agent",
    workspace: bool = True,
    out: bool = False,
    needs: Sequence[str] = (),
    needs_hint: str = "",
    on_path: Sequence[str] = (),
) -> Lab:
    """Check the setup, load the credential, and report what was found.

    `credential` is "none" for the labs that never call a model, "agent" for the Agent
    SDK labs, which take a subscription login or a key, and "api_key" for lab 5, which
    calls the Claude API directly and cannot use a subscription.

    `needs` names workspace-relative paths a part B depends on its part A having written.
    """
    here = Path.cwd()
    root = here.parent
    if not (root / "pyproject.toml").exists():
        raise SystemExit(_WRONG_DIRECTORY.format(here=here, expected=root / "pyproject.toml"))

    env_file = root / ".env"
    model = ""
    description = ""

    if credential != "none" or model_env:
        if not env_file.exists():
            raise SystemExit(_NO_ENV.format(env_file=env_file))
        from dotenv import load_dotenv

        load_dotenv(env_file)

    if credential != "none":
        description = _describe_credential(env_file)
        if credential == "api_key" and not os.environ.get(KEY):
            raise SystemExit(_NEEDS_KEY.format(env_file=env_file))

    if model_env:
        model = os.environ.get(model_env, "")
        if not model:
            raise SystemExit(f"{env_file} has no value for {model_env}.")

    lab = Lab(dir=here, root=root, env_file=env_file,
              workspace=here / "workspace", out=here / "out",
              model=model, credential=description)

    for missing in [name for name in needs if not (lab.workspace / name).exists()]:
        raise SystemExit(f"No {lab.workspace / missing}. {needs_hint}".rstrip())

    if workspace:
        lab.workspace.mkdir(parents=True, exist_ok=True)
    if out:
        lab.out.mkdir(parents=True, exist_ok=True)

    # A notebook kernel puts its own directory on sys.path, but nbconvert and some
    # editors do not promise that, so the lab's own modules are made importable here.
    for entry in [str(here), *[str(here / name) for name in on_path]]:
        if entry not in sys.path:
            sys.path.insert(0, entry)

    if workspace:
        print(f"workspace  {lab.workspace}")
    elif out:
        print(f"output     {lab.out}")
    if model:
        print(f"model      {model}  ({model_env} in {env_file.name})")
    if description:
        print(f"credential {description}")
    return lab
