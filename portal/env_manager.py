from __future__ import annotations

"""Utilities for managing per-agent Python environments."""

import os
import subprocess
import venv
from pathlib import Path
from typing import Sequence


def _python_executable(env_path: Path) -> Path:
    """Return path to the Python executable inside a virtual environment."""
    if os.name == "nt":
        return env_path / "Scripts" / "python.exe"
    return env_path / "bin" / "python"


def ensure_env(agent_name: str, requirements: Path | None = None) -> Path:
    """Ensure a virtual environment for *agent_name* exists and deps installed.

    The environment is created under ``~/.agents/<agent_name>/``. If a
    ``requirements.txt`` file is provided, dependencies are installed on first
    run. Subsequent calls skip re-installation.
    """
    env_dir = Path.home() / ".agents" / agent_name
    if not env_dir.exists():
        env_dir.parent.mkdir(parents=True, exist_ok=True)
        venv.create(env_dir, with_pip=True)

    marker = env_dir / ".requirements_installed"
    if requirements and requirements.exists() and not marker.exists():
        subprocess.check_call([
            str(_python_executable(env_dir)),
            "-m",
            "pip",
            "install",
            "-r",
            str(requirements),
        ])
        marker.touch()

    return env_dir


def run(
    agent_path: str | os.PathLike[str],
    command: Sequence[str] | str | None = None,
) -> subprocess.CompletedProcess:
    """Run *command* for an agent within its virtual environment.

    ``agent_path`` points to the directory containing the agent's code and
    optionally a ``requirements.txt`` file. ``command`` defaults to running
    ``main.py`` with the virtual environment's Python interpreter.
    """
    agent_dir = Path(agent_path).resolve()
    agent_name = agent_dir.name

    env_dir = ensure_env(agent_name, agent_dir / "requirements.txt")
    env_python = _python_executable(env_dir)

    if command is None:
        cmd: list[str] = [str(agent_dir / "main.py")]
    elif isinstance(command, (str, Path)):
        cmd = [str(command)]
    else:
        cmd = [str(c) for c in command]

    full_cmd = [str(env_python)] + cmd
    return subprocess.run(full_cmd, cwd=str(agent_dir), check=True)
