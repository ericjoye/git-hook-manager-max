# Screenshots — git-hook-manager-max

**Product:** git-hook-manager-max — A CLI tool for managing Git hooks with maximum features.

**Type:** CLI Tool (Python/Node)

---

## Screenshot 1: Main Interface — Hook List Overview

**What to capture:** Terminal showing the main command listing all configured git hooks with their status (enabled/disabled).

**Terminal Output Mockup:**

```
$ ghm list

──────────────────────────────────────────────
  git-hook-manager-max v1.0.0
  Repo: ~/projects/my-app
──────────────────────────────────────────────

  📋 Configured Hooks:

  ┌──────────────────┬──────────┬─────────────────────────┐
  │ Hook             │ Status   │ Description             │
  ├──────────────────┼──────────┼─────────────────────────┤
  │ pre-commit       │ ✅ On    │ Lint + format check     │
  │ pre-push         │ ✅ On    │ Run test suite          │
  │ commit-msg       │ ✅ On    │ Conventional commits    │
  │ post-merge       │ ✅ On    │ Auto-install deps       │
  │ post-checkout    │ ❌ Off   │ Branch name validation  │
  │ pre-rebase       │ ❌ Off   │ Prevent main rebase     │
  │ prepare-commit   │ ✅ On    │ Insert template         │
  └──────────────────┴──────────┴─────────────────────────┘

  5 active · 2 disabled · 7 total
──────────────────────────────────────────────
```

---

## Screenshot 2: Key Feature — Adding a Hook

**What to capture:** Terminal showing the interactive hook creation process.

**Terminal Output Mockup:**

```
$ ghm add pre-commit

  Creating hook: pre-commit

  Select template:
  > 1. Lint + Format (ESLint + Prettier)
    2. Type Check (TypeScript)
    3. Test (Jest)
    4. Security Scan (gitleaks)
    5. Custom command

  Choice: 1

  ✓ Created .git/hooks/pre-commit
  ✓ Registered in .ghm/config.yaml
  ✓ Hook is active

  Run `ghm test pre-commit` to verify.
```

---

## Screenshot 3: Configuration File

**What to capture:** Terminal showing the `.ghm/config.yaml` file contents with all hook configurations.

**Terminal Output Mockup:**

```
$ ghm config show

  ── .ghm/config.yaml ──

  version: "1.0"
  hooks:
    pre-commit:
      enabled: true
      commands:
        - name: "ESLint"
          run: "npx eslint --fix ."
          fail_on_error: true
        - name: "Prettier"
          run: "npx prettier --check ."
          fail_on_error: false

    pre-push:
      enabled: true
      commands:
        - name: "Test Suite"
          run: "npm test"
          fail_on_error: true
          timeout: 120

    commit-msg:
      enabled: true
      commands:
        - name: "Conventional Commits"
          run: "npx commitlint --edit"
          fail_on_error: true

    post-merge:
      enabled: true
      commands:
        - name: "Auto-install"
          run: "npm install"
          fail_on_error: false
```

---

## Screenshot 4: Results — Hook Execution Output

**What to capture:** Terminal showing a git commit being intercepted by a hook with pass/fail results.

**Terminal Output Mockup:**

```
$ git commit -m "feat: add user authentication"

──────────────────────────────────────────────
  🔧 Running pre-commit hooks...
──────────────────────────────────────────────

  ✅ ESLint — No issues found (2.1s)
  ✅ Prettier — All files formatted (1.4s)

──────────────────────────────────────────────
  ✅ All hooks passed — committing...
──────────────────────────────────────────────

  [main a1b2c3d] feat: add user authentication
   3 files changed, 45 insertions(+), 12 deletions(-)
```

---

## Notes for Actual Screenshots

1. **Use a dark terminal theme** with colored output (green ✅, red ❌)
2. **Table formatting** for the hook list is a key visual
3. **Show the config file** in a clean YAML format
4. **Hook execution** should show timing and pass/fail clearly
5. **Use realistic hook names** (ESLint, Prettier, TypeScript, Jest)
6. **Font:** Monospace with good syntax highlighting
7. **Show the `.ghm/` directory** in the project structure
8. **Error case** could be a bonus screenshot showing a failed hook
