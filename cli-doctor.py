#!/usr/bin/env python3
"""
cli-doctor.py
Validates that all required CLIs are installed and authenticated.
Compatible with Windows, Linux, and macOS.
"""

import subprocess
import sys
import platform
import shutil
from dataclasses import dataclass, field
from typing import Optional

# ─────────────────────────────────────────────
#  ANSI colors (disabled automatically on Windows without support)
# ─────────────────────────────────────────────
def supports_color() -> bool:
    if platform.system() == "Windows":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except Exception:
            return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

USE_COLOR = supports_color()

class C:
    RESET  = "\033[0m"  if USE_COLOR else ""
    BOLD   = "\033[1m"  if USE_COLOR else ""
    RED    = "\033[91m" if USE_COLOR else ""
    GREEN  = "\033[92m" if USE_COLOR else ""
    YELLOW = "\033[93m" if USE_COLOR else ""
    CYAN   = "\033[96m" if USE_COLOR else ""
    DIM    = "\033[2m"  if USE_COLOR else ""

def ok(msg):    print(f"  {C.GREEN}✔{C.RESET}  {msg}")
def fail(msg):  print(f"  {C.RED}✘{C.RESET}  {msg}")
def warn(msg):  print(f"  {C.YELLOW}⚠{C.RESET}  {msg}")
def info(msg):  print(f"  {C.CYAN}ℹ{C.RESET}  {C.DIM}{msg}{C.RESET}")
def hint(msg):  print(f"     {C.DIM}→ {msg}{C.RESET}")

# ─────────────────────────────────────────────
#  Data model
# ─────────────────────────────────────────────
@dataclass
class CLITool:
    name: str                          # Display name
    commands: list[str]                # Binary name(s) to look for (first found wins)
    version_args: list[str]            # Args to print version
    auth_check: Optional[dict]         # None = no auth needed
    install: dict[str, str]            # platform → install instructions
    auth_instructions: str = ""        # Shown when not authenticated

    # ── auth_check schema ──────────────────────────────────────────────────
    # {
    #   "args":       list[str],        # command args to run auth check
    #   "success_fn": callable(stdout, stderr, returncode) -> bool
    # }

# ─────────────────────────────────────────────
#  CLI definitions
#  ➕ To add a new CLI: append a new CLITool to this list.
# ─────────────────────────────────────────────
TOOLS: list[CLITool] = [

    CLITool(
        name="Claude Code",
        commands=["claude"],
        version_args=["--version"],
        auth_check={
            "args": ["auth", "status"],
            # `claude auth status` exits with code 0 when authenticated.
            # The output does NOT contain "logged in"; trusting the exit code is enough.
            "success_fn": lambda out, err, rc: rc == 0,
        },
        install={
            # npm install is DEPRECATED — use the native installer instead.
            # Ref: https://code.claude.com/docs/en/setup
            "windows": (
                "winget install Anthropic.ClaudeCode\n"
                "     Requires Git for Windows: https://git-scm.com/download/win\n"
                "     Note: winget installs do NOT auto-update. Run periodically:\n"
                "           winget upgrade Anthropic.ClaudeCode"
            ),
            "linux": (
                "curl -fsSL https://claude.ai/install.sh | sh\n"
                "     Note: native installer auto-updates in the background."
            ),
            "darwin": (
                "brew install claude-code\n"
                "     Note: Homebrew does NOT auto-update. Run periodically:\n"
                "           brew upgrade claude-code"
            ),
        },
        auth_instructions=(
            "Run:  claude auth login\n"
            "     Then follow the browser prompt to authenticate with your Anthropic account."
        ),
    ),

    CLITool(
        name="Jira CLI",
        commands=["jira"],
        version_args=["version"],
        auth_check={
            "args": ["me"],
            "success_fn": lambda out, err, rc: rc == 0 and ("account" in out.lower() or "@" in out),
        },
        install={
            "windows": (
                "winget install ankitpokhrel.jira-cli\n"
                "     Or download from: https://github.com/ankitpokhrel/jira-cli/releases"
            ),
            "linux": (
                "VER=1.7.0\n"
                "     curl -L https://github.com/ankitpokhrel/jira-cli/releases/download/v${VER}/"
                "jira_${VER}_linux_x86_64.tar.gz | tar xz\n"
                "     sudo mv jira_${VER}_linux_x86_64/bin/jira /usr/local/bin/\n"
                "     rm -rf jira_${VER}_linux_x86_64/"
            ),
            "darwin": "brew install ankitpokhrel/jira-cli/jira-cli",
        },
        auth_instructions=(
            "Run:  jira init\n"
            "     You will need your Jira base URL and an API token.\n"
            "     Generate a token at: https://id.atlassian.com/manage-profile/security/api-tokens"
        ),
    ),

    CLITool(
        name="Sentry CLI",
        commands=["sentry-cli"],
        version_args=["--version"],
        auth_check={
            "args": ["info"],
            "success_fn": lambda out, err, rc: rc == 0 and "logged in" not in (out + err).lower()
                                               or "sentry.io" in (out + err).lower(),
        },
        install={
            "windows": (
                "winget install sentry-cli\n"
                "     Or:  npm install -g @sentry/cli"
            ),
            "linux": (
                "curl -sL https://sentry.io/get-cli/ | bash\n"
                "     Or:  npm install -g @sentry/cli"
            ),
            "darwin": (
                "brew install getsentry/tools/sentry-cli\n"
                "     Or:  npm install -g @sentry/cli"
            ),
        },
        auth_instructions=(
            "Run:  sentry-cli login\n"
            "     Or set the environment variable:  SENTRY_AUTH_TOKEN=<your-token>\n"
            "     Generate a token at: https://sentry.io/settings/account/api/auth-tokens/"
        ),
    ),

    CLITool(
        name="GitHub CLI",
        commands=["gh"],
        version_args=["--version"],
        auth_check={
            "args": ["auth", "status"],
            "success_fn": lambda out, err, rc: rc == 0 or "logged in" in (out + err).lower(),
        },
        install={
            "windows": "winget install GitHub.cli",
            "linux": (
                "type -p curl >/dev/null || sudo apt install curl -y\n"
                "     curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg "
                "| sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg\n"
                "     echo 'deb [arch=$(dpkg --print-architecture) "
                "signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] "
                "https://cli.github.com/packages stable main' "
                "| sudo tee /etc/apt/sources.list.d/github-cli.list\n"
                "     sudo apt update && sudo apt install gh"
            ),
            "darwin": "brew install gh",
        },
        auth_instructions=(
            "Run:  gh auth login\n"
            "     Choose GitHub.com, select HTTPS, and authenticate via browser or token."
        ),
    ),

    # TODO: Add Google Workspace CLI (gam) once tested and validated.
    # Candidate binary: gam / gam7
    # Ref: https://github.com/GAM-team/GAM

]

