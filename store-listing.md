# Git Hook Manager Max — Chrome Web Store / Developer Tool Listing

## Product Name

**Git Hook Manager Max**

## Short Description

Manage Git hooks across projects with a visual dashboard. Create, edit, and share hooks — no command line needed.

## Long Description

Git Hook Manager Max is a developer tool that simplifies Git hook management across all your projects. Instead of manually editing `.git/hooks/` files or remembering hook syntax, use a visual interface to create, edit, organize, and share your Git hooks.

**VISUAL HOOK MANAGEMENT**
Managing Git hooks across multiple projects is tedious — you edit shell scripts in hidden `.git/hooks/` directories, copy them between repos, and hope they work. Git Hook Manager Max gives you a visual dashboard to see all your hooks at a glance, organized by project. Create new hooks with a built-in editor, toggle them on/off, and manage their execution order — all without touching the command line.

**PRE-BUILT TEMPLATES**
Get started quickly with pre-built hook templates for common workflows: run linters on pre-commit, enforce commit message format on commit-msg, run tests on pre-push, and validate branch names on pre-receive. Customize templates to match your team's standards, or write hooks from scratch in the built-in editor.

**CROSS-PLATFORM**
Works on macOS, Linux, and Windows (including WSL). Hooks are stored in a portable format and can be exported and shared across teams. JSON output mode enables integration with CI/CD pipelines and automation scripts.

## Key Features

- **Visual dashboard** — see all Git hooks across projects in one place
- **Built-in editor** — create and edit hooks with syntax highlighting
- **Pre-built templates** — lint, test, commit-msg, branch validation, and more
- **Toggle on/off** — enable or disable hooks without deleting them
- **Cross-platform** — macOS, Linux, Windows/WSL
- **Export & share** — portable hook format for team distribution
- **JSON output** — `--json` flag for scripting and CI/CD integration
- **Zero dependencies** — runs locally, no cloud or accounts

## Installation

```bash
pip install git-hook-manager-max
```

Or install from source:

```bash
git clone https://github.com/ericjoye/git-hook-manager-max.git
cd git-hook-manager-max
pip install -e .
```

## Requirements

- **Python:** 3.11+
- **Git:** 2.0+
- **No external dependencies** — stdlib only

## Support

- **Contact:** eric@ericjoye.com
- **GitHub:** https://github.com/ericjoye/git-hook-manager-max
- **Issues:** https://github.com/ericjoye/git-hook-manager-max/issues
- **License:** MIT

## Keywords

git, hooks, git hooks, pre-commit, pre-push, commit-msg, developer tools, devops, cli, python, automation, code quality, linting, testing
