# CLI Doctor

Validates that all required CLIs are installed and authenticated. Compatible with Windows, Linux, and macOS.

## Getting Started

```bash
# 1. Clone the repository
git clone https://github.com/alejmendez/cli-doctor.git
cd cli-doctor

# 2. Run the doctor
python cli-doctor.py
```

> No installation or virtual environment needed — the script has no external dependencies.

## Usage

```bash
python cli-doctor.py
```

## What it checks

| Tool | Binary | Checks |
|------|--------|--------|
| Claude Code | `claude` | Installed + authenticated (`claude auth status`) |
| Jira CLI | `jira` | Installed + authenticated (`jira me`) |
| Sentry CLI | `sentry-cli` | Installed + authenticated (`sentry-cli info`) |
| GitHub CLI | `gh` | Installed + authenticated (`gh auth status`) |

## Output

```
╔══════════════════════════════╗
║       CLI Doctor  v1.0       ║
╚══════════════════════════════╝
  Platform: Windows 11  |  Python 3.12.0

Claude Code
  ✔  Installed  —  claude/1.x.x
  ✔  Authenticated

Jira CLI
  ✔  Installed  —  jira version 1.7.0
  ✘  Not authenticated
     → Run:  jira init
     → You will need your Jira base URL and an API token.

──────────────────────────────────
  Summary:  3 OK  ·  1 issue(s)  /  4 tools

  Fix the issues above and run cli-doctor again.
```

Exit code is `0` if all tools pass, `1` if any fail.

## Requirements

Python 3.10+ (uses `list[str]` type hints without `from __future__ import annotations`).

No third-party dependencies — only the standard library.

## Adding a new CLI

Append a `CLITool` entry to the `TOOLS` list in `cli-doctor.py`:

```python
CLITool(
    name="My Tool",
    commands=["mytool"],          # binary names to search in PATH (first found wins)
    version_args=["--version"],   # args passed to print the version
    auth_check={
        "args": ["whoami"],       # args to verify authentication
        "success_fn": lambda out, err, rc: rc == 0,
    },
    install={
        "windows": "winget install MyTool",
        "linux":   "apt install mytool",
        "darwin":  "brew install mytool",
    },
    auth_instructions="Run:  mytool login",
),
```

Set `auth_check=None` if the tool requires no authentication.