# ─────────────────────────────────────────────
#  Core logic
# ─────────────────────────────────────────────
def run_cmd(cmd: list[str], timeout: int = 8) -> tuple[str, str, int]:
    """Run a command and return (stdout, stderr, returncode)."""
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True,
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "timeout", -1
    except Exception as e:
        return "", str(e), -1


def detect_binary(commands: list[str]) -> Optional[str]:
    """Return the first binary found in PATH, or None."""
    for cmd in commands:
        if shutil.which(cmd):
            return cmd
    return None


def get_platform_key() -> str:
    s = platform.system().lower()
    if s == "windows":
        return "windows"
    if s == "darwin":
        return "darwin"
    return "linux"


def get_install_instruction(tool: CLITool) -> str:
    plat = get_platform_key()
    return tool.install.get(plat) or tool.install.get("all", "No install instructions available.")


def check_tool(tool: CLITool) -> bool:
    """Check one tool. Returns True if everything is OK."""
    print(f"\n{C.BOLD}{tool.name}{C.RESET}")

    binary = detect_binary(tool.commands)

    # ── Not installed ──────────────────────────────────────────────────────
    if binary is None:
        fail(f"Not found  ({' / '.join(tool.commands)})")
        install_cmd = get_install_instruction(tool)
        hint(f"Install:  {install_cmd}")
        return False

    # ── Get version ────────────────────────────────────────────────────────
    out, err, rc = run_cmd([binary] + tool.version_args)
    version_line = (out or err).splitlines()[0] if (out or err) else "unknown version"
    ok(f"Installed  —  {version_line}")

    # ── Auth check (optional) ──────────────────────────────────────────────
    if tool.auth_check is None:
        return True

    a_out, a_err, a_rc = run_cmd([binary] + tool.auth_check["args"])
    authenticated = tool.auth_check["success_fn"](a_out, a_err, a_rc)

    if authenticated:
        ok("Authenticated")
        return True
    else:
        warn("Not authenticated")
        for line in tool.auth_instructions.splitlines():
            hint(line)
        return False


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────
def main():
    print(f"\n{C.BOLD}{C.CYAN}╔══════════════════════════════╗")
    print(f"║       CLI Doctor  v1.0       ║")
    print(f"╚══════════════════════════════╝{C.RESET}")
    print(f"  Platform: {platform.system()} {platform.release()}  |  Python {sys.version.split()[0]}")

    results = []
    for tool in TOOLS:
        results.append(check_tool(tool))

    total   = len(TOOLS)
    passed  = sum(results)
    failed  = total - passed

    print(f"\n{C.BOLD}{'─' * 34}{C.RESET}")
    print(f"  Summary:  {C.GREEN}{passed} OK{C.RESET}  ·  {C.RED}{failed} issue(s){C.RESET}  /  {total} tools\n")

    if failed == 0:
        print(f"  {C.GREEN}{C.BOLD}All CLIs are ready!{C.RESET} 🚀\n")
    else:
        print(f"  {C.YELLOW}Fix the issues above and run cli-doctor again.{C.RESET}\n")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()