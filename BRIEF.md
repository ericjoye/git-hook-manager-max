# portman — localhost port management CLI

## One-liner
A zero-dependency CLI that finds and kills processes on localhost ports — no more `lsof -i :3000` → `kill -9` → repeat.

## Target user
Full-stack developers, DevOps engineers, and anyone who runs local servers (React, Node, Python, Docker, etc.) and constantly hits "EADDRINUSE" / "port already in use" errors.

## Problem
Every developer wastes minutes per day dealing with stale processes holding ports:
- "Port 3000 is already in use" — what's using it?
- Forgot to Ctrl+C a dev server yesterday
- Docker containers left running
- Zombie Node/Python processes

Current workflow: `lsof -i :3000` → copy PID → `kill -9 12345` → hope you killed the right thing.
On Windows: `netstat -ano | findstr :3000` → `taskkill /PID 12345 /F` — even worse.

No dedicated, polished CLI tool exists. Developers cobble together shell aliases.

## Why now
- AI coding agents (Claude Code, Codex, Cursor) spin up servers automatically and leave them running
- Microservice development means more concurrent local servers than ever
- The rise of `pnpm dev`, `next dev`, `vite`, `turbo dev` — more dev servers, more conflicts

## MVP scope (buildable in <1 hour, zero paid deps)

1. `portman list` — show all listening ports with process names and PIDs (cross-platform)
2. `portman kill <port>` — find and kill the process on a given port, with confirmation
3. `portman kill --all` — kill all known dev server ports (3000, 3001, 5000, 8000, 8080, etc.)
4. `portman find <port>` — show what's using a port without killing it
5. `portman free <port>` — check if a port is available
6. `portman config` — manage a `~/.portmanrc` with custom port presets and ignore lists

## Tech approach
- **Language**: Python 3.11+ (stdlib only for core; `psutil` as optional pip dep for better cross-platform support)
- **Cross-platform**: macOS, Linux, Windows (WSL native)
- **No API keys, no cloud, no accounts** — runs entirely locally
- **Install**: `pip install portman-cli` or `brew install portman`
- **Entry point**: `portman` CLI via `pyproject.toml` scripts

## Monetization
- **Free tier**: All core commands (list, kill, find, free, config)
- **Pro tier** ($5/mo or $48/yr):
  - `portman team` — shared port registry so teammates don't collide on the same ports
  - `portman ci` — GitHub Actions integration that detects port conflicts in PRs
  - `portman watch` — background daemon that auto-kills stale processes after N minutes of inactivity
  - `portman history` — track which projects use which ports over time
- **Distribution**: npm (`npx portman`), pip, brew, standalone binary (PyInstaller)

## Risks
1. **Too simple** — might be seen as "just a shell alias." Mitigation: polish the UX (colors, tables, confirmation prompts, `--json` output) so it feels like a real tool.
2. **Platform differences** — `lsof` vs `netstat` vs `Get-NetTCPConnection`. Mitigation: use `psutil` as the abstraction layer.
3. **Existing alternatives** — `fkill`, `kill-port` (npm), shell aliases. Mitigation: portman is purpose-built for localhost dev ports with a better UX and team features.
4. **Low willingness to pay** — developers expect CLI tools to be free. Mitigation: the free tier is fully functional; team/CI features are the paid upsell.

## Definition of done for the MVP
- [ ] `portman list` works on macOS, Linux, and Windows
- [ ] `portman kill <port>` finds and kills the process with a confirmation prompt
- [ ] `portman find <port>` shows process info without killing
- [ ] `portman free <port>` returns exit code 0 (free) or 1 (in use)
- [ ] `~/.portmanrc` config file with custom presets
- [ ] `--json` flag on all commands for scripting
- [ ] `pyproject.toml` with proper entry point
- [ ] `pip install -e .` works locally
- [ ] README with install instructions and examples
