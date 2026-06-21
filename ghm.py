#!/usr/bin/env python3
"""git-hook-manager-max (ghm) — A visual Git hook manager CLI.

Usage:
    ghm list              List all hooks in the current git repo
    ghm list --all        List hooks across all discovered git repos
    ghm create <hook>     Create a new hook from template or scratch
    ghm edit <hook>       Edit an existing hook
    ghm delete <hook>     Delete a hook
    ghm toggle <hook>     Enable/disable a hook
    ghm templates         List available hook templates
    ghm init              Initialize git-hook-manager config in a repo
    ghm export            Export hooks as JSON
    ghm import <file>     Import hooks from JSON
"""

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import textwrap
from pathlib import Path
from datetime import datetime

__version__ = "0.1.0"

# ANSI color codes
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    @classmethod
    def disable(cls):
        for attr in ("RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "BOLD", "DIM", "RESET"):
            setattr(cls, attr, "")


# All standard Git hook names
GIT_HOOKS = [
    "applypatch-msg", "commit-msg", "fsmonitor-watchman", "post-applypatch",
    "post-checkout", "post-commit", "post-merge", "post-receive",
    "post-rewrite", "post-update", "pre-applypatch", "pre-auto-gc",
    "pre-commit", "pre-push", "pre-rebase", "pre-receive",
    "prepare-commit-msg", "push-to-checkout", "update",
]

# Hook templates
TEMPLATES = {
    "pre-commit": {
        "description": "Run linters before allowing commit",
        "script": '''#!/bin/sh
# pre-commit hook — Run linters
echo "🔍 Running pre-commit checks..."

# Run shellcheck on shell scripts
if command -v shellcheck >/dev/null 2>&1; then
    for file in $(git diff --cached --name-only --diff-filter=ACM | grep '\\.sh$'); do
        if [ -f "$file" ]; then
            shellcheck "$file" || exit 1
        fi
    done
fi

# Run Python linting
if command -v ruff >/dev/null 2>&1; then
    ruff check --diff --quiet || exit 1
elif command -v flake8 >/dev/null 2>&1; then
    flake8 $(git diff --cached --name-only --diff-filter=ACM | grep '\\.py$') || exit 1
fi

echo "✅ Pre-commit checks passed"
''',
    },
    "commit-msg": {
        "description": "Enforce conventional commit message format",
        "script": '''#!/bin/sh
# commit-msg hook — Enforce conventional commits
COMMIT_MSG_FILE=$1
MSG=$(head -n1 "$COMMIT_MSG_FILE")

# Conventional commit pattern
PATTERN="^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\\(.+\\))?: .{1,72}"

if ! echo "$MSG" | grep -qE "$PATTERN"; then
    echo "❌ Commit message does not follow conventional commits format."
    echo "   Expected: type(scope): description"
    echo "   Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert"
    echo "   Example: feat(auth): add OAuth2 login support"
    exit 1
fi

echo "✅ Commit message format OK"
''',
    },
    "pre-push": {
        "description": "Run tests before pushing",
        "script": '''#!/bin/sh
# pre-push hook — Run tests before push
echo "🧪 Running tests before push..."

# Python tests
if [ -f "pytest.ini" ] || [ -f "setup.cfg" ] || [ -f "pyproject.toml" ]; then
    if command -v pytest >/dev/null 2>&1; then
        pytest -x -q 2>&1 || { echo "❌ Tests failed"; exit 1; }
    fi
fi

# Node.js tests
if [ -f "package.json" ]; then
    if command -v npm >/dev/null 2>&1; then
        npm test --silent 2>&1 || { echo "❌ Tests failed"; exit 1; }
    fi
fi

echo "✅ All tests passed"
''',
    },
    "post-checkout": {
        "description": "Install dependencies after checkout",
        "script": '''#!/bin/sh
# post-checkout hook — Auto-install dependencies
PREV_HEAD=$1
NEW_HEAD=$2
BRANCH_SWITCH=$3

# Only run on branch switches
if [ "$BRANCH_SWITCH" = "1" ]; then
    echo "📦 Checking dependencies after checkout..."

    if [ -f "package.json" ] && [ -f "package-lock.json" ]; then
        if [ "package-lock.json" -nt "node_modules/.package-lock.json" ] 2>/dev/null; then
            echo "Installing npm dependencies..."
            npm install
        fi
    fi

    if [ -f "requirements.txt" ]; then
        if [ "requirements.txt" -nt "venv/.requirements-installed" ] 2>/dev/null; then
            if [ -f "venv/bin/pip" ]; then
                echo "Installing Python dependencies..."
                venv/bin/pip install -r requirements.txt
                touch venv/.requirements-installed
            fi
        fi
    fi
fi
''',
    },
    "pre-rebase": {
        "description": "Prevent rebasing published branches",
        "script": '''#!/bin/sh
# pre-rebase hook — Prevent rebasing main/master
BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null)

if echo "$BRANCH" | grep -qE "^(main|master|release/.*)$"; then
    echo "⚠️  Warning: You are about to rebase a protected branch ($BRANCH)."
    read -p "Are you sure? [y/N] " -n 1 -r
    echo
    if ! echo "$REPLY" | grep -qE "^[Yy]$"; then
        echo "Rebase aborted."
        exit 1
    fi
fi
''',
    },
    "post-merge": {
        "description": "Notify about merge conflicts or changes",
        "script": '''#!/bin/sh
# post-merge hook — Check for conflicts and notify
SQUASH=$1

# Check for conflict markers
CONFLICTS=$(git diff --name-only --diff-filter=U 2>/dev/null)
if [ -n "$CONFLICTS" ]; then
    echo "⚠️  Merge conflicts detected in:"
    echo "$CONFLICTS"
    exit 1
fi

echo "✅ Merge completed successfully"
''',
    },
}


def find_git_root(path=None):
    """Find the root of the git repository."""
    if path is None:
        path = os.getcwd()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, cwd=path, timeout=5
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def get_hooks_dir(repo_path=None):
    """Get the .git/hooks directory path."""
    git_root = find_git_root() if repo_path is None else Path(repo_path)
    if not git_root:
        return None
    # Use core.hooksPath if configured
    try:
        result = subprocess.run(
            ["git", "config", "core.hooksPath"],
            capture_output=True, text=True, cwd=str(git_root), timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            hooks_path = Path(result.stdout.strip())
            if not hooks_path.is_absolute():
                hooks_path = git_root / hooks_path
            return hooks_path
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return git_root / ".git" / "hooks"


def get_hook_info(hook_path):
    """Get information about a hook file."""
    if not hook_path.exists():
        return None

    st = hook_path.stat()
    is_executable = bool(st.st_mode & stat.S_IXUSR)
    is_disabled = not is_executable

    # Read first few lines for description
    description = ""
    try:
        with open(hook_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    break
                if line.startswith("# "):
                    description = line[2:].strip()
                    break
    except OSError:
        pass

    return {
        "name": hook_path.name,
        "path": str(hook_path),
        "size": st.st_size,
        "modified": datetime.fromtimestamp(st.st_mtime).isoformat(),
        "executable": is_executable,
        "disabled": is_disabled,
        "description": description,
    }


def list_hooks(hooks_dir):
    """List all hooks in a directory."""
    hooks = []
    if not hooks_dir or not hooks_dir.exists():
        return hooks

    for hook_name in GIT_HOOKS:
        hook_path = hooks_dir / hook_name
        if hook_path.exists():
            info = get_hook_info(hook_path)
            if info:
                hooks.append(info)

    return hooks


def find_all_repos(base_path=None, max_depth=3):
    """Find all git repositories under a path."""
    if base_path is None:
        base_path = Path.home()
    else:
        base_path = Path(base_path)

    repos = []
    _find_repos_recursive(base_path, repos, 0, max_depth)
    return repos


def _find_repos_recursive(path, repos, depth, max_depth):
    """Recursively find git repos."""
    if depth > max_depth:
        return
    try:
        for entry in path.iterdir():
            if entry.is_dir() and not entry.name.startswith("."):
                git_dir = entry / ".git"
                if git_dir.is_dir():
                    repos.append(entry)
                elif entry.name not in ("node_modules", "venv", ".venv", "__pycache__", "vendor"):
                    _find_repos_recursive(entry, repos, depth + 1, max_depth)
    except PermissionError:
        pass


def create_hook(hook_name, template=None, content=None, hooks_dir=None):
    """Create a new hook."""
    if hooks_dir is None:
        hooks_dir = get_hooks_dir()
    if not hooks_dir:
        return False, "Not in a git repository"

    if hook_name not in GIT_HOOKS:
        return False, f"Unknown hook: {hook_name}. Valid: {', '.join(GIT_HOOKS)}"

    hook_path = hooks_dir / hook_name
    if hook_path.exists():
        return False, f"Hook already exists: {hook_name}"

    # Create content
    if template and template in TEMPLATES:
        script = TEMPLATES[template]["script"]
    elif content:
        script = content
    else:
        script = f"#!/bin/sh\n# {hook_name} hook\n# Created by git-hook-manager-max\n\n"

    # Ensure hooks directory exists
    hooks_dir.mkdir(parents=True, exist_ok=True)

    with open(hook_path, "w") as f:
        f.write(script)

    # Make executable
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IWUSR | stat.S_IXUSR)

    return True, f"Created hook: {hook_name}"


def toggle_hook(hook_name, hooks_dir=None):
    """Toggle a hook on/off by changing executable permission."""
    if hooks_dir is None:
        hooks_dir = get_hooks_dir()
    if not hooks_dir:
        return False, "Not in a git repository"

    hook_path = hooks_dir / hook_name
    if not hook_path.exists():
        return False, f"Hook not found: {hook_name}"

    current = hook_path.stat().st_mode
    if current & stat.S_IXUSR:
        # Disable
        hook_path.chmod(current & ~stat.S_IXUSR)
        return True, f"Disabled hook: {hook_name}"
    else:
        # Enable
        hook_path.chmod(current | stat.S_IXUSR)
        return True, f"Enabled hook: {hook_name}"


def delete_hook(hook_name, hooks_dir=None):
    """Delete a hook."""
    if hooks_dir is None:
        hooks_dir = get_hooks_dir()
    if not hooks_dir:
        return False, "Not in a git repository"

    hook_path = hooks_dir / hook_name
    if not hook_path.exists():
        return False, f"Hook not found: {hook_name}"

    hook_path.unlink()
    return True, f"Deleted hook: {hook_name}"


def export_hooks(hooks_dir=None):
    """Export all hooks as JSON."""
    if hooks_dir is None:
        hooks_dir = get_hooks_dir()
    if not hooks_dir:
        return {}

    export = {"hooks": []}
    for hook_info in list_hooks(hooks_dir):
        hook_path = Path(hook_info["path"])
        try:
            with open(hook_path) as f:
                hook_info["content"] = f.read()
        except OSError:
            hook_info["content"] = ""
        export["hooks"].append(hook_info)

    return export


def import_hooks(data, hooks_dir=None):
    """Import hooks from JSON data."""
    if hooks_dir is None:
        hooks_dir = get_hooks_dir()
    if not hooks_dir:
        return False, "Not in a git repository"

    hooks = data.get("hooks", [])
    imported = 0
    for hook_data in hooks:
        name = hook_data.get("name")
        content = hook_data.get("content", "")
        if name and content:
            hook_path = hooks_dir / name
            hooks_dir.mkdir(parents=True, exist_ok=True)
            with open(hook_path, "w") as f:
                f.write(content)
            hook_path.chmod(0o755)
            imported += 1

    return True, f"Imported {imported} hook(s)"


def format_hook_table(hooks, repo_name=None):
    """Format hooks as a nice table."""
    if not hooks:
        return "No hooks found."

    lines = []
    if repo_name:
        lines.append(f"\n{Colors.BOLD}📁 {repo_name}{Colors.RESET}\n")

    # Header
    header = f"  {'HOOK':<22} {'STATUS':<12} {'SIZE':<8} {'DESCRIPTION'}"
    lines.append(header)
    lines.append("  " + "-" * 70)

    for hook in hooks:
        name = hook["name"]
        status = "✅ active" if hook["executable"] else "⏸️  disabled"
        size = f"{hook['size']}B"
        desc = hook.get("description", "") or ""

        # Color by status
        if hook["executable"]:
            status_colored = f"{Colors.GREEN}{status}{Colors.RESET}"
        else:
            status_colored = f"{Colors.YELLOW}{status}{Colors.RESET}"

        lines.append(f"  {name:<22} {status_colored:<12} {size:<8} {desc}")

    return "\n".join(lines)


def cmd_list(args):
    """List hooks."""
    if args.all:
        repos = find_all_repos(max_depth=args.depth)
        all_hooks = {}
        for repo in repos:
            hd = get_hooks_dir(str(repo))
            hooks = list_hooks(hd)
            if hooks:
                all_hooks[str(repo)] = hooks

        if args.json:
            print(json.dumps(all_hooks, indent=2, default=str))
            return

        if not all_hooks:
            print("No hooks found in any repository.")
            return

        print(f"\n{Colors.BOLD}Git hooks across {len(all_hooks)} repositor(ies):{Colors.RESET}")
        for repo, hooks in all_hooks.items():
            print(format_hook_table(hooks, repo_name=repo))
        print()
    else:
        hooks_dir = get_hooks_dir()
        if not hooks_dir:
            print(f"{Colors.RED}Error: Not in a git repository{Colors.RESET}")
            sys.exit(1)

        hooks = list_hooks(hooks_dir)

        if args.json:
            print(json.dumps(hooks, indent=2, default=str))
            return

        if not hooks:
            print("No hooks found. Use 'ghm create <hook>' to add one.")
            return

        git_root = find_git_root()
        repo_name = git_root.name if git_root else "current repo"
        print(format_hook_table(hooks, repo_name=repo_name))
        print(f"\n{Colors.DIM}Total: {len(hooks)} hook(s){Colors.RESET}\n")


def cmd_create(args):
    """Create a new hook."""
    hooks_dir = get_hooks_dir()
    if not hooks_dir:
        print(f"{Colors.RED}Error: Not in a git repository{Colors.RESET}")
        sys.exit(1)

    hook_name = args.hook
    template = args.template

    if hook_name not in GIT_HOOKS:
        print(f"{Colors.RED}Unknown hook: {hook_name}{Colors.RESET}")
        print(f"Valid hooks: {', '.join(GIT_HOOKS)}")
        sys.exit(1)

    # Check if template exists
    if template and template not in TEMPLATES:
        print(f"{Colors.YELLOW}Unknown template: {template}{Colors.RESET}")
        print(f"Available templates: {', '.join(TEMPLATES.keys())}")
        sys.exit(1)

    success, msg = create_hook(hook_name, template=template, hooks_dir=hooks_dir)

    if args.json:
        print(json.dumps({"success": success, "message": msg}))
        return

    if success:
        print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")
        if template and template in TEMPLATES:
            print(f"  Template: {TEMPLATES[template]['description']}")
    else:
        print(f"{Colors.RED}✗ {msg}{Colors.RESET}")
        sys.exit(1)


def cmd_edit(args):
    """Edit a hook."""
    hooks_dir = get_hooks_dir()
    if not hooks_dir:
        print(f"{Colors.RED}Error: Not in a git repository{Colors.RESET}")
        sys.exit(1)

    hook_name = args.hook
    hook_path = hooks_dir / hook_name

    if not hook_path.exists():
        print(f"{Colors.RED}Hook not found: {hook_name}{Colors.RESET}")
        sys.exit(1)

    # Open in editor
    editor = os.environ.get("EDITOR", os.environ.get("VISUAL", "vi"))
    try:
        subprocess.run([editor, str(hook_path)], check=True)
        print(f"{Colors.GREEN}✓ Edited {hook_name}{Colors.RESET}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"{Colors.RED}Failed to open editor: {e}{Colors.RESET}")
        sys.exit(1)


def cmd_delete(args):
    """Delete a hook."""
    hooks_dir = get_hooks_dir()
    if not hooks_dir:
        print(f"{Colors.RED}Error: Not in a git repository{Colors.RESET}")
        sys.exit(1)

    hook_name = args.hook

    if not args.yes:
        response = input(f"Delete hook '{hook_name}'? [y/N] ")
        if response.lower() != "y":
            print("Aborted.")
            return

    success, msg = delete_hook(hook_name, hooks_dir=hooks_dir)

    if args.json:
        print(json.dumps({"success": success, "message": msg}))
        return

    if success:
        print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")
    else:
        print(f"{Colors.RED}✗ {msg}{Colors.RESET}")
        sys.exit(1)


def cmd_toggle(args):
    """Toggle a hook on/off."""
    hooks_dir = get_hooks_dir()
    if not hooks_dir:
        print(f"{Colors.RED}Error: Not in a git repository{Colors.RESET}")
        sys.exit(1)

    hook_name = args.hook
    success, msg = toggle_hook(hook_name, hooks_dir=hooks_dir)

    if args.json:
        print(json.dumps({"success": success, "message": msg}))
        return

    if success:
        print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")
    else:
        print(f"{Colors.RED}✗ {msg}{Colors.RESET}")
        sys.exit(1)


def cmd_templates(args):
    """List available hook templates."""
    if args.json:
        templates = {name: info["description"] for name, info in TEMPLATES.items()}
        print(json.dumps(templates, indent=2))
        return

    print(f"\n{Colors.BOLD}Available hook templates:{Colors.RESET}\n")
    for name, info in TEMPLATES.items():
        print(f"  {Colors.CYAN}{name:<20}{Colors.RESET} {info['description']}")
    print()


def cmd_init(args):
    """Initialize git-hook-manager in a repo."""
    hooks_dir = get_hooks_dir()
    if not hooks_dir:
        print(f"{Colors.RED}Error: Not in a git repository{Colors.RESET}")
        sys.exit(1)

    # Create config marker
    config_file = hooks_dir / ".ghm-config"
    config = {
        "version": __version__,
        "initialized": datetime.now().isoformat(),
    }
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    if args.json:
        print(json.dumps({"success": True, "message": "Initialized", "config": config}))
        return

    print(f"{Colors.GREEN}✓ git-hook-manager initialized{Colors.RESET}")
    print(f"  Config: {config_file}")
    print(f"  Hooks:  {hooks_dir}")


def cmd_export(args):
    """Export hooks as JSON."""
    hooks_dir = get_hooks_dir()
    if not hooks_dir:
        print(f"{Colors.RED}Error: Not in a git repository{Colors.RESET}")
        sys.exit(1)

    data = export_hooks(hooks_dir)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"{Colors.GREEN}✓ Exported {len(data.get('hooks', []))} hook(s) to {args.output}{Colors.RESET}")
    else:
        print(json.dumps(data, indent=2, default=str))


def cmd_import(args):
    """Import hooks from JSON file."""
    hooks_dir = get_hooks_dir()
    if not hooks_dir:
        print(f"{Colors.RED}Error: Not in a git repository{Colors.RESET}")
        sys.exit(1)

    input_file = args.file
    if not os.path.exists(input_file):
        print(f"{Colors.RED}File not found: {input_file}{Colors.RESET}")
        sys.exit(1)

    with open(input_file) as f:
        data = json.load(f)

    success, msg = import_hooks(data, hooks_dir=hooks_dir)

    if args.json:
        print(json.dumps({"success": success, "message": msg}))
        return

    if success:
        print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")
    else:
        print(f"{Colors.RED}✗ {msg}{Colors.RESET}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="ghm",
        description="git-hook-manager-max — A visual Git hook manager CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
                ghm list                    # List hooks in current repo
                ghm list --all              # List hooks across all repos
                ghm create pre-commit       # Create pre-commit hook from template
                ghm create pre-push --template pre-push
                ghm toggle pre-commit       # Enable/disable a hook
                ghm edit pre-commit         # Edit hook in $EDITOR
                ghm delete pre-commit       # Delete a hook
                ghm templates               # List available templates
                ghm export                  # Export hooks as JSON
                ghm export -o hooks.json    # Export to file
                ghm import hooks.json       # Import hooks from file
        """),
    )
    parser.add_argument("--version", action="version", version=f"ghm {__version__}")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # list
    list_parser = subparsers.add_parser("list", help="List hooks")
    list_parser.add_argument("--all", action="store_true", help="List hooks across all repos")
    list_parser.add_argument("--depth", type=int, default=3, help="Max depth for repo search")

    # create
    create_parser = subparsers.add_parser("create", help="Create a new hook")
    create_parser.add_argument("hook", help="Hook name (e.g., pre-commit)")
    create_parser.add_argument("--template", "-t", help="Template to use")

    # edit
    edit_parser = subparsers.add_parser("edit", help="Edit a hook")
    edit_parser.add_argument("hook", help="Hook name")

    # delete
    delete_parser = subparsers.add_parser("delete", help="Delete a hook")
    delete_parser.add_argument("hook", help="Hook name")
    delete_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")

    # toggle
    toggle_parser = subparsers.add_parser("toggle", help="Enable/disable a hook")
    toggle_parser.add_argument("hook", help="Hook name")

    # templates
    subparsers.add_parser("templates", help="List available templates")

    # init
    subparsers.add_parser("init", help="Initialize in current repo")

    # export
    export_parser = subparsers.add_parser("export", help="Export hooks as JSON")
    export_parser.add_argument("-o", "--output", help="Output file path")

    # import
    import_parser = subparsers.add_parser("import", help="Import hooks from JSON")
    import_parser.add_argument("file", help="JSON file to import")

    args = parser.parse_args()

    if args.no_color or args.json:
        Colors.disable()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "list": cmd_list,
        "create": cmd_create,
        "edit": cmd_edit,
        "delete": cmd_delete,
        "toggle": cmd_toggle,
        "templates": cmd_templates,
        "init": cmd_init,
        "export": cmd_export,
        "import": cmd_import,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
