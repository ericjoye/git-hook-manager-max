# git-hook-manager-max

A visual Git hook manager CLI. Create, edit, and manage git hooks without manual shell scripting.

## Install

```bash
pip install git-hook-manager-max
```

## Usage

```bash
ghm list              # List all hooks
ghm create pre-commit # Create a hook from template
ghm edit pre-commit   # Edit a hook
ghm toggle pre-commit # Enable/disable a hook
ghm templates         # List available templates
ghm init              # Initialize hooks directory
```

## Requirements

Python 3.11+, stdlib only.
